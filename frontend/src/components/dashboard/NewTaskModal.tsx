"use client";
import { useState } from "react";
import { X, Plus, Loader2 } from "lucide-react";
import type { Repo, Task } from "@/types";
import { api } from "@/lib/api";

interface Props {
  repos: Repo[];
  workspaceId: string;
  onCreated: (task: Task) => void;
  onClose: () => void;
}

export function NewTaskModal({ repos, workspaceId, onCreated, onClose }: Props) {
  const [repoId, setRepoId] = useState(repos[0]?.id ?? "");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!description.trim() || !repoId) return;
    setLoading(true);
    setError(null);
    try {
      const task = await api.tasks.create(workspaceId, repoId, description.trim());
      onCreated(task);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg/80 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-surface p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-sans font-bold text-xl">New Task</h2>
          <button onClick={onClose} className="text-muted hover:text-text transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block font-mono text-xs text-muted mb-2">Repository</label>
            <select
              value={repoId}
              onChange={(e) => setRepoId(e.target.value)}
              className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2.5 font-body text-sm text-text focus:border-accent/50 focus:outline-none"
            >
              {repos.map((r) => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-mono text-xs text-muted mb-2">Task Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Migrate auth middleware to JWT tokens with refresh token support"
              rows={4}
              className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2.5 font-body text-sm text-text resize-none focus:border-accent/50 focus:outline-none placeholder:text-muted/50"
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
              }}
            />
            <p className="text-xs text-muted/60 mt-1 font-mono">⌘+Enter to submit</p>
          </div>

          {error && (
            <p className="text-xs text-danger font-mono bg-danger/5 rounded-lg px-3 py-2">{error}</p>
          )}
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-lg border border-border text-sm font-body text-muted hover:text-text hover:border-border-bright transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={loading || !description.trim() || !repoId}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-accent text-bg text-sm font-sans font-bold hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
            {loading ? "Creating..." : "Run Task"}
          </button>
        </div>
      </div>
    </div>
  );
}
