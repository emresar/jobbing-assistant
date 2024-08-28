import re
from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import Comment


def tag_visible(element):
    """Check if an HTML element should be visible in the final text output."""
    if element.parent.name in [
        "style",
        "script",
        "head",
        "title",
        "meta",
        "[document]",
    ]:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(soup):
    """Extract visible text from a BeautifulSoup object."""
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return " ".join(t.strip() for t in visible_texts)


def get_output_path(url: str) -> str:
    """Generate an output path for storing crawled data based on the input URL."""
    dataset_name = re.sub("^https?://", "", url).split("/")[0]
    return str(Path(f"crawler/storage/datasets/{dataset_name}"))
