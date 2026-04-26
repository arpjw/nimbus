"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { KeyInfo, GeneratedKey } from "@/types";

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).catch(() => {});
}

function CopyButton({ value, label = "copy" }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  function handleCopy() {
    copyToClipboard(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }
  return (
    <button
      onClick={handleCopy}
      style={{
        padding: "3px 10px", border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: 5, background: "none", color: copied ? "#22C55E" : "rgba(255,255,255,0.4)",
        fontSize: 11, fontFamily: "var(--font-jetbrains), monospace", cursor: "pointer",
      }}
    >
      {copied ? "copied!" : label}
    </button>
  );
}

function UsageBar({ used, limit }: { used: number; limit: number | null }) {
  if (limit === null) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 14, color: "#FAFAFA", fontFamily: "var(--font-jetbrains), monospace" }}>
          {used}
        </span>
        <span style={{ fontSize: 12, color: "rgba(255,255,255,0.3)" }}>tasks this month · unlimited</span>
      </div>
    );
  }
  const pct = Math.min((used / limit) * 100, 100);
  const color = pct > 80 ? "#EF4444" : pct > 50 ? "#F59E0B" : "#22C55E";
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 13, color: "rgba(255,255,255,0.6)" }}>
          {used} / {limit} tasks this month
        </span>
        <span style={{ fontSize: 12, color, fontFamily: "var(--font-jetbrains), monospace" }}>
          {Math.round(pct)}%
        </span>
      </div>
      <div style={{ height: 3, background: "rgba(255,255,255,0.06)", borderRadius: 2 }}>
        <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 2, transition: "width 0.3s" }} />
      </div>
    </div>
  );
}

