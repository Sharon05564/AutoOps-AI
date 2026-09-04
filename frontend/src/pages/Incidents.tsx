import { useState } from "react";
import { Link } from "react-router-dom";

import { IncidentStatusBadge, SeverityBadge } from "../components/Badge";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import { useIncidents } from "../hooks/useIncidents";
import { useServices } from "../hooks/useServices";
import { formatDateTime } from "../lib/format";

const STATUS_FILTERS = [
  "ALL",
  "DETECTED",
  "INVESTIGATING",
  "DIAGNOSED",
  "AWAITING_APPROVAL",
  "REMEDIATING",
  "VERIFYING",
  "RESOLVED",
  "FAILED",
];

function Incidents() {
  const [statusFilter, setStatusFilter] = useState("ALL");
  const incidentsQuery = useIncidents(statusFilter === "ALL" ? undefined : statusFilter);
  const servicesQuery = useServices();

  const serviceNameById = new Map(
    (servicesQuery.data ?? []).map((s) => [s.service.id, s.service.name])
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Incidents</h1>
          <p className="page-subtitle">Every incident detected across all services.</p>
        </div>
      </div>

      <div className="filter-bar">
        {STATUS_FILTERS.map((status) => (
          <button
            key={status}
            className={`filter-chip${statusFilter === status ? " filter-chip-active" : ""}`}
            onClick={() => setStatusFilter(status)}
          >
            {status.replace("_", " ")}
          </button>
        ))}
      </div>

      {incidentsQuery.isLoading && <LoadingState label="Loading incidents..." />}
      {incidentsQuery.isError && <ErrorState message="Could not load incidents." />}

      {incidentsQuery.data && incidentsQuery.data.length === 0 && (
        <p className="muted">No incidents match this filter.</p>
      )}

      {incidentsQuery.data && incidentsQuery.data.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Service</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Detected</th>
              <th>Resolved</th>
            </tr>
          </thead>
          <tbody>
            {incidentsQuery.data.map((incident) => (
              <tr key={incident.id}>
                <td>
                  <Link to={`/incidents/${incident.id}`}>{incident.title}</Link>
                </td>
                <td>{serviceNameById.get(incident.service_id) ?? "—"}</td>
                <td>
                  <SeverityBadge severity={incident.severity} />
                </td>
                <td>
                  <IncidentStatusBadge status={incident.status} />
                </td>
                <td>{formatDateTime(incident.detected_at)}</td>
                <td>{formatDateTime(incident.resolved_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default Incidents;
