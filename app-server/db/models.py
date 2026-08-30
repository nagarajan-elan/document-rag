from chats.models import Chat
from messages.models import Message
from documents.models import Document
from .session import engine
from .base import Base


Base.metadata.create_all(engine)
print("Database tables created successfully.")
