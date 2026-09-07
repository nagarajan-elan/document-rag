import logging
import tempfile
import os
from minio import Minio
import psycopg
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker


minio_client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=os.getenv("MINIO_SECURE") == "true",
)
converter = DocumentConverter()


logger = logging.getLogger(__name__)


def chunk_document(file_path: str):
    # 1. Convert File -> DoclingDocument
    conv = converter.convert(file_path)
    doc = conv.document

    # 2. Structure-aware + token-aware chunking
    chunker = HybridChunker()
    chunks = list(chunker.chunk(doc))
    result = []

    # 3. Inspect chunks
    for i, chunk in enumerate(chunks):
        headings = chunk.meta.headings or []
        breadcrumb = " > ".join(headings)
        pages = sorted({p.page_no for it in chunk.meta.doc_items for p in it.prov})

        result.append(
            {
                "chunk_index": i,
                "headers": breadcrumb,
                "content": chunk.text,
                "page_start": pages[0],
                "page_end": pages[-1],
            }
        )

    return result


def create_document_chunk_records(document_id: str, chunks: list):
    """
    Create document chunk records in the database for the given document_id and chunks.
    """
    conn = psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    try:
        with conn.cursor() as cursor:
            for i, chunk in enumerate(chunks, start=1):
                cursor.execute(
                    """
                    INSERT INTO document_chunks (document_id, chunk_index, headers, content, page_start, page_end)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    # TODO: ON CONFLICT (document_id, chunk_index) DO NOTHING;
                    (
                        document_id,
                        chunk["chunk_index"],
                        chunk["headers"],
                        chunk["content"],
                        chunk["page_start"],
                        chunk["page_end"],
                    ),
                )
                if i % 20 == 0:
                    logger.info(f"Inserted {i} chunks for document_id: {document_id}")
                    conn.commit()  # Commit every 20 inserts to avoid long transactions
            conn.commit()  # Final commit for any remaining inserts
            cursor.execute(
                """
                INSERT INTO jobs (document_id, type, status)
                VALUES (%s, 'document_chunks_embedding', 'pending');
                """,
                (document_id,),
            )
            conn.commit()
            logger.info(f"Inserted {len(chunks)} chunks for document_id: {document_id}")
    finally:
        conn.close()


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


def get_chunks_from_document(file_path: str, extension: str):
    if extension == ".pdf":
        return chunk_document(file_path)
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
        chunks = get_chunks_from_document(temp_path, extension=extension)
        logger.info(f"Document processed successfully. Result: {chunks}")

        create_document_chunk_records(document_id, chunks)

    except Exception as e:
        raise RuntimeError(f"Failed to process document {document_id}: {e}") from e

    finally:
        # Delete temporary file after processing
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
