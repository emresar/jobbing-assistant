import json
import os
import re
import shutil
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from config import load_config
from crawler.crawler.__main__ import main as run_crawler
from extract import extract_job_md
from prompts import (
    additional_context_for_website,
    cover_letter_prompt,
    cv_edit_suggestions_prompt,
    job_rating_prompt,
    system_prompt,
)
from query_engine import PlainQueryEngine, QueryEngine, RAGQueryEngine
from utils import convert_pdf_to_markdown
from wikipedia import search_wikipedia


@st.cache_data(ttl=3600)
def fetch_available_models(tags_url: str) -> List[str]:
    """Fetch available models from the API."""
    try:
        response = requests.get(tags_url)
        response.raise_for_status()
        data = response.json()
        return [model["name"] for model in data["models"]]
    except requests.RequestException as e:
        st.error(f"Failed to fetch available models: {str(e)}")
        return []


class JobEvaluator:
    def __init__(self, query_engine: QueryEngine):
        """Initialize JobEvaluator with a query engine."""
        self.query_engine = query_engine
        self.config = load_config()

    def construct_query(
        self,
        cv_markdown: str,
        job_markdown: str,
        job_details: Dict[str, str],
        prompt: str,
        additional_context: str,
    ) -> Dict[str, Any]:
        """Construct a query for the API."""
        query_template = {
            "messages": [
                {
                    "role": "system",
                    "content": "",
                },
                {"role": "user", "content": ""},
            ],
            "stream": False,
            "options": {
                "seed": 42,
                "num_predict": self.config.num_predict,
                "num_ctx": self.config.num_ctx,
                "temperature": self.config.temperature,
            },
        }
        system_content = f"{system_prompt}\n\n {cv_markdown}\n\n"

        if job_markdown == "":
            prompt = f"{prompt}\n\n {additional_context_for_website.format(company_name=job_details['company_name'])}"
        else:
            prompt = f"{prompt}\n\n Job Details for {job_details['job_title']}: \n {job_markdown}"

        if additional_context:
            prompt += f"\n\nAdditional Context:\n{additional_context}"

        query = query_template.copy()
        query["messages"][0]["content"] = system_content
        query["messages"][1]["content"] = prompt
        return query

    def evaluate_cv(
        self,
        cv_markdown: str,
        job_markdown: str,
        job_details: Dict[str, str],
        additional_context: str,
    ) -> str:
        """Evaluate a CV against job details."""
        query = self.construct_query(
            cv_markdown,
            job_markdown,
            job_details,
            job_rating_prompt,
            additional_context,
        )
        return self.query_engine.query(query)

    def write_cover_letter(
        self,
        cv_markdown: str,
        job_markdown: str,
        job_details: Dict[str, str],
        additional_context: str,
    ) -> str:
        """Generate a cover letter based on CV and job details."""
        query = self.construct_query(
            cv_markdown,
            job_markdown,
            job_details,
            cover_letter_prompt,
            additional_context,
        )
        return self.query_engine.query(query)

    def suggest_cv_edits(
        self,
        cv_markdown: str,
        job_markdown: str,
        job_details: Dict[str, str],
        additional_context: str,
    ) -> str:
        """Suggest edits for a CV based on job details."""
        query = self.construct_query(
            cv_markdown,
            job_markdown,
            job_details,
            cv_edit_suggestions_prompt,
            additional_context,
        )
        return self.query_engine.query(query)


