#!/usr/bin/env python3
"""Emit an agent run-record as OpenTelemetry spans.

This is a post-hoc telemetry exporter, not orchestration. It reads a run-record
JSON (see ../schema/run-record.schema.json), builds one trace for the defect run,
and ships nested spans to Logfire (OTel-native), any OTLP backend, or the console.

Usage (from repo root):
    python observability/emit_traces.py --input observability/examples/run-record.example.json --console
    $env:LOGFIRE_TOKEN="<token>"; python observability/emit_traces.py --input run.json
    $env:OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"; python observability/emit_traces.py --input run.json --otlp

Design notes:
    - No secrets/PII should ever reach here; the skill mandates redaction upstream.
      A light guard still warns on obvious secret-like attribute values.
    - Backend is chosen by flag/env, never by the run-record, so the same record
      can target Logfire, Tempo, Jaeger, Honeycomb, or Azure Monitor unchanged.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.trace import SpanKind, Status, StatusCode

# Attribute values matching these patterns almost certainly leaked a secret.
_SECRET_PATTERNS = [
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\."),           # JWT
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{10,}"),   # bearer token
    re.compile(r"(?i)(password|pwd|secret|api[_-]?key|pat)\s*[=:]\s*\S+"),
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),           # long base64-ish blob
]

_STATUS_MAP = {
    "ok": StatusCode.OK,
    "blocked": StatusCode.ERROR,
    "error": StatusCode.ERROR,
}


def _iso_to_ns(value: str | None) -> int | None:
    """Convert an ISO-8601 timestamp to epoch nanoseconds, or None."""
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def _scan_secrets(key: str, value: Any, path: str, warnings: list[str]) -> None:
    if isinstance(value, str):
        for pattern in _SECRET_PATTERNS:
            if pattern.search(value):
                warnings.append(f"{path}.{key}")
                return


def _clean_attributes(attrs: dict[str, Any] | None, path: str, warnings: list[str]) -> dict[str, Any]:
    if not attrs:
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in attrs.items():
        _scan_secrets(key, value, path, warnings)
        # OTel attributes must be scalar or homogeneous sequences; keep it scalar.
        if isinstance(value, (str, bool, int, float)):
            cleaned[key] = value
        else:
            cleaned[key] = json.dumps(value, separators=(",", ":"))
    return cleaned


def _emit_span(
    tracer: trace.Tracer,
    node: dict[str, Any],
    parent_ctx: Any,
    warnings: list[str],
    counter: dict[str, int],
) -> None:
    name = node["name"]
    start_ns = _iso_to_ns(node.get("started_at"))
    end_ns = _iso_to_ns(node.get("ended_at"))
    attributes = _clean_attributes(node.get("attributes"), f"span[{name}]", warnings)
    for meta_key in ("agent", "stage"):
        if node.get(meta_key):
            attributes[meta_key] = node[meta_key]

    span = tracer.start_span(
        name,
        context=parent_ctx,
        kind=SpanKind.INTERNAL,
        start_time=start_ns,
        attributes=attributes,
    )
    counter["spans"] += 1

    for event in node.get("events", []) or []:
        ev_attrs = _clean_attributes(event.get("attributes"), f"event[{event.get('name')}]", warnings)
        span.add_event(
            event["name"],
            attributes=ev_attrs,
            timestamp=_iso_to_ns(event.get("timestamp")),
        )

    status_key = node.get("status", "ok")
    code = _STATUS_MAP.get(status_key, StatusCode.UNSET)
    span.set_status(Status(code, description=None if code != StatusCode.ERROR else status_key))

    child_ctx = trace.set_span_in_context(span)
    for child in node.get("children", []) or []:
        _emit_span(tracer, child, child_ctx, warnings, counter)

    span.end(end_time=end_ns)


def _build_provider(args: argparse.Namespace) -> tuple[TracerProvider, str]:
    resource = Resource.create({"service.name": args.service})

    if args.console:
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        return provider, "console"

    if args.otlp:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        return provider, "otlp"

    # Default: Logfire (OTel-native). Requires `pip install logfire` and LOGFIRE_TOKEN.
    try:
        import logfire

        logfire.configure(service_name=args.service, console=False)
        provider = trace.get_tracer_provider()
        return provider, "logfire"
    except ImportError:
        print(
            "logfire not installed; falling back to --console. "
            "Install with `pip install logfire` or pass --otlp / --console.",
            file=sys.stderr,
        )
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        return provider, "console (fallback)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit an agent run-record as OpenTelemetry spans.")
    parser.add_argument("--input", required=True, help="Path to a run-record JSON file.")
    parser.add_argument("--service", default="copilot-resolution-hub", help="OTel service.name.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--console", action="store_true", help="Print spans to the console (no account needed).")
    mode.add_argument("--otlp", action="store_true", help="Export via OTLP/HTTP (uses OTEL_EXPORTER_OTLP_ENDPOINT).")
    parser.add_argument("--fail-on-secret", action="store_true", help="Exit non-zero if a secret-like value is detected.")
    args = parser.parse_args(argv)

    record_path = Path(args.input)
    if not record_path.is_file():
        print(f"Input not found: {record_path}", file=sys.stderr)
        return 2

    record = json.loads(record_path.read_text(encoding="utf-8"))
    spans = record.get("spans")
    if not isinstance(spans, list) or not spans:
        print("Run-record has no 'spans' array.", file=sys.stderr)
        return 2

    provider, backend = _build_provider(args)
    if isinstance(provider, TracerProvider):
        trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("agent-observability")

    warnings: list[str] = []
    counter = {"spans": 0}

    root_attrs = _clean_attributes(record.get("attributes"), "root", warnings)
    for key in ("run_id", "work_item_id", "system"):
        if record.get(key):
            root_attrs[key] = record[key]

    root = tracer.start_span(
        f"defect.run.{record.get('run_id', 'unknown')}",
        kind=SpanKind.SERVER,
        start_time=_iso_to_ns(record.get("started_at")),
        attributes=root_attrs,
    )
    counter["spans"] += 1
    root_ctx = trace.set_span_in_context(root)
    for node in spans:
        _emit_span(tracer, node, root_ctx, warnings, counter)
    root.set_status(Status(StatusCode.OK))
    root.end(end_time=_iso_to_ns(record.get("ended_at")))

    # Flush before exit so short-lived runs actually ship their spans.
    if isinstance(provider, TracerProvider):
        provider.force_flush()
        provider.shutdown()

    print(f"Emitted {counter['spans']} spans for run {record.get('run_id')} via {backend}.")

    if warnings:
        unique = sorted(set(warnings))
        print(f"WARNING: possible secret/PII in {len(unique)} attribute(s): {', '.join(unique)}", file=sys.stderr)
        if args.fail_on_secret:
            return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
