"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { Task, Repo, Phase } from "@/types";
import { WS_BASE } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const PHASES_ORDERED: Phase[] = [
  "cloning", "indexing", "planning", "implementing",
  "verifying", "reviewing", "pr_creation",
];

const PHASE_LABELS: Record<string, string> = {
  cloning: "Clone",
  indexing: "Index",
  planning: "Plan",
  implementing: "Implement",
  verifying: "Verify",
  reviewing: "Review",
  pr_creation: "PR",
};

const ACTIVE_PHASES = new Set([
  "queued", "cloning", "indexing", "planning",
  "implementing", "verifying", "fixing",
  "reviewing", "pr_creation", "cleanup",
  "awaiting_approval", "awaiting_diff_approval",
]);

interface Skill {
  id: string;
  name: string;
  description: string;
}

interface LogEvent {
  phase?: string;
  message: string;
  type?: string;
}

function apiReq<T>(path: string, apiKey: string, init?: RequestInit): Promise<T> {
  return fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
      ...(init?.headers as Record<string, string> ?? {}),
    },
  }).then(async (r) => {
    if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
    return r.json();
  });
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "#141414",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 10,
  padding: "14px",
  color: "#FAFAFA",
  fontSize: 15,
  fontFamily: "var(--font-jakarta), system-ui, sans-serif",
  outline: "none",
  minHeight: 44,
  boxSizing: "border-box",
};

const primaryBtn: React.CSSProperties = {
  background: "#FAFAFA",
  color: "#0A0A0A",
  border: "none",
  borderRadius: 10,
  width: "100%",
  height: 52,
  fontSize: 15,
  fontWeight: 600,
  cursor: "pointer",
  fontFamily: "var(--font-jakarta), system-ui, sans-serif",
  letterSpacing: "-0.01em",
};

const ghostBtn: React.CSSProperties = {
  background: "transparent",
  color: "rgba(255,255,255,0.5)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 10,
  width: "100%",
  height: 44,
  fontSize: 14,
  cursor: "pointer",
  fontFamily: "var(--font-jakarta), system-ui, sans-serif",
};

const label: React.CSSProperties = {
  fontSize: 11,
  color: "rgba(255,255,255,0.35)",
  textTransform: "uppercase",
  letterSpacing: "0.09em",
  marginBottom: 6,
  display: "block",
};

const card: React.CSSProperties = {
  width: "100%",
  maxWidth: 480,
  padding: "0 20px",
  boxSizing: "border-box",
};

function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <div style={{
      width: size,
      height: size,
      borderRadius: Math.floor(size * 0.25),
      background: "#7C3AED",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0,
    }}>
      <span style={{ color: "#fff", fontWeight: 900, fontSize: Math.floor(size * 0.44) }}>N</span>
    </div>
  );
}

function SetupScreen({ onConnected }: { onConnected: (key: string) => void }) {
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function connect() {
    const k = value.trim();
    if (!k) return;
    setLoading(true);
    setError("");
    try {
      await apiReq("/keys/me", k);
      localStorage.setItem("nimbus_api_key", k);
      onConnected(k);
    } catch {
      setError("Invalid API key — check and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      ...card,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "100dvh",
      gap: 0,
    }}>
      <LogoMark size={56} />
      <div style={{ height: 24 }} />
      <span style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>Nimbus</span>
      <div style={{ height: 6 }} />
      <span style={{ fontSize: 14, color: "rgba(255,255,255,0.4)", textAlign: "center" }}>
        Enter your API key to get started
      </span>
      <div style={{ height: 32 }} />
      <div style={{ width: "100%" }}>
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && connect()}
          placeholder="nk_..."
          autoComplete="off"
          spellCheck={false}
          style={{
            ...inputStyle,
            fontFamily: "var(--font-jetbrains), monospace",
            fontSize: 14,
            letterSpacing: "0.02em",
          }}
        />
        {error && (
          <div style={{ fontSize: 12, color: "#EF4444", marginTop: 8, paddingLeft: 2 }}>{error}</div>
        )}
        <div style={{ height: 12 }} />
        <button onClick={connect} disabled={loading} style={{ ...primaryBtn, opacity: loading ? 0.6 : 1 }}>
          {loading ? "Connecting..." : "Connect"}
        </button>
      </div>
    </div>
  );
}

