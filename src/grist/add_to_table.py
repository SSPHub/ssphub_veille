import polars as pl
from src.utils.access_grist_api import GristApi
from src.utils.logging import setup_logging


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
        "sender": "Qui_a_propose",
        "msg_link": "Quel_chanel",
        "body": "Resume",
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