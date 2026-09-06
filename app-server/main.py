from contextlib import asynccontextmanager
from pathlib import Path
from storage.minio import ensure_bucket

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from chats.router import router as chats_router
from document_chunks.router import router as document_chunks_router
from documents.router import router as documents_router

# TODO: Remove below import once db migrations are handled separately
from db.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_bucket()
    # initialize other app resources
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chats_router)
app.include_router(documents_router)
app.include_router(document_chunks_router)


@app.get("/")
def root():
    frontend_path = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    return FileResponse(frontend_path)
