from src.utils.access_grist_api import GristApi
from src.utils.logging import setup_logging
from src.data.complete_veille import (
    formula_target_columns,
    build_category_examples,
    build_category_ref_maps,
    category_vocabulary,
    select_rows,
    process_row,
    now_stamp
)
from src.utils.config import (
    COL_LINK,
    COL_RESUME,
    COL_TITLE,
    COL_CATEGORY,
    COL_PROCESS,
    TABLE_RUBRIQUES,
    DEFAULT_N_EXAMPLES
)


def complete_veille(
    table_id="Test",
    limit=None,
    dry_run=False,
    n_examples=DEFAULT_N_EXAMPLES,
    logger=None,
):
    """
    Complete the rows of `table_id` whose `Traitement` column is empty.

    Args:
        table_id: Grist table id (e.g. "Test" or "Veille").
        limit: optional cap on the number of rows processed (handy for testing).
        dry_run: compute everything but do NOT write back to Grist.
        n_examples: number of example category assignments sent to the LLM.

    Returns:
        the list of {"id", "fields"} updates that were (or would be) applied.
    """
    logger = logger or setup_logging()
    api = GristApi()

    # Pre-flight: make sure the columns we intend to write are writable.
    # `Traitement` in particular is often an (empty) formula column, which Grist
    # refuses to write to -> every PATCH would fail. Stop early if so.
    target_cols = [COL_PROCESS, COL_TITLE, COL_RESUME, COL_CATEGORY, COL_LINK]
    blocked = formula_target_columns(api, table_id, target_cols, logger)
    if blocked and not dry_run:
        raise RuntimeError(
            f"Ces colonnes sont des colonnes formule (non modifiables via l'API) : "
            f"{blocked}. Dans Grist, convertis-les en colonnes de donnees "
            f"(ex. type 'Text' pour {COL_PROCESS}) avant de relancer."
        )
    if blocked and dry_run:
        logger.warning(
            f"[dry-run] colonnes formule detectees (non modifiables) : {blocked}"
        )

    logger.info(f"Telechargement de la table Grist '{table_id}'")
    df = api.fetch_table_pl(table_id)
    rows = df.to_dicts()
    logger.info(f"{len(rows)} lignes recuperees")

    # The Categorie column references the Rubriques table; load it so we can show
    # the LLM real category names and write its answers back as Rubriques ids.
    try:
        rubriques_rows = api.fetch_table_pl(TABLE_RUBRIQUES).to_dicts()
    except Exception as exc:
        logger.warning(
            f"Impossible de charger la table '{TABLE_RUBRIQUES}' ({exc}); "
            "les categories ne pourront pas etre traitees."
        )
        rubriques_rows = []
    id_to_name, name_to_id = build_category_ref_maps(rubriques_rows)
    vocabulary = category_vocabulary(id_to_name)
    examples = build_category_examples(rows, id_to_name, n=n_examples)
    logger.info(
        f"{len(vocabulary)} categories dans '{TABLE_RUBRIQUES}', "
        f"{len(examples)} exemples d'affectation"
    )

    targets = select_rows(rows)  # rows whose Traitement is empty
    if limit is not None:
        targets = targets[:limit]
    logger.info(f"{len(targets)} lignes a traiter (Traitement vide)")

    updates = []
    for row in targets:
        try:
            fields = process_row(
                row, vocabulary, examples, logger, id_to_name, name_to_id
            )
        except Exception as exc:  # never let one row kill the batch
            logger.error(f"[id {row.get('id')}] erreur inattendue : {exc}")
            fields = {COL_PROCESS: f"ERREUR : {exc} - {now_stamp()}"}

        update = {"id": row.get("id"), "fields": fields}
        updates.append(update)

        if dry_run:
            logger.info(f"[dry-run] [id {update['id']}] {fields}")
            continue

        resp = api.update_records(table_id, json={"records": [update]})
        if resp.status_code == 200:
            logger.info(f"[id {update['id']}] mis a jour")
        else:
            logger.error(
                f"[id {update['id']}] echec maj ({resp.status_code}): {resp.text[:200]}"
            )

    logger.info(f"Termine : {len(updates)} lignes traitees (dry_run={dry_run})")
    return updates
