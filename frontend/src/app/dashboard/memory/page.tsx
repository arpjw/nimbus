"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { Repo, MemoryEntry } from "@/types";

function relTime(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function MemoryPage() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string>("");
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [label, setLabel] = useState("");
  const [text, setText] = useState("");
  const [adding, setAdding] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.repos.list().then((r) => {
      setRepos(r);
      if (r.length > 0) setSelectedRepo(r[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedRepo) return;
    setLoading(true);
    api.repos.memory.list(selectedRepo)
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, [selectedRepo]);

  async function handleAdd() {
    if (!text.trim() || !selectedRepo) return;
    setAdding(true);
    setError(null);
    try {
      const entry = await api.repos.memory.add(selectedRepo, text.trim(), label.trim());
      setEntries((prev) => [entry, ...prev]);
      setText("");
      setLabel("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add entry");
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(id: string) {
    if (!selectedRepo) return;
    setDeleting(id);
    try {
      await api.repos.memory.delete(selectedRepo, id);
      setEntries((prev) => prev.filter((e) => e.id !== id));
    } finally {
      setDeleting(null);
    }
  }

  const selectedRepoName = repos.find((r) => r.id === selectedRepo)?.name ?? "";

  const inputStyle: React.CSSProperties = {
    padding: "8px 11px", borderRadius: 7, fontSize: 12,
    border: "1px solid rgba(255,255,255,0.08)",
    background: "#0A0A0A", color: "#FAFAFA",
    fontFamily: "var(--font-jetbrains), monospace",
    outline: "none",
  };

  return (
    <div style={{ padding: 28 }}>
      <div style={{ marginBottom: 20, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <h1 style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em" }}>Memory</h1>
        <select
          value={selectedRepo}
          onChange={(e) => setSelectedRepo(e.target.value)}
          style={{
            ...inputStyle,
            paddingRight: 28,
            appearance: "none",
            backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='rgba(255,255,255,0.3)' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E")`,
            backgroundRepeat: "no-repeat",
            backgroundPosition: "right 10px center",
            cursor: "pointer",
            minWidth: 200,
          }}
        >
          {repos.map((r) => (
            <option key={r.id} value={r.id} style={{ background: "#141414" }}>
              {r.name}
            </option>
          ))}
          {repos.length === 0 && <option value="">No repos</option>}
        </select>
      </div>

      {selectedRepo && (
        <div style={{ background: "#141414", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 10, padding: 20, marginBottom: 24 }}>
          <h2 style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>
            Add entry
          </h2>
          <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
            <input
              placeholder="Label (optional)"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              style={{ ...inputStyle, width: 200 }}
            />
          </div>
          <textarea
            placeholder="Memory text..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            style={{
              ...inputStyle, width: "100%", resize: "vertical",
              lineHeight: 1.5, marginBottom: 10,
            }}
          />
          {error && (
            <div style={{ color: "#EF4444", fontSize: 12, marginBottom: 8, fontFamily: "var(--font-jetbrains), monospace" }}>
              {error}
            </div>
          )}
          <button
            onClick={handleAdd}
            disabled={adding || !text.trim()}
            style={{
              padding: "7px 16px", border: "none", borderRadius: 7,
              background: "#7C3AED", color: "#fff", fontSize: 13,
              fontWeight: 600, cursor: adding || !text.trim() ? "not-allowed" : "pointer",
              opacity: adding || !text.trim() ? 0.5 : 1,
            }}
          >
            {adding ? "Adding..." : "Add entry"}
          </button>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: "center", padding: 40, color: "rgba(255,255,255,0.25)", fontSize: 13, fontFamily: "var(--font-jetbrains), monospace" }}>
          loading...
        </div>
      ) : entries.length === 0 ? (
        <div style={{
          background: "#141414", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 10,
          padding: 40, textAlign: "center",
        }}>
          <p style={{ color: "rgba(255,255,255,0.25)", fontSize: 13, fontFamily: "var(--font-jetbrains), monospace" }}>
            {selectedRepo ? `no memory entries for ${selectedRepoName}` : "select a repo"}
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {entries.map((entry) => {
            const labelVal = entry.metadata.label || entry.metadata.task_description;
            const ts = entry.metadata.timestamp;
            return (
              <div
                key={entry.id}
                style={{
                  background: "#141414",
                  border: "1px solid rgba(255,255,255,0.06)",
                  borderRadius: 10,
                  padding: "14px 16px",
                  display: "flex",
                  gap: 14,
                  alignItems: "flex-start",
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    {labelVal && (
                      <span style={{
                        fontSize: 10, padding: "1px 7px", borderRadius: 3,
                        background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.3)",
                        color: "#A78BFA", fontFamily: "var(--font-jetbrains), monospace",
                      }}>
                        {labelVal.length > 40 ? labelVal.slice(0, 40) + "…" : labelVal}
                      </span>
                    )}
                    {ts && (
                      <span style={{ fontSize: 10, color: "rgba(255,255,255,0.2)", fontFamily: "var(--font-jetbrains), monospace" }}>
                        {relTime(ts)}
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: 13, color: "rgba(255,255,255,0.65)", lineHeight: 1.55, margin: 0 }}>
                    {entry.text}
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(entry.id)}
                  disabled={deleting === entry.id}
                  style={{
                    flexShrink: 0, background: "none", border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 6, padding: "4px 9px", cursor: "pointer",
                    color: "rgba(255,255,255,0.3)", fontSize: 11,
                    opacity: deleting === entry.id ? 0.4 : 1,
                  }}
                >
                  {deleting === entry.id ? "..." : "delete"}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
