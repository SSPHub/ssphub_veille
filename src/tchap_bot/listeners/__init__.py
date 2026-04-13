import importlib
import pkgutil
from pathlib import Path
import simplematrixbotlib as botlib
from ..core.room_filter import RoomFilter


def load_all(bot: botlib.Bot, room_filter: RoomFilter, prefix: str) -> None:
    package_dir = Path(__file__).parent
    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        module = importlib.import_module(f"src.tchap_bot.listeners.{module_name}")
        if hasattr(module, "register"):
            module.register(bot, room_filter, prefix)
            print(f"  ✔ Loaded listener: {module_name}")
