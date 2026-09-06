import logging
import tempfile
import os
from minio import Minio
from pypdf import PdfReader
import psycopg

minio_client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=os.getenv("MINIO_SECURE") == "true",
)


logger = logging.getLogger(__name__)


def get_document(document_id: str):
    conn = psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT filename, object_key
                FROM documents
                where id = %s;
            """,
                (document_id,),
            )

            return cursor.fetchone()
    finally:
        conn.close()


def process_file_from_disk(file_path: str, extension: str):
    if extension == ".pdf":
        # Placeholder for PDF processing logic
        # Read PDF
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text

        return text
    else:
        raise ValueError(f"Unsupported file type for processing: {file_path}")


def process_document(document_id: str):
    """
    Process the document with the given document_id.
    This function should contain the logic to process the document, e.g., send it to an AI model for analysis.
    """
    # Placeholder for document processing logic
    logger.info(f"Processing document with ID: {document_id}")
    # Add your processing logic here
    temp_path = None
    try:
        document = get_document(document_id)
        logger.info(f"Retrieved document from DB: {document}")
        filename, object_key = document
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        # Download MinIO object to local temp file
        minio_client.fget_object(
            "documents",
            object_key,
            temp_path,
        )
        # Now process the file
        extension = os.path.splitext(filename)[1].lower()
        result = process_file_from_disk(temp_path, extension=extension)
        logger.info(f"Document processed successfully. Result: {result}")

        # TODO: Make text as chunks and store
        return {
            "status": "success",
            "result": result,
        }

    except Exception as e:
        raise RuntimeError(f"Failed to process document {document_id}: {e}") from e

    finally:
        # Delete temporary file after processing
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
