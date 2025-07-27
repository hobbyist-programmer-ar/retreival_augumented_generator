# user_interface/ui_components.py

import streamlit as st
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

def add_custom_styling():
    """Injects custom CSS for styling the Streamlit app."""
    # Sourced from https://www.magicpattern.design/tools/css-backgrounds
    # A subtle, minimalist circuit board pattern for the background
    css = """
    <style>
        /* Base styling for light mode */
        body {
            background-color: #ffffff;
            background-image: radial-gradient(#d1d1d1 0.5px, #ffffff 0.5px);
            background-size: 15px 15px;
            color: #000000;
        }

        /* Styling for dark mode */
        body.dark-mode {
            background-color: #0e1117;
            background-image: radial-gradient(#4d4d4d 0.5px, #0e1117 0.5px);
            background-size: 15px 15px;
            color: #ffffff;
        }

        /* Apply dark mode based on system preference */
        @media (prefers-color-scheme: dark) {
            body:not(.light-mode) {
                background-color: #0e1117;
                background-image: radial-gradient(#4d4d4d 0.5px, #0e1117 0.5px);
                background-size: 15px 15px;
                color: #ffffff;
            }
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def login_page():
    """Displays the login page and handles authentication."""
    st.title("RAG Pipeline Login")

    with st.form("login_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="1234")
        submitted = st.form_submit_button("Login")

        if submitted:
            if username == "admin" and password == "1234":
                st.session_state.logged_in = True
                st.session_state.mode = "Admin" # Default to Admin mode after login
                st.rerun()
            else:
                st.error("Invalid username or password.")

def admin_mode():
    """The main interface for the Admin role."""
    st.title("⚙️ Admin Mode")
    st.markdown("---")

    # --- Section 1: Document Loading ---
    st.subheader("1. Load Documents into Vector DB")

    # Use a form to prevent rerunning on every input change
    with st.form("doc_loader_form", clear_on_submit=True):
        doc_path = st.text_input("Enter the path to your markdown documents folder:")
        submitted = st.form_submit_button("Load Documents")

        if submitted and doc_path:
            if not os.path.isdir(doc_path):
                st.error("The provided path is not a valid directory. Please try again.")
            else:
                with st.spinner(f"Processing documents from '{doc_path}'..."):
                    try:
                        # 1. Build the vector store in memory
                        manager = VectorStoreManager()
                        manager.process_directory_and_build_store(doc_path)

                        # 2. Initialize the search processor and save to session state
                        st.session_state.search_processor = SearchProcessor(manager.vector_store)
                        st.success("Documents loaded and vector store is ready!")
                    except Exception as e:
                        st.error(f"An error occurred during document processing: {e}")

    st.markdown("---")

    # --- Section 2: Raw Query Interface ---
    st.subheader("2. Raw Query Interface")

    if 'search_processor' not in st.session_state:
        st.warning("Please load documents first to enable the query interface.")
    else:
        with st.form("query_form"):
            query_text = st.text_area("Enter your search query:", height=100)
            k_value = st.number_input("Number of results to return (k):", min_value=1, max_value=10, value=2)
            query_submitted = st.form_submit_button("Execute Query")

            if query_submitted and query_text:
                with st.spinner("Searching..."):
                    try:
                        results = st.session_state.search_processor.retrieve_and_reconstruct_sections(
                            query=query_text,
                            k=k_value
                        )
                        st.success("Query executed successfully!")
                        st.json(results)
                    except Exception as e:
                        st.error(f"An error occurred during query execution: {e}")

def user_mode():
    """The main interface for the regular User."""
    st.title("💬 Chat Mode")
    st.info("The full chat interface is under construction. For now, you can use the search bar below.")

    st.text_input("Search the knowledge base...", key="user_search_bar", placeholder="Ask a question about the documents...")

    # Future implementation will go here

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="RAG Pipeline UI", layout="wide")
    add_custom_styling()

    # Initialize session state variables
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'mode' not in st.session_state:
        st.session_state.mode = "Login"
    if 'search_processor' not in st.session_state:
        st.session_state.search_processor = None

    # --- Main App Logic ---
    if not st.session_state.logged_in:
        login_page()
    else:
        # --- Sidebar Navigation ---
        st.sidebar.title("Navigation")
        st.session_state.mode = st.sidebar.radio(
            "Choose a mode:",
            ("Admin", "User"),
            index=0 if st.session_state.mode == "Admin" else 1
        )

        if st.sidebar.button("Logout"):
            # Clear session state on logout
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # --- Display selected mode ---
        if st.session_state.mode == "Admin":
            admin_mode()
        else:
            user_mode()

if __name__ == "__main__":
    main()
