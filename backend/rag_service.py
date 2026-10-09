import os

from dotenv import load_dotenv
from apify_client import ApifyClient

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore

from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# --------------------------------------------------
# 1. Load environment variables
# --------------------------------------------------

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set")

if not os.getenv("APIFY_TOKEN"):
    raise ValueError("APIFY_TOKEN is not set")


# --------------------------------------------------
# 2. Initialize clients
# --------------------------------------------------

apify_client = ApifyClient(
    os.getenv("APIFY_TOKEN")
)

llm = ChatOpenAI(
    model="gpt-5.4-mini"
)

embeddings = OpenAIEmbeddings()


# --------------------------------------------------
# 3. Global objects
# --------------------------------------------------

vector_store = None
retriever = None
current_url = None
dataset_id = None


# --------------------------------------------------
# 4. Crawl website
# --------------------------------------------------

def crawl_website(url: str):

    global vector_store
    global retriever
    global current_url
    global dataset_id

    print("\nStarting website crawl:")
    print(url)

    # -----------------------------------
    # Run Apify crawler
    # -----------------------------------

    run = apify_client.actor(
        "apify/website-content-crawler"
    ).call(
        run_input={
            "startUrls": [
                {
                    "url": url
                }
            ],
            "maxCrawlPages": 10,
            "crawlerType": "playwright:adaptive"
        }
    )

    # New Apify SDK returns Run object
    if isinstance(run, dict):
        dataset_id = run["defaultDatasetId"]
    else:
        dataset_id = run.default_dataset_id

    print("\nDataset ID:")
    print(dataset_id)

    # -----------------------------------
    # Read dataset
    # -----------------------------------

    dataset_items = (
        apify_client
        .dataset(dataset_id)
        .list_items(clean=True)
        .items
    )

    print(
        "Dataset item count:",
        len(dataset_items)
    )

    if dataset_items:

        print("\nAvailable keys:")

        print(
            dataset_items[0].keys()
        )

    # -----------------------------------
    # Convert Apify data to Documents
    # -----------------------------------

    documents = []

    for item in dataset_items:

        if not isinstance(item, dict):
            continue

        text = (
            item.get("text")
            or item.get("markdown")
            or item.get("content")
            or ""
        )

        source_url = (
            item.get("url")
            or item.get("loadedUrl")
            or url
        )

        print(
            "\nText length:",
            len(text)
        )

        print(
            "Source:",
            source_url
        )

        if text.strip():

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": source_url
                    }
                )
            )

    print(
        "\nDocuments created:",
        len(documents)
    )

    if not documents:

        raise ValueError(
            "Apify returned data, but no usable page content was found."
        )

    # -----------------------------------
    # Split documents into chunks
    # -----------------------------------

    text_splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    )

    chunks = (
        text_splitter
        .split_documents(
            documents
        )
    )

    print(
        "Chunks created:",
        len(chunks)
    )

    if not chunks:

        raise ValueError(
            "Documents were created but text splitting produced no chunks."
        )

    # -----------------------------------
    # Create vector database
    # -----------------------------------

    print(
        "Creating embeddings..."
    )

    vector_store = (
        InMemoryVectorStore
        .from_documents(
            chunks,
            embeddings
        )
    )

    print(
        "Vector store created successfully."
    )

    # -----------------------------------
    # Create retriever
    # -----------------------------------

    retriever = (
        vector_store
        .as_retriever(
            search_kwargs={
                "k": 4
            }
        )
    )

    current_url = url

    # -----------------------------------
    # Return status
    # -----------------------------------

    return {
        "message": "Website indexed successfully",
        "pages": len(documents),
        "chunks": len(chunks),
        "dataset_id": dataset_id
    }


# --------------------------------------------------
# 5. Ask question
# --------------------------------------------------

def ask_question(question: str):

    global retriever

    if retriever is None:

        raise ValueError(
            "Please crawl a website first."
        )

    # -----------------------------------
    # Retrieve relevant chunks
    # -----------------------------------

    docs = retriever.invoke(
        question
    )

    print(
        "\nRetrieved chunks:",
        len(docs)
    )

    for index, doc in enumerate(
        docs,
        start=1
    ):

        print(
            f"\n--- Retrieved chunk {index} ---"
        )

        print(
            doc.page_content[:300]
        )

    # -----------------------------------
    # Build context
    # -----------------------------------

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    # -----------------------------------
    # Prompt
    # -----------------------------------

    prompt = ChatPromptTemplate.from_template(
    """
    You are a helpful AI assistant.

    Answer the user's question using only the website context provided below.

    Important rules:

    1. You may summarize and infer an answer from the context.
    2. The exact wording of the answer does not need to appear in the context.
    3. Combine information from multiple context chunks when useful.
    4. Do not use outside knowledge.
    5. Only say "The information was not found in the website."
    when the provided context contains no information relevant to the question.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    )

    # -----------------------------------
    # Generate answer
    # -----------------------------------

    answer = (
        prompt | llm
    ).invoke(
        {
            "context": context,
            "question": question
        }
    ).content

    # -----------------------------------
    # Sources
    # -----------------------------------

    sources = list(
        {
            doc.metadata.get("source")
            for doc in docs
            if doc.metadata.get("source")
        }
    )

    return {
        "answer": answer,
        "sources": sources
    }