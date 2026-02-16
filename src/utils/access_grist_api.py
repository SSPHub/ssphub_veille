import polars as pl
from grist_api import GristDocAPI  # To write into grist doc
import os


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
    SERVER = "https://grist.numerique.gouv.fr"
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
    return pl.DataFrame(get_grist_api().fetch_table(table_id), infer_schema_length=None)