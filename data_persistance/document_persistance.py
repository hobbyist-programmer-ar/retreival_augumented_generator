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

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
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
        """
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)
        text = re.sub(r'(\*\*|__|\*|_)(.*?)\1', r'\2', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*>\s?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        return text.strip()

    def _parse_markdown_to_documents(self, markdown_data: Dict[str, str]) -> List[Document]:
        """
        Parses and cleans markdown content into a list of LangChain Documents.
        """
        all_documents = []
        for file_name, content in markdown_data.items():
            if not content.strip():
                continue
            page_title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
            page_title = self._clean_markdown_text(page_title_match.group(1)) if page_title_match else file_name
            sections = re.split(r'(^#+\s+.*)', content, flags=re.MULTILINE)
            if sections[0].strip():
                cleaned_intro = self._clean_markdown_text(sections[0].strip())
                chunks = self.text_splitter.split_text(cleaned_intro)
                for chunk in chunks:
                    metadata = {"section_name": "Introduction", "page_title": page_title, "file_name": file_name, "source": "Markdown File"}
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
                        metadata = {"section_name": section_name, "page_title": page_title, "file_name": file_name, "source": "Markdown File"}
                        all_documents.append(Document(page_content=chunk, metadata=metadata))
        return all_documents

    def build_vector_store_from_dict(self, markdown_data: Dict[str, str]) -> FAISS:
        """
        Creates documents from a markdown dictionary and builds a FAISS vector store.
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
            human_readable_docs.append({"content": document.page_content, "metadata": document.metadata})
        return human_readable_docs

    def query_vector_store(self, query: str, k: int = 4) -> List[Document]:
        """
        Performs a similarity search on the vector store.

        Args:
            query (str): The question or text to search for.
            k (int): The number of top results to return.

        Returns:
            A list of LangChain Document objects that are most relevant to the query.

        Raises:
            ValueError: If the vector store has not been built yet.
        """
        if not self.vector_store:
            raise ValueError("Vector store has not been built. Call 'build_vector_store' first.")

        # The similarity_search method returns a list of documents and their scores
        results = self.vector_store.similarity_search(query, k=k)
        return results

# This block allows the script to be executed directly from the command line.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process markdown files and store them in a FAISS vector DB.")
    parser.add_argument('--path', type=str, help="Path to the directory with markdown files. If not provided, you will be prompted.", default=None)
    args = parser.parse_args()

    input_path = args.path
    is_demo = False

    if not input_path:
        print("No directory path provided via command-line argument.")
        try:
            input_path = input("Please enter the path to your markdown directory (or press Enter for a demo): ")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user. Exiting.")
            sys.exit()

    if not input_path:
        print("\nNo path entered. Creating and running a temporary demo...")
        is_demo = True
        input_path = 'temp_rag_files'
        if os.path.exists(input_path):
            shutil.rmtree(input_path)
        os.makedirs(input_path)
        with open(os.path.join(input_path, 'rag_overview.md'), 'w') as f:
            f.write("# All About RAG\n\nThis document explains Retrieval Augmented Generation.\n\n## Core Idea\n\nThe core idea is to retrieve relevant documents from a knowledge base and provide them as context to a large language model (LLM) to generate a response. This improves accuracy and reduces hallucinations.")
        with open(os.path.join(input_path, 'setup_guide.md'), 'w') as f:
            f.write("# System Setup\n\nFollow these steps.\n\n### Python\n\n* Install Python 3.9+.\n\n### Dependencies\n\n> Run `pip install -r requirements.txt`.")
        print(f"Demo files created in '{input_path}/'")

    try:
        manager = VectorStoreManager()
        print(f"\nProcessing files from: {os.path.abspath(input_path)}")
        manager.process_directory_and_build_store(input_path)
        print("\n--- Vector Store Built Successfully ---")

        # --- Interactive Query Loop ---
        print("\nYou can now ask questions about the documents. Type 'exit' to quit.")
        while True:
            try:
                user_query = input("Query> ")
                if user_query.lower() == 'exit':
                    break
                if not user_query:
                    continue

                # Perform the query
                results = manager.query_vector_store(user_query, k=5)

                print("\n--- Top Results ---")
                if not results:
                    print("No relevant documents found.")
                else:
                    for i, doc in enumerate(results):
                        print(f"Result {i+1}:")
                        print(f"  Content: {doc.page_content}")
                        print(f"  Metadata: {doc.metadata}\n")
                print("-" * 20)

            except KeyboardInterrupt:
                print("\nExiting query loop.")
                break

    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure the path is a valid directory containing markdown files.")
    finally:
        if is_demo and os.path.exists(input_path):
            print(f"\nCleaning up demo directory: {input_path}")
            shutil.rmtree(input_path)
