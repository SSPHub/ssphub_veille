import json
import pandas as pd
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
        A dataframe (pd.Df) with columns : ['link_text', 'hyperlink', 'sender', 'msg_link', 'body', 'origin_server_ts']

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
    func_conv_df = pd.DataFrame(extracted_conv)

    # Tchap Link
    func_conv_df['msg_link'] = 'https://tchap.gouv.fr/#/room/' + func_conv_df['room_id'] + '/' + func_conv_df['event_id']  

    # Who sent the message
    func_conv_df['sender'] = (func_conv_df['sender'].str.removeprefix('@')
                                                .str.rpartition('-').iloc[:, 0]
                                                .str.replace('.', ' ')
                                                .str.title()
                            )


    # Extract href
    func_conv_df['hyperlink'] = func_conv_df['body'].apply(extract_link)
    func_conv_df['link_text'] = func_conv_df['body'].apply(extract_link_text)
    func_conv_df.dropna(subset='hyperlink', inplace=True)

    # Changing time format to 10 digts
    func_conv_df['origin_server_ts'] = func_conv_df['origin_server_ts'] // 1000

    cols_to_keep = ['link_text', 'hyperlink', 'sender', 'msg_link', 'body', 'origin_server_ts']

    func_conv_df = func_conv_df[cols_to_keep]

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


def convert_unix_time_df(df):
    """
    Convert unix time to date time

    Args:
        a dataframe with a column named "origin_server_ts"

    Returns:
        the df with origin_server_ts column parsed to date

    Example:
    """
    df['origin_server_ts'] = df['origin_server_ts'].apply(convert_unix_time)

    return df


def add_to_veille(my_conv_df):
    """
    add a dataframe to Veille grist table

    Args:
        a dataframe with records to updated to Veille grist table.
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
    my_conv_df.rename(columns=variable_mapping, inplace=True)

    # Export as dict to export to Grist
    my_conv_dict = my_conv_df.to_dict(orient='records')
    get_grist_api().add_records('Veille', my_conv_dict)


def extract_and_add_to_veille(input_conv_file_path, min_time=0, time_format_date=True):
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

    # Filter date
    my_conv_df = my_conv_df[my_conv_df['origin_server_ts'] >= min_time]

    # Convert time
    my_conv_df = convert_unix_time_df(my_conv_df)

    add_to_veille(my_conv_df)


def extract_max_date():
    """
    Extract max_date from Veille grist table 

    Args:
        None

    Returns:
        max date of the column as unix date

    Example:
        >>> extract_max_date()
        np.float64(1760356956.975651)
    """
    return pd.DataFrame(get_grist_api().fetch_table('Veille'))['Date'].max()


