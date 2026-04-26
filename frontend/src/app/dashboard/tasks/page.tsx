"use client";
import { useState, useEffect, useRef } from "react";
import { api, WS_BASE } from "@/lib/api";
import type { Task, Repo, Commit } from "@/types";

const ACTIVE_PHASES = new Set([
  "queued", "cloning", "indexing", "planning",
  "implementing", "verifying", "fixing",
  "reviewing", "pr_creation", "cleanup",
  "awaiting_approval", "awaiting_diff_approval",
]);

function statusColor(phase: string): string {
  if (phase === "done") return "#22C55E";
  if (phase === "failed") return "#EF4444";
  return "#F59E0B";
}

function StatusBadge({ phase }: { phase: string }) {
  const color = statusColor(phase);
  const active = ACTIVE_PHASES.has(phase);
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 7px", borderRadius: 4,
      background: `${color}14`, border: `1px solid ${color}38`,
      color, fontSize: 11, fontFamily: "var(--font-jetbrains), monospace",
    }}>
      {active && (
        <span style={{
          width: 4, height: 4, borderRadius: "50%", background: color,
          animation: "pulse 2s ease infinite",
        }} />
      )}
      {phase}
    </span>
  );
}

function duration(task: Task): string {
  const start = new Date(task.created_at).getTime();
  const end = task.completed_at ? new Date(task.completed_at).getTime() : Date.now();
  const s = Math.floor((end - start) / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ${s % 60}s`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
}

function relTime(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

interface LogEvent {
  phase: string;
  message: string;
  ts?: string;
  type?: string;
}

function TaskExpandedRow({ task }: { task: Task }) {
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const logsRef = useRef<HTMLDivElement>(null);
  const isActive = ACTIVE_PHASES.has(task.phase);

  useEffect(() => {
    if (!isActive) return;
    const ws = new WebSocket(`${WS_BASE}/tasks/${task.id}/ws`);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data) as LogEvent;
        setLogs((prev) => [...prev, evt]);
      } catch {}
    };
    return () => ws.close();
  }, [task.id, isActive]);

  useEffect(() => {
    logsRef.current?.scrollTo({ top: logsRef.current.scrollHeight, behavior: "smooth" });
  }, [logs.length]);

  const cellStyle: React.CSSProperties = {
    background: "#0D0D0D",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
    padding: "16px 20px",
  };

  if (!isActive) {
    return (
      <td colSpan={7} style={cellStyle}>
        <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
          <Detail label="Branch" value={task.branch_name ?? "—"} mono />
          <Detail label="Repo" value={task.repo_full_name ?? task.repo_id} mono />
          {task.pr_url && (
            <Detail label="PR">
              <a href={task.pr_url} target="_blank" rel="noopener"
                style={{ color: "#A78BFA", fontSize: 12, fontFamily: "var(--font-jetbrains), monospace" }}>
                {task.pr_url.split("/").slice(-2).join("/")}
              </a>
            </Detail>
          )}
          {task.error && (
            <Detail label="Error">
              <span style={{ color: "#EF4444", fontSize: 12, fontFamily: "var(--font-jetbrains), monospace" }}>
                {task.error}
              </span>
            </Detail>
          )}
          {task.plan && (
            <div style={{ width: "100%", marginTop: 8 }}>
              <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Plan</span>
              <pre style={{
                marginTop: 6, fontSize: 11, color: "rgba(255,255,255,0.5)",
                fontFamily: "var(--font-jetbrains), monospace", whiteSpace: "pre-wrap",
                maxHeight: 120, overflow: "auto", lineHeight: 1.5,
              }}>
                {task.plan.slice(0, 600)}{task.plan.length > 600 ? "..." : ""}
              </pre>
            </div>
          )}
        </div>
      </td>
    );
  }

  return (
    <td colSpan={7} style={{ ...cellStyle, padding: 0 }}>
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "6px 12px",
        borderBottom: "1px solid rgba(255,255,255,0.04)",
        background: "#0A0A0A",
      }}>
        <span style={{ fontSize: 10, color: "rgba(255,255,255,0.25)", fontFamily: "var(--font-jetbrains), monospace" }}>
          execution log
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 5, height: 5, borderRadius: "50%", background: connected ? "#22C55E" : "#555", display: "block" }} />
          <span style={{ fontSize: 10, color: "rgba(255,255,255,0.25)", fontFamily: "var(--font-jetbrains), monospace" }}>
            {connected ? "live" : "connecting"} · {logs.length} events
          </span>
        </div>
      </div>
      <div
        ref={logsRef}
        style={{
          maxHeight: 220, overflowY: "auto", padding: "8px 12px",
          fontFamily: "var(--font-jetbrains), monospace", fontSize: 11,
          lineHeight: 1.6, background: "#0A0A0A",
        }}
      >
        {logs.length === 0 ? (
          <span style={{ color: "rgba(255,255,255,0.2)" }}>Waiting for agent...</span>
        ) : (
          logs.map((l, i) => (
            <div key={i} style={{ color: l.type === "error" ? "#EF4444" : l.type === "tool" ? "#A78BFA" : "rgba(255,255,255,0.55)" }}>
              <span style={{ color: "rgba(255,255,255,0.18)", marginRight: 8 }}>
                {l.type === "tool" ? "→" : l.type === "error" ? "!" : " "}
              </span>
              {l.message}
            </div>
          ))
        )}
      </div>
    </td>
  );
}

function Detail({ label, value, mono, children }: {
  label: string; value?: string; mono?: boolean; children?: React.ReactNode;
}) {
  return (
    <div>
      <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 3 }}>
        {label}
      </div>
      {children ?? (
        <span style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", fontFamily: mono ? "var(--font-jetbrains), monospace" : undefined }}>
          {value}
        </span>
      )}
    </div>
  );
}

function TaskRow({ task, repoMap }: { task: Task; repoMap: Map<string, Repo> }) {
  const [expanded, setExpanded] = useState(false);
  const repo = repoMap.get(task.repo_id);
  const repoName = task.repo_full_name ?? repo?.name ?? task.repo_id.slice(0, 8);

  const trStyle: React.CSSProperties = {
    cursor: "pointer",
    borderBottom: expanded ? "none" : "1px solid rgba(255,255,255,0.04)",
    background: expanded ? "#111" : "transparent",
    transition: "background 0.1s",
  };
  const td: React.CSSProperties = {
    padding: "11px 14px", fontSize: 12, verticalAlign: "middle",
  };

  return (
    <>
      <tr style={trStyle} onClick={() => setExpanded(!expanded)}>
        <td style={td}>
          <StatusBadge phase={task.phase} />
        </td>
        <td style={{ ...td, maxWidth: 280, overflow: "hidden" }}>
          <span style={{ color: "#FAFAFA", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", display: "block" }}>
            {task.description}
          </span>
        </td>
        <td style={{ ...td, fontFamily: "var(--font-jetbrains), monospace", color: "rgba(255,255,255,0.4)", fontSize: 11 }}>
          {repoName}
        </td>
        <td style={{ ...td }}>
          {task.pr_url ? (
            <a
              href={task.pr_url}
              target="_blank"
              rel="noopener"
              onClick={(e) => e.stopPropagation()}
              style={{ color: "#A78BFA", fontSize: 11, fontFamily: "var(--font-jetbrains), monospace", textDecoration: "none" }}
            >
              #{task.pr_url.split("/").pop()}
            </a>
          ) : (
            <span style={{ color: "rgba(255,255,255,0.18)", fontSize: 11 }}>—</span>
          )}
        </td>
        <td style={{ ...td, fontFamily: "var(--font-jetbrains), monospace", color: "rgba(255,255,255,0.35)", fontSize: 11 }}>
          {duration(task)}
        </td>
        <td style={{ ...td, fontFamily: "var(--font-jetbrains), monospace", color: "rgba(255,255,255,0.3)", fontSize: 11 }}>
          {relTime(task.created_at)}
        </td>
        <td style={{ ...td, color: "rgba(255,255,255,0.2)", fontSize: 16, textAlign: "center" }}>
          {expanded ? "▾" : "▸"}
        </td>
      </tr>
      {expanded && (
        <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <TaskExpandedRow task={task} />
        </tr>
      )}
    </>
  );
}

function ChangelogSection() {
  const [commits, setCommits] = useState<Commit[]>([]);

  useEffect(() => {
    fetch("https://api.github.com/repos/arpjw/nimbus/commits?per_page=5")
      .then((r) => r.json())
      .then((data) => Array.isArray(data) && setCommits(data))
      .catch(() => {});
  }, []);

  if (commits.length === 0) return null;

  return (
    <section style={{ marginTop: 32 }}>
      <h2 style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 12 }}>
        Recent commits
      </h2>
      <div style={{ background: "#141414", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 10 }}>
        {commits.map((c, i) => (
          <a
            key={c.sha}
            href={c.html_url}
            target="_blank"
            rel="noopener"
            style={{
              display: "flex", alignItems: "flex-start", gap: 12,
              padding: "10px 16px",
              borderBottom: i < commits.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none",
              textDecoration: "none",
            }}
          >
            <span style={{
              fontSize: 10, fontFamily: "var(--font-jetbrains), monospace",
              color: "#A78BFA", flexShrink: 0, paddingTop: 1,
            }}>
              {c.sha.slice(0, 7)}
            </span>
            <span style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", flex: 1, lineHeight: 1.4 }}>
              {c.commit.message.split("\n")[0]}
            </span>
            <span style={{ fontSize: 10, color: "rgba(255,255,255,0.25)", fontFamily: "var(--font-jetbrains), monospace", flexShrink: 0 }}>
              {relTime(c.commit.author.date)}
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}

type Filter = "all" | "active" | "done" | "failed";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [repoMap, setRepoMap] = useState<Map<string, Repo>>(new Map());

  useEffect(() => {
    Promise.all([api.tasks.list(), api.repos.list()])
      .then(([t, r]) => {
        setTasks(t);
        setRepos(r);
        setRepoMap(new Map(r.map((repo) => [repo.id, repo])));
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = tasks.filter((t) => {
    if (filter === "active" && !ACTIVE_PHASES.has(t.phase)) return false;
    if (filter === "done" && t.phase !== "done") return false;
    if (filter === "failed" && t.phase !== "failed") return false;
    if (search) {
      const q = search.toLowerCase();
      const repoName = (t.repo_full_name ?? repoMap.get(t.repo_id)?.name ?? "").toLowerCase();
      return t.description.toLowerCase().includes(q) || repoName.includes(q);
    }
    return true;
  });

  const filterBtnStyle = (active: boolean): React.CSSProperties => ({
    padding: "4px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer",
    border: active ? "1px solid rgba(255,255,255,0.15)" : "1px solid rgba(255,255,255,0.06)",
    background: active ? "rgba(255,255,255,0.08)" : "transparent",
    color: active ? "#FAFAFA" : "rgba(255,255,255,0.35)",
    fontFamily: "var(--font-jetbrains), monospace",
  });

  const thStyle: React.CSSProperties = {
    padding: "8px 14px", fontSize: 10, fontWeight: 600,
    color: "rgba(255,255,255,0.3)", textTransform: "uppercase",
    letterSpacing: "0.08em", textAlign: "left",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
    background: "#141414",
  };

  return (
    <div style={{ padding: 28 }}>
      <div style={{ marginBottom: 20, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <h1 style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em" }}>Tasks</h1>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              padding: "5px 10px", borderRadius: 7, fontSize: 12,
              border: "1px solid rgba(255,255,255,0.08)",
              background: "#141414", color: "#FAFAFA",
              fontFamily: "var(--font-jetbrains), monospace",
              outline: "none", width: 180,
            }}
          />
          {(["all", "active", "done", "failed"] as Filter[]).map((f) => (
            <button key={f} onClick={() => setFilter(f)} style={filterBtnStyle(filter === f)}>
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 60, color: "rgba(255,255,255,0.25)", fontSize: 13, fontFamily: "var(--font-jetbrains), monospace" }}>
          loading...
        </div>
      ) : (
        <div style={{ background: "#141414", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 10, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ ...thStyle, width: 120 }}>Status</th>
                <th style={thStyle}>Description</th>
                <th style={thStyle}>Repo</th>
                <th style={thStyle}>PR</th>
                <th style={thStyle}>Duration</th>
                <th style={thStyle}>When</th>
                <th style={{ ...thStyle, width: 32 }} />
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", padding: "40px 20px", color: "rgba(255,255,255,0.2)", fontSize: 13, fontFamily: "var(--font-jetbrains), monospace" }}>
                    {tasks.length === 0 ? "no tasks yet" : "no tasks match filter"}
                  </td>
                </tr>
              ) : (
                filtered.map((t) => <TaskRow key={t.id} task={t} repoMap={repoMap} />)
              )}
            </tbody>
          </table>
        </div>
      )}

      <ChangelogSection />
    </div>
  );
}
