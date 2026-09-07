import time
import logging

from helpers import claim_pending_chunks, mark_document_as_completed, store_embeddings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
logger.info("Document watcher starting...")


def main():
    logger.info("Starting document chunk embedder loop...")
    while True:
        time.sleep(10)
        logger.info("Fetching pending document chunks from the database...")
        try:
            job_id, document_id, chunks = claim_pending_chunks()
            if not chunks:
                logger.info(
                    "No pending document chunks found. Waiting for the next fetch..."
                )
                continue

            logger.info("Embedding %s document chunks", len(chunks))
            store_embeddings(chunks)
            logger.info("Finished embedding %s document chunks", len(chunks))

            mark_document_as_completed(job_id, document_id)

        except Exception as e:
            logger.error("Error while embedding document chunks: %s", e)
            continue


if __name__ == "__main__":
    main()
