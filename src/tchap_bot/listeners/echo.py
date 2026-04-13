from datetime import datetime
from zoneinfo import ZoneInfo
import simplematrixbotlib as botlib
from ..core.room_filter import RoomFilter

def register(bot: botlib.Bot, room_filter: RoomFilter, prefix: str) -> None:
    @bot.listener.on_message_event
    async def echo(room, message):
        if not room_filter.allows(room.room_id):
            return
        else:
            match = botlib.MessageMatch(room, message, bot)

            if match.is_not_from_this_bot() and match.command("coucou"):
                await bot.api.send_text_message(
                    room.room_id,
                    f"Coucou, il est {datetime.now(ZoneInfo('Europe/Paris')).strftime('%H:%M:%S')} à Paris."
                )
