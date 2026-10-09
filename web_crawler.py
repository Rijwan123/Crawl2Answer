import os

from langchain_apify import ApifyScrapeUrlTool

#os.environ["APIFY_TOKEN"] = "APIFY key"

# pip install -U langchain-openai
# pip install -U langchain-openai langchain-apify langchain-core apify-client python-dotenv
#python .\crawlWebsite.py
import os

from langchain_apify import ApifyWrapper
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from apify_client import ApifyClient


# os.environ["OPENAI_API_KEY"] = "key"
# os.environ["APIFY_TOKEN"] = "apify_api_key"
# 1. Load API keys
# --------------------------------------------------

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in .env")

if not os.getenv("APIFY_TOKEN"):
    raise ValueError("APIFY_TOKEN is not set in .env")

tool = ApifyScrapeUrlTool()
print(tool.invoke({"url": "https://docs.langchain.com/oss/python/langchain/quickstart"}))
# --------------------------------------------------
# 2. Initialize Apify and OpenAI
# --------------------------------------------------

apify = ApifyWrapper()
llm = ChatOpenAI(model="gpt-5.4-mini")

# --------------------------------------------------
# 3. Crawl LangChain documentation
# --------------------------------------------------


# loader = apify.call_actor(
#     actor_id="apify/website-content-crawler",
#     run_input={"startUrls": [{"url": "https://docs.apify.com/integrations/langchain#crawl-a-website"}], "maxCrawlPages": 10, "crawlerType": "cheerio"},
#     dataset_mapping_function=lambda item: Document(
#         page_content=item["text"] or "", metadata={"source": item["url"]}
#     ),
# )
# Run Website Content Crawler

apify_client = ApifyClient(
    os.getenv("APIFY_TOKEN")
)

run = apify_client.actor(
    "apify/website-content-crawler"
).call(
    run_input={
        "startUrls": [
            {
                "url": "https://docs.apify.com/integrations/langchain#crawl-a-website"
            }
        ],
        "maxCrawlPages": 10,
        "crawlerType": "cheerio"
    }
)

# Get dataset ID created by this run
dataset_id = run["defaultDatasetId"]

print("Dataset ID:", dataset_id)


#ApifyDatasetLoader loads previously crawled data from an Apify dataset and 
#converts each record into LangChain Document objects for further RAG processing.

from langchain_apify import ApifyDatasetLoader
from langchain_core.documents import Document

loader = ApifyDatasetLoader(
    dataset_id=dataset_id,
    dataset_mapping_function=lambda item: Document(
        page_content=item["text"] or "", metadata={"source": item["url"]}
    ),
)
documents = loader.load()

vector_store = InMemoryVectorStore.from_documents(loader.load(), OpenAIEmbeddings())
retriever = vector_store.as_retriever()

prompt = ChatPromptTemplate.from_template(
    "Answer the question using only the context below.\n\n"
    "Context:\n{context}\n\nQuestion: {question}"
)


query = "What is LangChain?"
docs = retriever.invoke(query)
context = "\n\n".join(doc.page_content for doc in docs)
answer = (prompt | llm).invoke({"context": context, "question": query}).content
sources = ", ".join({doc.metadata["source"] for doc in docs})

print("answer:", answer)
print("source:", sources)