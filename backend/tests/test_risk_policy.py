from app.models.enums import ActionType, RiskLevel
from app.policies.risk import requires_approval, risk_level_for


def test_rollback_is_high_risk():
    assert risk_level_for(ActionType.ROLLBACK_DEPLOYMENT) == RiskLevel.HIGH


def test_restart_and_scale_are_medium_risk():
    assert risk_level_for(ActionType.RESTART_SERVICE) == RiskLevel.MEDIUM
    assert risk_level_for(ActionType.SCALE_SERVICE) == RiskLevel.MEDIUM


def test_high_risk_always_requires_approval():
    assert requires_approval(RiskLevel.HIGH, safe_auto_remediation=True) is True
    assert requires_approval(RiskLevel.HIGH, safe_auto_remediation=False) is True


def test_medium_risk_gated_by_safe_auto_remediation_flag():
    assert requires_approval(RiskLevel.MEDIUM, safe_auto_remediation=True) is False
    assert requires_approval(RiskLevel.MEDIUM, safe_auto_remediation=False) is True


def test_low_risk_never_requires_approval():
    assert requires_approval(RiskLevel.LOW, safe_auto_remediation=False) is False
