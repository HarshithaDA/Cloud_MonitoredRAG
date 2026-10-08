"""Phoenix/OpenTelemetry setup shared by the RAG API and Streamlit UI."""

from __future__ import annotations

import os
from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator


@lru_cache(maxsize=1)
def get_tracer():
    """Return a tracer configured for the Phoenix project."""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        raise RuntimeError(
            "Tracing dependencies are missing. Install requirements.txt before enabling Phoenix."
        ) from exc

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": os.getenv("PHOENIX_SERVICE_NAME", "cloud-monitored-rag"),
                "openinference.project.name": os.getenv(
                    "PHOENIX_PROJECT_NAME", "cloud-monitored-rag"
                ),
            }
        )
    )
    endpoint = os.getenv("PHOENIX_OTEL_ENDPOINT", "http://localhost:6006/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    return trace.get_tracer("cloud-monitored-rag")


@contextmanager
def rag_span(name: str, **attributes: object) -> Iterator[object]:
    """Create a span, while allowing guardrail-only local runs without OTEL installed."""
    try:
        tracer = get_tracer()
    except RuntimeError:
        yield None
        return
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
        yield span