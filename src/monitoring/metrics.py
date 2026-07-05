from prometheus_client import Counter, Histogram, Gauge, Info

APP_INFO = Info("ledgera", "Ledgera Book Reviewer application info")

REQUEST_LATENCY = Histogram(
    "ledgera_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint", "method"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

REQUEST_COUNT = Counter(
    "ledgera_requests_total",
    "Total request count",
    ["endpoint", "method", "status"],
)

API_ERRORS = Counter(
    "ledgera_api_errors_total",
    "Total API errors by source",
    ["source", "error_type"],
)

COLD_STARTS = Counter(
    "ledgera_cold_starts_total",
    "Number of cold starts",
)

RETRIEVAL_FAILURES = Counter(
    "ledgera_retrieval_failures_total",
    "Retrieval failures by source",
    ["source"],
)

CONFIDENCE_DISTRIBUTION = Histogram(
    "ledgera_confidence_score",
    "Distribution of confidence scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

FEEDBACK_SATISFACTION = Counter(
    "ledgera_feedback_total",
    "User feedback counts",
    ["rating"],
)

PIPELINE_STAGE_LATENCY = Histogram(
    "ledgera_pipeline_stage_seconds",
    "Latency per pipeline stage",
    ["stage"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

ACTIVE_ANALYSES = Gauge(
    "ledgera_active_analyses",
    "Currently running analyses",
)
