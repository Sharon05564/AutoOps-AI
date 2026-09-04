import { useQuery } from "@tanstack/react-query";

import { fetchDeployments } from "../api/deployments";

export function useDeployments(serviceId?: string) {
  return useQuery({
    queryKey: ["deployments", serviceId ?? "all"],
    queryFn: () => fetchDeployments(serviceId),
  });
}
