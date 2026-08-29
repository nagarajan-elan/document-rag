import uuid
from .repository import get_cloud_repository
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/")
def get_documents():
    return []


@router.post("/")
def upload_document(
    file: UploadFile = File(...), cloud_repo=Depends(get_cloud_repository)
):
    document_id = str(uuid.uuid4())
    object_name = f"documents/{document_id}/{file.filename}"
    try:
        cloud_repo.put_object(data=file, object_name=object_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")
    return {
        "id": document_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "object_name": object_name,
    }


@router.get("/{document_id}")
def get_document(document_id: str):
    return {"document_id": document_id, "message": "Document details"}


@router.delete("/{document_id}")
def delete_document(document_id: str):
    return {"document_id": document_id, "message": "Document deleted successfully!"}
