"""OpenTelemetry setup: traces, metrics and logs, exported over OTLP or to files."""

import logging
from importlib.metadata import version
from pathlib import Path
from typing import TextIO

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler, ReadableLogRecord
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
    ConsoleLogRecordExporter,
    LogRecordExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    MetricExporter,
    MetricsData,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExporter

from stock_analyzer.infrastructure.config.settings import Settings, TelemetryExporter

# uvicorn's loggers don't propagate to root, so OTel must be attached to them directly.
_EXTRA_LOGGERS = ("uvicorn", "uvicorn.access", "uvicorn.error")


def configure_telemetry(settings: Settings) -> None:
    """Install global OTel providers and attach OTel export to the loggers.

    Does nothing when ``SA_OTEL_ENABLED`` is false.
    """
    if not settings.otel_enabled:
        return

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": version("stock-analyzer"),
            "deployment.environment": settings.env.value,
        }
    )
    span_exporter, metric_exporter, log_exporter = _build_exporters(settings)

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    reader = PeriodicExportingMetricReader(
        metric_exporter, export_interval_millis=settings.otel_export_interval_ms
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)
    handler = LoggingHandler(logger_provider=logger_provider)
    for name in ("", *_EXTRA_LOGGERS):
        logging.getLogger(name).addHandler(handler)


def _build_exporters(settings: Settings) -> tuple[SpanExporter, MetricExporter, LogRecordExporter]:
    """Create the trace, metric and log exporters for the configured backend."""
    if settings.otel_exporter is TelemetryExporter.FILE:
        directory = Path(settings.otel_file_dir)
        directory.mkdir(parents=True, exist_ok=True)
        return (
            ConsoleSpanExporter(out=_open(directory / "traces.jsonl"), formatter=_span_line),
            ConsoleMetricExporter(out=_open(directory / "metrics.jsonl"), formatter=_metric_line),
            ConsoleLogRecordExporter(out=_open(directory / "logs.jsonl"), formatter=_log_line),
        )
    endpoint = settings.otel_endpoint.rstrip("/")
    return (
        OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces"),
        OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics"),
        OTLPLogExporter(endpoint=f"{endpoint}/v1/logs"),
    )


def _open(path: Path) -> TextIO:
    """Open a telemetry file for appending; it stays open for the process lifetime."""
    return path.open("a", encoding="utf-8", buffering=1)


def _span_line(span: ReadableSpan) -> str:
    return str(span.to_json(indent=None)) + "\n"


def _metric_line(data: MetricsData) -> str:
    return str(data.to_json(indent=None)) + "\n"


def _log_line(record: ReadableLogRecord) -> str:
    return str(record.to_json(indent=None)) + "\n"
