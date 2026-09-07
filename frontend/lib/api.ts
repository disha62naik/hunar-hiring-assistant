const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} failed: ${res.status} ${text}`);
  }
  return res.json();
}

// ---- Screenings (Project 1) ----
export const api = {
  listScreenings: () => request("/screenings"),
  createScreening: (body: { title: string; job_description: string; questions?: string[] }) =>
    request("/screenings", { method: "POST", body: JSON.stringify(body) }),
  getScreening: (id: number) => request(`/screenings/${id}`),
  addCandidates: (
    screeningId: number,
    candidates: { name: string; phone: string; email?: string }[]
  ) =>
    request(`/screenings/${screeningId}/candidates`, {
      method: "POST",
      body: JSON.stringify({ candidates }),
    }),
  triggerScreeningCalls: (screeningId: number) =>
    request(`/screenings/${screeningId}/trigger-calls`, { method: "POST" }),
  retryCreateScreeningAgent: (screeningId: number) =>
    request(`/screenings/${screeningId}/create-agent`, { method: "POST" }),

  // ---- Reachout (Project 2) ----
  createReachoutSearch: (body: { job_description: string; location?: string; max_results?: number }) =>
    request(`/reachout/search`, { method: "POST", body: JSON.stringify(body) }),
  getReachoutSearch: (id: number) => request(`/reachout/${id}`),
  triggerReachoutCalls: (searchId: number) =>
    request(`/reachout/${searchId}/trigger-calls`, { method: "POST" }),
  retryCreateReachoutAgent: (searchId: number) =>
    request(`/reachout/${searchId}/create-agent`, { method: "POST" }),

  // ---- Calls ----
  getCall: (id: number) => request(`/calls/${id}`),
};
