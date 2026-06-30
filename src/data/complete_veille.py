"""
Complete the Veille Grist table with the help of an LLM.

For every targeted row (e.g. modified/added after a given date and not yet
processed), the pipeline:

  1. Skips duplicate rows (Doublon_lien > 1) and records that in `Traitement`.
  2. Finds a working link: tries `Lien_article` first, then the links found in
     `Resume`; if none responds, writes "NO WORKING LINK FOUND".
  3. Calls the LLM to (a) extract / craft a title, (b) write a 2-3 sentence
     telegraphic summary, (c) pick categories from the `Rubriques` table (the
     closed category list), guided by example assignments taken from
     already-categorised rows.
  4. Stores the results in a dict keyed by Grist column names and PATCHes the
     row, stamping `Traitement` with a timestamp.

The `Categorie` column is a Reference List into the `Rubriques` table, so the
stored values are Rubriques row ids: the code translates them to names for the
LLM and translates the LLM's answers back into row ids before writing.

The LLM tasks (a/b/c) are issued as a single structured JSON call per row: the
article text only has to travel once and it is cheaper than three round-trips.
The prompt still carries the category vocabulary and the example assignments, so
the behaviour matches the three-step spec.
"""

import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from src.utils.llm_client import ask_json
from src.utils.config import (
    COL_LINK,
    COL_RESUME,
    COL_TITLE,
    COL_CATEGORY,
    COL_DUPLICATE,
    COL_PROCESS,
    COL_RUBRIQUE_CATEGORY,
    REQUEST_TIMEOUT,
    MAX_ARTICLE_CHARS,
    DEFAULT_N_EXAMPLES,
    PARIS_TZ,
    USER_AGENT,
    _URL_RE,
    _INTERNAL_PREFIXES
)


# --------------------------------------------------------------------------- #
# Small pure helpers (unit-tested)
# --------------------------------------------------------------------------- #
def now_stamp() -> str:
    """Current time in the Europe/Paris timezone, as 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.now(PARIS_TZ).strftime("%Y-%m-%d %H:%M:%S")


def is_duplicate(doublon_value) -> bool:
    """
    True when the row is a duplicate, i.e. Doublon_lien > 1.
    None / "" / non-numeric are treated as "not a duplicate".

    >>> is_duplicate(2)
    True
    >>> is_duplicate(1)
    False
    >>> is_duplicate(None)
    False
    """
    try:
        return float(doublon_value) > 1
    except (TypeError, ValueError):
        return False


def extract_all_links(text: str) -> list[str]:
    """
    Return every external http(s) link found in `text`, in order, deduplicated,
    Tchap/Matrix internal links removed.

    >>> extract_all_links("a https://x.fr b https://y.fr a https://x.fr")
    ['https://x.fr', 'https://y.fr']
    """
    if not text:
        return []
    out, seen = [], set()
    for raw in _URL_RE.findall(text):
        url = raw.rstrip(".,;")  # strip trailing sentence punctuation
        if url.startswith(_INTERNAL_PREFIXES):
            continue
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def clean_text(value) -> str:
    """
    Normalise a Grist text cell: None and the literal string 'None' (which shows
    up in the data) both become ''. Whitespace is stripped.

    >>> clean_text(None)
    ''
    >>> clean_text('None')
    ''
    >>> clean_text('  hello ')
    'hello'
    """
    text = ("" if value is None else str(value)).strip()
    return "" if text == "None" else text


def candidate_links(row: dict) -> list[str]:
    """
    Ordered list of links to try for a row: links found in `Lien_article` first,
    then links found in `Resume`. Order preserved, duplicates removed.

    We run the URL extractor on `Lien_article` (not just trust it as a bare URL)
    because real rows sometimes hold malformed markdown there, e.g.
    "[ici]([https://example.org/a] et [ici](https://example.org/b)".

    >>> candidate_links({"Lien_article": "https://a.fr", "Resume": "https://b.fr"})
    ['https://a.fr', 'https://b.fr']
    >>> candidate_links({"Lien_article": "[ici](https://a.fr) [x](https://b.fr)"})
    ['https://a.fr', 'https://b.fr']
    """
    links, seen = [], set()
    for source in (row.get(COL_LINK), row.get(COL_RESUME)):
        for url in extract_all_links(clean_text(source)):
            if url not in seen:
                seen.add(url)
                links.append(url)
    return links


def normalise_categories(value, id_to_name=None) -> list[str]:
    """
    Turn a Grist `Categorie` cell into a clean list of category *names*.

    The cell is a Reference List, encoded as ['L', id1, id2, ...] where the ids
    are rows of the `Rubriques` table. Pass `id_to_name` (a {row_id: name} map,
    see `build_category_ref_maps`) to translate those ids into category names;
    unknown ids are dropped.

    Without `id_to_name` the elements are returned as-is (handles a plain string
    cell, or a legacy ChoiceList of literal names).

    >>> normalise_categories(['L', 'IA', 'Stat publique'])
    ['IA', 'Stat publique']
    >>> normalise_categories(['L', '1', 2], {1: 'IA', 2: 'fun'})
    ['IA', 'fun']
    >>> normalise_categories('IA')
    ['IA']
    >>> normalise_categories(None)
    []
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        items = list(value)
        if items and items[0] == "L":  # drop Grist's list marker
            items = items[1:]
    else:
        text = str(value).strip()
        items = [text] if text else []

    if id_to_name is None:
        return [str(c).strip() for c in items if str(c).strip()]

    names = []
    for item in items:  # item is a Rubriques row id (int or stringified int)
        key = item
        try:
            key = int(item)
        except (TypeError, ValueError):
            pass
        name = id_to_name.get(key, id_to_name.get(str(item)))
        if name:
            names.append(name)
    return names


