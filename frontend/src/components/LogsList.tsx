import type { LogEntryRead } from "../api/types";
import { formatDateTime } from "../lib/format";

function LogsList({ logs }: { logs: LogEntryRead[] }) {
  if (logs.length === 0) {
    return <p className="muted">No log entries in this window.</p>;
  }

  return (
    <div className="log-list">
      {logs.map((log) => (
        <div key={log.id} className={`log-line log-level-${log.level.toLowerCase()}`}>
          <span className="log-time">{formatDateTime(log.timestamp)}</span>
          <span className="log-level">{log.level}</span>
          <span className="log-message">{log.message}</span>
        </div>
      ))}
    </div>
  );
}

export default LogsList;
