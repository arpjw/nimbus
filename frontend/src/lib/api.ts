import type { Task, Repo, Workspace } from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
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
    add: (workspace_id: string, url: string, name: string) =>
      req<Repo>("/repos/", { method: "POST", body: JSON.stringify({ workspace_id, url, name }) }),
    get: (id: string) => req<Repo>(`/repos/${id}`),
  },
  tasks: {
    list: (workspace_id?: string) =>
      req<Task[]>(`/tasks/${workspace_id ? `?workspace_id=${workspace_id}` : ""}`),
    get: (id: string) => req<Task>(`/tasks/${id}`),
    create: (workspace_id: string, repo_id: string, description: string) =>
      req<Task>("/tasks/", { method: "POST", body: JSON.stringify({ workspace_id, repo_id, description }) }),
  },
};
