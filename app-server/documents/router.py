from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/")
def get_documents():
    return []


@router.post("/")
def create_document():
    return {"message": "Document created successfully!"}


@router.get("/{document_id}")
def get_document(document_id: str):
    return {"document_id": document_id, "message": "Document details"}


@router.patch("/{document_id}")
def update_document(document_id: str):
    return {"document_id": document_id, "message": "Document updated successfully!"}


@router.delete("/{document_id}")
def delete_document(document_id: str):
    return {"document_id": document_id, "message": "Document deleted successfully!"}
