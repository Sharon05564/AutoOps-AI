import type { IncidentStatus, RemediationStatus, RiskLevel, Severity } from "../api/types";

type BadgeTone = "neutral" | "info" | "warning" | "danger" | "success";

const SEVERITY_TONE: Record<Severity, BadgeTone> = {
  LOW: "neutral",
  MEDIUM: "warning",
  HIGH: "danger",
  CRITICAL: "danger",
};

const INCIDENT_STATUS_TONE: Record<IncidentStatus, BadgeTone> = {
  DETECTED: "warning",
  INVESTIGATING: "info",
  DIAGNOSED: "info",
  AWAITING_APPROVAL: "warning",
  REMEDIATING: "info",
  VERIFYING: "info",
  RESOLVED: "success",
  FAILED: "danger",
};

const REMEDIATION_STATUS_TONE: Record<RemediationStatus, BadgeTone> = {
  PENDING_APPROVAL: "warning",
  APPROVED: "info",
  REJECTED: "danger",
  EXECUTING: "info",
  SUCCEEDED: "success",
  FAILED: "danger",
};

const RISK_TONE: Record<RiskLevel, BadgeTone> = {
  LOW: "success",
  MEDIUM: "warning",
  HIGH: "danger",
};

function Badge({ tone, children }: { tone: BadgeTone; children: React.ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <Badge tone={SEVERITY_TONE[severity]}>{severity}</Badge>;
}

export function IncidentStatusBadge({ status }: { status: IncidentStatus }) {
  return <Badge tone={INCIDENT_STATUS_TONE[status]}>{status.replace("_", " ")}</Badge>;
}

export function RemediationStatusBadge({ status }: { status: RemediationStatus }) {
  return <Badge tone={REMEDIATION_STATUS_TONE[status]}>{status.replace("_", " ")}</Badge>;
}

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  return <Badge tone={RISK_TONE[risk]}>{risk} RISK</Badge>;
}

export function HealthBadge({ status }: { status: "healthy" | "degraded" | "unknown" }) {
  const tone: BadgeTone = status === "healthy" ? "success" : status === "degraded" ? "danger" : "neutral";
  return <Badge tone={tone}>{status}</Badge>;
}