class ResponseParser:
    @staticmethod
    def parse_evaluation(response_text: str) -> Dict[str, Any]:
        """Parse the evaluation response into structured data."""
        sections = {
            "Top Matching Qualifications": [],
            "Areas for Improvement": [],
            "Suggestions for Improvement": [],
            "Cultural Fit Assessment": "",
            "Evaluation Scores": {},
            "Additional Comments": "",
        }

        current_section = None
        for line in response_text.split("\n"):
            line = line.strip()
            if line.startswith("**") and line.endswith(":**"):
                current_section = line[2:-3]
            elif current_section:
                if current_section in [
                    "Top Matching Qualifications",
                    "Areas for Improvement",
                    "Suggestions for Improvement",
                ]:
                    if line.startswith(str(len(sections[current_section]) + 1) + "."):
                        sections[current_section].append(line.split(".", 1)[1].strip())
                elif current_section == "Evaluation Scores":
                    if line.startswith("- "):
                        key, value = line[2:].split(":", 1)
                        sections[current_section][key.strip()] = value.strip()
                elif current_section in [
                    "Cultural Fit Assessment",
                    "Additional Comments",
                ]:
                    sections[current_section] += line + "\n"

        return sections

    @staticmethod
    def parse_cv_edit_suggestions(response_text: str) -> Dict[str, Any]:
        """Parse CV edit suggestions into structured data."""
        sections = {
            "Content Suggestions": [],
            "Structure Suggestions": [],
            "Language Suggestions": [],
            "Formatting Suggestions": [],
            "Key Skills to Highlight": [],
            "Additional Recommendations": "",
        }
        print("Response:", response_text)
        current_section = None
        for line in response_text.split("\n"):
            line = line.strip()
            if line.endswith(":") and line[:-1] in sections:
                current_section = line[:-1]
            elif current_section:
                if current_section in [
                    "Content Suggestions",
                    "Structure Suggestions",
                    "Language Suggestions",
                    "Formatting Suggestions",
                    "Key Skills to Highlight",
                ]:
                    if line.startswith(str(len(sections[current_section]) + 1) + "."):
                        sections[current_section].append(line.split(".", 1)[1].strip())
                elif current_section == "Additional Recommendations":
                    sections[current_section] += line + "\n"
        sections["Edited CV"] = response_text
        return sections


class UIHandler:
    @staticmethod
    def display_structured_response(parsed_response: Dict[str, Any]) -> str:
        """Display structured response in the UI and return markdown."""
        markdown = []

        markdown.append("## Job Evaluation Result:")

        # Evaluation Scores
        st.subheader("Evaluation Scores:")
        markdown.append("\n### Evaluation Scores:")
        for key, value in parsed_response["Evaluation Scores"].items():
            st.metric(key, value)
            markdown.append(f"**{key}**: {value}")

        # Top Matching Qualifications
        st.subheader("Top Matching Qualifications:")
        markdown.append("\n### Top Matching Qualifications:")
        for qual in parsed_response["Top Matching Qualifications"]:
            st.markdown(f"- {qual}")
            markdown.append(f"- {qual}")

        # Areas for Improvement
        st.subheader("Areas for Improvement:")
        markdown.append("\n### Areas for Improvement:")
        for area in parsed_response["Areas for Improvement"]:
            st.markdown(f"- {area}")
            markdown.append(f"- {area}")

        # Suggestions for Improvement
        st.subheader("Suggestions for Improvement:")
        markdown.append("\n### Suggestions for Improvement:")
        for suggestion in parsed_response["Suggestions for Improvement"]:
            st.markdown(f"- {suggestion}")
            markdown.append(f"- {suggestion}")

        # Cultural Fit Assessment
        st.subheader("Cultural Fit Assessment:")
        markdown.append("\n### Cultural Fit Assessment:")
        st.write(parsed_response["Cultural Fit Assessment"])
        markdown.append(parsed_response["Cultural Fit Assessment"])

        # Additional Comments
        st.subheader("Additional Comments:")
        markdown.append("\n### Additional Comments:")
        st.write(parsed_response["Additional Comments"])
        markdown.append(parsed_response["Additional Comments"])

        return "\n".join(markdown)

    @staticmethod
    def display_cv_edit_suggestions(parsed_response: Dict[str, Any]) -> str:
        """Display CV edit suggestions in the UI and return markdown."""
        markdown = []

        markdown.append("## CV Edit Suggestions")

        for section, suggestions in parsed_response.items():
            if len(suggestions) == 0:
                continue
            st.subheader(section)
            markdown.append(f"\n### {section}")
            if isinstance(suggestions, list):
                for suggestion in suggestions:
                    st.markdown(f"- {suggestion}")
                    markdown.append(f"- {suggestion}")
            else:
                st.write(suggestions)
                markdown.append(suggestions)

        return "\n".join(markdown)

    def export_to_markdown(self, content: str, filename: str):
        """Create a download button for exporting content to markdown."""
        st.download_button(
            label="Export to Markdown",
            data=content,
            file_name=filename,
            mime="text/markdown",
        )


