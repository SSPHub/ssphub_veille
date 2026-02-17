import os

import polars as pl
import requests


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
        """
        Wrapper for a GET requests

        Args:
            The grist table id
            Additionnal arguments to pass on to requets.get()

        Returns:
            response from requests.get

        Example:
        >>> GristApi().fetch_table("Test")
        <Response [200]>
        """
        response = requests.get(
            f"{self.table_url}/{table_id}/records", headers=self.headers, **kwarg
        )
        return response

    def fetch_table_pl(self, table_id, **kwarg):
        """
        Fetch data from a Grist table

        Args:
            The grist table id


        Returns:
            the table from Grist as a Polars DataFrame

        Example:
        >>> GristApi().fetch_table_pl("Test")
        """
        return (
            pl.DataFrame(
                self.fetch_table(table_id=table_id, **kwarg).json(),
                infer_schema_length=None,
                strict=False,
            )
            .unnest(columns="records")
            .unnest(columns="fields")
        )

    def add_records(self, table_id, **kwarg):
        """
        Wrapper for a POST requests to add records to a table.
        Records should have a particuliar format to get accepted by GRIST API

        Args:
            The grist table id
            Additionnal arguments to pass on to requets.post()

        Returns:
            response from requests.get

        Example:
        >>> GristApi().add_records("Test", json=data_json)
        <Response [200]>
        """
        response = requests.post(
            f"{self.table_url}/{table_id}/records", headers=self.headers, **kwarg
        )
        return response
