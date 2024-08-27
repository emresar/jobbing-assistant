import requests
import streamlit as st


@st.cache_data(ttl=3600)
def search_wikipedia(query):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|info",
        "exintro": True,
        "explaintext": True,
        "inprop": "url",
        "titles": query,
        "redirects": 1,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        page = next(iter(data["query"]["pages"].values()))

        if "missing" in page:
            return f"No page found for '{query}'. Please try a different search term."

        title = page["title"]
        summary = page.get("extract", "No summary available.")
        url = page.get("fullurl", "URL not available")

        # Format the output in Markdown
        markdown_output = f"""
# {title}

{summary}

[Read more on Wikipedia]({url})
"""
        return markdown_output

    except requests.RequestException as e:
        return f"An error occurred while fetching data: {str(e)}"


def main():
    print("Welcome to the Wikipedia search tool!")
    print("Enter your queries to get summaries from Wikipedia in Markdown format.")
    print("Type 'quit' to exit the program.")

    while True:
        query = input("\nEnter a Wikipedia search query (or 'quit' to exit): ")
        if query.lower() == "quit":
            print("Thank you for using the Wikipedia search tool. Goodbye!")
            break

        result = search_wikipedia(query)
        print("\n" + result)


if __name__ == "__main__":
    main()
