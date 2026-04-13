import os
from dataclasses import dataclass
from ..core.room_filter import FilterMode

@dataclass(frozen=True)
class Creds:
    homeserver: str
    username: str
    password: str
    session_stored_file: str


@dataclass(frozen=True)
class BotConfig:
    emoji_verify: bool
    ignore_unverified_devices: bool
    encryption_enabled: bool


@dataclass(frozen=True)
class Settings: 
    prefix: str
    filter_mode: FilterMode
    room_ids: list[str]
    no_grist: str


def load_all():
    return load_creds(), load_config(), load_settings()


def load_creds() -> Creds:
    return Creds(
        homeserver="https://matrix.agent.finances.tchap.gouv.fr",
        username=os.environ["TCHAP_BOT_SSPHUB_MATRIX_ID"],
        password=os.environ["TCHAP_BOT_SSPHUB_PWD"],
        session_stored_file="session.txt"
    )


def load_config() -> BotConfig:
    return BotConfig(
        emoji_verify=True,
        ignore_unverified_devices=True,
        encryption_enabled=True
    )


def load_settings() -> Settings:
    raw_ids = os.getenv("ROOM_IDS", "")
    return Settings(
        prefix=os.getenv("BOT_PREFIX", "!"),
        filter_mode=FilterMode[os.getenv("ROOM_FILTER_MODE", "DISABLED")],
        room_ids=[r.strip() for r in raw_ids.split(",") if r.strip()],
        no_grist="no Grist"
    )
