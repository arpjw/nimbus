export type Phase =
  | "queued" | "cloning" | "indexing" | "planning"
  | "implementing" | "verifying" | "fixing"
  | "reviewing" | "pr_creation" | "cleanup"
  | "done" | "failed";

export interface Task {
  id: string;
  workspace_id: string;
  repo_id: string;
  description: string;
  phase: Phase;
  iteration: number;
  branch_name: string | null;
  pr_url: string | null;
  error: string | null;
  plan: string | null;
  repo_full_name: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface MemoryEntry {
  id: string;
  text: string;
  metadata: {
    repo_id: string;
    label?: string;
    task_description?: string;
    timestamp: string;
  };
}

export interface KeyInfo {
  id: string;
  name: string;
  owner_email: string;
  tier: string;
  task_count_month: number;
  monthly_limit: number | null;
  last_used_at: string | null;
}

export interface GeneratedKey {
  id: string;
  raw_key: string;
  name: string;
  owner_email: string;
  tier: string;
}

export interface Commit {
  sha: string;
  commit: {
    message: string;
    author: { name: string; date: string };
  };
  html_url: string;
}

export interface Repo {
  id: string;
  workspace_id: string;
  name: string;
  url: string;
  status: "pending" | "indexed" | "error";
  file_count: number;
  chunk_count: number;
  indexed_at: string | null;
  created_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  system_prompt_addition: string;
  owner_key_id: string;
  created_at: string;
}

export interface WSEvent {
  task_id: string;
  phase: Phase;
  message: string;
  ts: string;
  data?: Record<string, unknown>;
}

export interface LogLine {
  id: string;
  phase: Phase;
  message: string;
  ts: string;
  type: "agent" | "tool" | "error" | "done" | "info";
}

export const PHASE_ORDER: Phase[] = [
  "queued", "cloning", "indexing", "planning",
  "implementing", "verifying", "fixing",
  "reviewing", "pr_creation", "cleanup", "done",
];

export const PHASE_LABELS: Record<Phase, string> = {
  queued: "Queued",
  cloning: "Clone",
  indexing: "Index",
  planning: "Plan",
  implementing: "Implement",
  verifying: "Verify",
  fixing: "Fix",
  reviewing: "Review",
  pr_creation: "PR",
  cleanup: "Cleanup",
  done: "Done",
  failed: "Failed",
};
