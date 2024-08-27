import json
import os
import re
import shutil
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from crawler.crawler.__main__ import main as run_crawler
from llama_index.core import (ServiceContext, Settings, SimpleDirectoryReader,
                              StorageContext, VectorStoreIndex,
                              get_response_synthesizer,
                              load_index_from_storage,
                              set_global_service_context)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from prompts import (additional_context_for_website, cover_letter_prompt,
                     cv_edit_suggestions_prompt, job_rating_prompt)

from extract import extract_job_md
from wikipedia import search_wikipedia

ENDPOINT_URL = "http://localhost:11434/api/chat"
TAGS_URL = "http://localhost:11434/api/tags"
DOCS_DIR = "./docs"
NUM_PREDICT_LEN = 12000
NUM_CTX = 116000


@st.cache_data(ttl=3600)
def fetch_available_models() -> List[str]:
    """Fetch available models from the API."""
    try:
        response = requests.get(TAGS_URL)
        response.raise_for_status()
        data = response.json()
        return [model["name"] for model in data["models"]]
    except requests.RequestException as e:
        st.error(f"Failed to fetch available models: {str(e)}")
        return []


class QueryEngine(ABC):
    @abstractmethod
    def query(self, query: Dict[str, Any]) -> str:
        """Abstract method to query the engine."""
        pass


class PlainQueryEngine(QueryEngine):
    def __init__(self, model_name: str):
        """Initialize PlainQueryEngine with a model name."""
        self.model_name = model_name

    def query(self, query: Dict[str, Any]) -> str:
        """Query the API with the given input."""
        try:
            query["model"] = self.model_name
            with requests.post(
                ENDPOINT_URL, json=query, stream=False, timeout=600
            ) as response:
                response.raise_for_status()
                return self.process_streaming_response(response)
        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred while communicating with the API: {str(e)}")
            return None

    def process_streaming_response(self, response: requests.Response) -> str:
        """Process the streaming response from the API."""
        full_response = ""
        for line in response.iter_lines():
            if line:
                json_obj = json.loads(line)
                if "message" in json_obj and "content" in json_obj["message"]:
                    full_response += json_obj["message"]["content"]
        return full_response


class JobEvaluator:
    def __init__(self, query_engine: QueryEngine):
        """Initialize JobEvaluator with a query engine."""
        self.query_engine = query_engine

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
                "num_predict": NUM_PREDICT_LEN,
                "num_ctx": NUM_CTX,
                "temperature": 0.1,
            },
        }
        system_content = f"As an AI assistant specializing in resume evaluation, your task is to analyze a CV for given job details. Here is my CV:\n\n {cv_markdown}\n\n"

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


class RAGQueryEngine(QueryEngine):
    def __init__(self, model_name: str, docs_path: str = None):
        """Initialize RAGQueryEngine with model name and optional docs path."""
        self.model_name = model_name
        self.docs_path = docs_path
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
        Settings.llm = Ollama(
            model=model_name,
            request_timeout=600.0,
            additional_kwargs={
                "temperature": 0.1,
                "seed": 42,
                "num_predict": NUM_PREDICT_LEN,
                "num_ctx": NUM_CTX,
            },
        )
        self.query_engine = self.initialize_vectorstore(docs_path)

    @staticmethod
    @st.cache_resource
    def initialize_vectorstore(docs_path):
        """Initialize the vector store with documents."""
        _docs_paths = (
            [Path(DOCS_DIR), Path(docs_path)] if docs_path else [Path(DOCS_DIR)]
        )
        documents = []
        for _docs_path in _docs_paths:
            if _docs_path.exists():
                print(_docs_path)
                _documents = SimpleDirectoryReader(_docs_path).load_data()
                documents.extend(_documents)
            else:
                st.warning(
                    "No documents found in the docs directory. Please upload some documents."
                )
                continue

            index = VectorStoreIndex.from_documents(
                documents,
                transformations=[
                    SentenceSplitter(chunk_size=1024, chunk_overlap=0),
                ],
            )
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=5,
            )
            qe = RetrieverQueryEngine(
                retriever=retriever,
            )
            return qe

    def query(self, query: Dict[str, Any]) -> str:
        """Query the RAG engine with the given input."""
        if self.query_engine is None:
            return "No documents have been uploaded for RAG. Please upload some documents and try again."
        query_string = f"{query['messages'][1]['content']}"
        Settings.llm.system_prompt = query["messages"][0]["content"]
        return str(self.query_engine.query(query_string))


