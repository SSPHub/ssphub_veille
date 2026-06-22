"""
Once the data has been filled, extract all the "a_garder" and format them in 
markdown format for easier writing.
"""


import polars as pl

from src.utils.access_grist_api import GristApi
from src.utils.logging import setup_logging
from src.data.complete_veille import build_category_ref_maps

TABLE_RUBRIQUES = "Rubriques"
COL_CATEGORY = "Categorie"


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


def create_veille_qmd(
    veille_df,
    output_path="veille.qmd",
    logger=setup_logging(),
):
    """
    Summarise all the rows of a Polars dataframe to the following format: 
    ## IA : [tags according to Rubriques table]
    - [Titre_article](lien_article): Resume
    Catégories: categories

    ## Ressources : [tags according to Rubriques table]
    - [Titre_article](lien_article): Resume
    Catégories: categories

    ## Fun: [tags according to Rubriques table]
    - [Titre_article](lien_article): Resume
    Catégories: categories

    Args:
        veille_df : the Polars dataframe (filter) whose rows will be summarised
        output_path (string) : path of the Qmd file to store the results
        logger

    Returns:
        the markdown formatted text

    Example:
    >>> create_veille_qmd(veille_df)
    """
    # Define category mappings
    category_groups = fetch_categories(logger=logger)

    # Initialize markdown content
    markdown_content = ""
    added_rows_ids = []
    # Process each category group
    for group, keywords in category_groups.items():

        if veille_df.height > 0:
            markdown_content += f"## {group} :\n"
            for row in veille_df.iter_rows(named=True):
                if row["id"] not in added_rows_ids:
                    titre = row['Titre_article']
                    lien = row['Lien_article']
                    resume = row['Resume']
                    categories = ", ".join(row['Categorie'])
                    markdown_content += f"- [{titre}]({lien}): {resume}\nCatégories : {categories}\n\n"
                    added_rows_ids = added_rows_ids.append(row['id'])
    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return markdown_content


def fetch_categories(logger=setup_logging()):
    """
    To fetch categories from the Rubrique table and send it back as a dictionnary 'Rubrique' : [list of categories]

    Args : 

    """
    logger.info(f"Récupération des catégories de la table {TABLE_RUBRIQUES}")
    rubriques_df = GristApi().fetch_table_pl(table_id=TABLE_RUBRIQUES)

    logger.info("Transformation en dictionnaire de catégories")
    category_groups = dict(
        rubriques_df
        .group_by("Rubrique")
        .agg(pl.col("Categories"))
        .iter_rows()
    )

    return category_groups


extract_rows_qmd()
