from .config.settings import load_all
from .core.bot import create_bot
from .core.room_filter import RoomFilter
from .listeners import load_all as load_all_listeners


def run(prefix: str, filter_mode: str):
    creds, config, settings = load_all(prefix, filter_mode)

    room_filter = RoomFilter(
        mode=settings.filter_mode,
        room_ids=settings.room_ids,
    )

    print(f"Filter mode is {settings.filter_mode.value} with authorized list : {settings.room_ids}")

    bot = create_bot(creds, config)

    print("Loading listeners...")
    load_all_listeners(bot, room_filter, settings.prefix)

    print("Starting bot...")
    bot.run()
