import { useState } from "react";

import { HealthBadge } from "../components/Badge";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import MetricsChart from "../components/MetricsChart";
import { useDeployments } from "../hooks/useDeployments";
import { useServiceMetrics, useServices } from "../hooks/useServices";
import { formatDateTime, formatPercent } from "../lib/format";

function Services() {
  const servicesQuery = useServices();
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Services</h1>
          <p className="page-subtitle">Health, deployments, and capacity for every service.</p>
        </div>
      </div>

      {servicesQuery.isLoading && <LoadingState label="Loading services..." />}
      {servicesQuery.isError && <ErrorState message="Could not load services." />}

      {(servicesQuery.data ?? []).map((health) => (
        <section key={health.service.id} className="panel">
          <div className="service-card-header">
            <div>
              <h2>{health.service.name}</h2>
              <p className="muted">{health.service.description || "No description."}</p>
            </div>
            <HealthBadge status={health.status} />
          </div>

          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-card-label">Error Rate</div>
              <div className="stat-card-value">{formatPercent(health.error_rate)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-label">P95 Latency</div>
              <div className="stat-card-value">{health.latency_p95_ms.toFixed(0)}ms</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-label">Replicas</div>
              <div className="stat-card-value">{health.service.replicas}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-label">Active Incidents</div>
              <div className="stat-card-value">{health.active_incidents}</div>
            </div>
          </div>

          <button
            className="btn-link"
            onClick={() => setExpandedId(expandedId === health.service.id ? null : health.service.id)}
          >
            {expandedId === health.service.id ? "Hide details" : "Show deployment history & metrics"}
          </button>

          {expandedId === health.service.id && <ServiceDetails serviceId={health.service.id} />}
        </section>
      ))}
    </div>
  );
}

function ServiceDetails({ serviceId }: { serviceId: string }) {
  const deploymentsQuery = useDeployments(serviceId);
  const metricsQuery = useServiceMetrics(serviceId, 300);

  return (
    <div className="service-details">
      {metricsQuery.data && metricsQuery.data.length > 0 && (
        <MetricsChart data={metricsQuery.data} />
      )}

      <h3>Deployment History</h3>
      {deploymentsQuery.data && deploymentsQuery.data.length > 0 ? (
        <table className="data-table">
          <thead>
            <tr>
              <th>Version</th>
              <th>Status</th>
              <th>Deployed</th>
              <th>Rolled Back</th>
            </tr>
          </thead>
          <tbody>
            {deploymentsQuery.data.map((deployment) => (
              <tr key={deployment.id}>
                <td>{deployment.version}</td>
                <td>{deployment.status}</td>
                <td>{formatDateTime(deployment.deployed_at)}</td>
                <td>{formatDateTime(deployment.rolled_back_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted">No deployment history yet.</p>
      )}
    </div>
  );
}

export default Services;
