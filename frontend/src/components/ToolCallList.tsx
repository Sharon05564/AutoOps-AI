import { useState } from "react";

import type { AgentToolCallRead } from "../api/types";

function ToolCallItem({ call }: { call: AgentToolCallRead }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="tool-call">
      <button className="tool-call-header" onClick={() => setExpanded((v) => !v)}>
        <span className="tool-call-name">{call.tool_name}</span>
        <span className="tool-call-duration">{call.duration_ms.toFixed(1)}ms</span>
        <span className="tool-call-chevron">{expanded ? "▾" : "▸"}</span>
      </button>
      {expanded && (
        <div className="tool-call-body">
          {Object.keys(call.arguments).length > 0 && (
            <>
              <div className="tool-call-label">Arguments</div>
              <pre className="tool-call-json">{JSON.stringify(call.arguments, null, 2)}</pre>
            </>
          )}
          <div className="tool-call-label">Result</div>
          <pre className="tool-call-json">{JSON.stringify(call.result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function ToolCallList({ calls }: { calls: AgentToolCallRead[] }) {
  if (calls.length === 0) {
    return <p className="muted">No tool calls recorded.</p>;
  }
  return (
    <div className="tool-call-list">
      {calls.map((call) => (
        <ToolCallItem key={call.id} call={call} />
      ))}
    </div>
  );
}

export default ToolCallList;
