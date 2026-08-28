from fastapi import APIRouter

router = APIRouter(tags=["Messages"])


@router.get("/")
def get_messages(chat_id: str):
    return []


@router.post("/")
def create_message(chat_id: str):
    return {"message": "Message created successfully!"}
