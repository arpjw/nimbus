"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard/tasks", label: "Tasks" },
  { href: "/dashboard/memory", label: "Memory" },
  { href: "/dashboard/keys", label: "Keys" },
  { href: "/dashboard/automations", label: "Automations" },
];

const S = {
  root: {
    display: "flex",
    minHeight: "100vh",
    background: "#0A0A0A",
    color: "#FAFAFA",
    fontFamily: "var(--font-jakarta), system-ui, sans-serif",
  } as React.CSSProperties,
  sidebar: {
    width: 240,
    flexShrink: 0,
    borderRight: "1px solid rgba(255,255,255,0.06)",
    display: "flex",
    flexDirection: "column" as const,
    position: "sticky" as const,
    top: 0,
    height: "100vh",
    overflowY: "auto" as const,
  },
  sidebarHeader: {
    padding: "20px 20px 16px",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    textDecoration: "none",
  },
  logoMark: {
    width: 26,
    height: 26,
    borderRadius: 6,
    background: "#7C3AED",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  nav: { padding: "12px 10px", flex: 1 },
  sidebarFooter: {
    padding: "14px 20px",
    borderTop: "1px solid rgba(255,255,255,0.06)",
  },
  content: { flex: 1, display: "flex", flexDirection: "column" as const, minWidth: 0 },
  topbar: {
    height: 50,
    borderBottom: "1px solid rgba(255,255,255,0.06)",
    display: "flex",
    alignItems: "center",
    padding: "0 24px",
    justifyContent: "flex-end",
    gap: 12,
    flexShrink: 0,
  },
  main: { flex: 1, overflowY: "auto" as const },
  overlay: {
    position: "fixed" as const,
    inset: 0,
    background: "rgba(0,0,0,0.85)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 100,
  },
  modal: {
    background: "#141414",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 12,
    padding: 32,
    width: 420,
    maxWidth: "90vw",
  },
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [keyInput, setKeyInput] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem("nimbus_api_key");
    if (stored) {
      setApiKey(stored);
    } else {
      setShowPrompt(true);
    }
  }, []);

  function saveKey() {
    const k = keyInput.trim();
    if (!k) return;
    localStorage.setItem("nimbus_api_key", k);
    setApiKey(k);
    setShowPrompt(false);
    setKeyInput("");
    window.location.reload();
  }

  const maskedKey = apiKey
    ? `${apiKey.slice(0, 5)}${"•".repeat(8)}`
    : null;

  return (
    <div style={S.root}>
      <aside style={S.sidebar}>
        <div style={S.sidebarHeader}>
          <Link href="/" style={S.logo}>
            <div style={S.logoMark}>
              <span style={{ color: "#fff", fontWeight: 900, fontSize: 11 }}>N</span>
            </div>
            <span style={{ color: "#FAFAFA", fontWeight: 700, fontSize: 14, letterSpacing: "-0.01em" }}>
              Nimbus
            </span>
          </Link>
        </div>

        <nav style={S.nav}>
          {NAV.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  display: "block",
                  padding: "7px 12px",
                  borderRadius: 7,
                  marginBottom: 1,
                  textDecoration: "none",
                  fontSize: 13,
                  fontWeight: active ? 600 : 400,
                  color: active ? "#FAFAFA" : "rgba(255,255,255,0.38)",
                  background: active ? "rgba(255,255,255,0.07)" : "transparent",
                  transition: "all 0.12s",
                }}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div style={S.sidebarFooter}>
          {mounted && maskedKey ? (
            <span style={{ fontSize: 11, color: "rgba(255,255,255,0.25)", fontFamily: "var(--font-jetbrains), monospace" }}>
              {maskedKey}
            </span>
          ) : (
            <span style={{ fontSize: 11, color: "rgba(255,255,255,0.15)", fontFamily: "var(--font-jetbrains), monospace" }}>
              no key set
            </span>
          )}
        </div>
      </aside>

      <div style={S.content}>
        <header style={S.topbar}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: mounted && apiKey ? "#22C55E" : "#444",
            }} />
            <span style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", fontFamily: "var(--font-jetbrains), monospace" }}>
              {mounted ? (apiKey ? "key active" : "no key") : ""}
            </span>
          </div>
          <button
            onClick={() => setShowPrompt(true)}
            style={{
              fontSize: 11,
              color: "rgba(255,255,255,0.3)",
              background: "none",
              border: "1px solid rgba(255,255,255,0.07)",
              borderRadius: 6,
              padding: "3px 9px",
              cursor: "pointer",
            }}
          >
            {apiKey ? "change key" : "set key"}
          </button>
        </header>

        <main style={S.main}>{children}</main>
      </div>

      {showPrompt && (
        <div style={S.overlay}>
          <div style={S.modal}>
            <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: 6, letterSpacing: "-0.02em" }}>
              API Key
            </h2>
            <p style={{ fontSize: 13, color: "rgba(255,255,255,0.38)", marginBottom: 20, lineHeight: 1.5 }}>
              Stored in localStorage, sent with every request as{" "}
              <code style={{ fontFamily: "var(--font-jetbrains), monospace", fontSize: 11, color: "rgba(255,255,255,0.5)" }}>
                X-API-Key
              </code>.
            </p>
            <input
              autoFocus
              type="text"
              placeholder="nk_••••••••••••••••"
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && saveKey()}
              style={{
                width: "100%",
                padding: "9px 12px",
                background: "#0A0A0A",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 8,
                color: "#FAFAFA",
                fontSize: 13,
                fontFamily: "var(--font-jetbrains), monospace",
                outline: "none",
                marginBottom: 14,
              }}
            />
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
              {apiKey && (
                <button
                  onClick={() => setShowPrompt(false)}
                  style={{
                    padding: "7px 14px",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 7,
                    background: "none",
                    color: "rgba(255,255,255,0.5)",
                    fontSize: 13,
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
              )}
              <button
                onClick={saveKey}
                style={{
                  padding: "7px 16px",
                  border: "none",
                  borderRadius: 7,
                  background: "#7C3AED",
                  color: "#fff",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Save key
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
