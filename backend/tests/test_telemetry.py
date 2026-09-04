from datetime import UTC, datetime, timedelta

from app.services.telemetry import TelemetryPoller


def test_is_new_with_no_cursor_accepts_everything():
    now = datetime.now(UTC).isoformat()
    assert TelemetryPoller._is_new(now, None) is True


def test_is_new_rejects_timestamps_at_or_before_cursor():
    cursor = datetime.now(UTC)
    older = (cursor - timedelta(seconds=5)).isoformat()
    assert TelemetryPoller._is_new(older, cursor) is False


def test_is_new_accepts_timestamps_after_cursor():
    cursor = datetime.now(UTC)
    newer = (cursor + timedelta(seconds=5)).isoformat()
    assert TelemetryPoller._is_new(newer, cursor) is True