def build_category_ref_maps(rubriques_rows: list[dict]) -> tuple[dict, dict]:
    """
    From the rows of the `Rubriques` table, build the two lookups we need:
      - id_to_name: {Rubriques row id -> category name}   (for reading -> LLM)
      - name_to_id: {category name -> Rubriques row id}    (for writing back)
    """
    id_to_name, name_to_id = {}, {}
    for row in rubriques_rows:
        rid = row.get("id")
        name = clean_text(row.get(COL_RUBRIQUE_CATEGORY))
        if rid is not None and name:
            id_to_name[rid] = name
            name_to_id.setdefault(name, rid)
    return id_to_name, name_to_id


def category_vocabulary(id_to_name: dict) -> list[str]:
    """The list of available category names (the closed vocabulary), de-duplicated."""
    vocab, seen = [], set()
    for name in id_to_name.values():
        if name not in seen:
            seen.add(name)
            vocab.append(name)
    return vocab


def to_grist_ref_list(names: list[str], name_to_id: dict, logger=None) -> list | None:
    """
    Encode category names as a Grist Reference List: ['L', id1, id2, ...] with
    the Rubriques row ids. Names absent from `Rubriques` cannot be referenced and
    are dropped (with a log line). Returns None if nothing maps.

    >>> to_grist_ref_list(['IA', 'fun'], {'IA': 1, 'fun': 2})
    ['L', 1, 2]
    >>> to_grist_ref_list(['inconnue'], {'IA': 1})
    """
    ids = []
    for name in names:
        rid = name_to_id.get(name)
        if rid is None:
            if logger is not None:
                logger.info(f"categorie absente de Rubriques, ignoree : {name!r}")
            continue
        ids.append(rid)
    return ["L", *ids] if ids else None


