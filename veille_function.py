import json
import pandas as pd
import polars as pl
from datetime import datetime, timedelta
import re  # to extract link
from grist_api import GristDocAPI  # To write into grist doc
import os

# Regular expression to identify hyperlinks in Markdown format
pattern = r'\[([^\]]+)\]\(([^)]+)\)'

# Function to extract the hyperlink
def extract_link(text):
    """
    Function to extract a link, formatted in Markodwn or plain text, from a string

    Args:
        text (string): text where to look for the link
    
    Returns:
        None if nothing found
        Url link (string) if found
    
    Example:
        >>> extract_link('https://www.tjis_is_my_link.fr')
        'https://www.tjis_is_my_link.fr'
        >>> extract_link('[a link](https://www.tjis_is_my_link.fr)')
        'https://www.tjis_is_my_link.fr'
    """
    match = re.search(pattern, text)
    if match:
        return match.group(2)
    else:
        # Check if the text itself is a URL
        if re.match(r'^https?://\S+$', text):
            return text
        return None


# Function to extract the link text
def extract_link_text(text):
    """
    Function to the text of a link if formatted in Markodwn, from a string

    Args:
        text (string): text where to look for the link
    
    Returns:
        None if nothing found
        Url link (string) if found
    
    Example:
        >>> extract_link_text('https://www.tjis_is_my_link.fr')
        None
        >>> extract_link_text('[a link](https://www.tjis_is_my_link.fr)')
        'a link'
    """
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None

def convert_unix_time(time_as_int):
    """
    Convert time from timestamp (ie seconds) to standard date

    Args:
        time_as_int (int): nix time, with either 10 or 13 digits

    Returns:
        date (string) format ("%Y-%m-%d %H:%M")

    Example:
        >>> convert_unix_time(1760297400000)
        '2025-10-12 21:30'
        >>> convert_unix_time(1760297400)
        '2025-10-12 21:30'
    """
    time_as_int = int(time_as_int)

    if time_as_int >= 1e12:
        time_as_int = time_as_int / 1000

    time = datetime.fromtimestamp(time_as_int) + timedelta(hours=+2)
    return time.strftime("%Y-%m-%d %H:%M")


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
    with open(file_path, mode = 'r') as read_file:
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
                msg_link = 'https://tchap.gouv.fr/#/room/' + pl.col('room_id') + '/' + pl.col('event_id'),  # Creating link to tchap msg
                # Who sent the message
                sender = pl.col('sender').str.extract(pattern=r'@(.*?)-')  # Turn @prenom.nom-insee.frBLABLA into prenom.nom
                                        .str.replace(r'\.', ' ')  # Turn prenom.nom into prenom nom
                                        .str.to_titlecase(),  # Turn prenom nom into Prenom Nom
                hyperlink = pl.col('body').map_elements(lambda x: extract_link(x)),  # Extract hyperlink : [my_link](https://mylink) -> https://mylink
                link_text = pl.col('body').map_elements(lambda x: extract_link_text(x))  # Extract hyperlink title or text : [my_link](https://mylink) -> my_link
            )
            .drop_nulls(subset='hyperlink')
            .with_columns(
                body = pl.when(pl.col('body') == pl.col('hyperlink')).then(None).otherwise('body'),  # If message is only a link, set body to ''
                origin_server_ts = pl.col("origin_server_ts") // 1000  ## Changing time format from 13 to 10 digts
            )
    )

    cols_to_keep = ['link_text', 'hyperlink', 'sender', 'msg_link', 'body', 'origin_server_ts']

    func_conv_df = func_conv_df.select(cols_to_keep)

    # Removing identical hyperlinks
    func_conv_df = func_conv_df.unique('hyperlink', keep='first')
    
    # Removing body of the message if just an hyperlink (body='[title](hyperlink)')
    func_conv_df = func_conv_df.with_columns(body=pl.when(pl.col.body=="["+pl.col.link_text+"]("+pl.col.hyperlink+")").then(pl.lit('')).otherwise(pl.col.body))

    return func_conv_df


def get_grist_api():
    """
    Get GRIST API credentials

    Args:
        None

    Returns:
        A grist API

    Example:
        >>> get_grist_api()
    """
    # Log in to GRIST API
    SERVER = "https://grist.numerique.gouv.fr/"
    DOC_ID = os.environ['GRIST_VEILLE_DOC_ID']

    if 'GRIST_API_KEY' not in os.environ:
        raise ValueError("The GRIST_API_KEY environment variable does not exist.")

    # Returning API details connection
    return GristDocAPI(DOC_ID, server=SERVER)


def download_table(table_id='Test'):
    """
    Fetch data from a Grist table

    Args:
        The grist table id
        

    Returns:
        the table from Grist as a Polars DataFrame

    Example:
    """
    return pl.DataFrame(get_grist_api().fetch_table(table_id))


def add_to_veille(my_conv_df, target_table='Test'):
    """
    add a dataframe to Veille grist table

    Args:
        a polars dataframe with records to updated to Veille grist table.
        Column names will be renamed to match target table column names.

    Returns:
        the records that have been added to table

    Example:
    """
    # Rename
    # Dictionnary for renaming variables / Right part must correspond to template keywords
    variable_mapping = {
            'link_text': 'Titre_article',
            'hyperlink': 'Lien_article',
            'sender': 'Qui_a_propose',
            'msg_link': 'Quel_chanel',
            'body': 'Resume',
            'origin_server_ts': 'Date'
    }
    my_conv_df = (my_conv_df
        .rename(variable_mapping)
        .sort('Date')
    )
    
    # Export as dict to export to Grist
    my_conv_dict = my_conv_df.to_dicts()
    res = get_grist_api().add_records(target_table, my_conv_dict)

    return f'{len(res)} records have been added to the {target_table} table, from row {res[0]} to {res[-1]}' 


def extract_and_add_to_veille(input_conv_file_path = 'ssphub_veille/export.json', min_time="2025-10-15", time_format_date=True, target_table='Test'):
    """
    wrapper to extract from a json Tcahp file and add records to Veille table.

    Args:
        input_conv_file_path (string) : ath to json file that has been extracted from Tchap
        min_time (int or date) : threshold date. Rows with date before that date will be skipped
        time_format_date (bool): if min_time is a string ('2025-01-01') or unix code

    Returns:
        the records that have been added to table

    Example:
    """
    # Clean the conversation
    my_conv_df = clean_conv(input_conv_file_path)

    # If date is a date formet (2025-01-01), we convert it to timestamp
    if time_format_date:
        min_time = datetime.strptime(min_time, "%Y-%m-%d").timestamp()
  
    my_conv_df = (
        my_conv_df\
            .filter(pl.col('origin_server_ts') >= min_time)  # Filter date
            .with_columns(
                pl.col('origin_server_ts').map_elements(lambda x: convert_unix_time(x)),   # Convert from Unix time to human readable time
                Add_records=True 
            )
    )

    return add_to_veille(my_conv_df, target_table)


def extract_max_date(target_table='Veille'):
    """
    Extract max_date from Veille grist table 

    Args:
        None

    Returns:
        max date of the column as unix date

    Example:
        >>> extract_max_date()
        array([[1.7602974e+09]])
    """
    df = pl.DataFrame(get_grist_api().fetch_table(target_table))
    max = df.filter(pl.col('Add_records') == True).select(pl.max('Date')).to_numpy()[0,0]

    return int(max)

