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


def claim_pending_chunks(batch_size: int = 10):
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
                    AND type = 'document_chunk_embedding'
                    AND chunk_id IS NOT NULL
                    AND attempts < 3
                    ORDER BY created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT %s
                )
                UPDATE jobs
                SET status = 'processing',
                    last_attempted_at = NOW(),
                    attempts = attempts + 1,
                    next_attempt_at = NOW() + INTERVAL '5 minutes'
                FROM locked
                WHERE jobs.id = locked.id
                RETURNING jobs.id, jobs.chunk_id,
                          (SELECT CONCAT(headers, content) FROM document_chunks WHERE id = jobs.chunk_id);
                """,
                (batch_size,),
            )
            jobs = cursor.fetchall()
            chunk_ids = [chunk_id for _, chunk_id, _ in jobs]
            if chunk_ids:
                cursor.execute(
                    """
                    UPDATE document_chunks
                    SET status = 'processing'
                    WHERE id = ANY(%s) AND status = 'pending';
                    """,
                    (chunk_ids,),
                )
            conn.commit()
            return jobs
    finally:
        conn.close()


def generate_dummy_embedding(content: str) -> list[float]:
    digest = hashlib.sha256(content.encode("utf-8")).digest()
    return [
        round(int.from_bytes(digest[index : index + 4], "big") / 2**32, 6)
        for index in (0, 4, 8)
    ]


def store_embeddings(jobs):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for job_id, chunk_id, content in jobs:
                embedding = generate_dummy_embedding(content)
                cursor.execute(
                    """
                    UPDATE document_chunks
                    SET embedding = %s, status = 'completed'
                    WHERE id = %s AND status = 'processing';
                    """,
                    (embedding, chunk_id),
                )
                cursor.execute(
                    """
                    UPDATE jobs
                    SET status = 'completed', completed_at = NOW()
                    WHERE id = %s AND status = 'processing';
                    """,
                    (job_id,),
                )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
