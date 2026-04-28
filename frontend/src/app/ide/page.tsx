"use client";
export const dynamic = "force-dynamic";

import { useState, useEffect, useRef, useCallback } from "react";
import lazy from "next/dynamic";

const MonacoEditor = lazy(() => import("@monaco-editor/react"), { ssr: false });
const TerminalPanel = lazy(() => import("@/components/ide/TerminalPanel"), { ssr: false });

const API = process.env.NEXT_PUBLIC_API_URL || "https://api.get-nimbus.com";

const C = {
  bg:       "#0C0B09",
  surface:  "#141210",
  elevated: "#1A1816",
  border:   "rgba(255,248,235,0.06)",
  border2:  "rgba(255,248,235,0.1)",
  text:     "#F5EFE6",
  muted:    "rgba(245,239,230,0.45)",
  faint:    "rgba(245,239,230,0.2)",
  ghost:    "rgba(245,239,230,0.08)",
  gold:     "#C9A96E",
  goldDim:  "rgba(201,169,110,0.15)",
  green:    "#7AAB8A",
  red:      "#A87070",
};

const mono = "'JetBrains Mono', 'Fira Code', 'Cascadia Mono', monospace";
const sans = "'Inter', system-ui, sans-serif";
const serif = "'Instrument Serif', Georgia, serif";

interface FileEntry {
  name: string;
  path: string;
  type: "file" | "directory";
  size?: number;
}

interface OpenFile {
  path: string;
  content: string;
  modified: boolean;
  language: string;
}

function detectLanguage(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() || "";
  const map: Record<string, string> = {
    ts: "typescript", tsx: "typescript", js: "javascript", jsx: "javascript",
    py: "python", rs: "rust", go: "go", java: "java", cpp: "cpp", c: "c",
    css: "css", scss: "scss", html: "html", json: "json", yaml: "yaml",
    yml: "yaml", md: "markdown", sh: "shell", dockerfile: "dockerfile",
    toml: "toml", sql: "sql", graphql: "graphql",
  };
  return map[ext] || "plaintext";
}

function FileIcon({ path, isDir }: { path: string; isDir: boolean }) {
  if (isDir) return <span style={{ color: C.gold, fontSize: 11 }}>▸</span>;
  const ext = path.split(".").pop()?.toLowerCase() || "";
  const colors: Record<string, string> = {
    ts: "#3B82F6", tsx: "#3B82F6", js: "#F59E0B", jsx: "#F59E0B",
    py: "#10B981", rs: "#F97316", go: "#06B6D4", css: "#8B5CF6",
    json: "#6B7280", md: "#9CA3AF", sh: "#10B981",
  };
  return (
    <span style={{
      width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
      background: colors[ext] || "rgba(245,239,230,0.2)",
      display: "inline-block",
    }} />
  );
}

function LoadingPhase() {
  const phases = [
    "spinning up your environment...",
    "cloning repository...",
    "installing nimbus...",
    "indexing codebase...",
    "almost ready...",
  ];
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setPhase(p => (p + 1) % phases.length), 2200);
    return () => clearInterval(t);
  }, []);

  return (
    <span style={{
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 12,
      color: "rgba(245,239,230,0.3)",
      transition: "opacity 0.3s ease",
    }}>
      {phases[phase]}
    </span>
  );
}

