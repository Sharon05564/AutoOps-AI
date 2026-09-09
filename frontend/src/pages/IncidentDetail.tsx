import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  IncidentStatusBadge,
  RemediationStatusBadge,
  RiskBadge,
  SeverityBadge,
} from "../components/Badge";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import LogsList from "../components/LogsList";
import MetricsChart from "../components/MetricsChart";
import TimelineList from "../components/TimelineList";
import ToolCallList from "../components/ToolCallList";
import { useIncidentActions } from "../hooks/useIncidentActions";
import { useIncident, useIncidentTimeline } from "../hooks/useIncidents";
import { useServiceLogs, useServiceMetrics } from "../hooks/useServices";
import { formatDateTime, formatDuration, formatPercent } from "../lib/format";

function IncidentDetail() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const incidentQuery = useIncident(incidentId);
  const timelineQuery = useIncidentTimeline(incidentId);
  const actions = useIncidentActions(incidentId ?? "");

  const incident = incidentQuery.data;
  const metricsQuery = useServiceMetrics(incident?.service_id, 300);
  const logsQuery = useServiceLogs(incident?.service_id, 300);

  const [approvedBy, setApprovedBy] = useState("operator");
  const [reason, setReason] = useState("");

  if (incidentQuery.isLoading) return <LoadingState label="Loading incident..." />;
  if (incidentQuery.isError || !incident) {
    return <ErrorState message="Could not load this incident." />;
  }

  const latestInvestigation = [...incident.investigations].sort((a, b) =>
    a.started_at.localeCompare(b.started_at)
  ).at(-1);
  const latestRemediation = [...incident.remediation_actions].sort((a, b) =>
    a.created_at.localeCompare(b.created_at)
  ).at(-1);
  const pendingApproval = incident.remediation_actions.find(
    (a) => a.status === "PENDING_APPROVAL"
  );

  const canInvestigate = incident.status === "DETECTED" || incident.status === "INVESTIGATING";
  const canRemediate = incident.status === "DIAGNOSED";
  const canVerify = incident.status === "VERIFYING";

  return (
    <div>
      <Link to="/incidents" className="back-link">
        ← Back to incidents
      </Link>

      <div className="page-header">
        <div>
          <h1>{incident.title}</h1>
          <p className="page-subtitle">
            Detected {formatDateTime(incident.detected_at)} · duration{" "}
            {formatDuration(incident.detected_at, incident.resolved_at)}
          </p>
        </div>
        <div className="badge-row">
          <SeverityBadge severity={incident.severity} />
          <IncidentStatusBadge status={incident.status} />
        </div>
      </div>

      <section className="panel action-panel">
        <h2>Actions</h2>
        <div className="action-row">
          {canInvestigate && (
            <button
              className="btn btn-primary"
              onClick={() => actions.investigate.mutate()}
              disabled={actions.investigate.isPending}
            >
              {actions.investigate.isPending ? "Investigating..." : "Run Investigation"}
            </button>
          )}
          {canRemediate && (
            <button
              className="btn btn-primary"
              onClick={() => actions.remediate.mutate(undefined)}
              disabled={actions.remediate.isPending}
            >
              {actions.remediate.isPending ? "Proposing..." : "Propose Remediation"}
            </button>
          )}
          {canVerify && (
            <button
              className="btn btn-secondary"
              onClick={() => actions.verify.mutate()}
              disabled={actions.verify.isPending}
            >
              {actions.verify.isPending ? "Verifying..." : "Verify Recovery Now"}
            </button>
          )}
          {(incident.status === "RESOLVED" || incident.status === "FAILED") && (
            <Link className="btn btn-secondary" to={`/incidents/${incident.id}/postmortem`}>
              View Postmortem
            </Link>
          )}
          {!canInvestigate && !canRemediate && !canVerify && incident.status !== "RESOLVED" && incident.status !== "FAILED" && incident.status !== "AWAITING_APPROVAL" && (
            <p className="muted">No action needed right now - status: {incident.status}.</p>
          )}
        </div>

        {pendingApproval && (
          <div className="approval-box">
            <h3>Approval Required</h3>
            <p>
              <strong>{pendingApproval.action_type.replace("_", " ")}</strong> is proposed with{" "}
              <RiskBadge risk={pendingApproval.risk_level} /> and needs a human decision before it
              runs.
            </p>
            <div className="approval-form">
              <label>
                Approved by
                <input
                  value={approvedBy}
                  onChange={(e) => setApprovedBy(e.target.value)}
                  placeholder="operator"
                />
              </label>
              <label>
                Reason
                <input
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Why are you approving/rejecting this?"
                />
              </label>
              <div className="action-row">
                <button
                  className="btn btn-primary"
                  disabled={actions.approve.isPending}
                  onClick={() =>
                    actions.approve.mutate({ approved: true, approvedBy, reason })
                  }
                >
                  Approve & Execute
                </button>
                <button
                  className="btn btn-danger-outline"
                  disabled={actions.approve.isPending}
                  onClick={() =>
                    actions.approve.mutate({ approved: false, approvedBy, reason })
                  }
                >
                  Reject
                </button>
              </div>
            </div>
          </div>
        )}
      </section>

      {latestInvestigation && (
        <section className="panel">
          <h2>Investigation</h2>
          <div className="diagnosis-box">
            <div className="diagnosis-row">
              <span className="diagnosis-label">Root cause</span>
              <p>{latestInvestigation.root_cause}</p>
            </div>
            <div className="diagnosis-meta">
              <span>
                Confidence: <strong>{formatPercent(latestInvestigation.confidence, 0)}</strong>
              </span>
              <span>
                Recommended:{" "}
                <strong>{latestInvestigation.recommended_action || "None"}</strong>
              </span>
              <span>
                Provider: <strong>{latestInvestigation.llm_provider}</strong>
              </span>
            </div>
            {latestInvestigation.evidence.length > 0 && (
              <>
                <div className="diagnosis-label">Evidence</div>
                <ul className="evidence-list">
                  {latestInvestigation.evidence.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
          <h3>Tool Calls</h3>
          <ToolCallList calls={latestInvestigation.tool_calls ?? []} />
        </section>
      )}

      {incident.remediation_actions.length > 0 && (
        <section className="panel">
          <h2>Remediation Actions</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Attempt</th>
                <th>Action</th>
                <th>Risk</th>
                <th>Status</th>
                <th>Approved By</th>
                <th>Executed</th>
              </tr>
            </thead>
            <tbody>
              {incident.remediation_actions.map((action) => (
                <tr key={action.id}>
                  <td>{action.attempt_number}</td>
                  <td>{action.action_type.replace("_", " ")}</td>
                  <td>
                    <RiskBadge risk={action.risk_level} />
                  </td>
                  <td>
                    <RemediationStatusBadge status={action.status} />
                  </td>
                  <td>{action.approval?.approved_by ?? "—"}</td>
                  <td>{formatDateTime(action.executed_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {incident.verifications.length > 0 && (
        <section className="panel">
          <h2>Recovery Verification</h2>
          {incident.verifications.map((verification) => (
            <div key={verification.id} className="verification-row">
              <span className={`verification-status verification-${verification.status.toLowerCase()}`}>
                {verification.status}
              </span>
              <span>
                error rate {formatPercent(verification.metrics_before.error_rate as number | undefined)}{" "}
                → {formatPercent(verification.metrics_after.error_rate as number | undefined)}
              </span>
              <span className="muted">{formatDateTime(verification.checked_at)}</span>
            </div>
          ))}
        </section>
      )}

      {latestRemediation && metricsQuery.data && metricsQuery.data.length > 0 && (
        <section className="panel">
          <h2>Metrics</h2>
          <MetricsChart data={metricsQuery.data} />
        </section>
      )}

      {incident.alerts.length > 0 && (
        <section className="panel">
          <h2>Alerts ({incident.alerts.length})</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Threshold</th>
                <th>Triggered</th>
              </tr>
            </thead>
            <tbody>
              {incident.alerts.slice(0, 10).map((alert) => (
                <tr key={alert.id}>
                  <td>{alert.metric_name}</td>
                  <td>{alert.value.toFixed(4)}</td>
                  <td>{alert.threshold.toFixed(4)}</td>
                  <td>{formatDateTime(alert.triggered_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {incident.alerts.length > 10 && (
            <p className="muted">Showing 10 of {incident.alerts.length} alerts.</p>
          )}
        </section>
      )}

      <section className="panel">
        <h2>Recent Logs</h2>
        {logsQuery.data ? <LogsList logs={logsQuery.data.slice(-40)} /> : <LoadingState />}
      </section>

      <section className="panel">
        <h2>Timeline</h2>
        {timelineQuery.data ? (
          <TimelineList events={timelineQuery.data} />
        ) : (
          <LoadingState label="Loading timeline..." />
        )}
      </section>
    </div>
  );
}

export default IncidentDetail;
