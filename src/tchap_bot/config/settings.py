import os
from dataclasses import dataclass
from tchap_bot.core.room_filter import FilterMode

@dataclass(frozen=True)
class Creds:
    homeserver: str
    username: str
    password: str
    prefix: str
    filter_mode: FilterMode
    room_ids: list[str]
    session_stored_file: str


class Config:
    emoji_verify: bool
    emoji_verify: bool
    emoji_verify: bool


def load_creds() -> Creds:
    raw_ids = os.getenv("ROOM_IDS", "")
    return Creds(
        homeserver="https://matrix.agent.finances.tchap.gouv.fr",
        username=os.environ["TCHAP_BOT_SSPHUB_MATRIX_ID"],
        password=os.environ["TCHAP_BOT_SSPHUB_PWD"],
        prefix=os.getenv("BOT_PREFIX", "!"),
        filter_mode=FilterMode[os.getenv("ROOM_FILTER_MODE", "DISABLED")],
        room_ids=[r.strip() for r in raw_ids.split(",") if r.strip()],
        session_stored_file="session.txt"
    )


def load_config() -> Config:
    return Config(
        emoji_verify=True,
        ignore_unverified_devices=True,
        encryption_enabled=True
    )
