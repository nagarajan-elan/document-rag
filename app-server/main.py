from contextlib import asynccontextmanager
from pathlib import Path

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from prometheus_client import start_http_server

from storage.minio import ensure_bucket

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from chats.router import router as chats_router
from document_chunks.router import router as document_chunks_router
from documents.router import router as documents_router
from config import settings

# TODO: Remove below import once db migrations are handled separately
from db.models import Base


resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
reader = PrometheusMetricReader()
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)

start_http_server(port=settings.OTEL_PROMETHEUS_PORT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_bucket()
    # initialize other app resources
    yield


app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chats_router)
app.include_router(documents_router)
app.include_router(document_chunks_router)


@app.get("/")
def root():
    frontend_path = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    return FileResponse(frontend_path)
