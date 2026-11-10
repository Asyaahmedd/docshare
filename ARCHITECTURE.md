# Architecture note

## What I prioritized
1. **A complete core loop** (create → edit → save → reopen → share) over breadth. Every requirement works end to end.
2. **Access control on the server.** Every document endpoint goes through one `load()` function that checks owner/editor/viewer. Users without access get 404, so document IDs don't leak.
3. **Safe shared content.** Documents are HTML shared between users, so content is sanitized with `nh3` (allow-list of formatting tags) before it's stored. Test covers this.
4. **Zero-friction review.** No Node build, one command to run, seeded users, free hosting tiers.

## Design
- **Backend:** FastAPI, three tables: `users`, `documents` (HTML content), `shares` (document, user, role; unique per pair).
- **Frontend:** one HTML page + vanilla JS + Quill (CDN). Autosave 0.8s after typing stops, with visible status.
- **Storage:** HTML is what Quill produces and what I sanitize, so formatting round-trips without a conversion layer.
- **Import:** `importers.py` converts txt/md/docx to HTML, then the same sanitizer runs.

## Deliberate cuts (and why)
- **Real authentication:** mocked via a user dropdown (allowed by the brief). Next: sessions/OAuth.
- **Real-time collaboration:** concurrent edits are last-write-wins. Next: Yjs/CRDT or at least version checks.
- **Sharing by email/invite:** only seeded users can be picked.
- **Version history, comments, export:** skipped to protect core quality.

## Known limitations
- Two people editing at once can overwrite each other.
- Mobile layout works but the editor is best on desktop.
- No browser-level automated tests; the API has pytest coverage.
