import { apiClient } from "./client";
import type {
  ActionType,
  IncidentDetail,
  IncidentRead,
  InvestigationDetail,
  PostmortemRead,
  RemediationActionRead,
  TimelineEvent,
  VerificationRead,
} from "./types";

export async function fetchIncidents(status?: string): Promise<IncidentRead[]> {
  const { data } = await apiClient.get<IncidentRead[]>("/incidents", {
    params: status ? { status } : undefined,
  });
  return data;
}

export async function fetchIncident(incidentId: string): Promise<IncidentDetail> {
  const { data } = await apiClient.get<IncidentDetail>(`/incidents/${incidentId}`);
  return data;
}

export async function fetchIncidentTimeline(incidentId: string): Promise<TimelineEvent[]> {
  const { data } = await apiClient.get<TimelineEvent[]>(`/incidents/${incidentId}/timeline`);
  return data;
}

export async function investigateIncident(incidentId: string): Promise<InvestigationDetail> {
  const { data } = await apiClient.post<InvestigationDetail>(
    `/incidents/${incidentId}/investigate`
  );
  return data;
}

export async function remediateIncident(
  incidentId: string,
  actionType?: ActionType
): Promise<RemediationActionRead> {
  const { data } = await apiClient.post<RemediationActionRead>(
    `/incidents/${incidentId}/remediate`,
    actionType ? { action_type: actionType } : {}
  );
  return data;
}

export async function approveRemediation(
  incidentId: string,
  approved: boolean,
  approvedBy: string,
  reason: string
): Promise<RemediationActionRead> {
  const { data } = await apiClient.post<RemediationActionRead>(
    `/incidents/${incidentId}/approve`,
    { approved, approved_by: approvedBy, reason }
  );
  return data;
}

export async function verifyIncidentRecovery(incidentId: string): Promise<VerificationRead> {
  const { data } = await apiClient.post<VerificationRead>(`/incidents/${incidentId}/verify`);
  return data;
}

export async function fetchPostmortem(incidentId: string): Promise<PostmortemRead> {
  const { data } = await apiClient.get<PostmortemRead>(`/incidents/${incidentId}/postmortem`);
  return data;
}

export function postmortemMarkdownUrl(incidentId: string): string {
  return `${apiClient.defaults.baseURL}/incidents/${incidentId}/postmortem/markdown`;
}
