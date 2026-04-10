from datetime import datetime
from zoneinfo import ZoneInfo
from src.tchap_bot.config import bot
import simplematrixbotlib as botlib

@bot.listener.on_message_event
async def echo(room, message):
    match = botlib.MessageMatch(room, message, bot)

    if match.is_not_from_this_bot() and match.command("coucou"):
        await bot.api.send_text_message(
            room.room_id,
            f"Coucou, il est {datetime.now(ZoneInfo('Europe/Paris')).strftime('%H:%M:%S')} à Paris."
        )
