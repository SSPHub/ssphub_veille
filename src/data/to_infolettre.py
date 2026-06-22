"""
Once the data has been filled, extract all the "a_garder" and format them in 
markdown format for easier writing.
"""


import polars as pl

from src.utils.access_grist_api import GristApi
from src.utils.logging import setup_logging
from src.data.complete_veille import normalise_categories


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
    # Download data to filter urls
    logger.info(f"Début du téléchargement de la table Grist cible {input_table}")
    veille_df = (
        GristApi().fetch_table_pl(table_id=input_table)
    )
    logger.info(
        f"Table Grist cible {input_table} téléchargée, nombre de lignes : {len(veille_df)}"
    )

    # Filter new articles in former Grist table
    logger.info("Filtrer les lignes à insérer dans la veille")
    veille_df = veille_df.filter(
       pl.col("A_garder"), pl.col("Lien_veille") == ""
    )
    logger.info(f"Nombre de lignes à garder sans veille renseignée: {len(veille_df)}")

    return create_veille_qmd(veille_df, output_path, logger)


def create_veille_qmd(
    veille_df,
    output_path="veille.qmd",
    logger=setup_logging(),
):
    """
    Summarise all the rows of a Polars dataframe to the following format: 
    IA : [if the list of category contains one of the following tags : IA, LLM]
    - [Titre_article](lien_article): Resume
    categories
    - [Titre_article](lien_article): Resume
    categories

    Ressources : [if the list of category contains one of the following tags : tools]
    - [Titre_article](lien_article): Resume
    categories
    - [Titre_article](lien_article): Resume
    categories

    Fun: [if the list of category contains one of the following tags : fun, formation]
    - [Titre_article](lien_article): Resume
    categories

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
    category_groups = {
        'IA': [
            'IA',
            'bulle',
            'RAG',
            'LLM',
            'IA agent',
            'Embedding',
            'MCP',
            'entrainement',
            'classification',
            'dangerIA',
            'Anthropic',
            'NLP/texte'
        ],
        'Ressources': [
            'Python',
            'Parquet',
            'techos',
            'tools',
            'R',
            'package',
            'SQL',
            'RShiny',
            'Quarto'
            ],
        'Fun': [
            'fun', 
            'formation'
            ]
    }

    # Initialize markdown content
    markdown_content = ""

    # Process each category group
    for group, keywords in category_groups.items():
        # Filter rows where 'Categorie' contains any of the keywords
        filtered_df = veille_df.filter(
            pl.any_horizontal(*[pl.col('Categorie').list.contains(keyword) for keyword in keywords])
        )

        if filtered_df.height > 0:
            markdown_content += f"## {group} :\n"
            for row in filtered_df.iter_rows(named=True):
                titre = row['Titre_article']
                lien = row['Lien_article']
                resume = row['Resume']
                categories = ", ".join(normalise_categories(row['Categorie']))
                markdown_content += f"- [{titre}]({lien}): {resume}\nCatégories : {categories}\n\n"

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return markdown_content


extract_rows_qmd()
