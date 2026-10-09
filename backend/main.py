from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback

from rag_service import (
    crawl_website,
    ask_question
)


app = FastAPI(
    title="Website RAG Assistant",
    docs_url="/docs"
)


# Allow React frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173"
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# CORS - keep ONLY this one CORS block
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


class CrawlRequest(BaseModel):
    url: str


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def home():

    return {
        "message":
        "Website RAG API is running"
    }


@app.post("/crawl")
def crawl(request: CrawlRequest):

    try:

        result = crawl_website(
            request.url
        )

        return result

    except Exception as e:

        print("\n========== CRAWL ERROR ==========")

        print(str(e))

        traceback.print_exc()

        print("=================================\n")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/ask")
def ask(request: QuestionRequest):

    try:

        result = ask_question(
            request.question
        )

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )