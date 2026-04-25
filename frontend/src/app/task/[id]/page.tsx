"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, GitPullRequest, ExternalLink, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { useTaskStream } from "@/lib/ws";
import type { Task } from "@/types";
import { PhaseTimeline } from "@/components/task/PhaseTimeline";
import { LogStream } from "@/components/task/LogStream";

export default function TaskPage({ params }: { params: { id: string } }) {
  const [task, setTask] = useState<Task | null>(null);

  useEffect(() => {
    api.tasks.get(params.id).then(setTask).catch(console.error);
  }, [params.id]);

  const { logs, connected } = useTaskStream(params.id);

  useEffect(() => {
    const last = logs[logs.length - 1];
    if (!last) return;
    if (task && last.phase !== task.phase) {
      api.tasks.get(params.id).then(setTask).catch(() => null);
    }
  }, [logs.length]);

  if (!task) {
    return (
      <div className="min-h-screen grid-bg flex items-center justify-center">
        <p className="font-mono text-muted text-sm">Loading task...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen grid-bg flex flex-col">

      {/* Header */}
      <header className="border-b border-border bg-bg/90 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between gap-6">
          <div className="flex items-center gap-4 min-w-0">
            <Link href="/dashboard" className="text-muted hover:text-text transition-colors flex-shrink-0">
              <ArrowLeft size={14} />
            </Link>
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-5 h-5 rounded-sm bg-accent flex items-center justify-center flex-shrink-0">
                <span className="font-sans font-black text-bg text-[10px]">N</span>
              </div>
              <p className="font-body text-sm text-muted truncate">{task.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            {task.pr_url && (
              <a
                href={task.pr_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-accent/30 text-accent text-xs font-mono hover:bg-accent/5 transition-colors"
              >
                <GitPullRequest size={11} /> View PR <ExternalLink size={10} />
              </a>
            )}
            <span className="font-mono text-xs text-muted/60">{task.id.slice(0, 8)}</span>
          </div>
        </div>
      </header>

      {/* Body */}
      <div className="flex-1 flex max-w-6xl mx-auto w-full px-6 py-6 gap-6 min-h-0">

        {/* Left: timeline + meta */}
        <aside className="w-52 flex-shrink-0 space-y-6">
          <div>
            <p className="font-mono text-xs text-muted/60 uppercase tracking-widest mb-4">Progress</p>
            <PhaseTimeline phase={task.phase} />
          </div>

          {task.iteration > 0 && (
            <div className="rounded-lg border border-border bg-surface p-4">
              <p className="font-mono text-xs text-muted mb-1">Iterations</p>
              <p className="font-sans font-bold text-2xl text-text">{task.iteration}</p>
            </div>
          )}

          {task.branch_name && (
            <div className="rounded-lg border border-border bg-surface p-4">
              <p className="font-mono text-xs text-muted mb-1">Branch</p>
              <p className="font-mono text-xs text-text break-all">{task.branch_name}</p>
            </div>
          )}

          {task.phase === "failed" && task.error && (
            <div className="rounded-lg border border-danger/20 bg-danger/5 p-4">
              <div className="flex items-center gap-1.5 mb-2">
                <AlertCircle size={12} className="text-danger" />
                <p className="font-mono text-xs text-danger">Error</p>
              </div>
              <p className="font-mono text-xs text-danger/80 break-words">{task.error}</p>
            </div>
          )}
        </aside>

        {/* Right: live log */}
        <div className="flex-1 rounded-xl border border-border bg-surface overflow-hidden min-h-[600px] flex flex-col">
          <LogStream logs={logs} connected={connected} />
        </div>
      </div>
    </div>
  );
}
