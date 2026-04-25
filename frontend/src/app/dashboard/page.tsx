"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { Plus, Layers, GitBranch, ArrowLeft, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { Task, Repo, Workspace } from "@/types";
import { TaskCard } from "@/components/dashboard/TaskCard";
import { NewTaskModal } from "@/components/dashboard/NewTaskModal";

export default function Dashboard() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<string | null>(null);
  const [repos, setRepos] = useState<Repo[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    api.workspaces.list().then((ws) => {
      setWorkspaces(ws);
      if (ws.length > 0) setActiveWorkspace(ws[0].id);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!activeWorkspace) return;
    Promise.all([
      api.workspaces.repos(activeWorkspace),
      api.tasks.list(activeWorkspace),
    ]).then(([r, t]) => {
      setRepos(r);
      setTasks(t);
    });
  }, [activeWorkspace]);

  async function refresh() {
    if (!activeWorkspace) return;
    setRefreshing(true);
    const t = await api.tasks.list(activeWorkspace);
    setTasks(t);
    setRefreshing(false);
  }

  const active = tasks.filter((t) => !["done", "failed"].includes(t.phase));
  const completed = tasks.filter((t) => ["done", "failed"].includes(t.phase));

  return (
    <div className="min-h-screen grid-bg">
      {/* Header */}
      <header className="border-b border-border bg-bg/90 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-1.5 text-muted hover:text-text transition-colors">
              <ArrowLeft size={14} />
            </Link>
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-sm bg-accent flex items-center justify-center">
                <span className="font-sans font-black text-bg text-[10px]">N</span>
              </div>
              <span className="font-sans font-bold text-sm">Dashboard</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={refresh}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono text-muted hover:text-text border border-border rounded-lg hover:border-border-bright transition-colors"
            >
              <RefreshCw size={11} className={refreshing ? "animate-spin" : ""} />
              Refresh
            </button>
            <button
              onClick={() => setShowModal(true)}
              disabled={repos.length === 0}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-accent text-bg text-xs font-sans font-bold rounded-lg hover:bg-accent/90 disabled:opacity-40 transition-colors"
            >
              <Plus size={12} /> New Task
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8 flex gap-8">

        {/* Sidebar */}
        <aside className="w-56 flex-shrink-0">
          <div className="sticky top-24 space-y-6">
            <div>
              <p className="font-mono text-xs text-muted/60 uppercase tracking-widest mb-3">Workspaces</p>
              <div className="space-y-1">
                {workspaces.map((ws) => (
                  <button
                    key={ws.id}
                    onClick={() => setActiveWorkspace(ws.id)}
                    className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors text-sm
                      ${activeWorkspace === ws.id
                        ? "bg-accent/10 text-accent border border-accent/20"
                        : "text-muted hover:text-text hover:bg-surface"
                      }`}
                  >
                    <Layers size={13} />
                    <span className="font-body truncate">{ws.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {repos.length > 0 && (
              <div>
                <p className="font-mono text-xs text-muted/60 uppercase tracking-widest mb-3">Repositories</p>
                <div className="space-y-1">
                  {repos.map((r) => (
                    <div key={r.id} className="flex items-center gap-2 px-3 py-2 text-sm">
                      <GitBranch size={12} className="text-muted flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="font-body text-muted truncate text-xs">{r.name}</p>
                        <p className="font-mono text-muted/50 text-[10px]">
                          {r.status === "indexed" ? `${r.chunk_count} chunks` : r.status}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 min-w-0">
          {loading ? (
            <div className="flex items-center justify-center h-40 text-muted font-mono text-sm">
              Loading...
            </div>
          ) : workspaces.length === 0 ? (
            <div className="text-center py-20">
              <p className="font-sans font-bold text-2xl mb-2">No workspaces yet</p>
              <p className="text-muted font-body text-sm mb-6">Create a workspace and add your first repository to get started.</p>
            </div>
          ) : (
            <div className="space-y-8 animate-in">
              {active.length > 0 && (
                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <span className="w-2 h-2 rounded-full bg-warning animate-pulse" />
                    <p className="font-mono text-xs text-muted uppercase tracking-widest">
                      Active ({active.length})
                    </p>
                  </div>
                  <div className="space-y-3">
                    {active.map((t) => <TaskCard key={t.id} task={t} />)}
                  </div>
                </section>
              )}

              {completed.length > 0 && (
                <section>
                  <p className="font-mono text-xs text-muted/60 uppercase tracking-widest mb-4">
                    Completed ({completed.length})
                  </p>
                  <div className="space-y-3">
                    {completed.map((t) => <TaskCard key={t.id} task={t} />)}
                  </div>
                </section>
              )}

              {tasks.length === 0 && (
                <div className="rounded-xl border border-dashed border-border p-12 text-center">
                  <p className="font-sans font-semibold text-lg mb-2">No tasks yet</p>
                  <p className="text-muted font-body text-sm mb-6">
                    Click "New Task" to run your first autonomous implementation.
                  </p>
                  <button
                    onClick={() => setShowModal(true)}
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-accent text-bg font-sans font-bold text-sm rounded-lg hover:bg-accent/90 transition-colors"
                  >
                    <Plus size={14} /> New Task
                  </button>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {showModal && (
        <NewTaskModal
          repos={repos}
          workspaceId={activeWorkspace!}
          onCreated={(task) => {
            setTasks((prev) => [task, ...prev]);
            setShowModal(false);
          }}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
}
