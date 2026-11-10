# Docshare

A lightweight collaborative document editor: create and edit rich-text documents, import files, and share them with other users.

**Stack:** FastAPI + SQLAlchemy (SQLite locally, Postgres in production) and a single-page frontend using the Quill editor. No build step.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000. Data is stored in `docs.db` (SQLite) and created on first start.

## Test accounts (mocked login)
Pick a user in the "Signed in as" dropdown: **Alice Johnson**, **Bob Smith**, **Carol Lee**. There are no passwords; this is intentional to keep scope on the document features (see ARCHITECTURE.md).

**To see sharing work:** as Alice, create or open a document → Share → pick Bob and "Can edit" or "View only". Switch to Bob: the document appears under "Shared with me". A view-only document can't be edited.

## Features
- Create, rename (edit the title), edit, autosave, reopen; the open document survives a refresh.
- Formatting: bold, italic, underline, Heading 1/2, bulleted and numbered lists.
- Upload `.txt`, `.md`, `.docx` (max 2 MB) → becomes a new editable document. Other types are rejected with a message. `.docx` import keeps text, headings and lists; images, tables and inline bold/italic are not imported.
- Sharing: owner, can edit / view only roles, remove access, "My documents" vs "Shared with me".
- Validation: title length, file type and size, HTML sanitization on save, access checks on every endpoint.

## Tests
```bash
pytest
```

## Deploy (Render + free Postgres)
1. Push this folder to GitHub.
2. Create a free Postgres database (Neon or Supabase) and copy its connection string.
3. On Render, create a **Web Service** from the repo: Build command `pip install -r requirements.txt`, Start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Add the environment variable `DATABASE_URL` = your connection string. Tables and seed users are created on first start.

Without `DATABASE_URL` the app uses SQLite, which is erased on Render's free tier when the service restarts. Use Postgres for the live link.
