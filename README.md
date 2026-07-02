# RAG Customer Support Chatbot

This project is a Retrieval-Augmented Generation (RAG) customer support chatbot for the fictional BrightCart company. It uses a local FAQ knowledge base, SQLite user lookup, Chroma vector search, HuggingFace sentence-transformer embeddings, LangChain, FastAPI, and the Groq API.

The current Groq chat model is:

```text
openai/gpt-oss-20b
```

Note: the original requested `llama3-8b-8192` Groq model has been decommissioned, so this project uses Groq's supported `openai/gpt-oss-20b` model instead.

## Project Files

- `app.py` - FastAPI app, RAG flow, `/ask` API, frontend serving, and terminal mode
- `company_faq.txt` - BrightCart FAQ knowledge base
- `create_db.py` - creates and seeds `users.db`
- `ingest.py` - chunks the FAQ and builds the Chroma vector store
- `static/` - basic browser frontend
- `requirements.txt` - pinned Python dependencies
- `.env.example` - environment variable template

Generated local data:

- `users.db` - SQLite customer database
- `chroma_db/` - persisted Chroma vector store

## Local Setup

Python 3.10+ is required. On this Windows machine, Python 3.11 is the recommended interpreter:

```bash
py -3.11 --version
```

Create and activate a virtual environment:

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file:

```bash
copy .env.example .env
```

Set your real Groq key in `.env`:

```text
GROQ_API_KEY=your_real_groq_api_key
```

Do not commit `.env`; it contains a secret.

## Build Local Data

Create and seed the SQLite user database:

```bash
py -3.11 create_db.py
```

Build the Chroma vector store from `company_faq.txt`:

```bash
py -3.11 ingest.py
```

Rerun `ingest.py` whenever you edit `company_faq.txt`.

## Run Locally

Run the browser app and API:

```bash
py -3.11 -m uvicorn app:app --reload
```

Open the frontend:

```text
http://127.0.0.1:8000/
```

FastAPI docs are available at:

```text
http://127.0.0.1:8000/docs
```

Run terminal mode instead:

```bash
py -3.11 app.py
```

## API Usage

Endpoint:

```http
POST /ask
```

Request body:

```json
{
  "user_id": 101,
  "user_query": "What is the refund policy?"
}
```

Response:

```json
{
  "answer": "..."
}
```

## Deploy

This repo includes a deployment helper:

```bash
bash deploy.sh build
```

It installs dependencies, creates `users.db`, and builds `chroma_db/`.

For production-style hosting, run Uvicorn on all interfaces:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Many hosting platforms provide a dynamic port through an environment variable. In that case, set the start command to the platform's expected format, for example:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

On Windows PowerShell:

```powershell
uvicorn app:app --host 0.0.0.0 --port $env:PORT
```

Deployment checklist:

- Use Python 3.10 or 3.11.
- Install dependencies from `requirements.txt`.
- Set `GROQ_API_KEY` in the hosting provider's environment variables.
- Include `company_faq.txt`, `users.db`, `chroma_db/`, `static/`, and all Python files.
- Do not deploy or commit a real `.env` file.
- If `users.db` or `chroma_db/` are missing on the server, run `python create_db.py` and `python ingest.py` during setup.

Suggested build/setup commands:

```bash
bash deploy.sh build
```

Suggested start command:

```bash
bash deploy.sh start
```

For Render, Railway, Fly.io, or similar platforms:

- Add `GROQ_API_KEY` as a secret/environment variable.
- Use `bash deploy.sh build` as the build command.
- Use `bash deploy.sh start` as the start command.
- Make sure persistent generated files are either committed when acceptable for the demo or regenerated during deployment.

## Sample Test Cases

1. `user_id` 101, `"What is the refund policy?"`

Expected behavior: answers from the refund policy using Riya Sharma / Gold context.

2. `user_id` 103, `"Do I get premium customer support?"`

Expected behavior: answers using Neha Iyer / Platinum context and explains Platinum premium support access.

3. `user_id` 999, `"What are my benefits?"`

Expected behavior:

```text
User not found. Please enter a valid user_id.
```

4. `user_id` 102, `"Can I cancel my account?"`

Expected behavior: answers from the account cancellation section.

## Error Handling

If `GROQ_API_KEY` is missing, the app returns a clear message asking you to set it instead of crashing. Groq API failures and rate limits are caught and returned as readable error messages.
