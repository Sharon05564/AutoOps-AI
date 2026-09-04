from app.config import SimulatorSettings
from app.state import SimulatorState


def make_state() -> SimulatorState:
    settings = SimulatorSettings(
        requests_per_tick_min=100, requests_per_tick_max=100, tick_interval_seconds=0.01
    )
    return SimulatorState(settings=settings)


def test_baseline_tick_has_low_error_rate():
    state = make_state()
    point = state.tick()
    assert point.error_rate < 0.05
    assert point.latency_p95_ms < 200


def test_bad_deployment_degrades_metrics():
    state = make_state()
    state.trigger_bad_deployment()
    point = state.tick()
    assert state.is_degraded is True
    assert point.error_rate > 0.2
    assert point.latency_p95_ms > 400


def test_restart_does_not_fix_bad_deployment():
    state = make_state()
    state.trigger_bad_deployment()
    state.tick()
    state.restart()
    point = state.tick()
    assert state.is_degraded is True
    assert point.error_rate > 0.2


def test_scaling_up_during_bad_deployment_worsens_error_rate():
    state = make_state()
    state.trigger_bad_deployment()
    baseline_point = state.tick()
    state.scale(9)
    scaled_point = state.tick()
    assert scaled_point.error_rate >= baseline_point.error_rate


def test_rollback_restores_healthy_metrics():
    state = make_state()
    state.trigger_bad_deployment()
    state.tick()
    previous = state.rollback()
    assert previous is not None
    assert state.is_degraded is False
    point = state.tick()
    assert point.error_rate < 0.05


def test_rollback_is_noop_when_not_degraded():
    state = make_state()
    assert state.rollback() is None


def test_reset_restores_initial_state():
    state = make_state()
    state.trigger_bad_deployment()
    state.scale(10)
    state.reset()
    assert state.is_degraded is False
    assert state.replicas == 3
    assert len(state.deployments) == 1
    assert len(state.metrics_history) == 0


def test_recent_logs_include_db_errors_when_degraded():
    state = make_state()
    state.trigger_bad_deployment()
    state.tick()
    logs = state.get_recent_logs(window_seconds=60, limit=500)
    assert any(log.level == "ERROR" for log in logs)
