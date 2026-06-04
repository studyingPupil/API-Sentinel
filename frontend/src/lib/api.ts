import type {
  CredentialWithLatest,
  MetricsResponse,
  UsageSnapshot,
  NotificationChannel,
} from "@/types";

const BASE = "/api";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Credentials
  listCredentials: () =>
    req<CredentialWithLatest[]>("/credentials"),

  addCredential: (data: { provider: string; api_key: string; alias: string }) =>
    req<CredentialWithLatest>("/credentials", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  deleteCredential: (id: number) =>
    req<void>(`/credentials/${id}`, { method: "DELETE" }),

  updateCredential: (id: number, data: Record<string, unknown>) =>
    req<CredentialWithLatest>(`/credentials/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  syncCredential: (id: number) =>
    req<CredentialWithLatest>(`/credentials/${id}/sync`, { method: "POST" }),

  getMetrics: (id: number) =>
    req<MetricsResponse>(`/credentials/${id}/metrics`),

  getHistory: (id: number, days: number = 7) =>
    req<UsageSnapshot[]>(`/credentials/${id}/history?days=${days}`),

  // Notifications
  listChannels: () =>
    req<NotificationChannel[]>("/notifications/channels"),

  addChannel: (data: { channel_type: string; config_json: string }) =>
    req<NotificationChannel>("/notifications/channels", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  deleteChannel: (id: number) =>
    req<void>(`/notifications/channels/${id}`, { method: "DELETE" }),

  updateChannel: (id: number, data: Record<string, unknown>) =>
    req<NotificationChannel>(`/notifications/channels/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  testChannel: (id: number) =>
    req<{ status: string; message: string }>(
      `/notifications/channels/${id}/test`,
      { method: "POST" }
    ),

  getEmailProviders: () =>
    req<{ value: string; label: string; smtp_host: string; smtp_port: number }[]>(
      "/notifications/email-providers"
    ),
};
