# Docshare

A lightweight collaborative document editor: create and edit rich-text documents, import files, and share them with other users.

**Stack:** FastAPI + SQLAlchemy (SQLite locally, Postgres in production) and a single-page frontend using the Quill editor. No build step.
# Docshare

A small Google Docs-style editor I built for Ajaia's take-home assignment. You can write and format documents, import a file as a new document, and share a document with another user as an editor or a viewer.

**Live app:** https://docshare-ashy.vercel.app
(The first load after a quiet period can take a few seconds.)

## Trying it

There is no real login. Use the "Signed in as" dropdown to switch between three test users: **[User 1]**, **[User 2]** and **[User 3]**.

A quick path through the app:

1. As [User 1], click New document, type something, make some of it bold and add a heading and a list. Refresh the page; the document is still there.
2. Click Share, choose [User 2] and "View only".
3. Switch to [User 2]. The document is under "Shared with me" and can't be edited.
4. Switch back, change [User 2] to "Can edit", and switch again. Now they can edit.
5. Click Upload file and choose a .txt, .md or .docx file to turn it into a new document.

## How it's built

- **Backend:** FastAPI and SQLAlchemy. `app/main.py` has the routes and permission checks, `app/db.py` defines the three tables (users, documents, shares), and `app/importers.py` converts uploaded files to HTML.
- **Frontend:** plain HTML, CSS and JavaScript in `app/static/`, with the Quill editor loaded from a CDN. No build step.
- **Database:** SQLite locally, Neon Postgres in production.
- **Tests:** `tests/test_api.py` (pytest).

## Decisions worth knowing about

- **Permissions are checked on the server.** Every document route goes through one function, `load()`, which works out whether the caller is the owner, an editor or a viewer. Someone with no access gets a 404, so they can't tell whether a document exists.
- **Content is sanitized before saving.** Documents are HTML shared between users, so `clean()` strips everything except basic formatting tags. This stops a script saved in one user's document from running in another's browser.
- **Login is mocked.** The browser sends the chosen username in a header. The brief allowed this, and I spent the time on documents, sharing and access rules instead. It's not secure and would be the first thing to replace.
- **Uploads are limited to .txt, .md and .docx, up to 2 MB.** .docx import keeps text, headings and lists. Images, tables and inline bold/italic are dropped.

## Run locally

```
python -m venv .venv
.venv\Scripts\activate        # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000. The database file (`docs.db`) is created on first start. Run the tests with `python -m pytest`.

## Deployment

Deployed on Vercel with a Neon Postgres database, configured through the `DATABASE_URL` environment variable. I first tried Render, but it asked for a payment card even on its free plan, and the assignment says reviewers shouldn't have to pay for anything.

## Known limits

- If two people edit the same document at once, the last save wins. There is no real-time collaboration or conflict detection.
- Anyone can pick any test user, since there's no real authentication.
- Text alignment and indentation aren't kept, because the sanitizer only allows basic formatting tags.
- Sharing is limited to the three seeded users.

## With another 2-4 hours

Real login, version history, Markdown/PDF export, a warning when someone else has saved changes first, and browser-level tests.
