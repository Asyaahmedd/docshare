# Architecture note

## What I prioritized
1. **The full loop working end to end:** create, edit, save, reopen, share. I preferred this to adding extra features.
2. **Permissions on the server.** Every document route calls one function, `load()`, which decides whether the caller is the owner, an editor or a viewer. If you have no access you get a 404, so nobody can tell whether a document ID exists.
3. **Safe shared content.** Documents are HTML that other users open, so `clean()` strips everything except basic formatting tags before saving. Otherwise a script saved by one user would run in another user's browser.
4. **Easy for reviewers to run.** No build step, one command to start, seeded test users, and free hosting.

## Design
- **Backend:** FastAPI with three tables: `users`, `documents` (the HTML) and `shares` (document, user, role, one row per pair).
- **Frontend:** one HTML page, plain JavaScript and the Quill editor from a CDN. It autosaves 0.8 seconds after you stop typing and shows the status.
- **Storage:** I store the HTML that Quill produces after sanitising it, so formatting survives a reload without a conversion step.
- **Uploads:** `importers.py` converts .txt, .md and .docx to HTML, and the same sanitiser runs on the result.

## What I cut and why
- **Real login:** it's a user dropdown, which the brief allows. I chose to spend the time on sharing and access rules instead.
- **Real-time collaboration:** if two people save at once, the last save wins.
- **Inviting by email:** you can only share with the three seeded users.
- **Version history, comments and export:** left out to keep the core solid.

## Known limits
- Simultaneous edits can overwrite each other.
- The layout works on a phone, but the editor is best on desktop.
- Only the API has automated tests. There are no browser-level tests.
