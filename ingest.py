from pathlib import Path
import shutil

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


FAQ_PATH = Path("company_faq.txt")
CHROMA_DIR = Path("chroma_db")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def ingest_faq() -> None:
    if not FAQ_PATH.exists():
        raise FileNotFoundError(f"{FAQ_PATH} not found. Create the FAQ file first.")

    text = FAQ_PATH.read_text(encoding="utf-8")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.create_documents([text], metadatas=[{"source": str(FAQ_PATH)}])

    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
    )
    print(f"Ingested {len(chunks)} chunks into {CHROMA_DIR}")


if __name__ == "__main__":
    ingest_faq()
