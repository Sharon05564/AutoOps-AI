from app.models.enums import Severity
from app.services.alerting import determine_severity


def test_severity_medium_just_over_threshold():
    assert determine_severity(error_rate=0.16, error_threshold=0.15) == Severity.MEDIUM


def test_severity_high_at_double_threshold():
    assert determine_severity(error_rate=0.30, error_threshold=0.15) == Severity.HIGH


def test_severity_critical_at_triple_threshold():
    assert determine_severity(error_rate=0.45, error_threshold=0.15) == Severity.CRITICAL
