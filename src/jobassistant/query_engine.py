import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

import requests
import streamlit as st
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import Document
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama


class QueryEngine(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def query(self, query: Dict[str, Any]) -> str:
        """Abstract method to query the engine."""
        pass


class PlainQueryEngine(QueryEngine):
    def __init__(self, config):
        """Initialize PlainQueryEngine with a model name."""
        super().__init__(config)
        self.model_name = self.config.model

    def query(self, query: Dict[str, Any]) -> str:
        """Query the API with the given input."""
        try:
            query["model"] = self.model_name
            with requests.post(
                self.config.endpoint_url, json=query, stream=False, timeout=600
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


class RAGQueryEngine(QueryEngine):
    def __init__(self, config: Dict[str, Any], docs_path: str = None):
        """Initialize RAGQueryEngine with model name and optional docs path."""
        super().__init__(config)
        self.model_name = self.config.model
        self.docs_path = docs_path
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
        Settings.llm = Ollama(
            model=self.model_name,
            request_timeout=600.0,
            additional_kwargs={
                "temperature": self.config.temperature,
                "seed": 42,
                "num_predict": self.config.num_predict,
                "num_ctx": self.config.num_ctx,
            },
        )
        docs_paths = [Path(self.config.docs_dir)]
        if self.docs_path:
            docs_paths.append(Path(self.docs_path))
        self.query_engine = self.initialize_vectorstore(docs_paths)

    @staticmethod
    @st.cache_resource
    def initialize_vectorstore(docs_paths):
        """Initialize the vector store with documents."""
        documents = []
        for _docs_path in docs_paths:
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
