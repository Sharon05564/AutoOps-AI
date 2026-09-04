from app.models.enums import ActionType, RiskLevel

ACTION_RISK_LEVELS: dict[ActionType, RiskLevel] = {
    ActionType.ROLLBACK_DEPLOYMENT: RiskLevel.HIGH,
    ActionType.RESTART_SERVICE: RiskLevel.MEDIUM,
    ActionType.SCALE_SERVICE: RiskLevel.MEDIUM,
}


def risk_level_for(action_type: ActionType) -> RiskLevel:
    return ACTION_RISK_LEVELS[action_type]


def requires_approval(risk_level: RiskLevel, safe_auto_remediation: bool) -> bool:
    """HIGH risk always needs a human approval. MEDIUM is gated by the
    SAFE_AUTO_REMEDIATION flag. LOW would auto-execute (not used by any
    action in this demo, but kept for a realistic risk model)."""
    if risk_level == RiskLevel.HIGH:
        return True
    if risk_level == RiskLevel.MEDIUM:
        return not safe_auto_remediation
    return False
