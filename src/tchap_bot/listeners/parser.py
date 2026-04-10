from config import bot
import simplematrixbotlib as botlib
# from src.tchap_clean.parsing_export import parse_tchap_message

def parse_tchap_message(event_match):

    extracted_conv = [
        {
            "body": event_match.body,  # To return "" when key not found
            "formatted_body": event_match.formatted_body,  # To return "" when key not found
            "event_id": event_match.event_id,
            "origin_server_ts": event_match.server_timestamp,
            "sender": event_match.sender,
            "room_id": event_match.room_id
        }
    ]

    return extracted_conv


@bot.listener.on_message_event
async def example(room, message):
    match = botlib.MessageMatch(room, message, bot)

    if match.is_not_from_this_bot() and match.contains('href'):
        example_reaction = "✅"
        await bot.api.send_reaction(
            room_id=room.room_id,
            event=message,
            key=example_reaction
        )

        await bot.api.send_text_message(
            room_id=room.room_id,
            message=f"I parsed your message: {parse_tchap_message(match.event)}",
            reply_to=match.event.event_id
        )