export default function IDEPage() {
  const [apiKey, setApiKey] = useState<string>('');

  useEffect(() => {
    const stored = localStorage.getItem('nimbus_ide_api_key');
    if (stored) setApiKey(stored);
  }, []);

  const [ideSession, setIdeSession] = useState<any>(null);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [repoInput, setRepoInput] = useState("");
  const [showRepoPicker, setShowRepoPicker] = useState(true);

  const [files, setFiles] = useState<FileEntry[]>([]);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());
  const [dirContents, setDirContents] = useState<Record<string, FileEntry[]>>({});

  const [openFiles, setOpenFiles] = useState<OpenFile[]>([]);
  const [activeFile, setActiveFile] = useState<string | null>(null);

  const [terminalOpen, setTerminalOpen] = useState(false);
  const [nimbusOpen, setNimbusOpen] = useState(false);
  const [nimbusChatHistory, setNimbusChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [nimbusInput, setNimbusInput] = useState("");
  const [nimbusLoading, setNimbusLoading] = useState(false);

  const [nimbusTab, setNimbusTab] = useState<"chat" | "agents">("chat");
  const [agents, setAgents] = useState<any[]>([]);
  const [runningAgent, setRunningAgent] = useState<string | null>(null);
  const [agentResult, setAgentResult] = useState<{ prUrl?: string; phase?: string } | null>(null);

  const [saving, setSaving] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [idleWarning, setIdleWarning] = useState(false);
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (!nimbusOpen) return;
    fetch(`${API}/agents/`, { headers: { Authorization: `Bearer ${apiKey}` } })
      .then(r => r.json())
      .then(data => setAgents(Array.isArray(data) ? data : []))
      .catch(() => {});
  }, [nimbusOpen]);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  const startSession = async (repo: string) => {
    setSessionLoading(true);
    setSessionError(null);
    try {
      const res = await fetch(`${API}/ide/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${apiKey}` },
        body: JSON.stringify({ repo, branch: "main" }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setIdeSession(data);
      setShowRepoPicker(false);
      pollSession(data.id);
    } catch (e: any) {
      setSessionError(e.message || "Failed to start session");
      setSessionLoading(false);
    }
  };

  const pollSession = async (sessionId: string) => {
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 2000));
      try {
        const res = await fetch(`${API}/ide/sessions/${sessionId}`, {
          headers: { "Authorization": `Bearer ${apiKey}` },
        });
        const data = await res.json();
        setIdeSession(data);
        if (data.status === "ready") {
          setSessionLoading(false);
          await loadFileTree("/");
          return;
        }
        if (data.status === "error") {
          setSessionError("Session failed to start");
          setSessionLoading(false);
          return;
        }
      } catch {}
    }
    setSessionError("Session timed out");
    setSessionLoading(false);
  };

  const sessionUrl = ideSession?.machine_url;

  const loadFileTree = useCallback(async (path: string) => {
    if (!sessionUrl) return;
    try {
      const res = await fetch(`${sessionUrl}/files?path=${encodeURIComponent(path)}`);
      const data = await res.json();
      const entries: FileEntry[] = (data.entries || [])
        .filter((e: FileEntry) => !e.name.startsWith(".") || e.name === ".env.example");
      if (path === "/") {
        setFiles(entries);
      } else {
        setDirContents(prev => ({ ...prev, [path]: entries }));
      }
    } catch {}
  }, [sessionUrl]);

  const openFile = useCallback(async (path: string) => {
    if (!sessionUrl) return;
    const existing = openFiles.find(f => f.path === path);
    if (existing) { setActiveFile(path); return; }
    try {
      const res = await fetch(`${sessionUrl}/files/content?path=${encodeURIComponent(path)}`);
      const data = await res.json();
      const file: OpenFile = {
        path,
        content: data.content || "",
        modified: false,
        language: detectLanguage(path),
      };
      setOpenFiles(prev => [...prev, file]);
      setActiveFile(path);
    } catch {}
  }, [sessionUrl, openFiles]);

  const saveFile = useCallback(async (path: string, content: string) => {
    if (!sessionUrl) return;
    setSaving(true);
    try {
      await fetch(`${sessionUrl}/files/content`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path, content }),
      });
      setOpenFiles(prev => prev.map(f => f.path === path ? { ...f, content, modified: false } : f));
    } finally {
      setTimeout(() => setSaving(false), 800);
    }
  }, [sessionUrl]);

  const handleEditorChange = useCallback((value: string | undefined) => {
    if (!activeFile || value === undefined) return;
    setOpenFiles(prev => prev.map(f => f.path === activeFile ? { ...f, content: value, modified: true } : f));
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(() => saveFile(activeFile, value), 1500);
  }, [activeFile, saveFile]);

  useEffect(() => {
    if (!ideSession || ideSession.status !== "ready") return;
    const timer = setTimeout(() => setIdleWarning(true), 86100 * 1000);
    return () => clearTimeout(timer);
  }, [ideSession?.status]);

  const activeFileData = openFiles.find(f => f.path === activeFile);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        if (activeFile && activeFileData) {
          saveFile(activeFile, activeFileData.content);
        }
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "`") {
        e.preventDefault();
        setTerminalOpen(v => !v);
      }
      if (e.key === "Escape" && nimbusOpen) {
        setNimbusOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeFile, activeFileData, nimbusOpen, saveFile]);

  const closeFile = (path: string) => {
    setOpenFiles(prev => {
      const idx = prev.findIndex(f => f.path === path);
      const next = prev.filter(f => f.path !== path);
      if (activeFile === path) {
        setActiveFile(next[Math.max(0, idx - 1)]?.path || null);
      }
      return next;
    });
  };

  const toggleDir = async (path: string) => {
    setExpandedDirs(prev => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
        loadFileTree(path);
      }
      return next;
    });
  };

  const runAgent = async (agentName: string) => {
    if (!ideSession || runningAgent) return;
    setRunningAgent(agentName);
    setAgentResult(null);
    try {
      const res = await fetch(`${API}/agents/${agentName}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
        body: JSON.stringify({
          workspace_id: "ide-session",
          repo_id: ideSession.id,
          dry_run: false,
        }),
      });
      const task = await res.json();
      for (let i = 0; i < 60; i++) {
        await new Promise(r => setTimeout(r, 5000));
        const statusRes = await fetch(`${API}/tasks/${task.id}/`, {
          headers: { Authorization: `Bearer ${apiKey}` },
        });
        const status = await statusRes.json();
        setAgentResult({ phase: status.phase, prUrl: status.pr_url });
        if (status.pr_url || status.phase === "completed" || status.phase === "failed") break;
      }
    } catch (e) {
      setAgentResult({ phase: "error" });
    } finally {
      setRunningAgent(null);
    }
  };

  const sendNimbusMessage = async () => {
    if (!nimbusInput.trim() || nimbusLoading) return;
    const msg = nimbusInput.trim();
    setNimbusInput("");
    setNimbusChatHistory(prev => [...prev, { role: "user", content: msg }]);
    setNimbusLoading(true);
    try {
      const res = await fetch(`${API}/tasks/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${apiKey}` },
        body: JSON.stringify({ description: msg }),
      });
      const data = await res.json();
      setNimbusChatHistory(prev => [...prev, {
        role: "assistant",
        content: data.plan || data.message || "Task submitted.",
      }]);
    } catch {
      setNimbusChatHistory(prev => [...prev, { role: "assistant", content: "Something went wrong." }]);
    } finally {
      setNimbusLoading(false);
    }
  };

  const renderTree = (entries: FileEntry[], depth = 0): React.ReactNode => {
    return entries.map(entry => (
      <div key={entry.path}>
        <div
          onClick={() => entry.type === "directory" ? toggleDir(entry.path) : openFile(entry.path)}
          style={{
            display: "flex", alignItems: "center", gap: 7,
            padding: `4px 12px 4px ${12 + depth * 14}px`,
            cursor: "pointer",
            borderRadius: 4,
            background: activeFile === entry.path ? C.elevated : "transparent",
            color: activeFile === entry.path ? C.text : C.muted,
            fontSize: 12, fontFamily: mono,
            transition: "all 0.1s ease",
            userSelect: "none",
          }}
          onMouseEnter={e => {
            if (activeFile !== entry.path) (e.currentTarget as HTMLDivElement).style.background = C.ghost;
          }}
          onMouseLeave={e => {
            if (activeFile !== entry.path) (e.currentTarget as HTMLDivElement).style.background = "transparent";
          }}
        >
          {entry.type === "directory" ? (
            <span style={{ color: C.gold, fontSize: 9, width: 10, textAlign: "center" }}>
              {expandedDirs.has(entry.path) ? "▾" : "▸"}
            </span>
          ) : (
            <FileIcon path={entry.path} isDir={false} />
          )}
          <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {entry.name}
          </span>
        </div>
        {entry.type === "directory" && expandedDirs.has(entry.path) && dirContents[entry.path] && (
          renderTree(dirContents[entry.path], depth + 1)
        )}
      </div>
    ));
  };

  if (isMobile) {
    return (
      <div style={{
        background: "#0C0B09", minHeight: "100vh",
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: 24, textAlign: "center",
      }}>
        <div>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: "#F5EFE6", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px" }}>
            <span style={{ color: "#0C0B09", fontWeight: 800, fontSize: 16 }}>N</span>
          </div>
          <p style={{ fontFamily: "'Instrument Serif', Georgia, serif", fontStyle: "italic", fontSize: 22, color: "#F5EFE6", marginBottom: 10 }}>
            Nimbus IDE
          </p>
          <p style={{ fontFamily: "system-ui", fontSize: 14, color: "rgba(245,239,230,0.4)", lineHeight: 1.7, marginBottom: 24 }}>
            The IDE requires a larger screen.<br />
            Open on desktop for the full experience.
          </p>
          <a href="/" style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "rgba(245,239,230,0.3)", textDecoration: "none" }}>
            ← back to get-nimbus.com
          </a>
        </div>
      </div>
    );
  }

  if (showRepoPicker) {
    return (
      <div style={{
        background: C.bg, minHeight: "100vh", display: "flex", alignItems: "center",
        justifyContent: "center", fontFamily: sans,
      }}>
        <div style={{ width: 480, textAlign: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, justifyContent: "center", marginBottom: 40 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 7, background: C.text,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <span style={{ color: C.bg, fontWeight: 800, fontSize: 14, fontFamily: sans }}>N</span>
            </div>
            <span style={{ fontFamily: serif, fontStyle: "italic", fontSize: 22, color: C.text }}>Nimbus IDE</span>
          </div>

          <h1 style={{
            fontFamily: serif, fontSize: 36, fontWeight: 400,
            letterSpacing: "-0.02em", color: C.text, marginBottom: 10,
          }}>
            Open a repository
          </h1>
          <p style={{ fontFamily: sans, fontSize: 15, color: C.muted, marginBottom: 36 }}>
            Enter a GitHub repo to open it in the browser.
          </p>

          <div style={{
            background: C.surface, border: `1px solid ${C.border2}`, borderRadius: 12,
            padding: "6px", display: "flex", gap: 6, marginBottom: 16,
          }}>
            <input
              autoFocus
              value={repoInput}
              onChange={e => setRepoInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && repoInput.trim() && apiKey.trim() && startSession(repoInput.trim())}
              placeholder="owner/repository"
              style={{
                flex: 1, background: "transparent", border: "none", outline: "none",
                fontFamily: mono, fontSize: 14, color: C.text, padding: "10px 14px",
              }}
            />
            <button
              onClick={() => repoInput.trim() && apiKey.trim() && startSession(repoInput.trim())}
              disabled={sessionLoading || !repoInput.trim() || !apiKey.trim()}
              style={{
                background: sessionLoading ? C.ghost : C.text,
                color: C.bg, border: "none", borderRadius: 8,
                padding: "10px 22px", fontFamily: sans, fontSize: 14,
                fontWeight: 600, cursor: sessionLoading ? "not-allowed" : "pointer",
                transition: "all 0.15s ease",
                opacity: sessionLoading || !repoInput.trim() ? 0.5 : 1,
              }}
            >
              {sessionLoading ? "Starting..." : "Open →"}
            </button>
          </div>

          {/* API key input */}
          <div style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 10, padding: "10px 14px",
            display: "flex", alignItems: "center", gap: 10, marginBottom: 8,
          }}>
            <span style={{ fontFamily: mono, fontSize: 11, color: C.faint, flexShrink: 0 }}>API key</span>
            <input
              type="password"
              value={apiKey}
              onChange={e => {
                setApiKey(e.target.value);
                localStorage.setItem('nimbus_ide_api_key', e.target.value);
              }}
              placeholder="nk_..."
              style={{
                flex: 1, background: "transparent", border: "none", outline: "none",
                fontFamily: mono, fontSize: 13, color: C.text,
              }}
            />
            {apiKey && <span style={{ color: C.green, fontSize: 11 }}>✓</span>}
          </div>

          {sessionLoading && (
            <div style={{ marginTop: 24, display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
              <div style={{
                width: 240, height: 2, background: "rgba(245,239,230,0.06)",
                borderRadius: 999, overflow: "hidden",
              }}>
                <div style={{
                  height: "100%", width: "40%",
                  background: "linear-gradient(90deg, transparent, #C9A96E, transparent)",
                  borderRadius: 999,
                  animation: "shimmer 1.4s ease-in-out infinite",
                }} />
              </div>
              <LoadingPhase />
              <style>{`
                @keyframes shimmer {
                  0% { transform: translateX(-150%); }
                  100% { transform: translateX(400%); }
                }
              `}</style>
            </div>
          )}

          {sessionError && (
            <div style={{
              marginTop: 16,
              padding: "12px 16px",
              background: "rgba(168,112,112,0.08)",
              border: "1px solid rgba(168,112,112,0.2)",
              borderRadius: 8,
              display: "flex",
              alignItems: "flex-start",
              gap: 10,
            }}>
              <span style={{ color: "#A87070", fontSize: 14, flexShrink: 0 }}>✗</span>
              <div>
                <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "#A87070", margin: "0 0 4px" }}>
                  Session failed to start
                </p>
                <p style={{ fontFamily: "system-ui", fontSize: 12, color: "rgba(245,239,230,0.3)", margin: 0, lineHeight: 1.5 }}>
                  {sessionError}
                </p>
                <button
                  onClick={() => { setSessionError(null); setSessionLoading(false); }}
                  style={{
                    marginTop: 10, background: "none", border: "1px solid rgba(168,112,112,0.3)",
                    borderRadius: 5, padding: "4px 12px",
                    fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "#A87070",
                    cursor: "pointer",
                  }}
                >try again</button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={{
      display: "grid",
      gridTemplateRows: "40px 1fr",
      gridTemplateColumns: `220px 1fr ${nimbusOpen ? "320px" : "0px"}`,
      height: "100vh",
      background: C.bg,
      color: C.text,
      fontFamily: sans,
      overflow: "hidden",
      transition: "grid-template-columns 0.2s ease",
    }}>

      {/* TITLEBAR */}
      <div style={{
        gridColumn: "1 / -1",
        display: "flex", alignItems: "center",
        padding: "0 12px", gap: 12,
        borderBottom: `1px solid ${C.border}`,
        background: C.bg,
        userSelect: "none",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
          <div style={{
            width: 18, height: 18, borderRadius: 4, background: C.text,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <span style={{ color: C.bg, fontWeight: 800, fontSize: 9 }}>N</span>
          </div>
          <span style={{ fontFamily: serif, fontStyle: "italic", fontSize: 14, color: C.muted }}>Nimbus</span>
        </div>

        <div style={{ width: 1, height: 14, background: C.border }} />

        <span style={{ fontFamily: mono, fontSize: 11, color: C.muted }}>
          {ideSession?.repo || "no repo"}
        </span>
        <span style={{ fontFamily: mono, fontSize: 11, color: C.faint }}>
          {ideSession?.branch || "main"}
        </span>

        <div style={{ display: "flex", alignItems: "center", gap: 5, marginLeft: "auto" }}>
          {saving && (
            <span style={{ fontFamily: mono, fontSize: 10, color: C.faint }}>saving...</span>
          )}
          <div style={{
            width: 6, height: 6, borderRadius: "50%",
            background: ideSession?.status === "ready" ? C.green : C.gold,
          }} />
          <span style={{ fontFamily: mono, fontSize: 10, color: C.faint }}>
            {ideSession?.status || "starting"}
          </span>
        </div>

        <button
          onClick={() => setTerminalOpen(v => !v)}
          style={{
            background: terminalOpen ? C.ghost : "transparent",
            border: `1px solid ${terminalOpen ? C.border2 : "transparent"}`,
            borderRadius: 5, padding: "3px 9px",
            fontFamily: mono, fontSize: 10, color: terminalOpen ? C.text : C.faint,
            cursor: "pointer", transition: "all 0.15s",
          }}
        >
          terminal
        </button>

        <button
          onClick={() => setNimbusOpen(v => !v)}
          style={{
            background: nimbusOpen ? C.goldDim : "transparent",
            border: `1px solid ${nimbusOpen ? C.gold + "40" : "transparent"}`,
            borderRadius: 5, padding: "3px 9px",
            fontFamily: mono, fontSize: 10,
            color: nimbusOpen ? C.gold : C.faint,
            cursor: "pointer", transition: "all 0.15s",
          }}
        >
          nimbus
        </button>

        <button
          onClick={() => { setShowRepoPicker(true); setFiles([]); setOpenFiles([]); }}
          style={{
            background: "transparent", border: "1px solid transparent",
            borderRadius: 5, padding: "3px 9px",
            fontFamily: mono, fontSize: 10, color: C.faint,
            cursor: "pointer",
          }}
        >
          ×
        </button>
      </div>

      {idleWarning && (
        <div style={{
          gridColumn: "1 / -1",
          background: "rgba(201,169,110,0.1)",
          border: "none",
          borderBottom: "1px solid rgba(201,169,110,0.2)",
          padding: "8px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontSize: 12,
          fontFamily: mono,
          color: C.gold,
        }}>
          <span>⚠ Your session expires in 10 minutes. Save your work.</span>
          <button
            onClick={() => setIdleWarning(false)}
            style={{ background: "none", border: "none", color: C.gold, cursor: "pointer", fontSize: 14 }}
          >×</button>
        </div>
      )}

      {/* SIDEBAR */}
      <div style={{
        borderRight: `1px solid ${C.border}`,
        background: C.bg,
        overflowY: "auto",
        display: "flex", flexDirection: "column",
        gridRow: "2 / 3",
      }}>
        <div style={{
          padding: "10px 12px 6px",
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <span style={{ fontFamily: mono, fontSize: 9, color: C.faint, letterSpacing: "0.08em", textTransform: "uppercase" }}>
            Explorer
          </span>
          <button
            onClick={() => loadFileTree("/")}
            style={{ background: "none", border: "none", color: C.faint, cursor: "pointer", fontSize: 12 }}
            title="Refresh"
          >
            &#8635;
          </button>
        </div>
        <div style={{ flex: 1, paddingBottom: 12 }}>
          {files.length === 0 ? (
            <div style={{ padding: "12px", fontFamily: mono, fontSize: 11, color: C.faint, lineHeight: 1.7 }}>
              {ideSession?.status === "ready" ? "empty repository" : "loading..."}
            </div>
          ) : renderTree(files)}
        </div>
      </div>

      {/* EDITOR */}
      <div style={{
        display: "flex", flexDirection: "column",
        background: "#0E0C0A",
        gridRow: "2 / 3",
        overflow: "hidden",
      }}>
        {openFiles.length > 0 && (
          <div style={{
            display: "flex", alignItems: "center",
            borderBottom: `1px solid ${C.border}`,
            background: C.bg,
            overflowX: "auto",
            flexShrink: 0,
            scrollbarWidth: "none",
          }}>
            {openFiles.map(file => {
              const isActive = file.path === activeFile;
              const name = file.path.split("/").pop() || file.path;
              return (
                <div
                  key={file.path}
                  onClick={() => setActiveFile(file.path)}
                  style={{
                    display: "flex", alignItems: "center", gap: 8,
                    padding: "0 14px",
                    height: 35,
                    borderRight: `1px solid ${C.border}`,
                    background: isActive ? "#0E0C0A" : "transparent",
                    borderBottom: isActive ? `1px solid ${C.gold}` : "1px solid transparent",
                    cursor: "pointer",
                    flexShrink: 0,
                    transition: "all 0.1s ease",
                    position: "relative",
                  }}
                >
                  <FileIcon path={file.path} isDir={false} />
                  <span style={{ fontFamily: mono, fontSize: 12, color: isActive ? C.text : C.faint, whiteSpace: "nowrap" }}>
                    {name}
                  </span>
                  {file.modified && (
                    <span style={{ width: 5, height: 5, borderRadius: "50%", background: C.gold, flexShrink: 0 }} />
                  )}
                  <span
                    onClick={e => { e.stopPropagation(); closeFile(file.path); }}
                    className="tab-close"
                    style={{ color: C.faint, fontSize: 13, cursor: "pointer", lineHeight: 1, padding: "0 2px" }}
                  >
                    ×
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {activeFileData ? (
          <MonacoEditor
            height="100%"
            language={activeFileData.language}
            value={activeFileData.content}
            onChange={handleEditorChange}
            theme="nimbus-dark"
            beforeMount={(monaco) => {
              monaco.editor.defineTheme("nimbus-dark", {
                base: "vs-dark",
                inherit: true,
                rules: [
                  { token: "comment", foreground: "4a4540", fontStyle: "italic" },
                  { token: "keyword", foreground: "C9A96E" },
                  { token: "string", foreground: "7AAB8A" },
                  { token: "number", foreground: "A87878" },
                  { token: "type", foreground: "8BA8C9" },
                  { token: "function", foreground: "D4C4A8" },
                  { token: "variable", foreground: "E8DDD0" },
                  { token: "operator", foreground: "8a7f73" },
                ],
                colors: {
                  "editor.background":                  "#0E0C0A",
                  "editor.foreground":                  "#E8DDD0",
                  "editor.lineHighlightBackground":     "#141210",
                  "editor.selectionBackground":         "#C9A96E25",
                  "editor.inactiveSelectionBackground": "#C9A96E15",
                  "editorCursor.foreground":            "#C9A96E",
                  "editorLineNumber.foreground":        "#3a3530",
                  "editorLineNumber.activeForeground":  "#6a5f54",
                  "editorIndentGuide.background":       "#1e1b18",
                  "editorIndentGuide.activeBackground": "#2e2a26",
                  "editor.findMatchBackground":         "#C9A96E30",
                  "editor.findMatchHighlightBackground":"#C9A96E15",
                  "editorWidget.background":            "#141210",
                  "editorWidget.border":                "#2a2520",
                  "input.background":                   "#1a1816",
                  "input.border":                       "#2a2520",
                  "list.hoverBackground":               "#1a1816",
                  "list.activeSelectionBackground":     "#C9A96E20",
                  "scrollbar.shadow":                   "#00000000",
                  "scrollbarSlider.background":         "#3a3530",
                  "scrollbarSlider.hoverBackground":    "#4a4540",
                },
              });
            }}
            options={{
              fontSize: 13,
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              fontLigatures: true,
              lineHeight: 22,
              letterSpacing: 0.3,
              minimap: { enabled: false },
              scrollbar: {
                vertical: "auto",
                horizontal: "auto",
                verticalScrollbarSize: 4,
                horizontalScrollbarSize: 4,
              },
              lineNumbers: "on",
              renderLineHighlight: "line",
              cursorBlinking: "smooth",
              cursorSmoothCaretAnimation: "on",
              smoothScrolling: true,
              padding: { top: 16, bottom: 16 },
              wordWrap: "off",
              glyphMargin: false,
              folding: true,
              bracketPairColorization: { enabled: true },
              guides: { bracketPairs: false, indentation: true },
              suggest: { showIcons: false },
              renderWhitespace: "none",
              overviewRulerBorder: false,
              hideCursorInOverviewRuler: true,
            }}
          />
        ) : (
          <div style={{
            flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
            flexDirection: "column", gap: 12,
          }}>
            <div style={{ fontFamily: serif, fontStyle: "italic", fontSize: 22, color: "rgba(245,239,230,0.08)" }}>
              Select a file to start editing
            </div>
            <div style={{ fontFamily: mono, fontSize: 11, color: "rgba(245,239,230,0.06)" }}>
              or open the terminal to run nimbus
            </div>
          </div>
        )}

        <div style={{
          height: terminalOpen ? 280 : 0,
          borderTop: terminalOpen ? `1px solid ${C.border}` : "none",
          overflow: "hidden",
          transition: "height 0.2s ease",
          background: "#080706",
          flexShrink: 0,
        }}>
          {terminalOpen && ideSession?.machine_url && (
            <TerminalPanel wsUrl={ideSession.machine_url.replace("https://", "wss://") + "/ws/shell"} />
          )}
        </div>
      </div>

      {/* NIMBUS PANEL */}
      {nimbusOpen && (
        <div style={{
          borderLeft: `1px solid ${C.border}`,
          background: C.surface,
          gridRow: "2 / 3",
          display: "flex", flexDirection: "column",
          overflow: "hidden",
        }}>
          <div style={{
            padding: "12px 16px",
            borderBottom: `1px solid ${C.border}`,
            display: "flex", alignItems: "center", gap: 8,
          }}>
            <div style={{
              width: 16, height: 16, borderRadius: 3, background: C.text,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <span style={{ color: C.bg, fontWeight: 800, fontSize: 8 }}>N</span>
            </div>
            <span style={{ fontFamily: sans, fontSize: 13, fontWeight: 600, color: C.text }}>Nimbus</span>
            <div style={{ display: "flex", gap: 4, marginLeft: "auto" }}>
              {(["chat", "agents"] as const).map(tab => (
                <button key={tab} onClick={() => setNimbusTab(tab)}
                  style={{
                    background: nimbusTab === tab ? C.ghost : "none",
                    border: "none", borderRadius: 4, padding: "3px 8px",
                    fontFamily: mono, fontSize: 10,
                    color: nimbusTab === tab ? C.text : C.faint,
                    cursor: "pointer",
                  }}>
                  {tab}
                </button>
              ))}
            </div>
          </div>

          {nimbusTab === "chat" ? (
            <>
              <div style={{ flex: 1, overflowY: "auto", padding: "12px 16px", display: "flex", flexDirection: "column", gap: 14 }}>
                {nimbusChatHistory.length === 0 && (
                  <div style={{ textAlign: "center", marginTop: 32 }}>
                    <p style={{ fontFamily: sans, fontSize: 13, color: C.faint, lineHeight: 1.7 }}>
                      Ask anything about the codebase, or describe a task for Nimbus to implement.
                    </p>
                  </div>
                )}
                {nimbusChatHistory.map((msg, i) => (
                  <div key={i} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <span style={{ fontFamily: mono, fontSize: 10, color: msg.role === "user" ? C.gold : C.faint }}>
                      {msg.role === "user" ? "you" : "nimbus"}
                    </span>
                    <p style={{ fontFamily: sans, fontSize: 13, color: C.muted, lineHeight: 1.65, margin: 0 }}>
                      {msg.content}
                    </p>
                  </div>
                ))}
                {nimbusLoading && (
                  <div style={{ fontFamily: mono, fontSize: 11, color: C.faint }}>thinking...</div>
                )}
              </div>

              <div style={{ padding: "10px 12px", borderTop: `1px solid ${C.border}` }}>
                <div style={{
                  display: "flex", gap: 6, background: C.elevated,
                  border: `1px solid ${C.border2}`, borderRadius: 8, padding: "6px 8px",
                }}>
                  <input
                    value={nimbusInput}
                    onChange={e => setNimbusInput(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendNimbusMessage()}
                    placeholder="run a task or ask about the code..."
                    style={{
                      flex: 1, background: "transparent", border: "none", outline: "none",
                      fontFamily: mono, fontSize: 12, color: C.text,
                    }}
                  />
                  <button
                    onClick={sendNimbusMessage}
                    disabled={nimbusLoading || !nimbusInput.trim()}
                    style={{
                      background: nimbusInput.trim() ? C.gold : "transparent",
                      color: nimbusInput.trim() ? C.bg : C.faint,
                      border: "none", borderRadius: 5, padding: "4px 10px",
                      fontFamily: mono, fontSize: 11, fontWeight: 600,
                      cursor: nimbusInput.trim() ? "pointer" : "default",
                      transition: "all 0.15s ease",
                    }}
                  >
                    &#8593;
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div style={{ flex: 1, overflowY: "auto", paddingTop: 12 }}>
              {(() => {
                const agentsByCategory = agents.reduce((acc: any, a: any) => {
                  const cat = a.category || "other";
                  if (!acc[cat]) acc[cat] = [];
                  acc[cat].push(a);
                  return acc;
                }, {});
                return (
                  <>
                    {agents.length === 0 && (
                      <div style={{ padding: "32px 16px", textAlign: "center", fontFamily: mono, fontSize: 11, color: C.faint }}>
                        no agents available
                      </div>
                    )}
                    {Object.entries(agentsByCategory).map(([category, agentList]: [string, any]) => (
                      <div key={category} style={{ marginBottom: 16 }}>
                        <p style={{ fontFamily: mono, fontSize: 9, color: C.faint, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6, padding: "0 16px" }}>
                          {category}
                        </p>
                        {(agentList as any[]).map((agent: any) => (
                          <div key={agent.name} style={{
                            display: "flex", alignItems: "center", justifyContent: "space-between",
                            padding: "7px 16px",
                            background: runningAgent === agent.name ? C.goldDim : "transparent",
                            transition: "background 0.15s",
                          }}>
                            <span style={{ fontFamily: mono, fontSize: 12, color: runningAgent === agent.name ? C.gold : C.muted }}>
                              {agent.name}
                            </span>
                            <button
                              onClick={() => runAgent(agent.name)}
                              disabled={!!runningAgent}
                              style={{
                                background: "none", border: `1px solid ${runningAgent === agent.name ? C.gold + "40" : C.border}`,
                                borderRadius: 4, padding: "2px 10px",
                                fontFamily: mono, fontSize: 10,
                                color: runningAgent === agent.name ? C.gold : C.faint,
                                cursor: runningAgent ? "not-allowed" : "pointer",
                                transition: "all 0.15s",
                              }}
                            >
                              {runningAgent === agent.name ? (agentResult?.phase || "running...") : "run →"}
                            </button>
                          </div>
                        ))}
                      </div>
                    ))}
                    {agentResult?.prUrl && (
                      <div style={{ margin: "12px 16px", padding: "8px 12px", background: C.goldDim, borderRadius: 6, border: `1px solid ${C.gold}30` }}>
                        <a href={agentResult.prUrl} target="_blank" rel="noopener noreferrer"
                          style={{ fontFamily: mono, fontSize: 11, color: C.gold, textDecoration: "none" }}>
                          &#8599; {agentResult.prUrl.split("/").slice(-3).join("/")}
                        </a>
                      </div>
                    )}
                  </>
                );
              })()}
            </div>
          )}
        </div>
      )}

      <style>{`
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(245,239,230,0.1); border-radius: 999px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(245,239,230,0.2); }
        .tab-close { opacity: 0; }
        div:hover > .tab-close { opacity: 1; }
      `}</style>
    </div>
  );
}
