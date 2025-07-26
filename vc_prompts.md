### Read Markdown data
You are an Expert python developer. You need to create some class to read and convert markdown test with the rules mentioned below.

Create a python class that will have functions which should do the following operations
1. It should take the input as a file path
2. It should read all the markdown files in the file path and create an output with the following structure
```json
{
	"file1" : "content of the file 1",
	"file2" : "content of the file 2"
}
```
#### Explanation of input
The method argument or the input is the directory that will contain a bunch of markdown files with some content in it.
#### Explanation of output
The output of the file should be a dict where the name of the file should be the key and the value should be the content of the file
#### Non Functional Requirements
It should make the class in such a way that I should be able to import these function at different class.
The Unit test cases should be written for these methods
The code should be optimized with detailed comments along the way
### Store Data in an in-memory vector DB
You are an expert AI Developer trying to create an local RAG project
It should encompass the following use cases

1. We need to process the data from the markdown processor and store it in a local instance of a vector database.
2. We are planning to use the Langchain FAISS database as the vector database.
3. based on the output of the markdown processor this should create the data documents following the below mentioned rules.
	1. It should chuck the data based on the sections and subsections for the markdown format.
	2. The document meta data should have the Section Name, the Page Title and the File name.
	3. Within each section if the chunk size is greater than 200 it should be split
#### Explanation of the input
I will provide a file path from this method and there should be a call made tot he markdown_processor to parse this file and provide get the Dict out put
The second method Argument is a Dict of the below format. This is the output of the above written markdown_processor method call.
```json
{
	"file1" : "content of the file 1",
	"file2" : "content of the file 2"
}
```
The Key is the name of the file, the value is the content of the markdown file in the markdown format.

#### Explanation of the output
The Output should be a vector database document. Each document should contain a section/subsection of the markdown file.
The Document Metadata should contain the the following data
1. Section Name
2. Page Title
3. File Name
4. Source (in this case its a constant which is Markdown File)

#### Non-Functional Requirement
1. There should be unit test cases for all the methods
2. The method should have proper method Documentations
3. The File name should be document_persistance.py
4. It should be made an an importable module for other classes.
5. There should be a get method which should allow me to print the documents stored in the vector database in a human readable format