class App:
    def __init__(self, use_rag: bool = False):
        """Initialize the App with configuration and optional RAG usage."""
        self.config = load_config()
        self.use_rag = use_rag
        self.response_parser = ResponseParser()
        self.ui_handler = UIHandler()
        self.processing = False

    def handle_cv_upload(self):
        """Handle CV file upload."""
        uploaded_file = st.file_uploader("Upload your CV", type=["md", "txt", "pdf"])
        if uploaded_file is not None:
            try:
                # Determine the file type and process accordingly
                if uploaded_file.type == "application/pdf":
                    cv_content = convert_pdf_to_markdown(uploaded_file)
                elif uploaded_file.type in [
                    "application/octet-stream",
                    "text/markdown",
                    "text/plain",
                ]:
                    # For text or markdown files, decode the content
                    file_content = uploaded_file.read()
                    cv_content = file_content.decode("utf-8")
                else:
                    st.error("Unsupported file type. Please upload a .md, .txt, or .pdf file.")
                    return None

                # Save the CV content to a file in the docs directory
                cv_filename = uploaded_file.name
                cv_path = os.path.join(self.config.docs_dir, cv_filename)
                os.makedirs(self.config.docs_dir, exist_ok=True)
                with open(cv_path, "w", encoding="utf-8") as f:
                    f.write(cv_content)

                st.success(f"CV uploaded and saved as {cv_filename}")
                return cv_content
            except Exception as e:
                st.error(f"An error occurred while processing the file: {str(e)}")
                st.error(traceback.format_exc())
                return None
        return None

    def handle_file_upload(self):
        """Handle file uploads for RAG."""
        uploaded_files = st.file_uploader(
            "Upload documents for RAG",
            accept_multiple_files=True,
            type=[
                "txt",
                "pdf",
                "doc",
                "docx",
                "pptx",
                "ppt",
                "xlsx",
                "xls",
                "md",
                "json",
            ],
        )
        if uploaded_files:
            os.makedirs(self.config.docs_dir, exist_ok=True)

            for uploaded_file in uploaded_files:
                file_path = os.path.join(self.config.docs_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            st.success(f"Uploaded {len(uploaded_files)} document(s) successfully!")

    @staticmethod
    @st.cache_data(ttl=3600)
    def crawl_website(url):
        if url:
            crawled_data_path = run_crawler(url)
            st.success(f"Crawled website to {crawled_data_path} document(s) successfully!")
            return crawled_data_path

    def run(self):
        st.title("Jobbing Assistant")

        available_models = fetch_available_models(self.config.tags_url)
        default_model_index = available_models.index(self.config.model)
        self.selected_model = st.selectbox(
            "Select a model:", available_models, index=default_model_index
        )
        markdown_response = None
        docs_path = None

        cv_markdown = self.handle_cv_upload()

        self.use_rag = st.checkbox("Use RAG (Retrieval-Augmented Generation)", value=False)
        if self.use_rag:
            self.handle_file_upload()

        input_type = st.radio(
            "Select input type:",
            ["Job ID", "URL to crawl"],
            key="input_type",
            on_change=lambda: st.session_state.update({"input_type": st.session_state.input_type}),
        )

        with st.form("job_form"):
            if st.session_state.input_type == "Job ID":
                id_input = st.text_input("Enter Job ID:", max_chars=10)
                url_input = ""
            else:
                id_input = ""
                url_input = st.text_input("Enter URL to crawl:", max_chars=100)

            additional_context = st.text_area("Additional Context (optional):", height=150)

            col1, col2, col3 = st.columns(3)
            with col1:
                cv_rating_button = st.form_submit_button("Get CV Rating")
            with col2:
                cover_letter_button = st.form_submit_button("Generate Cover Letter")
            with col3:
                cv_edit_suggestions_button = st.form_submit_button("Get CV Edit Suggestions")

            if (id_input or url_input) and (
                cv_rating_button or cover_letter_button or cv_edit_suggestions_button
            ):
                if url_input:
                    docs_path = self.crawl_website(url_input)
                    self.use_rag = True

                if docs_path:
                    self.query_engine = RAGQueryEngine(self.config, docs_path=docs_path)
                else:
                    if self.use_rag:
                        self.query_engine = RAGQueryEngine(self.config)
                    else:
                        self.query_engine = PlainQueryEngine(self.config)

                self.job_evaluator = JobEvaluator(self.query_engine)
                self.processing = True
                if id_input:
                    job_markdown, job_details = extract_job_md(id_input)
                    company_markdown = search_wikipedia(job_details["company"])
                    full_markdown = company_markdown + "\n" + job_markdown
                else:
                    job_markdown, job_details = "", {}
                    job_details["company_name"] = re.sub(r"https?://\S+", "", url_input).split("/")[
                        0
                    ]
                    company_markdown = ""
                    full_markdown = ""

                if cv_markdown is None:
                    st.stop()

                parsed_response = ""
                with st.spinner("Processing... This may take a moment."):
                    if cv_rating_button:
                        response = self.job_evaluator.evaluate_cv(
                            cv_markdown, full_markdown, job_details, additional_context
                        )
                        if response:
                            parsed_response = self.response_parser.parse_evaluation(response)
                            markdown_response = self.ui_handler.display_structured_response(
                                parsed_response
                            )
                        else:
                            st.error("Failed to evaluate the CV. Please try again later.")
                    elif cover_letter_button:
                        parsed_response = self.job_evaluator.write_cover_letter(
                            cv_markdown, full_markdown, job_details, additional_context
                        )
                        markdown_response = parsed_response
                        if parsed_response:
                            st.subheader("Example Cover Letter:")
                            st.markdown(parsed_response)
                        else:
                            st.error("Failed to generate a cover letter. Please try again later.")
                    elif cv_edit_suggestions_button:
                        response = self.job_evaluator.suggest_cv_edits(
                            cv_markdown, full_markdown, job_details, additional_context
                        )
                        if response:
                            parsed_response = self.response_parser.parse_cv_edit_suggestions(
                                response
                            )
                            markdown_response = self.ui_handler.display_cv_edit_suggestions(
                                parsed_response
                            )
                        else:
                            st.error(
                                "Failed to generate CV edit suggestions. Please try again later."
                            )

                st.subheader("Job Description:")
                st.markdown(job_markdown)

                st.subheader("Company Description:")
                st.markdown(company_markdown)

                self.processing = False

        if markdown_response:
            if cv_rating_button:
                self.ui_handler.export_to_markdown(markdown_response, f"cv_rating_{id_input}.md")
            elif cover_letter_button:
                self.ui_handler.export_to_markdown(
                    markdown_response, f"example_cover_letter_{id_input}.md"
                )
            elif cv_edit_suggestions_button:
                self.ui_handler.export_to_markdown(
                    markdown_response, f"cv_edit_suggestions_{id_input}.md"
                )

        if st.button("Clear Cache"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache cleared!")

        if self.processing:
            st.empty()
            time.sleep(0.1)
            st.experimental_rerun()


if __name__ == "__main__":
    app = App()
    app.run()
