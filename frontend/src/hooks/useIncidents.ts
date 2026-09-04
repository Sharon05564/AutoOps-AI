import { useQuery } from "@tanstack/react-query";

import { fetchIncident, fetchIncidentTimeline, fetchIncidents } from "../api/incidents";

export function useIncidents(status?: string) {
  return useQuery({
    queryKey: ["incidents", status ?? "all"],
    queryFn: () => fetchIncidents(status),
  });
}

export function useIncident(incidentId: string | undefined) {
  return useQuery({
    queryKey: ["incidents", incidentId],
    queryFn: () => fetchIncident(incidentId as string),
    enabled: Boolean(incidentId),
  });
}

export function useIncidentTimeline(incidentId: string | undefined) {
  return useQuery({
    queryKey: ["incidents", incidentId, "timeline"],
    queryFn: () => fetchIncidentTimeline(incidentId as string),
    enabled: Boolean(incidentId),
  });
}