function SubmitScreen({
  apiKey,
  onSubmitted,
}: {
  apiKey: string;
  onSubmitted: (task: Task) => void;
}) {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [repoId, setRepoId] = useState("");
  const [description, setDescription] = useState("");
  const [skillName, setSkillName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const maskedKey = `${apiKey.slice(0, 5)}${"•".repeat(6)}`;

  useEffect(() => {
    apiReq<Repo[]>("/repos/", apiKey)
      .then((r) => {
        setRepos(r);
        if (r.length > 0) setRepoId(r[0].id);
      })
      .catch(() => {});
    apiReq<Skill[]>("/skills/", apiKey)
      .then(setSkills)
      .catch(() => {});
  }, [apiKey]);

  async function submit() {
    if (!description.trim()) {
      setError("Add a task description.");
      return;
    }
    if (!repoId) {
      setError("Select a repository.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const repo = repos.find((r) => r.id === repoId);
      const task = await apiReq<Task>("/tasks/", apiKey, {
        method: "POST",
        body: JSON.stringify({
          workspace_id: repo?.workspace_id ?? "",
          repo_id: repoId,
          description: description.trim(),
          skill: skillName || undefined,
        }),
      });
      onSubmitted(task);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to submit task.");
    } finally {
      setLoading(false);
    }
  }

  const selectStyle: React.CSSProperties = {
    ...inputStyle,
    appearance: "none",
    WebkitAppearance: "none",
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' stroke='rgba(255,255,255,0.3)' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E")`,
    backgroundRepeat: "no-repeat",
    backgroundPosition: "right 14px center",
    paddingRight: 36,
    cursor: "pointer",
  };

  return (
    <div style={{ ...card, display: "flex", flexDirection: "column", minHeight: "100dvh" }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "20px 0 16px",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
          <LogoMark size={28} />
          <span style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.01em" }}>Nimbus</span>
        </div>
        <span style={{
          fontSize: 11,
          color: "rgba(255,255,255,0.28)",
          fontFamily: "var(--font-jetbrains), monospace",
          background: "#141414",
          padding: "4px 10px",
          borderRadius: 6,
          border: "1px solid rgba(255,255,255,0.07)",
        }}>
          {maskedKey}
        </span>
      </div>

      <div style={{ flex: 1, paddingTop: 24, display: "flex", flexDirection: "column", gap: 18 }}>
        <div>
          <span style={label}>Repository</span>
          {repos.length > 0 ? (
            <select
              value={repoId}
              onChange={(e) => setRepoId(e.target.value)}
              style={selectStyle}
            >
              {repos.map((r) => (
                <option key={r.id} value={r.id} style={{ background: "#141414" }}>
                  {r.name}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              placeholder="No repos yet — add one in the dashboard"
              disabled
              style={{ ...inputStyle, color: "rgba(255,255,255,0.3)", cursor: "not-allowed" }}
            />
          )}
        </div>

        <div>
          <span style={label}>Task</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what you want Nimbus to build..."
            rows={5}
            style={{
              ...inputStyle,
              resize: "none",
              minHeight: 120,
              lineHeight: 1.55,
              fontSize: 15,
            }}
          />
        </div>

        {skills.length > 0 && (
          <div>
            <span style={label}>Skill (optional)</span>
            <select
              value={skillName}
              onChange={(e) => setSkillName(e.target.value)}
              style={selectStyle}
            >
              <option value="" style={{ background: "#141414" }}>None</option>
              {skills.map((s) => (
                <option key={s.id} value={s.name} style={{ background: "#141414" }}>
                  {s.name} — {s.description}
                </option>
              ))}
            </select>
          </div>
        )}

        {error && (
          <div style={{ fontSize: 13, color: "#EF4444", paddingLeft: 2 }}>{error}</div>
        )}
      </div>

      <div style={{ padding: "20px 0 32px" }}>
        <button
          onClick={submit}
          disabled={loading || !repoId}
          style={{ ...primaryBtn, opacity: loading || !repoId ? 0.55 : 1 }}
        >
          {loading ? "Submitting..." : "Run Nimbus →"}
        </button>
      </div>
    </div>
  );
}

function PhaseTimeline({ currentPhase }: { currentPhase: Phase | string }) {
  const isDone = currentPhase === "done";
  const isFailed = currentPhase === "failed";

  function phaseStatus(phase: Phase): "done" | "active" | "failed" | "pending" {
    const idx = PHASES_ORDERED.indexOf(phase);
    const currentIdx = PHASES_ORDERED.indexOf(currentPhase as Phase);

    if (isFailed) {
      if (idx < currentIdx) return "done";
      if (idx === currentIdx) return "failed";
      return "pending";
    }
    if (isDone) return "done";
    if (idx < currentIdx) return "done";
    if (idx === currentIdx) return "active";
    return "pending";
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {PHASES_ORDERED.map((phase, i) => {
        const status = phaseStatus(phase);
        return (
          <div key={phase} style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 20 }}>
              <div style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                flexShrink: 0,
                marginTop: 3,
                background:
                  status === "done" ? "#22C55E" :
                  status === "active" ? "#F59E0B" :
                  status === "failed" ? "#EF4444" :
                  "rgba(255,255,255,0.12)",
                animation: status === "active" ? "pulse 1.4s ease-in-out infinite" : "none",
                boxShadow: status === "active" ? "0 0 8px rgba(245,158,11,0.5)" : "none",
              }} />
              {i < PHASES_ORDERED.length - 1 && (
                <div style={{
                  width: 1,
                  flex: 1,
                  minHeight: 18,
                  background: status === "done" ? "rgba(34,197,94,0.3)" : "rgba(255,255,255,0.07)",
                  margin: "3px 0",
                }} />
              )}
            </div>
            <div style={{ paddingBottom: i < PHASES_ORDERED.length - 1 ? 6 : 0 }}>
              <span style={{
                fontSize: 13,
                fontWeight: status === "active" ? 600 : 400,
                color:
                  status === "done" ? "rgba(255,255,255,0.7)" :
                  status === "active" ? "#FAFAFA" :
                  status === "failed" ? "#EF4444" :
                  "rgba(255,255,255,0.28)",
                letterSpacing: "-0.01em",
              }}>
                {PHASE_LABELS[phase]}
                {status === "done" && (
                  <span style={{ marginLeft: 6, color: "#22C55E", fontSize: 11 }}>✓</span>
                )}
                {status === "failed" && (
                  <span style={{ marginLeft: 6, fontSize: 11 }}>✕</span>
                )}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ProgressScreen({
  task: initialTask,
  apiKey,
  onReset,
}: {
  task: Task;
  apiKey: string;
  onReset: () => void;
}) {
  const [task, setTask] = useState<Task>(initialTask);
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const logsRef = useRef<HTMLDivElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const isActive = ACTIVE_PHASES.has(task.phase);
  const isDone = task.phase === "done";
  const isFailed = task.phase === "failed";
  const isTerminal = isDone || isFailed;

  const pollTask = useCallback(async () => {
    try {
      const t = await apiReq<Task>(`/tasks/${initialTask.id}`, apiKey);
      setTask(t);
      if (!ACTIVE_PHASES.has(t.phase)) {
        if (pollRef.current) clearInterval(pollRef.current);
      }
    } catch {}
  }, [initialTask.id, apiKey]);

  useEffect(() => {
    pollRef.current = setInterval(pollTask, 3000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [pollTask]);

  useEffect(() => {
    if (!isActive) return;

    const wsUrl = `${WS_BASE}/tasks/${initialTask.id}/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data) as LogEvent;
        setLogs((prev) => {
          const next = [...prev, evt];
          return next.length > 20 ? next.slice(-20) : next;
        });
      } catch {}
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [initialTask.id, isActive]);

  useEffect(() => {
    if (logsRef.current) {
      logsRef.current.scrollTop = logsRef.current.scrollHeight;
    }
  }, [logs.length]);

  const descTruncated = initialTask.description.length > 60
    ? `${initialTask.description.slice(0, 60)}...`
    : initialTask.description;

  return (
    <div style={{ ...card, display: "flex", flexDirection: "column", minHeight: "100dvh" }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "20px 0 16px",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
          <LogoMark size={28} />
          <span style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.01em" }}>Nimbus</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{
            width: 6, height: 6, borderRadius: "50%",
            background: isDone ? "#22C55E" : isFailed ? "#EF4444" : wsConnected ? "#F59E0B" : "#555",
            animation: isActive && wsConnected ? "pulse 1.4s ease-in-out infinite" : "none",
          }} />
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.28)", fontFamily: "var(--font-jetbrains), monospace" }}>
            {isDone ? "done" : isFailed ? "failed" : wsConnected ? "live" : "polling"}
          </span>
        </div>
      </div>

      <div style={{
        marginTop: 20,
        padding: "12px 14px",
        background: "#141414",
        borderRadius: 10,
        border: "1px solid rgba(255,255,255,0.07)",
      }}>
        <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Task
        </div>
        <div style={{ fontSize: 14, color: "#FAFAFA", lineHeight: 1.4, overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis" }}>
          {descTruncated}
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.09em", marginBottom: 14 }}>
          Progress
        </div>
        <PhaseTimeline currentPhase={task.phase} />
      </div>

      <div style={{ marginTop: 24, flex: 1 }}>
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 8,
        }}>
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.09em" }}>
            Logs
          </span>
          <span style={{ fontSize: 10, color: "rgba(255,255,255,0.2)", fontFamily: "var(--font-jetbrains), monospace" }}>
            {logs.length} events
          </span>
        </div>
        <div
          ref={logsRef}
          style={{
            background: "#0D0D0D",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: 10,
            padding: "12px",
            height: 160,
            overflowY: "auto",
            fontFamily: "var(--font-jetbrains), monospace",
            fontSize: 11,
            lineHeight: 1.65,
          }}
        >
          {logs.length === 0 ? (
            <span style={{ color: "rgba(255,255,255,0.2)" }}>
              {isActive ? "Waiting for agent..." : "No logs."}
            </span>
          ) : (
            logs.map((l, i) => (
              <div key={i} style={{
                color: l.type === "error" ? "#EF4444" :
                       l.type === "tool" ? "#A78BFA" :
                       "rgba(255,255,255,0.55)",
                wordBreak: "break-word",
              }}>
                <span style={{ color: "rgba(255,255,255,0.18)", marginRight: 6, userSelect: "none" }}>
                  {l.type === "tool" ? "→" : l.type === "error" ? "!" : " "}
                </span>
                {l.message}
              </div>
            ))
          )}
        </div>
      </div>

      {isTerminal && (
        <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 10 }}>
          {task.pr_url && (
            <a
              href={task.pr_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
                ...primaryBtn,
                textDecoration: "none",
                height: 52,
                borderRadius: 10,
                fontSize: 15,
                fontWeight: 600,
              }}
            >
              <span>Open PR</span>
              <span style={{ fontSize: 12, color: "rgba(0,0,0,0.5)", fontFamily: "var(--font-jetbrains), monospace" }}>
                #{task.pr_url.split("/").pop()}
              </span>
            </a>
          )}
          {isFailed && task.error && (
            <div style={{
              padding: "10px 14px",
              background: "rgba(239,68,68,0.08)",
              border: "1px solid rgba(239,68,68,0.2)",
              borderRadius: 10,
              fontSize: 12,
              color: "#EF4444",
              fontFamily: "var(--font-jetbrains), monospace",
              lineHeight: 1.5,
            }}>
              {task.error}
            </div>
          )}
          <button onClick={onReset} style={ghostBtn}>
            Run another task
          </button>
        </div>
      )}

      <div style={{ height: 32 }} />
    </div>
  );
}

type AppState = "setup" | "submit" | "progress";

export default function MobileApp() {
  const [state, setState] = useState<AppState>("setup");
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem("nimbus_api_key");
    if (stored) {
      setApiKey(stored);
      setState("submit");
    }
  }, []);

  if (!mounted) return null;

  if (state === "setup" || !apiKey) {
    return (
      <SetupScreen
        onConnected={(key) => {
          setApiKey(key);
          setState("submit");
        }}
      />
    );
  }

  if (state === "progress" && activeTask) {
    return (
      <ProgressScreen
        task={activeTask}
        apiKey={apiKey}
        onReset={() => {
          setActiveTask(null);
          setState("submit");
        }}
      />
    );
  }

  return (
    <SubmitScreen
      apiKey={apiKey}
      onSubmitted={(task) => {
        setActiveTask(task);
        setState("progress");
      }}
    />
  );
}
