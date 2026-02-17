import os

import polars as pl
import requests
from grist_api import GristDocAPI  # To write into grist doc


class GristApi:
    def __init__(self, doc_id=os.environ["GRIST_VEILLE_DOC_ID"]):
        if "GRIST_API_KEY" not in os.environ:
            raise ValueError("The GRIST_API_KEY environment variable does not exist.")

        self.base_url = "https://grist.numerique.gouv.fr/api"

        self.doc_url = f"{self.base_url}/docs"

        self.table_url = f"{self.doc_url}/{doc_id}/tables"

        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {os.environ['GRIST_API_KEY']}",
            "Content-Type": "application/json",
        }

    def fetch_table(self, table_id, **kwarg):
        response = requests.get(
            f"{self.table_url}/{table_id}/records", headers=self.headers, **kwarg
        )
        return response

    def add_records(self, table_id, **kwarg):
        response = requests.post(
            f"{self.table_url}/{table_id}/records", headers=self.headers, **kwarg
        )
        return response


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
    DOC_ID = os.environ["GRIST_VEILLE_DOC_ID"]

    if "GRIST_API_KEY" not in os.environ:
        raise ValueError("The GRIST_API_KEY environment variable does not exist.")

    # Returning API details connection
    return GristDocAPI(DOC_ID, server=SERVER)


def add_records(table_id, data_list):
    if "GRIST_API_KEY" not in os.environ:
        raise ValueError("The GRIST_API_KEY environment variable does not exist.")

    SERVER = "https://grist.numerique.gouv.fr"
    DOC_ID = os.environ["GRIST_VEILLE_DOC_ID"]

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.environ['GRIST_API_KEY']}",
        "Content-Type": "application/json",
    }

    data_json = {
        "records": data_list,
    }

    r = requests.post(
        f"{SERVER}/api/docs/{DOC_ID}/Tables/{table_id}/records",
        headers=headers,
        json=data_json,
    )

    return r


def download_table(table_id="Test"):
    """
    Fetch data from a Grist table

    Args:
        The grist table id


    Returns:
        the table from Grist as a Polars DataFrame

    Example:
    """
    return pl.DataFrame(get_grist_api().fetch_table(table_id), infer_schema_length=None)


class GristApi:
    def __init__(self, doc_id=os.environ["GRIST_VEILLE_DOC_ID"]):
        if "GRIST_API_KEY" not in os.environ:
            raise ValueError("The GRIST_API_KEY environment variable does not exist.")

        self.base_url = "https://grist.numerique.gouv.fr/api"

        self.doc_url = f"{self.base_url}/docs"

        self.table_url = f"{self.doc_url}/{doc_id}/tables"

        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {os.environ['GRIST_API_KEY']}",
            "Content-Type": "application/json",
        }

    def fetch_table(self, table_id, **kwarg):
        response = requests.get(
            f"{self.table_url}/{table_id}/records", headers=self.headers, **kwarg
        )
        return response

    def add_records(self, table_id, **kwarg):
        response = requests.post(
            f"{self.table_url}/{table_id}/records", headers=self.headers, **kwarg
        )
        return response
