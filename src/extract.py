import polars as pl

from src.data.clean_conv import clean_conv
from src.data.formatting_time import convert_unix_time
from src.utils.access_grist_api import GristApi
from src.utils.logging import setup_logging

# Regular expression to identify hyperlinks in Markdown format
pattern = r"\[([^\]]+)\]\(([^)]+)\)"


def add_to_veille(my_conv_df, target_table="Test", logger=setup_logging()):
    """
    add a dataframe to Veille grist table

    Args:
        a polars dataframe with records to update to Veille grist table.
        Column names will be renamed to match target table column names.

    Returns:
        the records that have been added to table

    Example:
        >>> add_to_veille(............, target_table='Test')
    """
    # Rename
    # Dictionnary for renaming variables / Right part must correspond to template keywords
    variable_mapping = {
        "link_text": "Titre_article",
        "hyperlink": "Lien_article",
        "msg_link": "Quel_chanel",
        "body": "Message",
        "origin_server_ts": "Date",
    }

    new_msg_df = my_conv_df.rename(variable_mapping).sort("Date")

    # Export as dict to export to Grist
    logger.info("Début de l'export de la table vers Grist")

    new_msg_dict = (
        new_msg_df.with_columns(pl.struct(new_msg_df.columns).alias("fields"))
        .select("fields")
        .to_dicts()
    )

    new_msg_json = {
        "records": new_msg_dict,
    }

    res = GristApi().add_records(target_table, json=new_msg_json)
    res = res.json().get("records", "")

    if len(res) == 0:
        res_msg = f"No record has been added to the {target_table} table"
    else:
        res_msg = f"{len(res)} records have been added to the {target_table} table, from id {res[0]['id']} to {res[-1]['id']}"

    logger.info(f"{res_msg}")

    logger.info("Fin de l'export de la table vers Grist")
    return res_msg


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
        f"Conversation transformée en table Grist, nombre de liens : {len(my_conv_df)}\nConversation propre (table my_conv_df):\n{my_conv_df}"
    )

    # Download data to filter new urls
    logger.info(f"Début du téléchargement de la table Grist cible {target_table}")
    old_conv_df = (
        GristApi().fetch_table_pl(table_id=target_table).select("Lien_article").unique()
    )
    logger.info(
        f"Table Grist cible {target_table} téléchargée, nombre de lignes : {len(old_conv_df)}\nTable cible téléchargée (table old_conv_df):\n{old_conv_df}"
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
    logger.info(f"Nombre de lignes après filtre liens déjà présents: {len(my_conv_df)}\nTable finale à ajouter (table my_conv_df):\n{my_conv_df}")

    return add_to_veille(my_conv_df, target_table)
