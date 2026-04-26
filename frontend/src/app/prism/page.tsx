"use client";
import { useState, useEffect } from "react";
import { Instrument_Serif } from "next/font/google";
import type { Repo, Task } from "@/types";

const serif = Instrument_Serif({ subsets: ["latin"], style: ["italic"], weight: "400" });

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const C = {
  bg:      "#0A0A0A",
  surface: "#141414",
  border:  "rgba(255,255,255,0.06)",
  text:    "#FAFAFA",
  muted:   "rgba(255,255,255,0.5)",
  gold:    "#c4a96a",
  green:   "#6aab7a",
  red:     "#e05c5c",
};

const ACTIVE_PHASES = new Set([
  "queued", "cloning", "indexing", "planning",
  "implementing", "verifying", "fixing",
  "reviewing", "pr_creation", "cleanup",
  "awaiting_approval", "awaiting_diff_approval",
]);

const SKILLS = ["add-tests", "add-openapi-docs", "dependency-audit", "add-logging", "add-error-handling"];

function getApiKey(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("nimbus_api_key");
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const apiKey = getApiKey();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (apiKey) headers["X-API-Key"] = apiKey;
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...headers, ...(init?.headers as Record<string, string> ?? {}) },
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

interface PrismTask {
  id: number;
  description: string;
  skill: string | null;
  depends_on: number[];
  priority: number;
}

interface QueuedTask {
  task_id: string;
  prism_id: number;
  description: string;
}

type AppState = "input" | "review" | "running";

const btn = (gold: boolean, disabled = false): React.CSSProperties => ({
  width: "100%",
  height: gold ? 44 : 40,
  background: disabled ? "rgba(196,169,106,0.35)" : gold ? C.gold : "transparent",
  color: gold ? "#0A0A0A" : C.muted,
  border: gold ? "none" : `1px solid ${C.border}`,
  borderRadius: 8,
  fontSize: 15,
  fontWeight: gold ? 600 : 400,
  cursor: disabled ? "not-allowed" : "pointer",
  fontFamily: "var(--font-jakarta), system-ui, sans-serif",
});

