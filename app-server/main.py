from contextlib import asynccontextmanager
from pathlib import Path

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import start_http_server

from storage.minio import ensure_bucket

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.types import ASGIApp

from chats.router import router as chats_router
from document_chunks.router import router as document_chunks_router
from documents.router import router as documents_router
from config import settings
from json_logging import configure_logging
from request_id import RequestIdMiddleware

# TODO: Remove below import once db migrations are handled separately
from db.models import Base


configure_logging()

resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
reader = PrometheusMetricReader()
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)

trace_provider = TracerProvider(resource=resource)
span_exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT)
trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
trace.set_tracer_provider(trace_provider)

start_http_server(port=settings.OTEL_PROMETHEUS_PORT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_bucket()
    # initialize other app resources
    yield


fastapi_app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(fastapi_app)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

fastapi_app.include_router(chats_router)
fastapi_app.include_router(documents_router)
fastapi_app.include_router(document_chunks_router)


@fastapi_app.get("/")
def root():
    frontend_path = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    return FileResponse(frontend_path)


app: ASGIApp = RequestIdMiddleware(fastapi_app)
