# Instrumentation

Observability made simple: traces, metrics, and logs.

## The Problem

Production apps need monitoring. Traditional observability requires complex setup with multiple libraries and configuration files.

**Traditional**: OpenTelemetry SDK + exporters + configuration + middleware = lots of boilerplate.

**PyNext**: Decorator-based, zero-config defaults, full customization when needed.

## Quick Start

```python
# instrumentation.py - Auto-discovered
from pynext import instrument, trace, metric, log

@instrument(traces=True, metrics=True, logs=True)
def configure():
    return {
        "service_name": "my-app",
        "exporter": "otlp",
        "endpoint": "http://localhost:4317",
    }
```

That's it. All routes are automatically traced.

## How It Works

### First Principles

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Request    │ →  │   Handler    │ →  │   Response   │
│              │    │   (traced)   │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
        │                  │                    │
        ▼                  ▼                    ▼
   ┌─────────┐        ┌─────────┐         ┌─────────┐
   │  Trace  │        │ Metrics │         │  Logs   │
   │  Start  │        │ Record  │         │  Write  │
   └─────────┘        └─────────┘         └─────────┘
        │                  │                    │
        └──────────────────┼────────────────────┘
                           ▼
                    ┌─────────────┐
                    │  Exporter   │
                    │ (OTLP/etc)  │
                    └─────────────┘
```

### Three Pillars

1. **Traces**: Follow requests across services
2. **Metrics**: Count events, measure durations
3. **Logs**: Structured, contextual messages

## API Reference

### @instrument Decorator

Configure global instrumentation:

```python
from pynext import instrument

@instrument(
    traces=True,    # Enable distributed tracing
    metrics=True,   # Enable Prometheus metrics
    logs=True,      # Enable structured logging
)
def configure():
    return {
        "service_name": "my-app",
        "service_version": "1.0.0",
        "environment": "production",
        "exporter": "otlp",  # "console", "jaeger", "zipkin"
        "endpoint": "http://collector:4317",
        "sample_rate": 1.0,  # 0.0 to 1.0
    }
```

### @trace Decorator

Trace individual functions:

```python
from pynext import trace

@trace("fetch-users")
async def get_users():
    return await db.users.find_all()

@trace()  # Uses function name
def process_data(data):
    return transform(data)

# With attributes
@trace("api-call", attributes={"api": "external"})
async def call_external_api():
    return await http.get("https://api.example.com")
```

### Tracer Class

Manual span creation:

```python
from pynext import get_tracer

tracer = get_tracer("my-service")

# Context manager
with tracer.start_span("operation") as span:
    span.set_attribute("user_id", 123)
    result = do_work()
    span.add_event("work_completed")

# Nested spans
with tracer.start_span("parent") as parent:
    with tracer.start_span("child") as child:
        # child.context.parent_id == parent.context.span_id
        pass
```

### Span Operations

```python
with tracer.start_span("operation") as span:
    # Set attributes
    span.set_attribute("key", "value")
    span.set_attribute("count", 42)
    
    # Add events
    span.add_event("checkpoint", {"progress": 50})
    
    # Record exceptions
    try:
        risky_operation()
    except Exception as e:
        span.record_exception(e)
        span.set_status("error", "Operation failed")
        raise
    
    # Access context
    print(span.context.trace_id)
    print(span.context.span_id)
```

### Metrics

Create and record metrics:

```python
from pynext import counter, gauge, histogram, metric

# Counter (only increases)
requests = counter("http_requests_total", "Total HTTP requests")
requests.inc()
requests.inc(5)
requests.inc(labels={"method": "GET", "path": "/"})

# Gauge (can increase or decrease)
connections = gauge("active_connections", "Active connections")
connections.set(42)
connections.inc()
connections.dec()

# Histogram (distribution)
latency = histogram(
    "request_latency_seconds",
    "Request latency",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)
latency.observe(0.123)

# Timer context
with latency.time():
    process_request()

# Generic metric()
page_views = metric("page_views", type="counter")
temperature = metric("temperature", type="gauge")
```

### Structured Logging

```python
from pynext import log, get_logger

# Global log object
log.info("User logged in", user_id=123, ip="1.2.3.4")
log.warning("Rate limit approaching", remaining=10)
log.error("Payment failed", order_id="abc", amount=99.99)

