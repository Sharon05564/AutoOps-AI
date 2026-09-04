import { apiClient } from "./client";

export async function triggerBadDeployment(): Promise<void> {
  await apiClient.post("/simulator/deployments/bad");
}

export async function resetSimulator(): Promise<void> {
  await apiClient.post("/simulator/reset");
}
