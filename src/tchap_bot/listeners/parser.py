from src.tchap_bot.config import bot
import simplematrixbotlib as botlib
from src.make_data.clean_conv import clean_conv
from src.grist.add_to_table import add_to_veille
import os 

no_grist="no Grist"

@bot.listener.on_message_event
async def msg_to_Grist(room, message):
    match = botlib.MessageMatch(os.environ["TCHAP_ROOM_ID"], message, bot)

    if match.is_not_from_this_bot() and (match.contains("href") or match.contains("http")) and not match.contains(no_grist):

        res_msg = add_to_veille(clean_conv(match.event))

        await bot.api.send_reaction(
            room_id=os.environ["TCHAP_ROOM_ID"],
            event=message,
            key="🔗"
        )

        await bot.api.send_text_message(
            room_id=room.room_id,
            message=f"I added your message to Grist at row {res_msg}.",
            reply_to=match.event.event_id
        )

    if match.is_not_from_this_bot() and match.contains(no_grist):
        await bot.api.send_reaction(
            room_id=os.environ["TCHAP_ROOM_ID"],
            event=message,
            key="❌")
