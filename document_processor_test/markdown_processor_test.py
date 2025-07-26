# test_markdown_processor.py

import unittest
import os
import sys
import tempfile
import shutil

# --- Fix for ModuleNotFoundError ---
# This code adds the project's root directory to the Python path.
# This allows the script to find and import the MarkdownProcessor module
# from its location in the project structure, regardless of where the
# test script is executed from.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Updated import path to reflect the new project structure
from document_processor.markdown_processor import MarkdownProcessor

class TestMarkdownProcessor(unittest.TestCase):
    """
    Unit test suite for the MarkdownProcessor class using the built-in unittest library.
    """

    def setUp(self):
        """
        This method is called before each test.
        It sets up a temporary directory and mock files for testing.
        """
        # Create a temporary directory which will be automatically cleaned up
        self.temp_dir = tempfile.mkdtemp()
        self.processor = MarkdownProcessor()

        # --- Create mock files for testing ---
        # 1. A valid markdown file
        self.md_content1 = "# Header 1\n\nSome content."
        with open(os.path.join(self.temp_dir, "test1.md"), "w") as f:
            f.write(self.md_content1)

        # 2. Another valid markdown file with a different case extension
        self.md_content2 = "This is the second file."
        with open(os.path.join(self.temp_dir, "test2.MD"), "w") as f:
            f.write(self.md_content2)

        # 3. A file that is NOT a markdown file and should be ignored
        with open(os.path.join(self.temp_dir, "ignore.txt"), "w") as f:
            f.write("This text file should not be included.")

        # 4. A subdirectory that should be ignored
        os.makedirs(os.path.join(self.temp_dir, "subdir"))

    def tearDown(self):
        """
        This method is called after each test.
        It cleans up the temporary directory.
        """
        shutil.rmtree(self.temp_dir)

    def test_read_markdown_files_from_directory_success(self):
        """
        Tests the successful reading of markdown files from the directory.
        """
        # Call the method under test
        result = self.processor.read_markdown_files_from_directory(self.temp_dir)

        # Define the expected output
        expected = {
            "test1": self.md_content1,
            "test2": self.md_content2,
        }

        # Assert that the result matches the expected output
        self.assertEqual(result, expected)

    def test_empty_directory(self):
        """
        Tests the behavior with an empty directory.
        """
        # Create a new empty temporary directory
        empty_dir = tempfile.mkdtemp()
        try:
            result = self.processor.read_markdown_files_from_directory(empty_dir)
            # Expecting an empty dictionary
            self.assertEqual(result, {})
        finally:
            # Ensure cleanup
            shutil.rmtree(empty_dir)

    def test_non_existent_directory(self):
        """
        Tests that a FileNotFoundError is raised for a non-existent directory.
        """
        # Use assertRaises as a context manager to check for the expected exception
        with self.assertRaises(FileNotFoundError):
            self.processor.read_markdown_files_from_directory("non_existent_path_12345")

    def test_path_is_a_file(self):
        """
        Tests that a NotADirectoryError is raised if the path is a file.
        """
        # Get the path to one of the files we created
        file_path = os.path.join(self.temp_dir, "test1.md")
        with self.assertRaises(NotADirectoryError):
            self.processor.read_markdown_files_from_directory(file_path)


# This allows the test to be run from the command line
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