# Create logger with context
logger = get_logger("payments")
logger.info("Processing payment", amount=99.99)

# With context
with logger.context(request_id="abc123"):
    logger.info("Step 1")
    logger.info("Step 2")  # Both have request_id

# Exception logging
try:
    risky_operation()
except Exception as e:
    log.exception("Operation failed", exc=e)
```

## Patterns

### Request Tracing

```python
from pynext import page, trace, log

@page
@trace("home-page")
def home():
    log.info("Rendering home page")
    return div["Welcome"]
```

### Database Tracing

```python
from pynext import trace

class Database:
    @trace("db.query")
    async def query(self, sql, params=None):
        with get_tracer().start_span("execute") as span:
            span.set_attribute("db.statement", sql)
            return await self._execute(sql, params)
```

### API Metrics

```python
from pynext import api_route, counter, histogram

api_requests = counter("api_requests_total", labels=["method", "endpoint", "status"])
api_latency = histogram("api_latency_seconds", labels=["endpoint"])

@api_route
async def handler(request):
    with api_latency.time(labels={"endpoint": "/api/users"}):
        result = await process_request(request)
        api_requests.inc(labels={
            "method": request.method,
            "endpoint": "/api/users",
            "status": "200",
        })
        return result
```

### Service Health

```python
from pynext import gauge

# Track service health
db_connected = gauge("db_connection_status")
cache_connected = gauge("cache_connection_status")

async def health_check():
    db_connected.set(1 if await db.ping() else 0)
    cache_connected.set(1 if await cache.ping() else 0)
```

## Exporters

### Console (Development)

```python
@instrument()
def configure():
    return {
        "service_name": "my-app",
        "exporter": "console",
    }
```

### OTLP (OpenTelemetry)

```python
@instrument()
def configure():
    return {
        "service_name": "my-app",
        "exporter": "otlp",
        "endpoint": "http://otel-collector:4317",
    }
```

### Jaeger

```python
@instrument()
def configure():
    return {
        "service_name": "my-app",
        "exporter": "jaeger",
        "endpoint": "http://jaeger:14268/api/traces",
    }
```

### Prometheus Metrics

```python
from pynext.instrumentation.metrics import export_prometheus

# Add to your server
@app.get("/metrics")
def metrics():
    return Response(
        content=export_prometheus(),
        media_type="text/plain",
    )
```

## Configuration

### InstrumentConfig

```python
from pynext.instrumentation import InstrumentConfig, configure_instrumentation

config = InstrumentConfig(
    service_name="my-app",
    service_version="1.0.0",
    environment="production",
    traces=True,
    metrics=True,
    logs=True,
    exporter=Exporter.OTLP,
    endpoint="http://collector:4317",
    sample_rate=0.5,  # Sample 50% of traces
    attributes={"deployment": "kubernetes"},
)

configure_instrumentation(config)
```

### Environment Variables

```bash
PYNEXT_SERVICE_NAME=my-app
PYNEXT_SERVICE_VERSION=1.0.0
PYNEXT_ENV=production
PYNEXT_EXPORTER=otlp
PYNEXT_EXPORTER_ENDPOINT=http://collector:4317
```

## Migration from OpenTelemetry SDK

### Before (Manual Setup)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="..."))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("operation"):
    do_work()
```

### After (PyNext)

```python
from pynext import instrument, trace

@instrument()
def configure():
    return {"service_name": "my-app", "exporter": "otlp"}

@trace("operation")
def do_work():
    pass
```

## Troubleshooting

### Traces Not Appearing

```python
# Check configuration is loaded
from pynext.instrumentation.config import get_config

config = get_config()
print(f"Traces enabled: {config.traces}")
print(f"Exporter: {config.exporter}")
print(f"Endpoint: {config.endpoint}")
```

### Missing Span Attributes

```python
# Ensure span is active
from pynext import get_current_span

span = get_current_span()
if span:
    span.set_attribute("key", "value")
else:
    print("No active span!")
```

### Metrics Not Exporting

```python
# Check metrics are registered
from pynext.instrumentation import get_metrics

metrics = get_metrics()
print(f"Registered metrics: {list(metrics.keys())}")
```