def build_category_examples(
    rows: list[dict], id_to_name=None, n: int = DEFAULT_N_EXAMPLES
) -> list[dict]:
    """
    Up to `n` example assignments drawn from rows that already have a category,
    used as few-shot guidance: {"contenu": <title or summary>, "categorie": [...]}.
    Category ids are translated to names via `id_to_name`.
    """
    examples = []
    for row in rows:
        cats = normalise_categories(row.get(COL_CATEGORY), id_to_name)
        if not cats:
            continue
        content = clean_text(row.get(COL_TITLE)) or clean_text(row.get(COL_RESUME))
        if not content:
            continue
        examples.append({"contenu": content[:200], "categorie": cats})
        if len(examples) >= n:
            break
    return examples


def html_to_text(html: str, max_chars: int = MAX_ARTICLE_CHARS) -> str:
    """Extract a readable text blob (title + meta description + body) from HTML."""
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    parts = []
    if soup.title and soup.title.get_text(strip=True):
        parts.append(soup.title.get_text(strip=True))
    meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    if meta and meta.get("content"):
        parts.append(meta["content"].strip())

    body = soup.get_text(separator=" ", strip=True)
    body = re.sub(r"\s+", " ", body)
    parts.append(body)

    return "\n".join(p for p in parts if p)[:max_chars]


# --------------------------------------------------------------------------- #
# Network + LLM (side effects)
# --------------------------------------------------------------------------- #
def fetch_if_working(url: str, logger) -> str | None:
    """GET the url; return its HTML if it responds < 400, else None."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code < 400 and resp.text:
            return resp.text
        logger.info(f"  lien KO ({resp.status_code}) : {url}")
    except requests.RequestException as exc:
        logger.info(f"  lien injoignable ({exc.__class__.__name__}) : {url}")
    return None


def resolve_working_link(row: dict, logger) -> tuple[str | None, str | None]:
    """
    First working (url, html) among the candidate links, or (None, None).
    """
    for url in candidate_links(row):
        html = fetch_if_working(url, logger)
        if html is not None:
            return url, html
    return None, None


def _build_analysis_messages(
    article_text, url, vocabulary, examples, from_page=True
) -> list[dict]:
    system = (
        "Tu es un assistant de veille pour la statistique publique francaise. "
        "Tu reponds UNIQUEMENT avec un objet JSON valide, sans aucun texte ni "
        "balise Markdown autour."
    )
    vocab_str = ", ".join(vocabulary) if vocabulary else "(aucune pour l'instant)"
    examples_str = (
        "\n".join(
            f'- "{ex["contenu"]}" -> {ex["categorie"]}' for ex in examples
        )
        or "(aucun exemple disponible)"
    )

    # Category instruction is the same in both modes. Categories are a closed
    # list (the Rubriques table), so the model must pick from it, not invent.
    cat_instr = (
        '- "categories": une à quatre categories en francais, choisies '
        "EXCLUSIVEMENT dans la liste des categories existantes ci-dessous "
        "(ne cree aucune nouvelle categorie, evite les doublons proches). "
        'IMPORTANT : si tu n\'es pas sur, ou si aucune categorie ne convient, '
        'reponds exactement ["??"] (categorie reservee a l\'incertitude) ; '
        "ne devine pas. Ne donne pas plus de 4 catgégories à un article."
        " Les catégories sont en français ('education' est formation par exemple)"
    )

    if from_page:
        intro = "A partir du contenu de l'article ci-dessous, renvoie un objet JSON avec exactement ces cles :"
        titre_instr = (
            '- "titre": le titre de l\'article. Pour un billet de blog, le titre du '
            "billet ; pour un article de recherche, le titre de l'article, etc. Si "
            "aucun titre clair n'existe, invente un titre court de 10 mots maximum."
        )
        resume_instr = (
            '- "resume": un resume tres concis, en francais, style telegraphique, '
            "2 a 3 phrases maximum."
        )
        content_label = "Contenu de l'article :"
    else:
        # Fallback: the page could not be fetched; we only have the title/summary
        # already stored. Do NOT invent facts that are absent from this text.
        intro = (
            "La page de l'article n'a PAS pu etre telechargee. Tu disposes uniquement "
            "du titre et/ou du resume deja saisis ci-dessous. Renvoie un objet JSON "
            "avec exactement ces cles, sans inventer d'information absente du texte :"
        )
        titre_instr = (
            '- "titre": si un titre est deja present dans le texte, reprends-le tel '
            "quel ; sinon propose un titre court de 10 mots maximum a partir du texte. "
            "Si le texte ne permet pas de titre, laisse une chaine vide."
        )
        resume_instr = (
            '- "resume": uniquement si le texte fournit assez d\'information, un resume '
            "tres concis en francais (style telegraphique, 2-3 phrases). Sinon, laisse "
            "une chaine vide. Donne le résultat de l'analyse s'il existe."
            "Par exemple, ne dit pas 'estimation du bénéfice économique lié au "
            "maintien de l'intégrité des données officielles' mais plutot"
            " benefice économique lié au maintien de l'intégrité des données officielles "
            "estimé à 25$ par $ investi. Enfin et surtout n'invente rien. "
        )
        content_label = "Titre et resume existants (la page est inaccessible) :"

    user = f"""{intro}

