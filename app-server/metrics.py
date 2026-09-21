from prometheus_client import Counter, Histogram

DOCUMENTS_UPLOADED_TOTAL = Counter(
    "documents_uploaded_total",
    "Total number of documents successfully uploaded to storage.",
)

DOCUMENT_CHUNK_FETCH_DURATION = Histogram(
    "document_chunk_fetch_duration_seconds",
    "Time spent fetching document chunks from the database.",
    labelnames=("operation",),
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)

EMBEDDING_GENERATION_DURATION = Histogram(
    "embedding_generation_duration_seconds",
    "Time spent generating vector embeddings for content.",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)
