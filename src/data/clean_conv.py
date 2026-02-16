import json
import polars as pl
from src.data.formatting_link import (
    extract_link, 
    extract_link_text
)

# Regular expression to identify hyperlinks in Markdown format
pattern = r'\[([^\]]+)\]\(([^)]+)\)'


def clean_conv(file_path):
    """
    Converts a json file extracted from Tchap to a database.

    Args:
        file_path (string): path to json file to convert.

    Returns:
        A dataframe (pl.Df) with columns : ['link_text', 'hyperlink', 'sender', 'msg_link', 'body', 'origin_server_ts']

    Example:
        >>> clean_conv('matrix - SSPLab - Veille - Chat Export - 2025-10-13T12-19-53.163Z.json')
                                                     link_text  ... origin_server_ts
        6    Linux a sa réponse à Microsoft Copilot, et ell...  ...       1754574677
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

    # Create a DataFrame
    func_conv_df = pl.DataFrame(extracted_conv)

    # Streamlining data
    func_conv_df = (
        func_conv_df\
            .with_columns(
                msg_link='https://tchap.gouv.fr/#/room/' + pl.col('room_id') + '/' + pl.col('event_id'),  # Creating link to tchap msg
                # Who sent the message
                sender=pl.col('sender').str.extract(pattern=r'@(.*?)-')  # Turn @prenom.nom-insee.frBLABLA into prenom.nom
                                        .str.replace(r'\.', ' ')  # Turn prenom.nom into prenom nom
                                        .str.to_titlecase(),  # Turn prenom nom into Prenom Nom
                hyperlink=pl.col('body').map_elements(lambda x: extract_link(x)),  # Extract hyperlink : [my_link](https://mylink) -> https://mylink
                link_text=pl.col('body').map_elements(lambda x: extract_link_text(x))  # Extract hyperlink title or text : [my_link](https://mylink) -> my_link
            )
            .drop_nulls(subset='hyperlink')
            .with_columns(
                body=pl.when(pl.col('body') == pl.col('hyperlink')).then(None).otherwise('body'),  # If message is only a link, set body to ''
                origin_server_ts=pl.col("origin_server_ts") // 1000  ## Changing time format from 13 to 10 digts
            )
    )

    cols_to_keep = ['link_text', 'hyperlink', 'sender', 'msg_link', 'body', 'origin_server_ts']

    func_conv_df = func_conv_df.select(cols_to_keep)

    # Removing identical hyperlinks
    func_conv_df = func_conv_df.unique('hyperlink', keep='first')
    
    # Removing body of the message if just an hyperlink (body='[title](hyperlink)')
    func_conv_df = func_conv_df.with_columns(body=pl.when(pl.col.body == "["+pl.col.link_text+"]("+pl.col.hyperlink+")").then(pl.lit('')).otherwise(pl.col.body))

    return func_conv_df