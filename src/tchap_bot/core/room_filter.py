from enum import Enum


class FilterMode(Enum):
    ALLOWLIST = "allowlist"
    BLOCKLIST = "blocklist"
    DISABLED = "disabled"


class RoomFilter:
    def __init__(self, mode: FilterMode, room_ids: list[str] = None):
        self.mode = mode
        self.room_ids = set(room_ids or [])

    def allows(self, room_id: str) -> bool:
        if self.mode == FilterMode.DISABLED:
            return True
        if self.mode == FilterMode.ALLOWLIST:
            return room_id in self.room_ids
        if self.mode == FilterMode.BLOCKLIST:
            return room_id not in self.room_ids
            