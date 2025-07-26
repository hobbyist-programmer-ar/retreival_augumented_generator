# document_persistance.py

import re
import os
import sys
import argparse
import json
import shutil
from typing import Dict, List, Optional

# To make this module runnable, you might need to install the following packages:
# pip install langchain langchain-community faiss-cpu sentence-transformers
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Fix for ModuleNotFoundError ---
# This ensures the script can find the project's modules when run directly.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from document_processor.markdown_processor import MarkdownProcessor


class VectorStoreManager:
    """
    Manages the creation, processing, and storage of documents in a FAISS vector store
    from markdown files.
    """

    def __init__(self, chunk_size: int = 200, chunk_overlap: int = 20):
        """
        Initializes the VectorStoreManager.

        Args:
            chunk_size (int): The maximum size of text chunks.
            chunk_overlap (int): The overlap between consecutive chunks.
        """
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        self.vector_store: Optional[FAISS] = None

    def _clean_markdown_text(self, text: str) -> str:
        """
        Removes common markdown syntax from a string to prepare it for embedding.

        Args:
            text: The raw markdown text.

        Returns:
            The cleaned text.
        """
        # Remove links, keeping the link text: [text](url) -> text
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # Remove image tags, keeping the alt text: ![alt](src) -> alt
        text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)
        # Remove bold/italics: **text** or *text* -> text
        text = re.sub(r'(\*\*|__|\*|_)(.*?)\1', r'\2', text)
        # Remove inline code backticks: `code` -> code
        text = re.sub(r'`(.*?)`', r'\1', text)
        # Remove list markers (at the beginning of a line)
        text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
        # Remove blockquotes
        text = re.sub(r'^\s*>\s?', '', text, flags=re.MULTILINE)
        # Remove horizontal rules
        text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

        return text.strip()

    def _parse_markdown_to_documents(self, markdown_data: Dict[str, str]) -> List[Document]:
        """
        Parses a dictionary of markdown content into a list of LangChain Documents.
        The content is cleaned of markdown syntax before being stored.

        Args:
            markdown_data: A dictionary with filename as key and markdown content as value.

        Returns:
            A list of LangChain Document objects ready for embedding.
        """
        all_documents = []

        for file_name, content in markdown_data.items():
            if not content.strip():
                continue # Skip empty files

            page_title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
            page_title = page_title_match.group(1).strip() if page_title_match else file_name

            sections = re.split(r'(^#+\s+.*)', content, flags=re.MULTILINE)

            if sections[0].strip():
                cleaned_intro = self._clean_markdown_text(sections[0].strip())
                chunks = self.text_splitter.split_text(cleaned_intro)
                for chunk in chunks:
                    metadata = {
                        "section_name": "Introduction",
                        "page_title": page_title,
                        "file_name": file_name,
                        "source": "Markdown File"
                    }
                    all_documents.append(Document(page_content=chunk, metadata=metadata))

            for i in range(1, len(sections), 2):
                if i + 1 < len(sections):
                    header = sections[i].strip()
                    body = sections[i+1].strip()

                    section_name = self._clean_markdown_text(header.lstrip('#').strip())
                    cleaned_body = self._clean_markdown_text(body)

                    if not cleaned_body:
                        continue

                    chunks = self.text_splitter.split_text(cleaned_body)

                    for chunk in chunks:
                        metadata = {
                            "section_name": section_name,
                            "page_title": page_title,
                            "file_name": file_name,
                            "source": "Markdown File"
                        }
                        all_documents.append(Document(page_content=chunk, metadata=metadata))

        return all_documents

    def build_vector_store_from_dict(self, markdown_data: Dict[str, str]) -> FAISS:
        """
        Creates documents from a markdown dictionary and builds a FAISS vector store.

        Args:
            markdown_data: A dictionary with filename as key and markdown content as value.

        Returns:
            A FAISS vector store instance containing the processed documents.
        """
        documents = self._parse_markdown_to_documents(markdown_data)
        if not documents:
            raise ValueError("No documents were created from the provided markdown data. Check the content.")

        print(f"Creating vector store with {len(documents)} document chunks.")
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        return self.vector_store

    def process_directory_and_build_store(self, directory_path: str) -> FAISS:
        """
        A convenience method to process a directory of markdown files and build the vector store.
        """
        markdown_processor = MarkdownProcessor()
        markdown_data = markdown_processor.read_markdown_files_from_directory(directory_path)
        return self.build_vector_store_from_dict(markdown_data)

    def get_all_documents_in_store(self) -> List[Dict]:
        """
        Retrieves all documents from the vector store in a human-readable format.
        """
        if not self.vector_store:
            raise ValueError("Vector store has not been built. Call a build method first.")

        docstore = self.vector_store.docstore._dict

        human_readable_docs = []
        for doc_id, document in docstore.items():
            human_readable_docs.append({
                "content": document.page_content,
                "metadata": document.metadata
            })
        return human_readable_docs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Process markdown files from a directory and store them in a FAISS vector DB."
    )
    parser.add_argument(
        '--path',
        type=str,
        help="The path to the directory containing markdown files.",
        default=""
    )
    args = parser.parse_args()

    # input_path = args.path
    input_path = "./test-data"
    is_demo = False

    if not input_path:
        print("No path provided. Creating a temporary demo directory...")
        is_demo = True
        input_path = 'temp_rag_files'
        if os.path.exists(input_path):
            shutil.rmtree(input_path)
        os.makedirs(input_path)

        with open(os.path.join(input_path, 'rag_overview.md'), 'w') as f:
            f.write(
                "# All About RAG\n\nThis document explains the concept of **Retrieval Augmented Generation**.\n\n"
                "## Core Idea\n\nThe core idea is to retrieve relevant documents from a `knowledge base` and provide them as context to a large language model (LLM) to generate a response. This improves [accuracy](http://example.com) and reduces hallucinations."
            )
        with open(os.path.join(input_path, 'setup_guide.md'), 'w') as f:
            f.write(
                "# System Setup\n\nFollow these steps to set up the environment.\n\n"
                "### Python\n\n* Install Python 3.9 or higher.\n\n"
                "### Dependencies\n\n> Run `pip install -r requirements.txt`."
            )
        print(f"Demo files created in '{input_path}/'")

    try:
        manager = VectorStoreManager()
        print(f"\nProcessing files from: {input_path}")
        manager.process_directory_and_build_store(input_path)

        print("\n--- Documents in Vector Store (Cleaned Content) ---")
        all_docs = manager.get_all_documents_in_store()

        print(json.dumps(all_docs, indent=2))
        print("\nProcessing complete.")

    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if is_demo and os.path.exists(input_path):
            print(f"\nCleaning up demo directory: {input_path}")
            shutil.rmtree(input_path)
