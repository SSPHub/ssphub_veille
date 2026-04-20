import asyncio
import os
from datetime import datetime, timezone

from nio import AsyncClient, LoginResponse, RoomMessagesResponse
from nio.events.room_events import RoomMessage

_HOMESERVER = "https://matrix.agent.finances.tchap.gouv.fr"
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


def _format_event(event: RoomMessage, room_id: str) -> dict:
    return {
        "event_id": event.event_id,
        "room_id": room_id,
        "sender": event.sender,
        "timestamp_ms": event.server_timestamp,
        "datetime_utc": datetime.fromtimestamp(
            event.server_timestamp / 1000, tz=timezone.utc
        ).isoformat(),
        "msgtype": event.msgtype,
        "body": event.body,
    }


async def _fetch(room_id: str, limit: int) -> list[dict]:
    username = os.environ["TCHAP_BOT_SSPHUB_MATRIX_ID"]
    password = os.environ["TCHAP_BOT_SSPHUB_PWD"]

    client = AsyncClient(_HOMESERVER, username)
    try:
        resp = await client.login(password)
        if not isinstance(resp, LoginResponse):
            raise RuntimeError(f"Login failed: {resp}")

        sync_resp = await client.sync(
            timeout=15000,
            full_state=False,
            sync_filter=_SYNC_FILTER,
        )

        room_sync = sync_resp.rooms.join.get(room_id)
        if room_sync is None:
            join_resp = await client.join(room_id)
            if (
                hasattr(join_resp, "transport_response")
                and join_resp.transport_response.status >= 400
            ):
                raise RuntimeError(f"Could not join room {room_id}: {join_resp}")
            sync_resp = await client.sync(
                timeout=15000,
                full_state=False,
                sync_filter=_SYNC_FILTER,
            )
            room_sync = sync_resp.rooms.join.get(room_id)
            if room_sync is None:
                raise RuntimeError(f"Room {room_id} not found after join")

        messages: list[dict] = []

        for event in reversed(room_sync.timeline.events):
            if isinstance(event, RoomMessage):
                messages.append(_format_event(event, room_id))

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
                if isinstance(event, RoomMessage):
                    messages.append(_format_event(event, room_id))
            if not page.end or page.end == current_token:
                break
            current_token = page.end

        messages.sort(key=lambda m: m["timestamp_ms"])
        return messages[-limit:]

    finally:
        await client.logout()
        await client.close()


def fetch_messages(room_id: str, limit: int = 100) -> list[dict]:
    """Fetch the last `limit` messages from a Tchap/Matrix room.

    Requires env vars:
      TCHAP_BOT_SSPHUB_MATRIX_ID  - bot Matrix user ID
      TCHAP_BOT_SSPHUB_PWD        - bot password

    Returns a list of message dicts sorted oldest-first.
    """
    return asyncio.run(_fetch(room_id, limit))
