"""
Once the data has been filled, extract all the "a_garder" and format them in 
markdown format for easier writing.
"""


import polars as pl

from src.utils.access_grist_api import GristApi
from src.utils.logging import setup_logging
from src.data.complete_veille import build_category_ref_maps

from src.data.to_infolettre import create_veille_qmd
from src.utils.config import TABLE_RUBRIQUES, COL_CATEGORY


def extract_rows_qmd(
    input_table="Veille",
    output_path="veille.qmd",
    logger=setup_logging(),
):
    """
    wrapper to extract from the table records a garder, format them into a markdown list 
    and store them as qmd file.

    Args:
        input_table : Grist table id to fetch the rows from.
        output_path (string) : path of the Qmd file to store the results 

    Returns:
        the markdown formatted text

    Example:
    >>> extract_rows_qmd()
    """
    api = GristApi()

    # Download data to filter urls
    logger.info(f"Début du téléchargement de la table Grist cible {input_table}")
    veille_df = (
        api.fetch_table_pl(table_id=input_table)
    )
    logger.info(
        f"Table Grist cible {input_table} téléchargée, nombre de lignes : {len(veille_df)}"
    )

    # Filter new articles in former Grist table
    logger.info("Filtrer les lignes à insérer dans la veille")
    veille_df = (
        veille_df
        .filter(
            pl.col("A_garder"), pl.col("Lien_veille") == ""
        )
    )
    logger.info(f"Nombre de lignes à garder sans veille renseignée: {len(veille_df)}")

    # Update categories with labels and not ids
    logger.info("Remplacement des catégories")
    rubriques_rows = api.fetch_table_pl(TABLE_RUBRIQUES).to_dicts()
    id_to_name, _ = build_category_ref_maps(rubriques_rows)
    veille_df = (
        veille_df
        .explode(COL_CATEGORY)
        .filter(
            pl.col(COL_CATEGORY) != "L"
        )  # droping "L"
        .with_columns(pl.col(COL_CATEGORY).replace(id_to_name))  # renaming
        .sort(by=pl.col(COL_CATEGORY).str.to_lowercase())
        .group_by("id")
        .agg(pl.col(COL_CATEGORY))
        .join(veille_df.drop(COL_CATEGORY), how="right", on="id", maintain_order="right")
    )

    logger.info("Remplacement des catégories effectué")

    return create_veille_qmd(veille_df, output_path, logger)