{titre_instr}
{resume_instr}
{cat_instr}

Categories existantes (note : "??" signifie "categorie inconnue / incertaine") : {vocab_str}

Exemples d'affectation (contenu -> categorie) :
{examples_str}

URL : {url}

{content_label}
\"\"\"
{article_text}
\"\"\"

Reponds uniquement avec le JSON, par exemple :
{{"titre": "...", "resume": "...", "categories": ["..."]}}"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def analyze_article(article_text, url, vocabulary, examples, from_page=True) -> dict:
    """
    Single LLM call returning {"titre", "resume", "categories"} for the article.
    `from_page=False` switches to the fallback prompt (work from existing
    title/summary because the page could not be fetched).
    Defensive: always returns the three keys with sane fallbacks.
    """
    data = ask_json(
        _build_analysis_messages(article_text, url, vocabulary, examples, from_page)
    )

    titre = str(data.get("titre", "")).strip()
    resume = str(data.get("resume", "")).strip()
    cats = data.get("categories", [])
    if isinstance(cats, str):
        cats = [cats]
    categories = [str(c).strip() for c in cats if str(c).strip()]

    return {"titre": titre, "resume": resume, "categories": categories}


# --------------------------------------------------------------------------- #
# Per-row orchestration
# --------------------------------------------------------------------------- #
def fallback_text(row: dict) -> str:
    """
    Text to feed the LLM when the page can't be fetched: the existing title and
    summary already stored on the row. Returns '' if there's nothing to work
    with.
    """
    parts = [clean_text(row.get(COL_TITLE)), clean_text(row.get(COL_RESUME))]
    return "\n".join(p for p in parts if p)


