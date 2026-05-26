"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
function getKey() { return typeof window !== "undefined" ? localStorage.getItem("nimbus_api_key") ?? "" : ""; }
async function apiFetch(path: string, init?: RequestInit) {
  return fetch(`${API}${path}`, { ...init, headers: { "Content-Type": "application/json", "X-API-Key": getKey(), ...(init?.headers as Record<string, string> ?? {}) } });
}

interface Session {
  id: string;
  repo_id: string;
  status: string;
  daily_spend_cap_usd: number;
  label_filter: string | null;
  confidence_threshold: number;
  started_at: string;
  expires_at: string;
  total_spent_usd: number;
  tasks_completed: number;
  tasks_failed: number;
}

const C = {
  bg: "#0A0A0A",
  text: "#FAFAFA",
  muted: "rgba(255,255,255,0.4)",
  border: "rgba(255,255,255,0.08)",
  gold: "#C9A84C",
  green: "#4ADE80",
  red: "#F87171",
  yellow: "#FCD34D",
};

function statusColor(s: string): string {
  if (s === "active") return C.green;
  if (s === "stopped" || s === "cap_reached") return C.red;
  return C.yellow;
}

export default function ContinuousPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch("/continuous/sessions")
      .then((r) => r.json())
      .then(setSessions)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const act = async (id: string, action: "pause" | "resume" | "stop") => {
    await apiFetch(`/continuous/sessions/${id}/${action}`, { method: "POST" });
    setSessions((prev) =>
      prev.map((s) =>
        s.id === id
          ? { ...s, status: action === "stop" ? "stopped" : action === "pause" ? "paused" : "active" }
          : s
      )
    );
  };

  return (
    <div style={{ padding: 28, maxWidth: 860 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 6 }}>
          Continuous mode
        </h1>
        <p style={{ fontSize: 13, color: C.muted, lineHeight: 1.5 }}>
          Nimbus watches your repo for open issues and opens PRs automatically, up to your daily spend cap.
          Start sessions via{" "}
          <code style={{ background: "rgba(255,255,255,0.06)", padding: "1px 5px", borderRadius: 3, fontSize: 12 }}>
            nimbus continuous start
          </code>
          .
        </p>
      </div>

      {loading && <p style={{ color: C.muted, fontSize: 13 }}>Loading...</p>}
      {error && <p style={{ color: C.red, fontSize: 13 }}>Error: {error}</p>}

      {!loading && !error && sessions.length === 0 && (
        <div
          style={{
            border: `1px dashed ${C.border}`,
            borderRadius: 8,
            padding: "32px 24px",
            textAlign: "center",
          }}
        >
          <p style={{ color: C.muted, fontSize: 13, marginBottom: 12 }}>No continuous sessions yet.</p>
          <code style={{ background: "rgba(255,255,255,0.06)", padding: "6px 12px", borderRadius: 4, fontSize: 12, color: C.gold }}>
            nimbus continuous start --repo owner/repo --cap-per-day 5
          </code>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {sessions.map((s) => (
          <div
            key={s.id}
            style={{
              border: `1px solid ${C.border}`,
              borderRadius: 8,
              padding: "16px 20px",
              background: "rgba(255,255,255,0.02)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
              <div>
                <span
                  style={{
                    display: "inline-block",
                    padding: "2px 8px",
                    borderRadius: 4,
                    fontSize: 11,
                    fontWeight: 600,
                    background: `${statusColor(s.status)}22`,
                    color: statusColor(s.status),
                    marginRight: 8,
                  }}
                >
                  {s.status}
                </span>
                <span style={{ fontSize: 12, color: C.muted, fontFamily: "monospace" }}>{s.id.slice(0, 8)}</span>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                {s.status === "active" && (
                  <button
                    onClick={() => act(s.id, "pause")}
                    style={{ fontSize: 11, padding: "3px 10px", borderRadius: 4, border: `1px solid ${C.border}`, background: "transparent", color: C.muted, cursor: "pointer" }}
                  >
                    Pause
                  </button>
                )}
                {s.status === "paused" && (
                  <button
                    onClick={() => act(s.id, "resume")}
                    style={{ fontSize: 11, padding: "3px 10px", borderRadius: 4, border: `1px solid ${C.green}`, background: "transparent", color: C.green, cursor: "pointer" }}
                  >
                    Resume
                  </button>
                )}
                {s.status !== "stopped" && (
                  <button
                    onClick={() => act(s.id, "stop")}
                    style={{ fontSize: 11, padding: "3px 10px", borderRadius: 4, border: `1px solid ${C.red}`, background: "transparent", color: C.red, cursor: "pointer" }}
                  >
                    Stop
                  </button>
                )}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
              {[
                ["Cap / day", `$${s.daily_spend_cap_usd.toFixed(2)}`],
                ["Total spent", `$${s.total_spent_usd.toFixed(3)}`],
                ["Tasks done", String(s.tasks_completed)],
                ["Tasks failed", String(s.tasks_failed)],
              ].map(([label, val]) => (
                <div key={label}>
                  <div style={{ fontSize: 10, color: C.muted, marginBottom: 2 }}>{label}</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{val}</div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: 10, fontSize: 11, color: C.muted }}>
              {s.label_filter && <span style={{ marginRight: 12 }}>label: {s.label_filter}</span>}
              <span style={{ marginRight: 12 }}>confidence: {s.confidence_threshold}%</span>
              <span>expires: {new Date(s.expires_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
