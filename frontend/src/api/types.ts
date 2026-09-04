export type IncidentStatus =
  | "DETECTED"
  | "INVESTIGATING"
  | "DIAGNOSED"
  | "AWAITING_APPROVAL"
  | "REMEDIATING"
  | "VERIFYING"
  | "RESOLVED"
  | "FAILED";

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";
export type ActionType = "ROLLBACK_DEPLOYMENT" | "RESTART_SERVICE" | "SCALE_SERVICE";
export type RemediationStatus =
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "REJECTED"
  | "EXECUTING"
  | "SUCCEEDED"
  | "FAILED";
export type DeploymentStatus = "ACTIVE" | "ROLLED_BACK" | "SUPERSEDED";
export type InvestigationStatus = "IN_PROGRESS" | "COMPLETED" | "FAILED";
export type VerificationStatus = "PASSED" | "FAILED" | "IN_PROGRESS";
export type LogLevel = "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";

export interface ServiceRead {
  id: string;
  name: string;
  description: string;
  replicas: number;
  active_deployment_id: string | null;
  last_seen_at: string | null;
  created_at: string;
}

export interface ServiceHealth {
  service: ServiceRead;
  error_rate: number;
  latency_p95_ms: number;
  active_incidents: number;
  status: "healthy" | "degraded" | "unknown";
}

export interface MetricSnapshotRead {
  id: string;
  service_id: string;
  timestamp: string;
  request_count: number;
  error_count: number;
  error_rate: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
}

export interface LogEntryRead {
  id: string;
  service_id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  source: string;
}

export interface DeploymentRead {
  id: string;
  service_id: string;
  version: string;
  status: DeploymentStatus;
  is_bad_deployment: boolean;
  deployed_at: string;
  rolled_back_at: string | null;
  rolled_back_from_id: string | null;
}

export interface AlertRead {
  id: string;
  incident_id: string;
  service_id: string;
  metric_name: string;
  value: number;
  threshold: number;
  message: string;
  triggered_at: string;
}

export interface AgentToolCallRead {
  id: string;
  investigation_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
  duration_ms: number;
  called_at: string;
}

export interface InvestigationRead {
  id: string;
  incident_id: string;
  status: InvestigationStatus;
  llm_provider: string;
  root_cause: string;
  confidence: number;
  summary: string;
  recommended_action: string;
  evidence: string[];
  started_at: string;
  completed_at: string | null;
}

export interface InvestigationDetail extends InvestigationRead {
  tool_calls: AgentToolCallRead[];
}

export interface ApprovalRead {
  id: string;
  remediation_action_id: string;
  approved: boolean;
  approved_by: string;
  reason: string;
  decided_at: string;
}

export interface RemediationActionRead {
  id: string;
  incident_id: string;
  action_type: ActionType;
  risk_level: RiskLevel;
  status: RemediationStatus;
  parameters: Record<string, unknown>;
  result: Record<string, unknown>;
  idempotency_key: string;
  attempt_number: number;
  created_at: string;
  executed_at: string | null;
  approval: ApprovalRead | null;
}

export interface VerificationRead {
  id: string;
  incident_id: string;
  remediation_action_id: string;
  status: VerificationStatus;
  metrics_before: Record<string, number | string>;
  metrics_after: Record<string, number | string>;
  checked_at: string;
}

export interface IncidentRead {
  id: string;
  service_id: string;
  title: string;
  description: string;
  severity: Severity;
  status: IncidentStatus;
  triggering_deployment_id: string | null;
  detected_at: string;
  resolved_at: string | null;
}

export interface IncidentDetail extends IncidentRead {
  alerts: AlertRead[];
  investigations: InvestigationDetail[];
  remediation_actions: RemediationActionRead[];
  verifications: VerificationRead[];
  has_postmortem: boolean;
}

export interface TimelineEvent {
  timestamp: string;
  event_type: string;
  title: string;
  description: string;
  metadata: Record<string, unknown>;
}

export interface PostmortemRead {
  id: string;
  incident_id: string;
  summary: string;
  root_cause: string;
  timeline: Array<Record<string, unknown>>;
  evidence: string[];
  remediation_summary: string;
  recovery_verification: string;
  prevention_recommendations: string[];
  markdown_report: string;
  generated_at: string;
}
