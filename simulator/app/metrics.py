from prometheus_client import Counter, Histogram

simulator_request_total = Counter(
    "simulator_request_total", "Total simulated requests handled", ["service"]
)
simulator_error_total = Counter(
    "simulator_error_total", "Total simulated requests that errored", ["service"]
)
simulator_request_latency_seconds = Histogram(
    "simulator_request_latency_seconds",
    "Simulated request latency in seconds",
    ["service"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.5, 5.0),
)


def record_tick(service: str, request_count: int, error_count: int, latencies_ms: list[float]) -> None:
    simulator_request_total.labels(service=service).inc(request_count)
    simulator_error_total.labels(service=service).inc(error_count)
    for latency_ms in latencies_ms:
        simulator_request_latency_seconds.labels(service=service).observe(latency_ms / 1000)