class App:
    def __init__(self, use_rag: bool = False):
        """Initialize the App with optional RAG usage."""
        self.use_rag = use_rag
        self.response_parser = ResponseParser()
        self.ui_handler = UIHandler()
        self.processing = False

    @staticmethod
    @st.cache_data(ttl=3600)
    def read_cv_md():
        """Read the CV markdown file."""
        try:
            with open("./cv.md", "r") as file:
                return file.read()
        except FileNotFoundError:
            st.error(
                "CV file not found. Please ensure 'cv.md' exists in the same directory as this script."
            )
            return None

    @staticmethod
    def handle_file_upload():
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
            os.makedirs(DOCS_DIR, exist_ok=True)

            for uploaded_file in uploaded_files:
                file_path = os.path.join(DOCS_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            st.success(f"Uploaded {len(uploaded_files)} document(s) successfully!")

    @staticmethod
    @st.cache_data(ttl=3600)
    def crawl_website(url):
        if url:
            crawled_data_path = run_crawler(url)
            # self.add_crawled_data_to_rag(crawled_data_path)
            st.success(
                f"Crawled website to {crawled_data_path} document(s) successfully!"
            )

            return crawled_data_path

    # @staticmethod
    # def add_crawled_data_to_rag(crawled_data_path):
    #     for filename in  Path(crawled_data_path).glob('*.json'):
    #         with open(filename, 'r') as f:
    #             data = json.load(f)
    #             title = data.get('title', '')
    #             text = data.get('text', '')
    #             _dir_path = Path(DOCS_DIR, f"{filename.parent.name}")
    #             _dir_path.mkdir(parents=True, exist_ok=True)
    #             if text:
    #                 _path = _dir_path / f"{filename.name}"
    #                 with open(_path, 'w') as f:
    #                     f.write(f"Title: {title}\n\n{text}")

    def run(self):
        st.title("Jobbing Assistant")

        available_models = fetch_available_models()
        default_model_index = available_models.index("llama3.1:latest")
        self.selected_model = st.selectbox(
            "Select a model:", available_models, index=default_model_index
        )
        markdown_response = None
        docs_path = None

        self.use_rag = st.checkbox(
            "Use RAG (Retrieval-Augmented Generation)", value=False
        )
        if self.use_rag:
            self.handle_file_upload()

        with st.form("job_form"):

            id_input = st.text_input("Enter Job ID:", max_chars=100)

            url_input = st.text_input("Or enter URL to crawl")
            # if st.button("Crawl Website"):
            #     docs_path = self.crawl_website(url)
            #     self.use_rag = True

            #     # st.success(f"Crawled {url} and added data to RAG pipeline. Data saved to: {docs_path}")
            # else:
            #     docs_path = None

            additional_context = st.text_area(
                "Additional Context (optional):", height=100
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                cv_rating_button = st.form_submit_button("Get CV Rating")
            with col2:
                cover_letter_button = st.form_submit_button("Generate Cover Letter")
            with col3:
                cv_edit_suggestions_button = st.form_submit_button(
                    "Get CV Edit Suggestions"
                )

            if (id_input or url_input) and (
                cv_rating_button or cover_letter_button or cv_edit_suggestions_button
            ):

                if url_input:
                    docs_path = self.crawl_website(url_input)
                    self.use_rag = True

                if docs_path:
                    self.query_engine = RAGQueryEngine(
                        self.selected_model, docs_path=docs_path
                    )
                else:
                    if self.use_rag:
                        self.query_engine = RAGQueryEngine(self.selected_model)
                    else:
                        self.query_engine = PlainQueryEngine(self.selected_model)

                self.job_evaluator = JobEvaluator(self.query_engine)
                self.processing = True
                if id_input:
                    job_markdown, job_details = extract_job_md(id_input)
                    company_markdown = search_wikipedia(job_details["company"])
                    full_markdown = company_markdown + "\n" + job_markdown
                else:
                    job_markdown, job_details = "", {}  # extract_job_md(url_input)
                    job_details["company_name"] = re.sub(
                        r"https?://\S+", "", url_input
                    ).split("/")[0]
                    company_markdown = ""  # search_wikipedia(job_details["company"])
                    full_markdown = ""

                cv_markdown = self.read_cv_md()
                if cv_markdown is None:
                    st.stop()

                parsed_response = ""
                with st.spinner("Processing... This may take a moment."):
                    if cv_rating_button:
                        response = self.job_evaluator.evaluate_cv(
                            cv_markdown, full_markdown, job_details, additional_context
                        )
                        print("CV Rating Response:", response)
                        if response:
                            parsed_response = self.response_parser.parse_evaluation(
                                response
                            )
                            markdown_response = (
                                self.ui_handler.display_structured_response(
                                    parsed_response
                                )
                            )
                        else:
                            st.error(
                                "Failed to evaluate the CV. Please try again later."
                            )
                    elif cover_letter_button:
                        parsed_response = self.job_evaluator.write_cover_letter(
                            cv_markdown, full_markdown, job_details, additional_context
                        )
                        print("Cover Letter Response:", parsed_response)
                        markdown_response = parsed_response
                        if parsed_response:
                            st.subheader("Example Cover Letter:")
                            st.markdown(parsed_response)
                        else:
                            st.error(
                                "Failed to generate a cover letter. Please try again later."
                            )
                    elif cv_edit_suggestions_button:
                        response = self.job_evaluator.suggest_cv_edits(
                            cv_markdown, full_markdown, job_details, additional_context
                        )
                        print("CV Edit Suggestions Response:", response)
                        if response:
                            parsed_response = (
                                self.response_parser.parse_cv_edit_suggestions(response)
                            )
                            markdown_response = (
                                self.ui_handler.display_cv_edit_suggestions(
                                    parsed_response
                                )
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
                self.ui_handler.export_to_markdown(
                    markdown_response, f"cv_rating_{id_input}.md"
                )
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
    import argparse

    parser = argparse.ArgumentParser(description="Job Application Assistant")
    parser.add_argument("--model", default="llama3.1:latest", help="Model name to use")
    parser.add_argument(
        "--num_predict",
        type=int,
        default=NUM_PREDICT_LEN,
        help="Number of tokens to predict",
    )
    parser.add_argument(
        "--num_ctx", type=int, default=NUM_CTX, help="Context window size"
    )
    args = parser.parse_args()

    # Reset globals based on command line arguments
    NUM_PREDICT_LEN = args.num_predict
    NUM_CTX = args.num_ctx
    app.run()
