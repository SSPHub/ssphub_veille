from src.tchap_bot.config import bot
import simplematrixbotlib as botlib
from src.make_data.clean_conv import clean_conv
from src.grist.add_to_table import add_to_veille

@bot.listener.on_message_event
async def example(room, message):
    match = botlib.MessageMatch(room, message, bot)

    if match.is_not_from_this_bot() and match.contains('href'):

        res_msg = add_to_veille(clean_conv(match.event))

        await bot.api.send_reaction(
            room_id=room.room_id,
            event=message,
            key="🔗"
        )

        await bot.api.send_text_message(
            room_id=room.room_id,
            message=f"I added your message to Grist.\n Here is the reply:{res_msg}",
            reply_to=match.event.event_id
        )
