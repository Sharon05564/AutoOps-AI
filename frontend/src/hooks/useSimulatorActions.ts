import { useMutation, useQueryClient } from "@tanstack/react-query";

import { resetSimulator, triggerBadDeployment } from "../api/simulator";

export function useSimulatorActions() {
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["services"] });
    queryClient.invalidateQueries({ queryKey: ["incidents"] });
    queryClient.invalidateQueries({ queryKey: ["deployments"] });
  };

  const triggerBad = useMutation({
    mutationFn: triggerBadDeployment,
    onSuccess: invalidate,
  });

  const reset = useMutation({
    mutationFn: resetSimulator,
    onSuccess: invalidate,
  });

  return { triggerBad, reset };
}
