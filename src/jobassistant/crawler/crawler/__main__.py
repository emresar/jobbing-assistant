import argparse
import json
import os
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .routes import get_output_path, tag_visible, text_from_html


def crawl(url: str, max_pages: int = 50) -> str:
    """The crawler entry point."""
    visited = set()
    to_visit = [url]
    output_path = get_output_path(url)
    os.makedirs(output_path, exist_ok=True)

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        try:
            response = requests.get(current_url)
            soup = BeautifulSoup(response.content, "html.parser")

            # Save the page content
            page_data = {
                "url": current_url,
                "title": soup.title.string if soup.title else None,
                "text": text_from_html(soup),
            }
            filename = f"page_{len(visited)}.json"
            with open(os.path.join(output_path, filename), "w") as f:
                json.dump(page_data, f)

            visited.add(current_url)

            # Find new links
            for link in soup.find_all("a"):
                href = link.get("href")
                if href:
                    full_url = urljoin(current_url, href)
                    if (
                        urlparse(full_url).netloc == urlparse(url).netloc
                        and full_url not in visited
                    ):
                        to_visit.append(full_url)

        except requests.RequestException:
            print(f"Failed to fetch {current_url}")

    return output_path


def main(url: str) -> str:
    """Main function to run the crawler."""
    return crawl(url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="The URL to crawl")
    args = parser.parse_args()

    output_path = main(args.url)
    print(f"Crawled data saved to: {output_path}")
