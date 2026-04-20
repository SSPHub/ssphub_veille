import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from nio import AsyncClient, AsyncClientConfig, LoginResponse, RoomMessagesResponse
from nio.events.room_events import MegolmEvent, RoomMessage
from nio.exceptions import EncryptionError

_HOMESERVER = "https://matrix.agent.finances.tchap.gouv.fr"
_DEFAULT_STORE = Path.home() / ".local" / "share" / "tchap_agent" / "store"

_SYNC_FILTER = {
    "room": {
        "timeline": {"limit": 50},
        "state": {"types": []},
        "ephemeral": {"types": []},
        "account_data": {"types": []},
    },
    "presence": {"types": []},
    "account_data": {"types": []},
}


def _format_event(event, room_id: str) -> dict:
    return {
        "event_id": event.event_id,
        "room_id": room_id,
        "sender": event.sender,
        "timestamp_ms": event.server_timestamp,
        "datetime_utc": datetime.fromtimestamp(
            event.server_timestamp / 1000, tz=timezone.utc
        ).isoformat(),
        "msgtype": getattr(event, "msgtype", None),
        "body": getattr(event, "body", None),
    }


def _try_add(client: AsyncClient, event, room_id: str, out: list) -> None:
    """Append a formatted message dict if the event is a readable text message."""
    if isinstance(event, MegolmEvent):
        decrypted = client.decrypt_event(event)
        if isinstance(decrypted, EncryptionError):
            # Missing session keys (forward secrecy / bot wasn't present) — skip
            return
        event = decrypted
    if isinstance(event, RoomMessage):
        out.append(_format_event(event, room_id))


async def _fetch(room_id: str, limit: int, store_path: Path) -> list[dict]:
    username = os.environ["TCHAP_BOT_SSPHUB_MATRIX_ID"]
    password = os.environ["TCHAP_BOT_SSPHUB_PWD"]

    store_path.mkdir(parents=True, exist_ok=True)

    config = AsyncClientConfig(
        encryption_enabled=True,
        store_sync_tokens=True,
    )
    client = AsyncClient(
        homeserver=_HOMESERVER,
        user=username,
        store_path=str(store_path),
        config=config,
    )
    try:
        resp = await client.login(password)
        if not isinstance(resp, LoginResponse):
            raise RuntimeError(f"Login failed: {resp}")

        # Sync gives us the room's timeline and the prev_batch pagination token.
        # With encryption_enabled=True, events already in the sync window are
        # decrypted automatically from the in-memory session keys.
        sync_resp = await client.sync(
            timeout=15000,
            full_state=False,
            sync_filter=_SYNC_FILTER,
        )

        room_sync = sync_resp.rooms.join.get(room_id)
        if room_sync is None:
            await client.join(room_id)
            sync_resp = await client.sync(
                timeout=15000,
                full_state=False,
                sync_filter=_SYNC_FILTER,
            )
            room_sync = sync_resp.rooms.join.get(room_id)
            if room_sync is None:
                raise RuntimeError(f"Room {room_id} not found after join")

        messages: list[dict] = []

        # Sync timeline events (already decrypted by matrix-nio when E2E is on)
        for event in room_sync.timeline.events:
            _try_add(client, event, room_id, messages)

        # Paginate backwards via /messages — events here are NOT auto-decrypted,
        # so _try_add calls client.decrypt_event() manually.
        current_token: str | None = room_sync.timeline.prev_batch
        while len(messages) < limit and current_token:
            batch_size = min(100, limit - len(messages))
            page = await client.room_messages(
                room_id=room_id,
                start=current_token,
                limit=batch_size,
                direction="b",
            )
            if not isinstance(page, RoomMessagesResponse) or not page.chunk:
                break
            for event in page.chunk:
                _try_add(client, event, room_id, messages)
            if not page.end or page.end == current_token:
                break
            current_token = page.end

        # /messages returns oldest-first within each page but we collected
        # sync events (newest) first, then paginated backwards (older).
        # Sort everything chronologically and trim to the requested limit.
        messages.sort(key=lambda m: m["timestamp_ms"])
        return messages[-limit:]

    finally:
        await client.logout()
        await client.close()


def fetch_messages(
    room_id: str,
    limit: int = 100,
    store_path: Path = _DEFAULT_STORE,
) -> list[dict]:
    """Fetch the last `limit` messages from a Tchap/Matrix room.

    Requires env vars:
      TCHAP_BOT_SSPHUB_MATRIX_ID  - bot Matrix user ID
      TCHAP_BOT_SSPHUB_PWD        - bot password

    `store_path` persists E2E session keys between runs so that decryption
    succeeds on subsequent calls even for messages from earlier sessions.
    Returns a list of message dicts sorted oldest-first.
    """
    return asyncio.run(_fetch(room_id, limit, store_path))
