import { useQuery } from "@tanstack/react-query";

import { fetchPostmortem } from "../api/incidents";

export function usePostmortem(incidentId: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ["incidents", incidentId, "postmortem"],
    queryFn: () => fetchPostmortem(incidentId as string),
    enabled: Boolean(incidentId) && enabled,
    retry: false,
  });
}