def process_row(row: dict, vocabulary, examples, logger, id_to_name=None, name_to_id=None) -> dict:
    """
    Compute the {column_name: new_value} dict to PATCH for a single row.
    Never raises on expected conditions; the `Traitement` column always reflects
    what happened.

    `id_to_name` / `name_to_id` are the Rubriques lookups (see
    `build_category_ref_maps`): the first translates the row's stored category
    ids to names, the second turns the LLM's chosen names back into Rubriques row
    ids for the Reference List write.

    Link handling:
      - if a link works, the article page is analysed and the LLM results are
        written to the cells (overwrite). If the link that worked is not the one
        stored in `Lien_article` (a backup link taken from `Resume`, or a clean
        URL extracted from malformed markdown), `Lien_article` is updated to it;
      - if no link works but the row already has a title/summary, we fall back to
        analysing that existing text so a category can still be assigned. In this
        fallback we ONLY fill empty cells (no overwrite), because there is no new
        ground truth, just a re-reading of the same text;
      - if there's neither a working link nor any existing text, the row is left
        with "NO WORKING LINK FOUND".
    """
    row_id = row.get("id")

    # 1. Duplicates are skipped (but recorded).
    if is_duplicate(row.get(COL_DUPLICATE)):
        logger.info(f"[id {row_id}] doublon -> ignore")
        return {
            COL_PROCESS: f"Ignore : doublon (Doublon_lien={row.get(COL_DUPLICATE)}) - {now_stamp()}"
        }

    has_title = bool(clean_text(row.get(COL_TITLE)))
    has_resume = bool(clean_text(row.get(COL_RESUME)))
    has_cat = bool(normalise_categories(row.get(COL_CATEGORY), id_to_name))

    # 2. Find a working link.
    url, html = resolve_working_link(row, logger)

    if url is not None:
        # Page fetched: analyse it and overwrite the cells.
        logger.info(f"[id {row_id}] analyse LLM de {url}")
        analysis = analyze_article(html_to_text(html), url, vocabulary, examples, from_page=True)
        gap_only = False
        note = f"Traite le {now_stamp()}"
    else:
        # 3. Fallback: no reachable link -> use the existing title/summary so we
        #    can at least categorise. Never overwrite curated cells here.
        text = fallback_text(row)
        if not text:
            logger.info(f"[id {row_id}] aucun lien valide, aucun texte existant")
            return {COL_PROCESS: f"NO WORKING LINK FOUND - {now_stamp()}"}
        logger.info(f"[id {row_id}] lien injoignable -> fallback sur le texte existant")
        link_for_context = clean_text(row.get(COL_LINK))
        analysis = analyze_article(text, link_for_context, vocabulary, examples, from_page=False)
        gap_only = True
        note = f"Traite via texte existant (lien injoignable) le {now_stamp()}"

    # 4. Build the update dict keyed by Grist column names.
    #    `gap_only` (fallback only) -> never overwrite a cell that already has content.
    fields = {COL_PROCESS: note}
    # If the link that actually worked is not the one stored in Lien_article
    # (a backup link from Resume, or a clean URL extracted from malformed
    # markdown), write it back so the table holds the working link.
    if url is not None and url != clean_text(row.get(COL_LINK)):
        logger.info(f"[id {row_id}] Lien_article mis a jour -> {url}")
        fields[COL_LINK] = url
    if analysis["titre"] and not (gap_only and has_title):
        fields[COL_TITLE] = analysis["titre"]
    if analysis["resume"] and not (gap_only and has_resume):
        fields[COL_RESUME] = analysis["resume"]
    if analysis["categories"] and not (gap_only and has_cat):
        # Categorie is a Reference List -> write Rubriques row ids, not names.
        if name_to_id is not None:
            ref = to_grist_ref_list(analysis["categories"], name_to_id, logger)
            if ref is not None:
                fields[COL_CATEGORY] = ref
        else:
            fields[COL_CATEGORY] = ["L", *analysis["categories"]]
    return fields


def select_rows(rows) -> list[dict]:
    """
    Keep only the rows that still need processing: those whose `Traitement`
    column is empty.
    """
    return [row for row in rows if not clean_text(row.get(COL_PROCESS))]


def formula_target_columns(api, table_id, target_cols, logger) -> list[str]:
    """
    Among `target_cols`, return those that are formula columns in Grist (and thus
    NOT writable through the API). Returns [] if everything is writable, or if the
    column metadata could not be fetched (we warn and let the run proceed).

    Grist's API rejects a record update that touches a formula column, so writing
    e.g. `Traitement` while it is a formula column makes every PATCH fail. This
    pre-flight surfaces the problem before any LLM call is made.
    """
    try:
        resp = api.fetch_columns(table_id)
        cols = resp.json().get("columns", [])
    except Exception as exc:  # don't block the run on a flaky metadata call
        logger.warning(f"Impossible de verifier les colonnes ({exc}); on continue.")
        return []

    is_formula = {
        c.get("id"): bool(c.get("fields", {}).get("isFormula")) for c in cols
    }
    return [col for col in target_cols if is_formula.get(col)]

