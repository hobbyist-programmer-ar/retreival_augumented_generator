# main_pipeline.py

import argparse
import sys
import os
import json

# --- Fix for ModuleNotFoundError ---
# This ensures the script can find the project's modules.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data_persistance.document_persistance import VectorStoreManager
from data_persistance.search_processor import SearchProcessor

def run_pipeline():
    """
    Orchestrates the entire RAG pipeline from ingestion to querying
    with a single command.
    """
    parser = argparse.ArgumentParser(
        description="A one-step script to build a vector store from markdown files and immediately start querying it."
    )
    parser.add_argument(
        '--input_path',
        type=str,
        required=True,
        help="Path to the directory containing the markdown files."
    )
    parser.add_argument(
        '--k',
        type=int,
        help="Number of top results to retrieve for each query.",
        default=2
    )
    args = parser.parse_args()

    try:
        # --- Step 1: Ingestion ---
        print("--- Step 1: Building Vector Store ---")
        print(f"Reading markdown files from: {args.input_path}")

        # Instantiate the manager and build the store in memory
        ingestion_manager = VectorStoreManager()
        ingestion_manager.process_directory_and_build_store(args.input_path)

        # Check if the vector store was created
        if not ingestion_manager.vector_store:
            print("Error: Vector store could not be built. Please check the input files.")
            sys.exit(1)

        print("--- Vector Store Built Successfully ---")

        # --- Step 2: Retrieval Setup ---
        print("\n--- Step 2: Initializing Search Processor ---")

        # Pass the in-memory vector store directly to the SearchProcessor
        searcher = SearchProcessor(ingestion_manager.vector_store)

        print("--- Search Processor Ready ---")

        # --- Step 3: Interactive Querying ---
        print("\nYou can now ask questions about the documents. Type 'exit' to quit.")
        while True:
            try:
                user_query = input("Query> ")
                if user_query.lower() == 'exit':
                    break
                if not user_query:
                    continue

                results = searcher.retrieve_and_reconstruct_sections(user_query, k=args.k)

                print("\n--- Reconstructed Sections ---")
                if not results:
                    print("No relevant sections found.")
                else:
                    print(json.dumps(results, indent=2))
                print("\n" + "-" * 20)

            except KeyboardInterrupt:
                print("\nExiting query loop.")
                break

    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure the input path is a valid directory containing markdown files.")
        sys.exit(1)

if __name__ == '__main__':
    run_pipeline()
