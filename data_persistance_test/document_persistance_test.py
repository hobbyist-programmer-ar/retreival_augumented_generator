# test_document_persistance.py

import unittest
import os
import sys
import tempfile
import shutil

# --- Fix for ModuleNotFoundError ---
# This ensures the test script can find the project's modules.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Langchain is a peer dependency for this module
from langchain_community.vectorstores import FAISS
from data_persistance.document_persistance import VectorStoreManager

class TestVectorStoreManager(unittest.TestCase):
    """
    Revamped and comprehensive unit test suite for the VectorStoreManager class.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up mock data that can be shared across all tests.
        This runs only once for the entire class.
        """
        cls.long_section_content = "This is a very long piece of text designed to test the chunking functionality of the text splitter. It needs to be over one hundred characters to ensure that it actually gets split into multiple documents as per the requirements. Let's add more words to be absolutely sure."

        cls.mock_markdown_data = {
            "test_file1": (
                "# Main Page Title\n\n"
                "This is the introduction before the first real section.\n\n"
                "## Section One\n\n"
                "Content for the first section. It is short.\n\n"
                f"## Section Two (Long)\n\n{cls.long_section_content}"
            ),
            "test_file2": (
                "## No H1 Title\n\n"
                "This content belongs to a file with no H1, so the filename should be the title."
            ),
            "test_file3_empty": "",
            "test_file4_whitespace": "   \n\n\t   "
        }

    def setUp(self):
        """
        This method is called before each individual test.
        It sets up a fresh VectorStoreManager instance and a temporary directory.
        """
        self.manager = VectorStoreManager(chunk_size=100, chunk_overlap=10)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """
        This method is called after each test to clean up the temporary directory.
        """
        shutil.rmtree(self.temp_dir)

    def test_parse_markdown_documents_metadata(self):
        """
        Tests if metadata (page_title, section_name, file_name) is correctly assigned.
        """
        documents = self.manager._parse_markdown_to_documents(self.mock_markdown_data)

        # Find the document for the "Introduction" of test_file1
        intro_doc = next(d for d in documents if d.metadata['section_name'] == 'Introduction')
        self.assertEqual(intro_doc.metadata['page_title'], 'Main Page Title')
        self.assertEqual(intro_doc.metadata['file_name'], 'test_file1')
        self.assertEqual(intro_doc.page_content, 'This is the introduction before the first real section.')

        # Find the document for "Section One"
        section_one_doc = next(d for d in documents if d.metadata['section_name'] == 'Section One')
        self.assertEqual(section_one_doc.metadata['page_title'], 'Main Page Title')

        # Find the document where filename is used as page_title
        no_h1_doc = next(d for d in documents if d.metadata['file_name'] == 'test_file2')
        self.assertEqual(no_h1_doc.metadata['page_title'], 'test_file2')
        self.assertEqual(no_h1_doc.metadata['section_name'], 'No H1 Title')

    def test_chunking_of_long_sections(self):
        """
        Tests if long sections are correctly split into multiple documents (chunks).
        """
        documents = self.manager._parse_markdown_to_documents(self.mock_markdown_data)

        # Filter for chunks from the long section
        long_section_chunks = [d for d in documents if d.metadata['section_name'] == 'Section Two (Long)']

        # The section should be split into at least two chunks
        self.assertGreater(len(long_section_chunks), 1, "Long section was not split into multiple chunks.")

        # All chunks from the same section should have identical metadata
        first_chunk_metadata = long_section_chunks[0].metadata
        for chunk in long_section_chunks[1:]:
            self.assertEqual(chunk.metadata, first_chunk_metadata)

        # The combined content of the chunks should approximate the original content
        reconstructed_content = "".join(chunk.page_content for chunk in long_section_chunks)
        self.assertTrue(self.long_section_content.startswith(long_section_chunks[0].page_content))
        self.assertTrue(len(reconstructed_content) > len(self.long_section_content) - 20, "Reconstructed content is too small")


    def test_empty_and_whitespace_files_are_ignored(self):
        """
        Tests that empty files or files with only whitespace do not produce documents.
        """
        documents = self.manager._parse_markdown_to_documents(self.mock_markdown_data)

        # No documents should have the filename of the empty or whitespace files
        filenames_in_docs = {doc.metadata['file_name'] for doc in documents}
        self.assertNotIn('test_file3_empty', filenames_in_docs)
        self.assertNotIn('test_file4_whitespace', filenames_in_docs)

    def test_build_vector_store_and_get_all_documents(self):
        """
        Tests the end-to-end process of building the store and retrieving documents.
        """
        store = self.manager.build_vector_store_from_dict(self.mock_markdown_data)
        self.assertIsNotNone(self.manager.vector_store)
        self.assertIsInstance(store, FAISS)

        retrieved_docs = self.manager.get_all_documents_in_store()

        # Expected chunks:
        # file1: intro(1), section1(1), section2(2) -> 4
        # file2: section1(1) -> 1
        # Total -> 5
        self.assertEqual(len(retrieved_docs), 5)

        # Check the structure of a retrieved document
        sample_doc = retrieved_docs[0]
        self.assertIn('content', sample_doc)
        self.assertIn('metadata', sample_doc)

    def test_get_documents_raises_error_if_store_not_built(self):
        """
        Tests that calling get_all_documents_in_store before building raises a ValueError.
        """
        with self.assertRaisesRegex(ValueError, "Vector store has not been built"):
            self.manager.get_all_documents_in_store()

    def test_build_store_raises_error_for_empty_input(self):
        """
        Tests that building a store with no valid documents raises a ValueError.
        """
        with self.assertRaisesRegex(ValueError, "No documents were created"):
            self.manager.build_vector_store_from_dict({"file1": "", "file2": "   "})

    def test_integration_with_process_directory_and_build_store(self):
        """
        An integration test that uses the file system to test the whole process.
        """
        # Create mock files in the temporary directory
        for filename, content in self.mock_markdown_data.items():
            with open(os.path.join(self.temp_dir, f"{filename}.md"), "w") as f:
                f.write(content)

        # Run the full process
        self.manager.process_directory_and_build_store(self.temp_dir)
        retrieved_docs = self.manager.get_all_documents_in_store()

        self.assertEqual(len(retrieved_docs), 5)

        # Verify one of the documents to ensure the process worked
        found_doc = any(
            d['metadata']['section_name'] == 'Section One' and
            d['metadata']['file_name'] == 'test_file1'
            for d in retrieved_docs
        )
        self.assertTrue(found_doc, "Document from integration test was not found.")


# This allows the test to be run from the command line
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
