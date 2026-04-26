"use client";
import { useState } from "react";
import { useIsMobile } from "@/hooks/useIsMobile";
import NavMobile from "@/components/NavMobile";

const serif = "var(--font-serif,'Georgia',serif)";
const sans  = "var(--font-sans,system-ui,sans-serif)";
const mono  = "var(--font-mono,monospace)";
const W     = 800;

const C = {
  bg:   "#0A0A0A", text: "#FAFAFA",
  muted: "rgba(255,255,255,0.5)", faint: "rgba(255,255,255,0.25)",
  gold: "#c4a96a", green: "#6aab7a", border: "rgba(255,255,255,0.07)",
};

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };
  return (
    <button onClick={copy} style={{ background: "none", border: "none", cursor: "pointer", fontFamily: mono, fontSize: 11, color: copied ? C.green : C.faint, padding: "2px 6px", borderRadius: 4, transition: "color 0.2s" }}>
      {copied ? "copied ✓" : "copy"}
    </button>
  );
}

function CodeBlock({ code, lang = "bash" }: { code: string; lang?: string }) {
  return (
    <div style={{ position: "relative", background: "#0d0d0d", border: `1px solid ${C.border}`, borderRadius: 10, overflow: "hidden", marginTop: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 16px", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <span style={{ fontFamily: mono, fontSize: 10, color: "rgba(255,255,255,0.2)", letterSpacing: "0.06em" }}>{lang}</span>
        <CopyButton text={code} />
      </div>
      <pre style={{ margin: 0, padding: "16px 20px", fontFamily: mono, fontSize: 13, lineHeight: 1.75, color: "rgba(255,255,255,0.75)", overflowX: "auto", whiteSpace: "pre" }}>
        {code}
      </pre>
    </div>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", gap: 20, marginBottom: 36 }}>
      <div style={{ flexShrink: 0, width: 28, height: 28, borderRadius: "50%", border: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", marginTop: 2 }}>
        <span style={{ fontFamily: mono, fontSize: 12, color: C.faint }}>{n}</span>
      </div>
      <div style={{ flex: 1 }}>
        <p style={{ fontFamily: sans, fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 6 }}>{title}</p>
        {children}
      </div>
    </div>
  );
}

function Tab({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{ border: "none", cursor: "pointer", fontFamily: mono, fontSize: 12, color: active ? C.text : C.faint, padding: "8px 16px", borderRadius: 6, background: active ? "rgba(255,255,255,0.07)" : "transparent", transition: "all 0.15s", letterSpacing: "0.03em" }}>
      {label}
    </button>
  );
}

export default function DownloadPage() {
  const [method, setMethod] = useState<"pip" | "brew" | "curl">("pip");
  const isMobile = useIsMobile();

  return (
    <div style={{ background: C.bg, color: C.text, minHeight: "100vh", fontFamily: sans }}>

      {/* Nav */}
      <nav style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 100, height: 56, borderBottom: "1px solid rgba(255,255,255,0.06)", background: "rgba(10,10,10,0.9)", backdropFilter: "blur(16px)" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "0 28px", height: "100%", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
            <a href="/" style={{ display: "flex", alignItems: "center", gap: 9, textDecoration: "none" }}>
              <div style={{ width: 22, height: 22, borderRadius: 5, background: C.text, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: C.bg, fontWeight: 800, fontSize: 12, fontFamily: sans }}>N</span>
              </div>
              <span style={{ fontWeight: 400, fontSize: 17, fontStyle: "italic", color: C.text, fontFamily: serif }}>Nimbus</span>
            </a>
            <div className="nav-desktop-links" style={{ display: "flex", gap: 32 }}>
              {([["Product", "/#product"], ["Docs", "https://docs.get-nimbus.com"], ["GitHub", "https://github.com/arpjw/nimbus"], ["Download", "/download"]] as [string, string][]).map(([l, h]) => (
                <a key={l} href={h} style={{ fontFamily: sans, fontSize: 14, color: l === "Download" ? C.text : C.muted, textDecoration: "none", fontWeight: l === "Download" ? 500 : 400 }}>{l}</a>
              ))}
            </div>
          </div>
          <div className="nav-auth-desktop">
            <a href="https://api.get-nimbus.com/keys/generate" style={{ fontFamily: sans, fontSize: 14, fontWeight: 600, color: C.bg, background: C.text, padding: "8px 20px", borderRadius: 999, textDecoration: "none" }}>Get started</a>
          </div>
          <div className="nav-mobile-menu" style={{ display: "none" }}>
            <NavMobile />
          </div>
        </div>
      </nav>

      {/* Hero */}
      <div style={{ paddingTop: isMobile ? 90 : 120, paddingBottom: 64, paddingLeft: isMobile ? 20 : 28, paddingRight: isMobile ? 20 : 28, textAlign: "center", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 18 }}>Install Nimbus</p>
          <h1 style={{ fontFamily: serif, fontSize: 44, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.12, marginBottom: 16, color: C.text }}>
            Get started in <em style={{ fontStyle: "italic" }}>two minutes.</em>
          </h1>
          <p style={{ fontFamily: sans, fontSize: 16, color: C.muted, lineHeight: 1.65, maxWidth: 480, margin: "0 auto 32px" }}>
            Nimbus runs locally on your machine using your own API keys. Python 3.11+ required.
          </p>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "#111", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10, padding: "10px 20px" }}>
            <span style={{ fontFamily: mono, fontSize: 14, color: C.gold }}>pip install nimbus-ai</span>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div style={{ maxWidth: W, margin: "0 auto", padding: isMobile ? "40px 20px" : "64px 28px" }}>

        {/* Install method tabs */}
        <div style={{ marginBottom: 48 }}>
          <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>Choose your install method</p>
          <div style={{ display: "flex", gap: 4, background: "#0d0d0d", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 10, padding: 4, width: "fit-content", marginBottom: 24, flexWrap: isMobile ? "wrap" : "nowrap" }}>
            <Tab label={isMobile ? "pip" : "pip  (recommended)"} active={method === "pip"} onClick={() => setMethod("pip")} />
            <Tab label={isMobile ? "Homebrew" : "Homebrew  (Mac)"} active={method === "brew"} onClick={() => setMethod("brew")} />
            <Tab label="curl" active={method === "curl"} onClick={() => setMethod("curl")} />
          </div>

          {method === "pip" && (
            <div>
              <Step n={1} title="Install the package">
                <CodeBlock code="pip install nimbus-ai" />
              </Step>
              <Step n={2} title="Set your API keys">
                <p style={{ fontFamily: sans, fontSize: 14, color: C.muted, lineHeight: 1.7, marginBottom: 8 }}>
                  Nimbus uses <a href="https://console.anthropic.com" target="_blank" rel="noopener noreferrer" style={{ color: C.gold, textDecoration: "none" }}>Anthropic</a> for reasoning and <a href="https://dash.voyageai.com" target="_blank" rel="noopener noreferrer" style={{ color: C.gold, textDecoration: "none" }}>Voyage AI</a> for embeddings. Both have free tiers.
                </p>
                <CodeBlock code={`export ANTHROPIC_API_KEY=sk-ant-...\nexport VOYAGE_API_KEY=pa-...`} />
                <p style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.2)", marginTop: 8 }}>Add to ~/.zshrc or ~/.bashrc to persist across sessions.</p>
              </Step>
              <Step n={3} title="Run in your project">
                <CodeBlock code={`cd your-project\nnimbus`} />
              </Step>
            </div>
          )}

          {method === "brew" && (
            <div>
              <Step n={1} title="Add the Nimbus tap">
                <CodeBlock code="brew tap arpjw/tap" />
              </Step>
              <Step n={2} title="Install Nimbus">
                <CodeBlock code="brew install nimbus" />
              </Step>
              <Step n={3} title="Set your API keys">
                <CodeBlock code={`export ANTHROPIC_API_KEY=sk-ant-...\nexport VOYAGE_API_KEY=pa-...`} />
              </Step>
              <Step n={4} title="Run in your project">
                <CodeBlock code={`cd your-project\nnimbus`} />
              </Step>
            </div>
          )}

          {method === "curl" && (
            <div>
              <Step n={1} title="Run the install script">
                <CodeBlock code="curl -fsSL https://get-nimbus.com/install | sh" />
              </Step>
              <Step n={2} title="Set your API keys">
                <CodeBlock code={`export ANTHROPIC_API_KEY=sk-ant-...\nexport VOYAGE_API_KEY=pa-...`} />
              </Step>
              <Step n={3} title="Run in your project">
                <CodeBlock code={`cd your-project\nnimbus`} />
              </Step>
            </div>
          )}
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: "rgba(255,255,255,0.06)", marginBottom: 48 }} />

        {/* API Keys */}
        <div style={{ marginBottom: 48 }}>
          <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 24 }}>Get your API keys</p>
          <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: 12 }}>
            {[
              { name: "Anthropic", description: "Powers the planning and implementation agents. Claude Opus for planning, Claude Sonnet for implementation.", url: "https://console.anthropic.com", var: "ANTHROPIC_API_KEY", free: "Free tier available" },
              { name: "Voyage AI", description: "Generates code embeddings for RAG retrieval. voyage-code-2 model, purpose-built for source code.", url: "https://dash.voyageai.com", var: "VOYAGE_API_KEY", free: "50M tokens free/month" },
            ].map(k => (
              <div key={k.name} style={{ border: "1px solid rgba(255,255,255,0.07)", borderRadius: 12, padding: "22px 24px", background: "#0d0d0d" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                  <p style={{ fontFamily: sans, fontSize: 15, fontWeight: 600, color: C.text }}>{k.name}</p>
                  <span style={{ fontFamily: mono, fontSize: 10, color: C.green, background: "rgba(106,171,122,0.08)", border: "1px solid rgba(106,171,122,0.2)", padding: "2px 8px", borderRadius: 999 }}>{k.free}</span>
                </div>
                <p style={{ fontFamily: sans, fontSize: 13, color: C.muted, lineHeight: 1.65, marginBottom: 14 }}>{k.description}</p>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: "#111", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 6, padding: "6px 10px", marginBottom: 14 }}>
                  <code style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.4)" }}>{k.var}</code>
                </div>
                <a href={k.url} target="_blank" rel="noopener noreferrer" style={{ fontFamily: sans, fontSize: 13, fontWeight: 500, color: C.bg, background: C.text, padding: "7px 16px", borderRadius: 999, textDecoration: "none", display: "inline-block" }}>
                  Get key →
                </a>
              </div>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: "rgba(255,255,255,0.06)", marginBottom: 48 }} />

        {/* Optional extras */}
        <div style={{ marginBottom: 48 }}>
          <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 24 }}>Optional extras</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              { label: "Voice input", pkg: "pip install nimbus-ai[voice]", desc: "Speak your tasks. Requires mic access. Uses local Whisper (base model)." },
              { label: "Soundtrack", pkg: "pip install nimbus-ai[sound]", desc: "Audio feedback for task start, verify pass, complete, and failed states." },
              { label: "Both", pkg: "pip install nimbus-ai[voice,sound]", desc: "Voice input and soundtrack together." },
            ].map(e => (
              <div key={e.label} style={{ display: "flex", flexDirection: isMobile ? "column" : "row", alignItems: isMobile ? "flex-start" : "center", gap: 16, border: "1px solid rgba(255,255,255,0.07)", borderRadius: 10, padding: "14px 18px", background: "#0d0d0d" }}>
                <div style={{ flexShrink: 0, width: isMobile ? "auto" : 80 }}>
                  <span style={{ fontFamily: sans, fontSize: 12, fontWeight: 600, color: C.muted }}>{e.label}</span>
                </div>
                <code style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.55)", flex: 1 }}>{e.pkg}</code>
                <p style={{ fontFamily: sans, fontSize: 12, color: "rgba(255,255,255,0.3)", flex: isMobile ? "none" : 1.5, lineHeight: 1.5 }}>{e.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: "rgba(255,255,255,0.06)", marginBottom: 48 }} />

        {/* Verify install */}
        <div style={{ marginBottom: 48 }}>
          <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>Verify your install</p>
          <CodeBlock code="nimbus --version\n# nimbus 1.1.0" />
          <p style={{ fontFamily: sans, fontSize: 13, color: C.muted, marginTop: 12, lineHeight: 1.65 }}>
            If Nimbus is installed but keys are missing, it will show a setup panel guiding you through the configuration. Run <code style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.5)" }}>nimbus</code> in any git repo to start the REPL.
          </p>
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: "rgba(255,255,255,0.06)", marginBottom: 48 }} />

        {/* What's next */}
        <div>
          <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 24 }}>{"What's next"}</p>
          <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(3,1fr)", gap: 12 }}>
            {[
              { title: "Run your first task", desc: "Step-by-step walkthrough of the full Nimbus REPL from welcome screen to merged PR.", href: "https://docs.get-nimbus.com/getting-started/first-task" },
              { title: "Explore built-in agents", desc: "20 pre-configured agents for security, testing, docs, and more. No configuration needed.", href: "https://docs.get-nimbus.com/agents/overview" },
              { title: "Connect integrations", desc: "Set up GitHub App, Slack slash commands, Linear webhooks, and VS Code extension.", href: "https://docs.get-nimbus.com/integrations/github-app" },
            ].map(card => (
              <a key={card.title} href={card.href} target="_blank" rel="noopener noreferrer" style={{ display: "block", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 12, padding: "20px 22px", background: "#0d0d0d", textDecoration: "none", transition: "border-color 0.15s" }}>
                <p style={{ fontFamily: sans, fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 8 }}>{card.title}</p>
                <p style={{ fontFamily: sans, fontSize: 13, color: C.muted, lineHeight: 1.6, marginBottom: 14 }}>{card.desc}</p>
                <span style={{ fontFamily: sans, fontSize: 13, color: C.gold }}>Read the docs →</span>
              </a>
            ))}
          </div>
        </div>

      </div>

      {/* Footer */}
      <div style={{ borderTop: "1px solid rgba(255,255,255,0.05)", padding: "28px", textAlign: "center" }}>
        <p style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.2)" }}>
          Nimbus v1.1.0 · MIT License · <a href="https://pypi.org/project/nimbus-ai" style={{ color: "rgba(255,255,255,0.3)", textDecoration: "none" }}>PyPI</a> · <a href="https://github.com/arpjw/nimbus" style={{ color: "rgba(255,255,255,0.3)", textDecoration: "none" }}>GitHub</a>
        </p>
      </div>
    </div>
  );
}
