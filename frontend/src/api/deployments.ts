import { apiClient } from "./client";
import type { DeploymentRead } from "./types";

export async function fetchDeployments(serviceId?: string): Promise<DeploymentRead[]> {
  const { data } = await apiClient.get<DeploymentRead[]>("/deployments", {
    params: serviceId ? { service_id: serviceId } : undefined,
  });
  return data;
}
