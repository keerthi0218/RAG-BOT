import os
import sqlite3
import warnings
from pathlib import Path
from typing import Optional

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field


load_dotenv()
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

DB_PATH = Path("users.db")
CHROMA_DIR = Path("chroma_db")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL = "openai/gpt-oss-20b"
NO_INFO_MESSAGE = "I do not have enough information in the provided knowledge base to answer this."
USER_NOT_FOUND_MESSAGE = "User not found. Please enter a valid user_id."
MISSING_KEY_MESSAGE = "GROQ_API_KEY is not set. Please set it in your environment or .env file."

PROMPT_TEMPLATE = """You are an AI customer support assistant.
You are speaking with:
Name: {name}
Membership Tier: {membership_tier}
Answer the user's question using only the context provided below.
Do not infer, expand, or invent policy details.
If the context states a limited membership benefit, include the exact limit.
If the answer is not available in the context, say:
"I do not have enough information in the provided knowledge base to answer this."
Context:
{retrieved_chunks}
User Question:
{user_query}
Answer:"""

app = FastAPI(title="RAG Customer Support Chatbot")
app.mount("/static", StaticFiles(directory="static"), name="static")


class AskRequest(BaseModel):
    user_id: int = Field(..., examples=[101])
    user_query: str = Field(..., examples=["What is the refund policy?"])


class AskResponse(BaseModel):
    answer: str


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


def get_user(user_id: int) -> Optional[dict]:
    if not DB_PATH.exists():
        return None

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, membership_tier FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()

    if row is None:
        return None

    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "membership_tier": row["membership_tier"],
    }


def load_vector_store() -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )


def retrieve_context(user_query: str, k: int = 4, min_relevance: float = 0.2) -> str:
    if not CHROMA_DIR.exists():
        return ""

    vector_store = load_vector_store()
    results = vector_store.similarity_search_with_relevance_scores(user_query, k=k)
    relevant_docs = [doc for doc, score in results if score >= min_relevance]

    if not relevant_docs:
        return ""

    return "\n\n".join(doc.page_content for doc in relevant_docs)


def build_prompt(name: str, membership_tier: str, retrieved_chunks: str, user_query: str) -> str:
    return PROMPT_TEMPLATE.format(
        name=name,
        membership_tier=membership_tier,
        retrieved_chunks=retrieved_chunks,
        user_query=user_query,
    )


def ask_customer_support(user_id: int, user_query: str) -> str:
    user = get_user(user_id)
    if user is None:
        return USER_NOT_FOUND_MESSAGE

    retrieved_chunks = retrieve_context(user_query)
    if not retrieved_chunks:
        return NO_INFO_MESSAGE

    if not os.getenv("GROQ_API_KEY"):
        return MISSING_KEY_MESSAGE

    prompt = build_prompt(
        name=user["name"],
        membership_tier=user["membership_tier"],
        retrieved_chunks=retrieved_chunks,
        user_query=user_query,
    )

    try:
        llm = ChatGroq(model=GROQ_MODEL, temperature=0)
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as exc:
        return f"Groq API error: {exc}"


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    answer = ask_customer_support(request.user_id, request.user_query)
    return AskResponse(answer=answer)


def run_cli() -> None:
    print("BrightCart RAG Customer Support CLI")
    print("Type 'exit' to quit.")

    while True:
        raw_user_id = input("\nUser ID: ").strip()
        if raw_user_id.lower() in {"exit", "quit"}:
            break

        try:
            user_id = int(raw_user_id)
        except ValueError:
            print("Please enter a numeric user_id.")
            continue

        user_query = input("Question: ").strip()
        if user_query.lower() in {"exit", "quit"}:
            break
        if not user_query:
            print("Please enter a question.")
            continue

        print(f"Answer: {ask_customer_support(user_id, user_query)}")


if __name__ == "__main__":
    run_cli()
