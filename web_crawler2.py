import os

from dotenv import load_dotenv
from apify_client import ApifyClient

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore

from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings


# --------------------------------------------------
# 1. Load API keys
# --------------------------------------------------

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY is not set in .env"
    )

if not os.getenv("APIFY_TOKEN"):
    raise ValueError(
        "APIFY_TOKEN is not set in .env"
    )


# --------------------------------------------------
# 2. Initialize clients
# --------------------------------------------------

apify_client = ApifyClient(
    os.getenv("APIFY_TOKEN")
)

llm = ChatOpenAI(
    model="gpt-5.4-mini"
)


# --------------------------------------------------
# 3. Run crawler ONCE
# --------------------------------------------------

run = apify_client.actor(
    "apify/website-content-crawler"
).call(
    run_input={
        "startUrls": [
            {
                "url":
                "https://docs.langchain.com/oss/python/langchain/quickstart"
            }
        ],
        "maxCrawlPages": 10,
        "crawlerType": "cheerio"
    }
)


# --------------------------------------------------
# 4. Get dataset ID from SAME run
# --------------------------------------------------

dataset_id = run["defaultDatasetId"]

print(
    "Dataset ID:",
    dataset_id
)


# --------------------------------------------------
# 5. Read SAME dataset
# --------------------------------------------------

dataset_items = (
    apify_client
    .dataset(dataset_id)
    .list_items(clean=True)
    .items
)


# --------------------------------------------------
# 6. Convert to LangChain Documents
# --------------------------------------------------

documents = []

for item in dataset_items:

    if not isinstance(item, dict):
        continue

    text = item.get("text") or ""

    url = item.get("url") or ""

    if text:

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": url
                }
            )
        )


print(
    "Documents loaded:",
    len(documents)
)


# --------------------------------------------------
# 7. Vector store
# --------------------------------------------------

vector_store = (
    InMemoryVectorStore.from_documents(
        documents,
        OpenAIEmbeddings()
    )
)

retriever = vector_store.as_retriever()


# --------------------------------------------------
# 8. Prompt
# --------------------------------------------------

prompt = ChatPromptTemplate.from_template(
    """
Answer the question using only the context below.

Context:
{context}

Question:
{question}
"""
)


# --------------------------------------------------
# 9. Query
# --------------------------------------------------

query = "What is LangChain?"

docs = retriever.invoke(
    query
)

context = "\n\n".join(
    doc.page_content
    for doc in docs
)


# --------------------------------------------------
# 10. Generate answer
# --------------------------------------------------

answer = (
    prompt | llm
).invoke(
    {
        "context": context,
        "question": query
    }
).content


sources = ", ".join(
    {
        doc.metadata.get("source", "")
        for doc in docs
        if doc.metadata.get("source")
    }
)


print(
    "\nAnswer:",
    answer
)

print(
    "\nSource:",
    sources
)