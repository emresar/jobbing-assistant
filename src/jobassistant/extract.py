import re
from urllib.request import urlopen

import streamlit as st
from bs4 import BeautifulSoup


@st.cache_data(ttl=3600)  # Cache for 1 hour
def scrape(identifier):
    job_url = f"https://www.linkedin.com/jobs/view/{identifier}"
    response = urlopen(job_url)
    html = BeautifulSoup(response.read(), "html.parser").prettify()
    return html


def scrape_generic(url):
    response = urlopen(url)
    html = BeautifulSoup(response.read(), "html.parser").prettify()
    return html


@st.cache_data(ttl=3600)  # Cache for 1 hour
def extract_job_details(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    job_title = soup.find("h3", class_="sub-nav-cta__header").text.strip()
    company = soup.find("a", class_="sub-nav-cta__optional-url").text.strip()
    location = soup.find("span", class_="sub-nav-cta__meta-text").text.strip()

    description_div = soup.find("div", class_="show-more-less-html__markup")
    description = description_div.get_text(separator="\n", strip=True)

    # Extract responsibilities and requirements
    responsibilities = extract_section(description, "Responsibilities", "Requirements")
    requirements = extract_section(description, "Requirements", "About Us")

    return {
        "job_title": job_title,
        "company": company,
        "location": location,
        "description": description,
        "responsibilities": responsibilities,
        "requirements": requirements,
    }


def extract_section(text, start_marker, end_marker):
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start != -1 and end != -1:
        section = text[start:end].strip()
        # Remove the section title and any leading/trailing whitespace
        section = re.sub(f"^{start_marker}\s*", "", section).strip()
        return section
    return ""


@st.cache_data(ttl=3600)  # Cache for 1 hour
def convert_to_markdown(job_details):
    markdown = f"# {job_details['job_title']}\n\n"
    markdown += f"**Company:** {job_details['company']}\n"
    markdown += f"**Location:** {job_details['location']}\n\n"

    markdown += "## Description\n\n"
    markdown += job_details["description"] + "\n\n"

    if job_details["responsibilities"]:
        markdown += "## Responsibilities\n\n"
        markdown += job_details["responsibilities"] + "\n\n"

    if job_details["requirements"]:
        markdown += "## Requirements\n\n"
        markdown += job_details["requirements"] + "\n\n"

    return markdown


@st.cache_data(ttl=3600)  # Cache for 1 hour
def extract_job_md(identifier):
    html_content = scrape(identifier)
    job_details = extract_job_details(html_content)
    markdown_output = convert_to_markdown(job_details)
    return markdown_output, job_details
