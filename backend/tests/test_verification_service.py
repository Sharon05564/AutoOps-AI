from app.services.verification_service import _snapshot_to_dict


class FakeSnapshot:
    def __init__(self, timestamp, error_rate, latency_p95_ms, request_count):
        self.timestamp = timestamp
        self.error_rate = error_rate
        self.latency_p95_ms = latency_p95_ms
        self.request_count = request_count


def test_snapshot_to_dict_handles_none():
    assert _snapshot_to_dict(None) == {}


def test_snapshot_to_dict_extracts_fields():
    from datetime import UTC, datetime

    snapshot = FakeSnapshot(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        error_rate=0.02,
        latency_p95_ms=95.0,
        request_count=100,
    )
    result = _snapshot_to_dict(snapshot)
    assert result["error_rate"] == 0.02
    assert result["latency_p95_ms"] == 95.0
    assert result["request_count"] == 100
    assert "2026-01-01" in result["timestamp"]
