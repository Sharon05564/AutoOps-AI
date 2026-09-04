import { useQuery } from "@tanstack/react-query";

import { fetchService, fetchServiceLogs, fetchServiceMetrics, fetchServices } from "../api/services";

export function useServices() {
  return useQuery({ queryKey: ["services"], queryFn: fetchServices });
}

export function useService(serviceId: string | undefined) {
  return useQuery({
    queryKey: ["services", serviceId],
    queryFn: () => fetchService(serviceId as string),
    enabled: Boolean(serviceId),
  });
}

export function useServiceMetrics(serviceId: string | undefined, windowSeconds = 300) {
  return useQuery({
    queryKey: ["services", serviceId, "metrics", windowSeconds],
    queryFn: () => fetchServiceMetrics(serviceId as string, windowSeconds),
    enabled: Boolean(serviceId),
  });
}

export function useServiceLogs(serviceId: string | undefined, windowSeconds = 300) {
  return useQuery({
    queryKey: ["services", serviceId, "logs", windowSeconds],
    queryFn: () => fetchServiceLogs(serviceId as string, windowSeconds),
    enabled: Boolean(serviceId),
  });
}
