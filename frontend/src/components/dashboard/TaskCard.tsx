"use client";
import { GitPullRequest, Clock, CheckCircle2, XCircle, Loader2, AlertCircle } from "lucide-react";
import Link from "next/link";
import type { Task, Phase } from "@/types";
import { PHASE_LABELS } from "@/types";

const PHASE_CONFIG: Record<string, { color: string; bg: string; icon: React.ReactNode }> = {
  queued:       { color: "text-muted",   bg: "bg-muted/10",    icon: <Clock size={11} /> },
  cloning:      { color: "text-info",    bg: "bg-info/10",     icon: <Loader2 size={11} className="animate-spin" /> },
  indexing:     { color: "text-info",    bg: "bg-info/10",     icon: <Loader2 size={11} className="animate-spin" /> },
  planning:     { color: "text-warning", bg: "bg-warning/10",  icon: <Loader2 size={11} className="animate-spin" /> },
  implementing: { color: "text-warning", bg: "bg-warning/10",  icon: <Loader2 size={11} className="animate-spin" /> },
  verifying:    { color: "text-warning", bg: "bg-warning/10",  icon: <Loader2 size={11} className="animate-spin" /> },
  fixing:       { color: "text-warning", bg: "bg-warning/10",  icon: <AlertCircle size={11} /> },
  reviewing:    { color: "text-accent",  bg: "bg-accent/10",   icon: <Loader2 size={11} className="animate-spin" /> },
  pr_creation:  { color: "text-accent",  bg: "bg-accent/10",   icon: <GitPullRequest size={11} /> },
  cleanup:      { color: "text-accent",  bg: "bg-accent/10",   icon: <Loader2 size={11} className="animate-spin" /> },
  done:         { color: "text-accent",  bg: "bg-accent/10",   icon: <CheckCircle2 size={11} /> },
  failed:       { color: "text-danger",  bg: "bg-danger/10",   icon: <XCircle size={11} /> },
};

function PhaseBadge({ phase }: { phase: Phase }) {
  const cfg = PHASE_CONFIG[phase] ?? PHASE_CONFIG.queued;
  return (
    <span className={`phase-badge ${cfg.color} ${cfg.bg}`}>
      {cfg.icon}
      {PHASE_LABELS[phase]}
    </span>
  );
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function TaskCard({ task }: { task: Task }) {
  const active = !["done", "failed", "queued"].includes(task.phase);

  return (
    <Link href={`/task/${task.id}`}>
      <div className={`rounded-xl border p-5 card-hover cursor-pointer
        ${task.phase === "failed" ? "border-danger/20 bg-surface" : "border-border bg-surface"}
        ${active ? "border-warning/20" : ""}
        ${task.phase === "done" ? "border-accent/15" : ""}
      `}>
        <div className="flex items-start justify-between gap-4 mb-3">
          <p className="font-body text-sm text-text leading-snug line-clamp-2 flex-1">
            {task.description}
          </p>
          <PhaseBadge phase={task.phase} />
        </div>

        <div className="flex items-center gap-4 text-xs text-muted font-mono">
          <span>{timeAgo(task.created_at)}</span>
          {task.iteration > 0 && <span>iter {task.iteration}</span>}
          {task.pr_url && (
            <span
              className="flex items-center gap-1 text-accent hover:underline"
              onClick={(e) => { e.preventDefault(); window.open(task.pr_url!, "_blank"); }}
            >
              <GitPullRequest size={11} /> PR
            </span>
          )}
          {task.phase === "failed" && task.error && (
            <span className="text-danger truncate max-w-[200px]">{task.error}</span>
          )}
        </div>
      </div>
    </Link>
  );
}
