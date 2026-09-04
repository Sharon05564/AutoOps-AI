import type { TimelineEvent } from "../api/types";
import { formatDateTime } from "../lib/format";

const EVENT_ICON: Record<string, string> = {
  INCIDENT_DETECTED: "🔴",
  ALERT: "⚠️",
  INVESTIGATION_STARTED: "🔍",
  INVESTIGATION_COMPLETED: "🧠",
  REMEDIATION_PROPOSED: "🛠️",
  APPROVAL_DECIDED: "✅",
  REMEDIATION_EXECUTED: "🚀",
  VERIFICATION: "📈",
  INCIDENT_RESOLVED: "🎉",
};

function TimelineList({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return <p className="muted">No timeline events yet.</p>;
  }

  return (
    <ol className="timeline">
      {events.map((event, index) => (
        <li key={`${event.timestamp}-${index}`} className="timeline-item">
          <span className="timeline-icon">{EVENT_ICON[event.event_type] ?? "•"}</span>
          <div className="timeline-body">
            <div className="timeline-header">
              <span className="timeline-title">{event.title}</span>
              <span className="timeline-time">{formatDateTime(event.timestamp)}</span>
            </div>
            {event.description && <p className="timeline-description">{event.description}</p>}
          </div>
        </li>
      ))}
    </ol>
  );
}

export default TimelineList;
