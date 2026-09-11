import hashlib
import logging
import os

import psycopg
from pgvector.psycopg import register_vector


logger = logging.getLogger(__name__)


def get_connection():
    conn = psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    register_vector(conn)
    return conn


def claim_pending_chunks():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                WITH locked AS (
                    SELECT id
                    FROM jobs
                    WHERE status = 'pending'
                    AND next_attempt_at <= NOW()
                    AND type = 'document_chunks_embedding'
                    AND attempts < 3
                    ORDER BY created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE jobs
                SET status = 'processing',
                    last_attempted_at = NOW(),
                    locked_at = NOW(),
                    attempts = attempts + 1,
                    next_attempt_at = NOW() + INTERVAL '5 minutes'
                FROM locked
                WHERE jobs.id = locked.id
                RETURNING jobs.id, jobs.document_id;
                """
            )
            job = cursor.fetchone()
            if not job:
                return None, None, []
            job_id, document_id = job
            conn.commit()

            cursor.execute(
                """
                SELECT id, chunk_index, headers, content
                from document_chunks
                where document_id = %s AND
                embedding is NULL
                """,
                (document_id,),
            )
            chunks = cursor.fetchall()
            return job_id, document_id, chunks
    finally:
        conn.close()


def generate_dummy_embedding(content: str) -> list[float]:
    digest = hashlib.sha256(content.encode("utf-8")).digest()
    return [
        round(int.from_bytes(digest[index : index + 4], "big") / 2**32, 6)
        for index in (0, 4, 8)
    ]


def store_embeddings(chunks):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for id, index, headers, content in chunks:
                embedding = generate_dummy_embedding(headers + content)
                cursor.execute(
                    """
                    UPDATE document_chunks
                    SET embedding = %s
                    WHERE id = %s;
                    """,
                    (embedding, id),
                )
                conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def mark_document_as_completed(job_id: str, document_id: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE jobs
                SET status = 'completed'
                WHERE id = %s;
                """,
                (job_id,),
            )
            cursor.execute(
                """
                UPDATE documents
                SET status = 'ready'
                WHERE id = %s;
                """,
                (document_id,),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