export default function PrismPage() {
  const [appState, setAppState] = useState<AppState>("input");
  const [spec, setSpec] = useState("");
  const [tasks, setTasks] = useState<PrismTask[]>([]);
  const [repos, setRepos] = useState<Repo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState("");
  const [workspaceId, setWorkspaceId] = useState("");
  const [repoFallback, setRepoFallback] = useState("");
  const [workspaceFallback, setWorkspaceFallback] = useState("");
  const [parsing, setParsing] = useState(false);
  const [queueing, setQueueing] = useState(false);
  const [queued, setQueued] = useState<QueuedTask[]>([]);
  const [taskStatuses, setTaskStatuses] = useState<Record<string, Task>>({});

  useEffect(() => {
    req<Repo[]>("/repos/").then(r => {
      setRepos(r);
      if (r.length > 0) {
        setSelectedRepo(r[0].id);
        setWorkspaceId(r[0].workspace_id);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    const repo = repos.find(r => r.id === selectedRepo);
    if (repo) setWorkspaceId(repo.workspace_id);
  }, [selectedRepo, repos]);

  const handleParse = async () => {
    if (!spec.trim()) return;
    setParsing(true);
    try {
      const result = await req<{ tasks: PrismTask[] }>("/prism/parse", {
        method: "POST",
        body: JSON.stringify({ spec }),
      });
      setTasks(result.tasks);
      setAppState("review");
    } finally {
      setParsing(false);
    }
  };

  const handleQueue = async () => {
    const repoId = selectedRepo || repoFallback;
    const wsId = workspaceId || workspaceFallback;
    if (!repoId || !wsId) return;
    setQueueing(true);
    try {
      const result = await req<{ queued: QueuedTask[] }>("/prism/queue", {
        method: "POST",
        body: JSON.stringify({ tasks, repo_id: repoId, workspace_id: wsId }),
      });
      setQueued(result.queued);
      setAppState("running");
    } finally {
      setQueueing(false);
    }
  };

  useEffect(() => {
    if (appState !== "running" || queued.length === 0) return;
    const poll = async () => {
      for (const qt of queued) {
        try {
          const task = await req<Task>(`/tasks/${qt.task_id}`);
          setTaskStatuses(prev => ({ ...prev, [qt.task_id]: task }));
        } catch {}
      }
    };
    poll();
    const id = setInterval(poll, 4000);
    return () => clearInterval(id);
  }, [appState, queued]);

  const doneCount = queued.filter(qt => taskStatuses[qt.task_id]?.phase === "done").length;
  const allDone = queued.length > 0 && doneCount === queued.length;

  const updateTask = (id: number, field: keyof PrismTask, value: string | null | number[]) =>
    setTasks(prev => prev.map(t => t.id === id ? { ...t, [field]: value } : t));

  const deleteTask = (id: number) =>
    setTasks(prev => prev.filter(t => t.id !== id));

  const addTask = () => {
    const maxId = tasks.length > 0 ? Math.max(...tasks.map(t => t.id)) : 0;
    setTasks(prev => [...prev, { id: maxId + 1, description: "", skill: null, depends_on: [], priority: 1 }]);
  };

  const resetAll = () => {
    setAppState("input");
    setSpec("");
    setTasks([]);
    setQueued([]);
    setTaskStatuses({});
  };

  const inputStyle: React.CSSProperties = {
    width: "100%",
    background: C.surface,
    border: `1px solid ${C.border}`,
    borderRadius: 8,
    color: C.text,
    fontSize: 14,
    padding: "10px 14px",
    outline: "none",
    fontFamily: "var(--font-jakarta), system-ui, sans-serif",
  };

  return (
    <div style={{ minHeight: "100vh", background: C.bg, padding: "60px 24px", fontFamily: "var(--font-jakarta), system-ui, sans-serif" }}>
      <div style={{ maxWidth: 720, margin: "0 auto" }}>

        {appState === "input" && (
          <>
            <h1 style={{ fontFamily: serif.style.fontFamily, fontStyle: "italic", fontSize: 32, color: C.text, marginBottom: 6, fontWeight: 400 }}>
              Prism
            </h1>
            <p style={{ fontFamily: "var(--font-jetbrains), monospace", fontSize: 13, color: C.muted, marginBottom: 40 }}>
              spec to pull requests
            </p>

            <textarea
              value={spec}
              onChange={e => setSpec(e.target.value)}
              placeholder="Describe what you want to build — a PRD, a feature description, or plain English. Prism will break it into a sequence of Nimbus tasks."
              style={{
                ...inputStyle,
                minHeight: 200,
                resize: "vertical",
                lineHeight: 1.6,
                marginBottom: 16,
                fontSize: 15,
              }}
            />

            <div style={{ marginBottom: 16 }}>
              {repos.length > 0 ? (
                <select
                  value={selectedRepo}
                  onChange={e => setSelectedRepo(e.target.value)}
                  style={inputStyle}
                >
                  {repos.map(r => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  <input
                    value={repoFallback}
                    onChange={e => setRepoFallback(e.target.value)}
                    placeholder="Repo ID"
                    style={inputStyle}
                  />
                  <input
                    value={workspaceFallback}
                    onChange={e => setWorkspaceFallback(e.target.value)}
                    placeholder="Workspace ID"
                    style={inputStyle}
                  />
                </div>
              )}
            </div>

            <button onClick={handleParse} disabled={parsing || !spec.trim()} style={btn(true, parsing || !spec.trim())}>
              {parsing ? "Parsing..." : "Parse spec →"}
            </button>
          </>
        )}

        {appState === "review" && (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 32 }}>
              <h2 style={{ fontSize: 20, color: C.text, fontWeight: 500 }}>Review tasks</h2>
              <span style={{
                background: "rgba(196,169,106,0.12)", border: "1px solid rgba(196,169,106,0.3)",
                color: C.gold, fontSize: 11, fontFamily: "var(--font-jetbrains), monospace",
                padding: "2px 8px", borderRadius: 4,
              }}>
                {tasks.length}
              </span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 20 }}>
              {tasks.map((task, i) => (
                <div key={task.id} style={{
                  background: C.surface, border: `1px solid ${C.border}`,
                  borderRadius: 10, padding: "14px 16px", position: "relative",
                }}>
                  <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                    <span style={{ fontFamily: "var(--font-jetbrains), monospace", color: C.gold, fontSize: 11, minWidth: 22, paddingTop: 3, flexShrink: 0 }}>
                      #{i + 1}
                    </span>
                    <div style={{ flex: 1 }}>
                      <textarea
                        value={task.description}
                        onChange={e => updateTask(task.id, "description", e.target.value)}
                        rows={2}
                        style={{
                          width: "100%", background: "transparent", border: "none",
                          color: C.text, fontSize: 14, fontFamily: "var(--font-jetbrains), monospace",
                          resize: "vertical", outline: "none", lineHeight: 1.6,
                        }}
                      />
                      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 8 }}>
                        <select
                          value={task.skill ?? ""}
                          onChange={e => updateTask(task.id, "skill", e.target.value || null)}
                          style={{
                            background: "#1a1a1a", border: `1px solid ${C.border}`,
                            color: task.skill ? C.gold : C.muted, fontSize: 12,
                            fontFamily: "var(--font-jetbrains), monospace",
                            padding: "3px 8px", borderRadius: 4, outline: "none",
                          }}
                        >
                          <option value="">no skill</option>
                          {SKILLS.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                        {task.depends_on.length > 0 && (
                          <span style={{ fontSize: 12, color: C.muted, fontFamily: "var(--font-jetbrains), monospace" }}>
                            depends on {task.depends_on.map(d => `#${d}`).join(", ")}
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => deleteTask(task.id)}
                      style={{ background: "none", border: "none", color: C.muted, cursor: "pointer", fontSize: 18, lineHeight: 1, padding: "0 4px", flexShrink: 0 }}
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={addTask}
              style={{
                width: "100%", height: 38, background: "transparent",
                border: `1px dashed ${C.border}`, color: C.muted,
                borderRadius: 8, cursor: "pointer", fontSize: 14, marginBottom: 24,
                fontFamily: "var(--font-jakarta), system-ui, sans-serif",
              }}
            >
              + Add task
            </button>

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <button onClick={handleQueue} disabled={queueing || tasks.length === 0} style={btn(true, queueing || tasks.length === 0)}>
                {queueing ? "Queueing..." : "Queue all tasks →"}
              </button>
              <button onClick={() => setAppState("input")} style={btn(false)}>
                ← Edit spec
              </button>
            </div>
          </>
        )}

        {appState === "running" && (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
              <h2 style={{ fontSize: 20, color: C.text, fontWeight: 500 }}>
                {allDone ? "All tasks complete" : "Running"}
              </h2>
              <span style={{ fontSize: 13, color: C.muted, fontFamily: "var(--font-jetbrains), monospace" }}>
                {doneCount} of {queued.length} complete
              </span>
            </div>

            <div style={{ height: 4, background: "rgba(255,255,255,0.06)", borderRadius: 2, marginBottom: 32, overflow: "hidden" }}>
              <div style={{
                height: "100%",
                width: `${queued.length > 0 ? (doneCount / queued.length) * 100 : 0}%`,
                background: C.gold, borderRadius: 2, transition: "width 0.5s ease",
              }} />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 32 }}>
              {queued.map(qt => {
                const task = taskStatuses[qt.task_id];
                const phase = task?.phase;
                const done = phase === "done";
                const failed = phase === "failed";
                const active = phase && ACTIVE_PHASES.has(phase);
                return (
                  <div key={qt.task_id} style={{
                    background: C.surface, border: `1px solid ${C.border}`,
                    borderRadius: 10, padding: "14px 18px",
                    display: "flex", alignItems: "flex-start", gap: 14,
                  }}>
                    <div style={{ width: 16, flexShrink: 0, paddingTop: 2 }}>
                      {done ? (
                        <span style={{ color: C.green, fontSize: 14 }}>✓</span>
                      ) : failed ? (
                        <span style={{ color: C.red, fontSize: 14 }}>×</span>
                      ) : active ? (
                        <div style={{
                          width: 8, height: 8, borderRadius: "50%", background: C.gold,
                          animation: "pulse 2s ease-in-out infinite",
                        }} />
                      ) : (
                        <div style={{ width: 8, height: 8, borderRadius: "50%", background: "rgba(255,255,255,0.15)" }} />
                      )}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, color: C.text, fontFamily: "var(--font-jetbrains), monospace", lineHeight: 1.5 }}>
                        {qt.description}
                      </div>
                      {failed && task?.error && (
                        <div style={{ fontSize: 12, color: C.red, marginTop: 4 }}>{task.error}</div>
                      )}
                    </div>
                    {done && task?.pr_url && (
                      <a
                        href={task.pr_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          fontSize: 12, color: C.green, fontFamily: "var(--font-jetbrains), monospace",
                          textDecoration: "none", borderBottom: `1px solid ${C.green}`, flexShrink: 0,
                        }}
                      >
                        PR ↗
                      </a>
                    )}
                  </div>
                );
              })}
            </div>

            {allDone && (
              <button onClick={resetAll} style={btn(true)}>
                Run another spec
              </button>
            )}
          </>
        )}

      </div>
    </div>
  );
}