export default function KeysPage() {
  const [keyInfo, setKeyInfo] = useState<KeyInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiKeyRaw, setApiKeyRaw] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [genName, setGenName] = useState("");
  const [genEmail, setGenEmail] = useState("");
  const [generating, setGenerating] = useState(false);
  const [newKey, setNewKey] = useState<GeneratedKey | null>(null);

  const [revoking, setRevoking] = useState(false);
  const [confirmRevoke, setConfirmRevoke] = useState(false);

  useEffect(() => {
    const raw = typeof window !== "undefined" ? localStorage.getItem("nimbus_api_key") : null;
    setApiKeyRaw(raw);

    api.keys.me()
      .then((info) => {
        setKeyInfo(info);
        if (info.owner_email) setGenEmail(info.owner_email);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleGenerate() {
    if (!genName.trim() || !genEmail.trim()) return;
    setGenerating(true);
    setError(null);
    try {
      const result = await api.keys.generate(genName.trim(), genEmail.trim());
      setNewKey(result);
      localStorage.setItem("nimbus_api_key", result.raw_key);
      setApiKeyRaw(result.raw_key);
      setGenName("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate key");
    } finally {
      setGenerating(false);
    }
  }

  async function handleRevoke() {
    if (!keyInfo?.id) return;
    setRevoking(true);
    try {
      await api.keys.revoke(keyInfo.id);
      localStorage.removeItem("nimbus_api_key");
      window.location.reload();
    } finally {
      setRevoking(false);
      setConfirmRevoke(false);
    }
  }

  const maskedKey = apiKeyRaw
    ? `${apiKeyRaw.slice(0, 5)}${"•".repeat(8)}${apiKeyRaw.slice(-3)}`
    : null;

  const cardStyle: React.CSSProperties = {
    background: "#141414",
    border: "1px solid rgba(255,255,255,0.06)",
    borderRadius: 10,
    padding: "20px 24px",
    marginBottom: 16,
  };

  const inputStyle: React.CSSProperties = {
    padding: "8px 11px", borderRadius: 7, fontSize: 12,
    border: "1px solid rgba(255,255,255,0.08)",
    background: "#0A0A0A", color: "#FAFAFA",
    fontFamily: "var(--font-jetbrains), monospace",
    outline: "none",
  };

  return (
    <div style={{ padding: 28 }}>
      <h1 style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 24 }}>Keys</h1>

      {loading ? (
        <div style={{ textAlign: "center", padding: 40, color: "rgba(255,255,255,0.25)", fontSize: 13, fontFamily: "var(--font-jetbrains), monospace" }}>
          loading...
        </div>
      ) : (
        <>
          <div style={cardStyle}>
            <h2 style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 16 }}>
              Current key
            </h2>
            {error && !keyInfo ? (
              <p style={{ color: "rgba(255,255,255,0.35)", fontSize: 13, fontFamily: "var(--font-jetbrains), monospace" }}>
                {error.includes("401") ? "No valid API key set — use the form below to generate one." : error}
              </p>
            ) : keyInfo ? (
              <>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                  <span style={{ fontFamily: "var(--font-jetbrains), monospace", fontSize: 14, color: "#FAFAFA", letterSpacing: "0.02em" }}>
                    {maskedKey ?? "nk_••••••••••••"}
                  </span>
                  {apiKeyRaw && <CopyButton value={apiKeyRaw} />}
                </div>
                <div style={{ display: "flex", gap: 20, marginBottom: 16, flexWrap: "wrap" }}>
                  <div>
                    <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 3 }}>Name</div>
                    <span style={{ fontSize: 13, color: "rgba(255,255,255,0.7)" }}>{keyInfo.name}</span>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 3 }}>Tier</div>
                    <span style={{
                      fontSize: 11, padding: "1px 8px", borderRadius: 3,
                      background: keyInfo.tier === "pro" ? "rgba(124,58,237,0.15)" : "rgba(255,255,255,0.06)",
                      border: keyInfo.tier === "pro" ? "1px solid rgba(124,58,237,0.3)" : "1px solid rgba(255,255,255,0.1)",
                      color: keyInfo.tier === "pro" ? "#A78BFA" : "rgba(255,255,255,0.5)",
                      fontFamily: "var(--font-jetbrains), monospace",
                    }}>
                      {keyInfo.tier}
                    </span>
                  </div>
                </div>
                <UsageBar used={keyInfo.task_count_month} limit={keyInfo.monthly_limit} />
                <div style={{ marginTop: 20, paddingTop: 16, borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                  {!confirmRevoke ? (
                    <button
                      onClick={() => setConfirmRevoke(true)}
                      style={{
                        padding: "6px 14px", border: "1px solid rgba(239,68,68,0.3)",
                        borderRadius: 7, background: "none", color: "#EF4444",
                        fontSize: 12, cursor: "pointer",
                      }}
                    >
                      Revoke key
                    </button>
                  ) : (
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 12, color: "rgba(255,255,255,0.5)" }}>Are you sure? This cannot be undone.</span>
                      <button
                        onClick={handleRevoke}
                        disabled={revoking}
                        style={{
                          padding: "5px 12px", border: "none", borderRadius: 6,
                          background: "#EF4444", color: "#fff", fontSize: 12,
                          cursor: revoking ? "not-allowed" : "pointer", opacity: revoking ? 0.6 : 1,
                        }}
                      >
                        {revoking ? "Revoking..." : "Yes, revoke"}
                      </button>
                      <button
                        onClick={() => setConfirmRevoke(false)}
                        style={{
                          padding: "5px 12px", border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: 6, background: "none", color: "rgba(255,255,255,0.4)",
                          fontSize: 12, cursor: "pointer",
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : null}
          </div>

          {newKey && (
            <div style={{
              ...cardStyle,
              border: "1px solid rgba(34,197,94,0.3)",
              background: "rgba(34,197,94,0.05)",
              marginBottom: 16,
            }}>
              <h2 style={{ fontSize: 12, fontWeight: 600, color: "#22C55E", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>
                New key generated — copy it now, it won't show again
              </h2>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <code style={{
                  fontFamily: "var(--font-jetbrains), monospace", fontSize: 13,
                  color: "#FAFAFA", letterSpacing: "0.02em",
                  background: "#0A0A0A", padding: "7px 12px", borderRadius: 6, flex: 1, wordBreak: "break-all",
                }}>
                  {newKey.raw_key}
                </code>
                <CopyButton value={newKey.raw_key} label="copy key" />
              </div>
              <p style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", marginTop: 10 }}>
                Key saved to localStorage automatically.
              </p>
            </div>
          )}

          <div style={cardStyle}>
            <h2 style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 16 }}>
              Generate new key
            </h2>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
              <input
                placeholder="Key name (e.g. production)"
                value={genName}
                onChange={(e) => setGenName(e.target.value)}
                style={{ ...inputStyle, flex: 1, minWidth: 180 }}
              />
              <input
                placeholder="Owner email"
                value={genEmail}
                onChange={(e) => setGenEmail(e.target.value)}
                style={{ ...inputStyle, flex: 1, minWidth: 200 }}
              />
            </div>
            {error && (
              <div style={{ color: "#EF4444", fontSize: 12, marginBottom: 10, fontFamily: "var(--font-jetbrains), monospace" }}>
                {error}
              </div>
            )}
            <button
              onClick={handleGenerate}
              disabled={generating || !genName.trim() || !genEmail.trim()}
              style={{
                padding: "7px 16px", border: "none", borderRadius: 7,
                background: "#7C3AED", color: "#fff", fontSize: 13,
                fontWeight: 600, cursor: generating || !genName.trim() || !genEmail.trim() ? "not-allowed" : "pointer",
                opacity: generating || !genName.trim() || !genEmail.trim() ? 0.5 : 1,
              }}
            >
              {generating ? "Generating..." : "Generate key"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
