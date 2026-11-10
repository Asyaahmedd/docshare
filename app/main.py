from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import nh3
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select

from .db import Base, Document, Share, SessionLocal, User, engine
from .importers import SUPPORTED, to_html

SEED_USERS = [("alice", "Asya Ahmed"), ("bob", "Narin Patel"), ("carol", "Salim Khan")]
MAX_UPLOAD = 2 * 1024 * 1024
ALLOWED_TAGS = {"p", "br", "strong", "em", "u", "s", "h1", "h2", "h3", "ul", "ol", "li", "blockquote"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        if not s.scalar(select(User).limit(1)):
            s.add_all([User(username=u, name=n) for u, n in SEED_USERS])
            s.commit()
    yield


app = FastAPI(title="Docshare", lifespan=lifespan)


def clean(html: str) -> str:
    """Documents are shared between users, so strip anything but basic formatting tags."""
    return nh3.clean(html, tags=ALLOWED_TAGS, attributes={})


def db():
    with SessionLocal() as s:
        yield s


def current_user(x_user: str | None = Header(None), s=Depends(db)) -> User:
    # Mocked auth: the browser sends the chosen seeded username. Replace with real auth in production.
    user = s.scalar(select(User).where(User.username == x_user)) if x_user else None
    if not user:
        raise HTTPException(401, "Choose a user to continue.")
    return user


def load(s, doc_id: int, user: User, need: str = "view"):
    """Fetch a document and enforce access. Users without access get 404 so IDs don't leak."""
    doc = s.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    if doc.owner_id == user.id:
        access = "owner"
    else:
        share = s.scalar(select(Share).where(Share.doc_id == doc.id, Share.user_id == user.id))
        if not share:
            raise HTTPException(404, "Document not found.")
        access = share.role
    if need == "edit" and access == "viewer":
        raise HTTPException(403, "You have view-only access to this document.")
    if need == "owner" and access != "owner":
        raise HTTPException(403, "Only the owner can do this.")
    return doc, access


def brief(s, doc: Document, access: str) -> dict:
    return {
        "id": doc.id,
        "title": doc.title,
        "access": access,
        "owner": s.get(User, doc.owner_id).name,
        "updated_at": doc.updated_at.replace(tzinfo=None).isoformat() + "Z",
    }


def detail(s, doc: Document, access: str) -> dict:
    out = brief(s, doc, access) | {"content": doc.content, "shares": []}
    if access == "owner":
        rows = s.execute(select(User, Share.role).join(Share, Share.user_id == User.id).where(Share.doc_id == doc.id)).all()
        out["shares"] = [{"username": u.username, "name": u.name, "role": r} for u, r in rows]
    return out


class DocIn(BaseModel):
    title: str | None = Field(None, max_length=200)
    content: str | None = Field(None, max_length=2_000_000)


class ShareIn(BaseModel):
    username: str
    role: Literal["viewer", "editor"] = "editor"


@app.get("/api/users")
def users(s=Depends(db)):
    return [{"username": u.username, "name": u.name} for u in s.scalars(select(User).order_by(User.id))]


@app.get("/api/docs")
def list_docs(user=Depends(current_user), s=Depends(db)):
    owned = s.scalars(select(Document).where(Document.owner_id == user.id).order_by(Document.updated_at.desc())).all()
    shared = s.execute(
        select(Document, Share.role).join(Share, Share.doc_id == Document.id)
        .where(Share.user_id == user.id).order_by(Document.updated_at.desc())
    ).all()
    return {"owned": [brief(s, d, "owner") for d in owned], "shared": [brief(s, d, r) for d, r in shared]}


@app.post("/api/docs", status_code=201)
def create_doc(body: DocIn, user=Depends(current_user), s=Depends(db)):
    title = (body.title or "").strip() or "Untitled document"
    doc = Document(title=title, content=clean(body.content or ""), owner_id=user.id)
    s.add(doc)
    s.commit()
    return detail(s, doc, "owner")


@app.get("/api/docs/{doc_id}")
def get_doc(doc_id: int, user=Depends(current_user), s=Depends(db)):
    doc, access = load(s, doc_id, user)
    return detail(s, doc, access)


@app.put("/api/docs/{doc_id}")
def update_doc(doc_id: int, body: DocIn, user=Depends(current_user), s=Depends(db)):
    doc, access = load(s, doc_id, user, "edit")
    if body.title is not None:
        if not body.title.strip():
            raise HTTPException(422, "Title can't be empty.")
        doc.title = body.title.strip()
    if body.content is not None:
        doc.content = clean(body.content)
    s.commit()
    return detail(s, doc, access)


@app.delete("/api/docs/{doc_id}", status_code=204)
def delete_doc(doc_id: int, user=Depends(current_user), s=Depends(db)):
    doc, _ = load(s, doc_id, user, "owner")
    for sh in s.scalars(select(Share).where(Share.doc_id == doc.id)):
        s.delete(sh)
    s.delete(doc)
    s.commit()


@app.post("/api/docs/{doc_id}/share")
def share_doc(doc_id: int, body: ShareIn, user=Depends(current_user), s=Depends(db)):
    doc, access = load(s, doc_id, user, "owner")
    target = s.scalar(select(User).where(User.username == body.username))
    if not target:
        raise HTTPException(404, "That user doesn't exist.")
    if target.id == user.id:
        raise HTTPException(400, "You already own this document.")
    share = s.scalar(select(Share).where(Share.doc_id == doc.id, Share.user_id == target.id))
    if share:
        share.role = body.role
    else:
        s.add(Share(doc_id=doc.id, user_id=target.id, role=body.role))
    s.commit()
    return detail(s, doc, access)


@app.delete("/api/docs/{doc_id}/share/{username}")
def unshare_doc(doc_id: int, username: str, user=Depends(current_user), s=Depends(db)):
    doc, access = load(s, doc_id, user, "owner")
    target = s.scalar(select(User).where(User.username == username))
    share = target and s.scalar(select(Share).where(Share.doc_id == doc.id, Share.user_id == target.id))
    if share:
        s.delete(share)
        s.commit()
    return detail(s, doc, access)


@app.post("/api/upload", status_code=201)
async def upload(file: UploadFile = File(...), user=Depends(current_user), s=Depends(db)):
    name = file.filename or ""
    ext = Path(name).suffix.lower()
    if ext not in SUPPORTED:
        raise HTTPException(400, "Unsupported file type. Upload a .txt, .md or .docx file.")
    raw = await file.read()
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, "File is too large. The limit is 2 MB.")
    try:
        content = clean(to_html(ext, raw))
    except Exception:
        raise HTTPException(400, "We couldn't read that file. Check that it isn't corrupted.")
    doc = Document(title=(Path(name).stem or "Untitled document")[:200], content=content, owner_id=user.id)
    s.add(doc)
    s.commit()
    return detail(s, doc, "owner")


STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
