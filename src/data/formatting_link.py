import re

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
import warnings
from src.utils.config import _INTERNAL_PREFIXES

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)  # Filter out warning message from bs4 that identifies input to parse as html


def extract_link_rawtxt(text):
    """
    Returns thr first url from raw text (not formatted as html or other)

    Args:
        text (string): raw text where to look for the link

    Returns: 
        Url link (string) - None if nothing found

    Example:
        >>> extract_link_rawtxt('coucou https://www.tjis_is_my_link.fr zoubidou https://exemple.fr')
        'https://www.tjis_is_my_link.fr'
    """
    
    pattern = r"\bhttps?://\S+|www\.\S+"  # Regex pattern to match HTTP/HTTPS URLs
    match = re.search(pattern, text)
    if match:
        href = match.group(0)
        if href.startswith(_INTERNAL_PREFIXES[0]) or href.startswith(
            _INTERNAL_PREFIXES[1]
        ):
            href = None
    else:
        href = None
    return href


# Function to extract the hyperlink and its title from an html formatted body
def extract_link_title_html(text):
    """
    Function to extract a link, formatted in Markodwn or plain text, from a string

    Args:
        text (string): text where to look for the link

    Returns: a tuple with :
        None if nothing found
        Url link (string), Title (if found otherwise empty)

    Example:
        >>> extract_link('coucou https://www.tjis_is_my_link.fr')
        'https://www.tjis_is_my_link.fr'
        >>> extract_link('[a link](https://www.tjis_is_my_link.fr)')
        'https://www.tjis_is_my_link.fr'
    """
    # Parse the formatted body
    soup = BeautifulSoup(text, "html.parser")

    # Remove all <mx-reply> tags when you reply to a msg
    for mx_reply in soup.find_all("mx-reply"):
        mx_reply.decompose()

    # Find all <a> tags with href attributes
    links = soup.find_all("a", href=True)

    # Filter HTTPS/HTTP links and get the first match
    first_link = None
    first_title = ""
    for link in links:
        href = link["href"]
        if href.startswith(_INTERNAL_PREFIXES[0]) or href.startswith(
            _INTERNAL_PREFIXES[1]
        ):  # Filtering internal links
            href = None
        if href is not None:
            if href.startswith(("http://", "https://")):
                first_link = href
                first_title = link.get_text(strip=True)  # Extract the title text
                break

    if first_link:
        return first_link, first_title
    else:
        return None, None


# %%
def extract_link_title(text):
    link, title = extract_link_title_html(text)

    if not link or link == "None":
        link, title = extract_link_rawtxt(text), ""

    return link, title


# %%
