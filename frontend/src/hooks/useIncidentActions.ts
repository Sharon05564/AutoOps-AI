import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  approveRemediation,
  investigateIncident,
  remediateIncident,
  verifyIncidentRecovery,
} from "../api/incidents";
import type { ActionType } from "../api/types";

export function useIncidentActions(incidentId: string) {
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["incidents", incidentId] });
    queryClient.invalidateQueries({ queryKey: ["incidents", "all"] });
    queryClient.invalidateQueries({ queryKey: ["services"] });
  };

  const investigate = useMutation({
    mutationFn: () => investigateIncident(incidentId),
    onSuccess: invalidate,
  });

  const remediate = useMutation({
    mutationFn: (actionType?: ActionType) => remediateIncident(incidentId, actionType),
    onSuccess: invalidate,
  });

  const approve = useMutation({
    mutationFn: ({
      approved,
      approvedBy,
      reason,
    }: {
      approved: boolean;
      approvedBy: string;
      reason: string;
    }) => approveRemediation(incidentId, approved, approvedBy, reason),
    onSuccess: invalidate,
  });

  const verify = useMutation({
    mutationFn: () => verifyIncidentRecovery(incidentId),
    onSuccess: invalidate,
  });

  return { investigate, remediate, approve, verify };
}
