import json
import os
import time
import logging
import psycopg

from typing import Any
from kafka import KafkaProducer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
logger.info("Document watcher starting...")

producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS").split(","),
    client_id=os.getenv("KAFKA_CLIENT_ID"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
    acks="all",
    retries=3,
    linger_ms=10,
)
KAFKA_DOCUMENT_PARSING_TOPIC = os.getenv("KAFKA_DOCUMENT_PARSING_TOPIC")


def publish_event(topic: str, payload: dict[str, Any], key: str | None = None) -> None:
    try:
        producer.send(topic=topic, key=key, value=payload)
        producer.flush()
    except Exception:
        pass


def get_uploaded_documents_from_db():
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
                SELECT id, filename, object_key, created_at
                FROM documents
                ORDER BY created_at DESC;
            """
            )

            return cursor.fetchall()
    finally:
        conn.close()


def main():
    logger.info("Starting document watcher loop...")
    try:
        while True:
            logger.info("Fetching uploaded documents from the database...")
            documents = get_uploaded_documents_from_db()

            for document in documents:
                logger.info(f"Processing document: {document}")

                payload = {
                    "event": "document.uploaded",
                    "document_id": str(document[0]),
                    "filename": document[1],
                    "object_key": document[2],
                    "created_at": document[3].isoformat(),
                }

                try:
                    producer.send(topic=KAFKA_DOCUMENT_PARSING_TOPIC, value=payload)
                    producer.flush()
                    logger.info(
                        f"Published event to topic '{KAFKA_DOCUMENT_PARSING_TOPIC}': {payload}"
                    )
                except Exception as e:
                    logger.error(f"Failed to publish event: {e}")

            time.sleep(5)  # Sleep for 5 seconds before the next fetch

    except Exception as e:
        logger.error(f"Error fetching documents: {e}")


if __name__ == "__main__":
    main()
