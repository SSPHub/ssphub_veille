"""
Once the data has been filled, extract all the "a_garder" and format them in 
markdown format for easier writing.
"""


import polars as pl

from src.utils.access_grist_api import GristApi
from src.utils.logging import setup_logging
from src.utils.config import COL_LINK

from src.utils.config import (
    TABLE_RUBRIQUES,
    COL_CATEGORY,
    COL_RUBRIQUE_CATEGORY,
    COL_RUBRIQUE_RUBRIQUE
)


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
    rubriques_groups = fetch_rubriques(logger=logger)

    # Initialize markdown content
    markdown_content = ""
    added_rows_ids = []

    # Fetch rubrique order (tag 1 prevails over tag in 2 ...)
    groups_ordered = (
        GristApi()
        .fetch_table_pl(table_id=TABLE_RUBRIQUES)
        .unique(COL_RUBRIQUE_RUBRIQUE)
        .select([COL_RUBRIQUE_RUBRIQUE, "Ordre"])
        .sort("Ordre")[COL_RUBRIQUE_RUBRIQUE]
        .to_list()
    )

    # Process each category group in the right order
    for group in groups_ordered:
        keywords = rubriques_groups[group]
        filtered_df = (
            veille_df
            .remove(pl.col("id").is_in(added_rows_ids))
            .filter(
                pl.any_horizontal(*[pl.col(COL_CATEGORY).list.contains(keyword) for keyword in keywords])
            )
        )
        if filtered_df.height > 0:
            markdown_content += f"## {group} :\n"
            for row in filtered_df.iter_rows(named=True):
                titre = row['Titre_article']
                lien = row[COL_LINK]
                resume = row['Resume']
                categories = ", ".join(row[COL_CATEGORY])
                markdown_content += f"- [{titre}]({lien}): {resume}\nCatégories : {categories}\n\n"
                added_rows_ids = added_rows_ids + [row['id']]
    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return markdown_content


def fetch_rubriques(logger=setup_logging()):
    """
    To fetch categories from the Rubrique table and send it back as a dictionnary 'Rubrique' : [list of categories]

    Args : 

    """
    logger.info(f"Récupération des catégories de la table {TABLE_RUBRIQUES}")
    rubriques_df = GristApi().fetch_table_pl(table_id=TABLE_RUBRIQUES)

    logger.info("Transformation en dictionnaire de catégories")
    rubriques_groups = dict(
        rubriques_df
        .group_by(COL_RUBRIQUE_RUBRIQUE)
        .agg(pl.col(COL_RUBRIQUE_CATEGORY))
        .iter_rows()
    )

    return rubriques_groups
