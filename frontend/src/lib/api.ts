import type { Task, Repo, Workspace, MemoryEntry, KeyInfo, GeneratedKey } from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const WS_BASE = BASE.replace(/^http/, "ws");

function getApiKey(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("nimbus_api_key");
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const apiKey = getApiKey();
  const baseHeaders: Record<string, string> = { "Content-Type": "application/json" };
  if (apiKey) baseHeaders["X-API-Key"] = apiKey;

  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...baseHeaders, ...(init?.headers as Record<string, string> ?? {}) },
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export const api = {
  workspaces: {
    list: () => req<Workspace[]>("/workspaces/"),
    create: (name: string, description?: string) =>
      req<Workspace>("/workspaces/", { method: "POST", body: JSON.stringify({ name, description }) }),
    repos: (id: string) => req<Repo[]>(`/workspaces/${id}/repos`),
  },
  repos: {
    list: () => req<Repo[]>("/repos/"),
    add: (workspace_id: string, url: string, name: string) =>
      req<Repo>("/repos/", { method: "POST", body: JSON.stringify({ workspace_id, url, name }) }),
    get: (id: string) => req<Repo>(`/repos/${id}`),
    memory: {
      list: (repoId: string) => req<MemoryEntry[]>(`/repos/${repoId}/memory`),
      add: (repoId: string, text: string, label: string) =>
        req<MemoryEntry>(`/repos/${repoId}/memory`, {
          method: "POST",
          body: JSON.stringify({ text, label }),
        }),
      delete: (repoId: string, memoryId: string) =>
        req<{ deleted: string }>(`/repos/${repoId}/memory/${memoryId}`, { method: "DELETE" }),
    },
  },
  tasks: {
    list: (workspace_id?: string) =>
      req<Task[]>(`/tasks/${workspace_id ? `?workspace_id=${workspace_id}` : ""}`),
    get: (id: string) => req<Task>(`/tasks/${id}`),
    create: (workspace_id: string, repo_id: string, description: string) =>
      req<Task>("/tasks/", { method: "POST", body: JSON.stringify({ workspace_id, repo_id, description }) }),
  },
  keys: {
    me: () => req<KeyInfo>("/keys/me"),
    generate: (name: string, owner_email: string) =>
      req<GeneratedKey>("/keys/generate", {
        method: "POST",
        body: JSON.stringify({ name, owner_email }),
      }),
    revoke: (keyId: string) => req<{ deleted: string }>(`/keys/${keyId}`, { method: "DELETE" }),
  },
};
