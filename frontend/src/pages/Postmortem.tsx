import { Link, useParams } from "react-router-dom";

import { postmortemMarkdownUrl } from "../api/incidents";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import { useIncident } from "../hooks/useIncidents";
import { usePostmortem } from "../hooks/usePostmortem";
import { formatDateTime } from "../lib/format";

function Postmortem() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const incidentQuery = useIncident(incidentId);
  const isResolvedOrFailed =
    incidentQuery.data?.status === "RESOLVED" || incidentQuery.data?.status === "FAILED";
  const postmortemQuery = usePostmortem(incidentId, isResolvedOrFailed);

  if (incidentQuery.isLoading) return <LoadingState label="Loading incident..." />;

  if (!isResolvedOrFailed) {
    return (
      <div>
        <Link to={`/incidents/${incidentId}`} className="back-link">
          ← Back to incident
        </Link>
        <ErrorState message="A postmortem is only available once this incident is resolved or failed." />
      </div>
    );
  }

  if (postmortemQuery.isLoading) return <LoadingState label="Generating postmortem..." />;
  if (postmortemQuery.isError || !postmortemQuery.data) {
    return <ErrorState message="Could not load the postmortem." />;
  }

  const postmortem = postmortemQuery.data;

  return (
    <div>
      <Link to={`/incidents/${incidentId}`} className="back-link">
        ← Back to incident
      </Link>

      <div className="page-header">
        <div>
          <h1>Postmortem</h1>
          <p className="page-subtitle">Generated {formatDateTime(postmortem.generated_at)}</p>
        </div>
        <a
          className="btn btn-secondary"
          href={postmortemMarkdownUrl(incidentId ?? "")}
          target="_blank"
          rel="noreferrer"
        >
          Download Markdown
        </a>
      </div>

      <section className="panel">
        <h2>Summary</h2>
        <p>{postmortem.summary}</p>
      </section>

      <section className="panel">
        <h2>Root Cause</h2>
        <p>{postmortem.root_cause}</p>
      </section>

      <section className="panel">
        <h2>Evidence</h2>
        {postmortem.evidence.length > 0 ? (
          <ul className="evidence-list">
            {postmortem.evidence.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">No evidence recorded.</p>
        )}
      </section>

      <section className="panel">
        <h2>Timeline</h2>
        <ol className="timeline">
          {postmortem.timeline.map((event, i) => (
            <li key={i} className="timeline-item">
              <span className="timeline-icon">•</span>
              <div className="timeline-body">
                <div className="timeline-header">
                  <span className="timeline-title">{String(event.title)}</span>
                  <span className="timeline-time">{formatDateTime(String(event.timestamp))}</span>
                </div>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="panel">
        <h2>Remediation</h2>
        <p>{postmortem.remediation_summary}</p>
      </section>

      <section className="panel">
        <h2>Recovery Verification</h2>
        <p>{postmortem.recovery_verification}</p>
      </section>

      <section className="panel">
        <h2>Prevention Recommendations</h2>
        <ul className="evidence-list">
          {postmortem.prevention_recommendations.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}

export default Postmortem;
