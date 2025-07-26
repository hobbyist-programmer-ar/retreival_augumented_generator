# Setting up this project

## Setup for a Virtual Environment
* Execute the below mentioned command to create a Virtual environment.
* This Virtual Environment will be used to install all of the required python packages
```bash
python3 -m venv .ragvenv ## Creates the venv in the folder mentioned in the second argument
source .ragvenv/bin/activate ## Activate the ragvenv that we just created
which python ## Checks if the venv is activated
## O/P for the command will be the ./.ragvenv/bin/python folder.
```

## Prep th PIP
* Make sure you are using the latest version of pip to install all the python libraries
```bash
python3 -m pip install --upgrade pip ## Upgrades the PIP version
python3 -m pip --version ## Check ths installed version of PIP
## O/P pip 25.1.1 from ./.ragvenv/lib/python3.13/site-packages/pip
```


### Install all the necessary Packages
* Now we need to install all the required libraries for this project
```bash
pip install --quiet --upgrade langchain-text-splitters langchain-community langgraph
```

### Getting the Lang Smith Key
Many of the applications you build with LangChain will contain multiple steps with multiple invocations of LLM calls. As these applications get more complex, it becomes crucial to be able to inspect what exactly is going on inside your chain or agent. The best way to do this is with LangSmith.
After you sign up at the link above, make sure to set your environment variables, in the bash cource of z shell source which ever is being used in the system ,  to start logging traces

```bash
export LANGSMITH_TRACING="true"
export LANGSMITH_API_KEY="..."
```

### Install the Cmponents
#### Install the Chat model to be used
1. We use the chat model to give the Context Message from the Vector DB and the User Message and get back a proper human readable Natural Language Response.
2. In this Project we are using the Mistral AI Embedding model.

```bash
pip install -qU "langchain[mistralai]"
```
#### Install the embedding model
1. The embedding model is used to get the user input and get the relevant document from the Vector Database to process it furth. Based on the Number ort result an appropriate number of document is returned
```bash
pip install -qU langchain-mistralai
```

#### Install Vector Store
1. We are Storing the data in a vector store for getting the context to be passed on to the model.
2. The Markdown data is is converted to chucks and we create the document with these chunks which contains the metadata of these chunks.
3. In this project we are using an In Memory Vector database Langchain FAISS and the necessary installations are given below
```bash
pip install -qU langchain-core
pip install sentence-transformers
## Based on the Processor you have install one of the below
pip install faiss-gpu # If you have any NVidia CUDA Supported gpu
pip install faiss-cpu # If there is not CUDA Supported GPU
```
