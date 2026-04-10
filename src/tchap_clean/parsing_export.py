import json


def parse_json(file_path):
    """
    Function to parse a Tchap exported conversation (as a json) 

    Args:
        file_path (string): path to the json file to parse

    Returns:
        List of all messages parsed. Each message is an item of the list stored as a dictionnary

    Example:
        >>> parse_json("export.json")
        [{'body': 'ici un message',
        'event_id': '$1771513608349875nfPuD:agent.finances.tchap.gouv.fr',
        'origin_server_ts': 1771517808130,
        'sender': '@agent1.fr:agent.finances.tchap.gouv.fr',
        'room_id': 'idroom:agent.finances.tchap.gouv.fr'},
    """

    with open(file_path, mode='r') as read_file:
        conv_tchap = json.load(read_file)

    extracted_conv = []
    for record in conv_tchap["messages"]:
        extracted_msg = {
            "body": record["content"].get("body", ""),  # To return "" when key not found
            # "formatted_body": record["content"].get("formatted_body", ""),  # To return "" when key not found
            "event_id": record["event_id"],
            "origin_server_ts": record["origin_server_ts"],
            "sender": record["sender"],
            "room_id": record["room_id"]
        }

        extracted_conv.append(extracted_msg)

    return extracted_conv


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


def parse(file_or_event):
    if type(file_or_event) is str:
        return parse_json(file_or_event)
    else:
        return parse_tchap_message(file_or_event)