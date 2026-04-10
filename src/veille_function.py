import polars as pl

from src.make_data.clean_conv import clean_conv
from src.data.formatting_time import convert_unix_time
from src.grist.access_grist_api import GristApi
from src.utils.logging import setup_logging
from src.grist.add_to_table import add_to_veille

# Regular expression to identify hyperlinks in Markdown format
pattern = r"\[([^\]]+)\]\(([^)]+)\)"


def extract_and_add_to_veille(
    input_conv_file_path="export.json",
    target_table="Test",
    logger=setup_logging(),
):
    """
    wrapper to extract from a json Tchap file and add records to Veille table.
    Url that are already present in Target table will be discarded when updating the Grist table

    Args:
        input_conv_file_path (string) : path to json file that has been extracted from Tchap
        target_table : Grist table id to update the rows to.

    Returns:
        the records that have been added to table

    Example:
    >>> extract_and_add_to_veille()
    '170 records have been added to the Test table, from row 319 to 488'
    """
    logger.info("Début de la récupération de la veille")
    # Clean the conversation
    my_conv_df = clean_conv(input_conv_file_path)
    logger.info(
        f"Conversation transformée en table Grist, nombre de liens : {len(my_conv_df)}"
    )

    # Download data to filter new urls
    logger.info(f"Début du téléchargement de la table Grist cible {target_table}")
    old_conv_df = (
        GristApi().fetch_table_pl(table_id=target_table).select("Lien_article").unique()
    )
    logger.info(
        f"Table Grist cible {target_table} téléchargée, nombre de lignes : {len(old_conv_df)}"
    )

    # Join new articles in former Grist table
    logger.info("Début de la création de la table Grist finale")
    my_conv_df = my_conv_df.join(
        old_conv_df, left_on="hyperlink", right_on="Lien_article", how="anti"
    ).with_columns(  # To keep only url that are not already present in the Grist table
        pl.col("origin_server_ts").map_elements(
            lambda x: convert_unix_time(x)
        )  # Convert from Unix time to human readable time
    )
    logger.info(f"Nombre de lignes après filtre liens déjà présents: {len(my_conv_df)}")

    return add_to_veille(my_conv_df, target_table)
