# Retreival Augumented Generation
* RAG is a technique used to enable LLMs answer question based on a specific source of information. While LLMs are trained on the data available on the internet which could be useful on a high level this RAG allows use to add context to the LLM to specify the scope of search and answers. So the possibilities of retrieving randon information reduces.

## Overview
* RAG involves two mains components.
  * Indexing - A pipeline for ingesting data from a source and indexing it. This usually happens offline.
  * Retrieval and Generation - The actual RAG Chain which takes the use queries at run time and retrieves the relevan data from the index and passes that to the model.

### Indexing
* Load : First we need to load the data which is done with the [Document Loaders](https://python.langchain.com/docs/concepts/document_loaders/)
* Split : Text Splitters break large Documents in to smaller chuncks. This is useful for both data indexing and passing it into a model, as large chucks are harder to search over and won't fit in a model's finite context window.
* Store : We need somewhere to store and index our splits, so they can be searched over later. This is often done using a [Vector store](https://python.langchain.com/docs/concepts/vectorstores/) and [Embeddings](https://python.langchain.com/docs/concepts/embedding_models/) model

### Retreival and Generation
* Retrieve :  Given a user input, relevant splits are retrieved from storage using a [Retriever](https://python.langchain.com/docs/concepts/retrievers/)
* Generate : A Chat Model/ LLM produces an answer using a prompt that includes both the question with the retrieved data


**NOTE : The Entire Project is vibe coded and you can find the prompts to create this in the vc_prompts.md file**
