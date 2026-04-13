import simplematrixbotlib as botlib
from ...make_data.clean_conv import clean_conv
from ...grist.add_to_table import add_to_veille
from ..core.room_filter import RoomFilter
from ..config.settings import load_settings


no_grist = load_settings().no_grist


def register(bot: botlib.Bot, room_filter: RoomFilter, prefix: str) -> None:
    @bot.listener.on_message_event
    async def msg_to_Grist(room, message):
        if not room_filter.allows(room.room_id):
            return
        
        match = botlib.MessageMatch(room, message, bot)

        if match.is_not_from_this_bot() and (match.contains("href") or match.contains("http")) and not match.contains(no_grist):

            res_msg = add_to_veille(clean_conv(match.event))

            await bot.api.send_reaction(
                room_id=room.room_id,
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
                room_id=room.room_id,
                event=message,
                key="❌")
