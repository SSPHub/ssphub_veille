import re  # to extract link


# Regular expression to identify hyperlinks in Markdown format
pattern = r'\[([^\]]+)\]\(([^)]+)\)'


# Function to extract the hyperlink
def extract_link(text):
    """
    Function to extract a link, formatted in Markodwn or plain text, from a string

    Args:
        text (string): text where to look for the link
    
    Returns:
        None if nothing found
        Url link (string) if found
    
    Example:
        >>> extract_link('https://www.tjis_is_my_link.fr')
        'https://www.tjis_is_my_link.fr'
        >>> extract_link('[a link](https://www.tjis_is_my_link.fr)')
        'https://www.tjis_is_my_link.fr'
    """
    match = re.search(pattern, text)
    if match:
        return match.group(2)
    else:
        # Check if the text itself is a URL
        if re.match(r'^https?://\S+$', text):
            return text
        return None


# Function to extract the link text
def extract_link_text(text):
    """
    Function to the text of a link if formatted in Markodwn, from a string

    Args:
        text (string): text where to look for the link
    
    Returns:
        None if nothing found
        Url link (string) if found
    
    Example:
        >>> extract_link_text('https://www.tjis_is_my_link.fr')
        None
        >>> extract_link_text('[a link](https://www.tjis_is_my_link.fr)')
        'a link'
    """
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None