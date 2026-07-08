import type {
  CreateJobResponse,
  HistoryItem,
  JobResultsResponse,
  Settings,
  SettingsPayload,
} from "./types";

export function getSettings(): Promise<Settings> {
  return fetch("/api/settings").then((r) => r.json());
}

export function saveSettings(payload: SettingsPayload): Promise<Settings> {
  return fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then((r) => r.json());
}

export function getHistory(): Promise<HistoryItem[]> {
  return fetch("/api/history").then((r) => r.json());
}

export function getHistoryDetail(id: string): Promise<JobResultsResponse> {
  return fetch(`/api/history/${id}`).then((r) => r.json());
}

export function createJob(formData: FormData): Promise<CreateJobResponse> {
  return fetch("/api/jobs", { method: "POST", body: formData }).then((r) => r.json());
}

export function getJobResults(jobId: string): Promise<JobResultsResponse> {
  return fetch(`/api/jobs/${jobId}/results`).then((r) => r.json());
}

export function cancelJob(jobId: string): Promise<Response> {
  return fetch(`/api/jobs/${jobId}/cancel`, { method: "POST" });
}

export function downloadUrl(jobId: string): string {
  return `/api/jobs/${jobId}/download`;
}
