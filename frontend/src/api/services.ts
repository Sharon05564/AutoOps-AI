import { apiClient } from "./client";
import type { LogEntryRead, MetricSnapshotRead, ServiceHealth } from "./types";

export async function fetchServices(): Promise<ServiceHealth[]> {
  const { data } = await apiClient.get<ServiceHealth[]>("/services");
  return data;
}

export async function fetchService(serviceId: string): Promise<ServiceHealth> {
  const { data } = await apiClient.get<ServiceHealth>(`/services/${serviceId}`);
  return data;
}

export async function fetchServiceMetrics(
  serviceId: string,
  windowSeconds = 300
): Promise<MetricSnapshotRead[]> {
  const { data } = await apiClient.get<MetricSnapshotRead[]>(`/services/${serviceId}/metrics`, {
    params: { window_seconds: windowSeconds },
  });
  return data;
}

export async function fetchServiceLogs(
  serviceId: string,
  windowSeconds = 300,
  limit = 100
): Promise<LogEntryRead[]> {
  const { data } = await apiClient.get<LogEntryRead[]>(`/services/${serviceId}/logs`, {
    params: { window_seconds: windowSeconds, limit },
  });
  return data;
}
