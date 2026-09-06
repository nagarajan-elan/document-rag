import os
import time
import logging
import multiprocessing
import psycopg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
logger.info("Document watcher starting...")


def _process_document_child(document_id):
    from helpers import process_document

    try:
        process_document(document_id)
    except BaseException:
        logger.exception("Document processing child failed for document_id: %s", document_id)
        raise


def process_document_isolated(document_id):
    context = multiprocessing.get_context("spawn")
    process = context.Process(target=_process_document_child, args=(document_id,))
    process.start()
    process.join()
    exitcode = process.exitcode
    process.close()

    if exitcode != 0:
        raise RuntimeError(f"Document processing child exited with status {exitcode}")


def get_uploaded_document_from_db():
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
                WITH locked AS (
                    SELECT id
                    FROM jobs
                    WHERE status = 'pending'
                    AND next_attempt_at <= NOW()
                    AND type = 'document_extraction'
                    AND attempts < 3
                    ORDER BY created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE jobs j
                SET status = 'processing', last_attempted_at = NOW(), attempts = attempts + 1, next_attempt_at = NOW() + INTERVAL '5 minutes'
                FROM locked
                WHERE j.id = locked.id
                RETURNING j.id, j.document_id;
            """
            )

            document = cursor.fetchone()
            conn.commit()  # Commit the transaction to release the lock
            return document
    finally:
        conn.close()


def main():
    logger.info("Starting document watcher loop...")
    while True:
        time.sleep(5)  # Sleep for 5 seconds before the next fetch
        logger.info("Fetching uploaded documents from the database...")
        try:
            document = get_uploaded_document_from_db()
            if not document:
                logger.info(
                    "No uploaded documents found. Waiting for the next fetch..."
                )
                continue

            logger.info(f"Processing document: {document}")
            document_id = document[1]
            process_document_isolated(document_id)

        except Exception as e:
            logger.exception("Error while processing document: %s", e)
            continue


if __name__ == "__main__":
    main()
