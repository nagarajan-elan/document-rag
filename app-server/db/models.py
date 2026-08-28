from chats.models import Chat
from .session import engine
from .base import Base


Base.metadata.create_all(engine)
print("Database tables created successfully.")