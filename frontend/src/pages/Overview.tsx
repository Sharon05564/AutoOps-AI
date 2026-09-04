import { Link } from "react-router-dom";

import { IncidentStatusBadge, SeverityBadge } from "../components/Badge";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import MetricsChart from "../components/MetricsChart";
import StatCard from "../components/StatCard";
import { useIncidents } from "../hooks/useIncidents";
import { useServiceMetrics, useServices } from "../hooks/useServices";
import { useSimulatorActions } from "../hooks/useSimulatorActions";
import { formatDateTime, formatPercent } from "../lib/format";

const OPEN_STATUSES = new Set([
  "DETECTED",
  "INVESTIGATING",
  "DIAGNOSED",
  "AWAITING_APPROVAL",
  "REMEDIATING",
  "VERIFYING",
]);

function Overview() {
  const servicesQuery = useServices();
  const incidentsQuery = useIncidents();
  const { triggerBad, reset } = useSimulatorActions();

  const primaryService = servicesQuery.data?.[0];
  const metricsQuery = useServiceMetrics(primaryService?.service.id, 300);

  const openIncidents = (incidentsQuery.data ?? []).filter((incident) =>
    OPEN_STATUSES.has(incident.status)
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Overview</h1>
          <p className="page-subtitle">Live health for the checkout-service demo environment.</p>
        </div>
        <div className="page-actions">
          <button
            className="btn btn-danger"
            onClick={() => triggerBad.mutate()}
            disabled={triggerBad.isPending}
          >
            {triggerBad.isPending ? "Deploying..." : "Trigger Bad Deployment"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => reset.mutate()}
            disabled={reset.isPending}
          >
            {reset.isPending ? "Resetting..." : "Reset Demo"}
          </button>
        </div>
      </div>

      {servicesQuery.isLoading && <LoadingState label="Loading services..." />}
      {servicesQuery.isError && <ErrorState message="Could not load services." />}

      {primaryService && (
        <>
          <div className="stat-grid">
            <StatCard
              label="Active Incidents"
              value={String(openIncidents.length)}
              tone={openIncidents.length > 0 ? "danger" : "success"}
            />
            <StatCard
              label="Service Status"
              value={primaryService.status}
              tone={
                primaryService.status === "healthy"
                  ? "success"
                  : primaryService.status === "degraded"
                    ? "danger"
                    : "neutral"
              }
            />
            <StatCard label="Error Rate" value={formatPercent(primaryService.error_rate)} />
            <StatCard
              label="P95 Latency"
              value={`${primaryService.latency_p95_ms.toFixed(0)}ms`}
            />
            <StatCard label="Replicas" value={String(primaryService.service.replicas)} />
          </div>

          <section className="panel">
            <h2>Metrics - {primaryService.service.name}</h2>
            {metricsQuery.data && metricsQuery.data.length > 0 ? (
              <MetricsChart data={metricsQuery.data} />
            ) : (
              <p className="muted">No metrics yet. Trigger a bad deployment to see activity.</p>
            )}
          </section>
        </>
      )}

      <section className="panel">
        <h2>Active Incidents</h2>
        {incidentsQuery.isLoading && <LoadingState label="Loading incidents..." />}
        {openIncidents.length === 0 && !incidentsQuery.isLoading && (
          <p className="muted">No active incidents. Everything looks healthy.</p>
        )}
        {openIncidents.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Detected</th>
              </tr>
            </thead>
            <tbody>
              {openIncidents.map((incident) => (
                <tr key={incident.id}>
                  <td>
                    <Link to={`/incidents/${incident.id}`}>{incident.title}</Link>
                  </td>
                  <td>
                    <SeverityBadge severity={incident.severity} />
                  </td>
                  <td>
                    <IncidentStatusBadge status={incident.status} />
                  </td>
                  <td>{formatDateTime(incident.detected_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

export default Overview;
