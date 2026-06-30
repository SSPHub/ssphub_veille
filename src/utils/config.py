# --------------------------------------------------------------------------- #
# Configuration knobs
# --------------------------------------------------------------------------- #

from zoneinfo import ZoneInfo
import re


COL_LINK = "Lien_article"
COL_RESUME = "Resume"
COL_TITLE = "Titre_article"
COL_CATEGORY = "Categorie"
COL_DUPLICATE = "Doublon_lien"
COL_PROCESS = "Traitement"

# The Categorie column is a Reference List into the `Rubriques` table: the cell
# holds Rubriques row ids (e.g. ["L", 1, 2]), not category names. The category
# label lives in the Rubriques "Category" column.
TABLE_RUBRIQUES = "Rubriques"
COL_RUBRIQUE_CATEGORY = "Categories"

REQUEST_TIMEOUT = 15  # seconds, when checking/fetching a link
MAX_ARTICLE_CHARS = 8000  # how much article text we feed the LLM
DEFAULT_N_EXAMPLES = 15  # category example assignments sent to the LLM
PARIS_TZ = ZoneInfo("Europe/Paris")  # timestamps written to Grist use Paris time
USER_AGENT = (
    "Mozilla/5.0 (compatible; ssphub-veille-bot/1.0; "
    "+https://github.com/SSPHub/ssphub_veille)"
)

# http(s) URL matcher (no trailing punctuation captured)
_URL_RE = re.compile(r"https?://[^\s)\]<>\"']+")
# internal links we never treat as the article
_INTERNAL_PREFIXES = ("https://tchap.gouv.fr/", "https://matrix.to")
