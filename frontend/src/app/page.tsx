"use client";
import { useEffect, useState, useRef, ReactNode } from "react";
import { useIsMobile } from "@/hooks/useIsMobile";

const serif = "var(--font-serif,'Georgia',serif)";
const sans  = "var(--font-sans,system-ui,sans-serif)";
const mono  = "var(--font-mono,monospace)";
const W     = 1100;

const C = {
  bg:   "#0A0A0A", surface: "#111", border: "rgba(255,255,255,0.06)",
  text: "#FAFAFA", muted: "rgba(255,255,255,0.5)", faint: "rgba(255,255,255,0.25)",
  gold: "#c4a96a", green: "#6aab7a",
};

function FadeUp({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [v, setV] = useState(false);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    const o = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setV(true); o.disconnect(); } }, { threshold: 0.08 });
    o.observe(el); return () => o.disconnect();
  }, []);
  return (
    <div ref={ref} style={{ opacity: v ? 1 : 0, transform: v ? "none" : "translateY(22px)", transition: `opacity .55s ease ${delay}ms,transform .55s ease ${delay}ms` }}>
      {children}
    </div>
  );
}

const LINES = [
  { d: 0,    t: "$ nimbus",                                         c: C.text },
  { d: 600,  t: "",                                                  c: "" },
  { d: 700,  t: "  NIMBUS  ·  autonomous software engineering",      c: C.gold },
  { d: 900,  t: "  v1.2.0  ·  github.com/acme/api  ·  847 files",   c: "rgba(255,255,255,0.2)" },
  { d: 1200, t: "",                                                   c: "" },
  { d: 1300, t: "  nimbus › run 'migrate auth to JWT'",              c: C.text },
  { d: 1900, t: "",                                                   c: "" },
  { d: 2000, t: "  confidence  ████████░░  92%  ·  low ambiguity",   c: C.gold },
  { d: 2600, t: "  Proceed with 3 changes? [y/N] y",                 c: "rgba(255,255,255,0.5)" },
  { d: 3200, t: "",                                                   c: "" },
  { d: 3300, t: "  write  src/lib/jwt.ts                +42",        c: C.green },
  { d: 3600, t: "  write  src/middleware/auth.ts        +18",        c: C.green },
  { d: 3900, t: "  write  src/routes/login.ts           +9",         c: C.green },
  { d: 4300, t: "",                                                   c: "" },
  { d: 4400, t: "  tsc ✓   eslint ✓   47 tests pass",               c: "rgba(255,255,255,0.4)" },
  { d: 4900, t: "  PR #47 opened  ↗  acme/api/pull/47",              c: C.text },
  { d: 5400, t: "",                                                   c: "" },
  { d: 5500, t: "  nimbus › search 'JWT validation'",                c: C.text },
  { d: 6000, t: "  ├─ src/lib/jwt.ts              score 0.97",       c: C.muted },
  { d: 6200, t: "  └─ src/middleware/auth.ts      score 0.91",       c: C.muted },
  { d: 6500, t: "",                                                   c: "" },
  { d: 6600, t: "  nimbus › chat",                                   c: C.text },
  { d: 6900, t: "  you › how does the new JWT auth work?",           c: "rgba(255,255,255,0.5)" },
  { d: 7400, t: "  JWT issued at src/lib/jwt.ts:12 · 30 day TTL.",   c: C.muted },
  { d: 7800, t: "  verified in middleware/auth.ts:18",               c: C.muted },
  { d: 8100, t: "  done in 34.2s",                                   c: "rgba(255,255,255,0.25)" },
];

function Terminal() {
  const [vis, setVis] = useState<number[]>([]);
  const isMobile = useIsMobile();
  useEffect(() => {
    const ts = LINES.map((_, i) => setTimeout(() => setVis(v => [...v, i]), LINES[i].d));
    return () => ts.forEach(clearTimeout);
  }, []);
  return (
    <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10, overflow: "hidden", background: "#0c0c0c", overflowX: "auto" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 16px", borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(255,255,255,0.02)" }}>
        {[0,1,2].map(i => <div key={i} style={{ width: 11, height: 11, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />)}
        <span style={{ marginLeft: 10, fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.2)" }}>nimbus · zsh</span>
      </div>
      <div style={{ padding: "22px 28px", fontFamily: mono, fontSize: isMobile ? 11 : 13, lineHeight: 1.75, minHeight: 360 }}>
        {LINES.map((l, i) => vis.includes(i) && (
          <div key={i} style={{ color: l.c, minHeight: l.t ? undefined : 12, whiteSpace: "pre" }}>{l.t}</div>
        ))}
        {vis.length < LINES.length && (
          <span style={{ display: "inline-block", width: 7, height: 13, background: "rgba(255,255,255,0.5)", verticalAlign: "middle", animation: "blink 1s step-end infinite" }} />
        )}
      </div>
      <style>{`@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}`}</style>
    </div>
  );
}

function WinBar({ title }: { title: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "8px 12px", background: "rgba(255,255,255,0.02)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
      {[0,1,2].map(i => <div key={i} style={{ width: 8, height: 8, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />)}
      <span style={{ fontFamily: mono, fontSize: 10, color: "rgba(255,255,255,0.2)", marginLeft: 8 }}>{title}</span>
    </div>
  );
}

function PRDemo() {
  return (
    <div style={{ border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, overflow: "hidden", background: "#0c0c0c" }}>
      <WinBar title="github.com / acme / api / pull / 47" />
      <div style={{ padding: "18px 22px" }}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 14 }}>
          <span style={{ fontFamily: mono, fontSize: 11, padding: "2px 10px", borderRadius: 999, border: "1px solid rgba(106,171,122,0.3)", background: "rgba(106,171,122,0.08)", color: C.green, whiteSpace: "nowrap", marginTop: 2 }}>Open</span>
          <div>
            <p style={{ fontSize: 14, fontWeight: 600, color: "#FAFAFA", lineHeight: 1.4, fontFamily: sans }}>Migrate auth middleware to JWT</p>
            <p style={{ fontSize: 12, color: C.muted, marginTop: 4, fontFamily: mono }}>nimbus-bot · 2 minutes ago · 3 files</p>
          </div>
        </div>
        {([["src/lib/jwt.ts", "+42", C.green], ["src/middleware/auth.ts", "+18 −31", C.muted], ["src/routes/login.ts", "+9 −4", C.muted]] as [string,string,string][]).map(([f,s,col]) => (
          <div key={f} style={{ display: "flex", justifyContent: "space-between", padding: "7px 10px", borderRadius: 6, border: "1px solid rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.04)", marginBottom: 5 }}>
            <span style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.65)" }}>{f}</span>
            <span style={{ fontFamily: mono, fontSize: 12, color: col }}>{s}</span>
          </div>
        ))}
        <div style={{ border: "1px solid rgba(255,255,255,0.06)", borderRadius: 8, overflow: "hidden", marginTop: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: "rgba(255,255,255,0.02)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
            <div style={{ width: 16, height: 16, borderRadius: 4, background: "rgba(196,169,106,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ color: C.gold, fontWeight: 700, fontSize: 9 }}>N</span>
            </div>
            <span style={{ fontSize: 12, color: C.muted, fontFamily: mono }}>nimbus-bot · self-review · APPROVE</span>
          </div>
          <div style={{ padding: "10px 12px", fontFamily: mono, fontSize: 12, lineHeight: 1.7, background: "rgba(0,0,0,0.2)" }}>
            <p style={{ color: C.green }}>JWT with Redis refresh tokens. 47 tests pass.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function MemoryDemo() {
  const entries = [
    { k: "convention", v: "Uses Zod for all request validation. Never Joi." },
    { k: "testing",    v: "pytest only. Fixtures in conftest.py. No unittest." },
    { k: "auth",       v: "JWT + Redis refresh tokens, migrated in PR #47." },
    { k: "patterns",   v: "Prefers functional middleware over class-based handlers." },
  ];
  return (
    <div style={{ border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, overflow: "hidden", background: "#0c0c0c" }}>
      <WinBar title="nimbus memory · acme/api" />
      <div style={{ padding: "14px 18px", display: "flex", flexDirection: "column", gap: 7 }}>
        {entries.map((e, i) => (
          <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start", padding: "9px 10px", borderRadius: 6, border: "1px solid rgba(255,255,255,0.05)", background: "rgba(255,255,255,0.02)" }}>
            <span style={{ fontFamily: mono, fontSize: 10, color: C.gold, background: "rgba(196,169,106,0.08)", border: "1px solid rgba(196,169,106,0.15)", padding: "1px 6px", borderRadius: 4, whiteSpace: "nowrap", marginTop: 2 }}>{e.k}</span>
            <p style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", lineHeight: 1.6, fontFamily: mono }}>{e.v}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function SlackDemo() {
  return (
    <div style={{ border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, overflow: "hidden", background: "#0c0c0c" }}>
      <WinBar title="Slack · #engineering" />
      <div style={{ padding: "18px 22px", display: "flex", flexDirection: "column", gap: 16, fontFamily: mono, fontSize: 12 }}>
        <div style={{ display: "flex", gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 6, background: "rgba(106,171,122,0.1)", border: "1px solid rgba(255,255,255,0.05)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <span style={{ color: C.green, fontWeight: 700, fontSize: 11 }}>K</span>
          </div>
          <div>
            <p style={{ marginBottom: 3 }}><span style={{ color: C.text, fontWeight: 600 }}>kira</span><span style={{ color: C.faint, fontSize: 10, marginLeft: 8 }}>9:14 AM</span></p>
            <p style={{ color: "rgba(255,255,255,0.75)" }}>/nimbus fix the rate limiting bug on /api/upload</p>
          </div>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 6, background: "rgba(196,169,106,0.08)", border: "1px solid rgba(196,169,106,0.15)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <span style={{ color: C.gold, fontWeight: 700, fontSize: 11 }}>N</span>
          </div>
          <div>
            <p style={{ marginBottom: 3 }}>
              <span style={{ color: C.gold, fontWeight: 600 }}>Nimbus</span>
              <span style={{ color: C.faint, background: "rgba(255,255,255,0.04)", fontSize: 9, padding: "1px 5px", borderRadius: 3, marginLeft: 6 }}>APP</span>
              <span style={{ color: C.faint, fontSize: 10, marginLeft: 6 }}>9:14 AM</span>
            </p>
            <p style={{ color: "rgba(255,255,255,0.6)", lineHeight: 1.9 }}>
              {"On it. Cloning "}<span style={{ color: "rgba(255,255,255,0.8)" }}>acme/api</span>{"..."}<br />
              {"PR opened "}<span style={{ color: C.gold }}>github.com/acme/api/pull/52</span><br />
              <span style={{ color: "rgba(255,255,255,0.3)" }}>{"Self-review: APPROVE · done in 22.7s"}</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Stage({ children }: { children: ReactNode }) {
  return (
    <div style={{ background: "#141210", borderRadius: 16, padding: "28px", border: "1px solid rgba(255,255,255,0.07)" }}>
      {children}
    </div>
  );
}

const divider = { height: 1, background: "rgba(255,255,255,0.05)", maxWidth: W, margin: "0 auto" } as const;

export default function Page() {
  const isMobile = useIsMobile();
  const px = isMobile ? 20 : 28;

  return (
    <div style={{ background: C.bg, color: C.text, minHeight: "100vh", fontFamily: sans, overflowX: "hidden" }}>

      {/* HERO */}
      <section style={{ paddingTop: isMobile ? 100 : 140, paddingBottom: 0, paddingLeft: px, paddingRight: px }}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <div style={{ maxWidth: isMobile ? "100%" : 520, marginBottom: 56 }}>
            <h1 style={{ fontFamily: serif, fontSize: isMobile ? 30 : 40, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 20, color: C.text }}>
              {"Autonomous software engineering, "}
              <em style={{ fontStyle: "italic" }}>stratified.</em>
            </h1>
            <p style={{ fontFamily: sans, fontSize: 16, color: C.muted, lineHeight: 1.65, marginBottom: 32 }}>
              Nimbus plans, implements, and reviews code against real repositories entirely on its own. From task description to merged PR.
            </p>
            <a href="/download" style={{ display: "inline-flex", alignItems: "center", gap: 8, fontFamily: sans, fontSize: 15, fontWeight: 600, color: C.bg, background: C.text, padding: "12px 28px", borderRadius: 999, textDecoration: "none" }}>
              Get started free ↓
            </a>
          </div>
          <Terminal />
        </div>
      </section>

      {/* LOGOS */}
      <div style={{ borderTop: "1px solid rgba(255,255,255,0.05)", borderBottom: "1px solid rgba(255,255,255,0.05)", padding: isMobile ? "28px 20px" : "28px 28px", marginTop: 72 }}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.18)", textAlign: "center", marginBottom: 24, letterSpacing: "0.07em", textTransform: "uppercase" }}>Works with your stack</p>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: isMobile ? 28 : 44, flexWrap: "wrap" }}>
            {([
              { name: "GitHub",    slug: "github" },
              { name: "Linear",    slug: "linear" },
              { name: "Slack",     slug: "slack" },
              { name: "Railway",   slug: "railway" },
              { name: "VS Code",   slug: "vscode" },
              { name: "PagerDuty", slug: "pagerduty" },
              { name: "Anthropic", slug: "anthropic" },
            ] as { name: string; slug: string }[]).map(({ name, slug }) => (
              <div key={name} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, opacity: 0.35 }}>
                <img src={`https://cdn.simpleicons.org/${slug}/ffffff`} alt={name} width={22} height={22} onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
                <span style={{ fontFamily: mono, fontSize: isMobile ? 9 : 10, color: "rgba(255,255,255,0.5)", letterSpacing: "0.04em" }}>{name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* USE NIMBUS EVERYWHERE */}
      <section id="product" style={{ padding: isMobile ? "60px 20px" : "100px 28px" }}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <FadeUp>
            <h2 style={{ fontFamily: serif, fontSize: 34, fontWeight: 400, letterSpacing: "-0.02em", marginBottom: 8, color: C.text }}>Use Nimbus everywhere you work</h2>
            <p style={{ fontFamily: sans, fontSize: 16, color: C.muted, marginBottom: 48 }}>A unified engineering agent across every surface.</p>
          </FadeUp>
          <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(2,1fr)", gap: 12 }}>

            {/* Terminal card */}
            <FadeUp delay={0}>
              <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, overflow: "hidden", background: "#0d0d0d", display: "flex", flexDirection: "column", height: "100%" }}>
                <div style={{ background: "#0a0a0a", padding: "20px 18px 0", minHeight: 240, overflow: "hidden" }}>
                  <div style={{ background: "#0c0c0c", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px 8px 0 0", overflow: "hidden" }}>
                    <WinBar title="nimbus · zsh" />
                    <div style={{ padding: "14px 16px", fontFamily: mono, fontSize: 11, lineHeight: 1.8 }}>
                      <div style={{ color: C.gold, fontSize: 13, fontWeight: 700, letterSpacing: "0.15em", marginBottom: 8, fontFamily: mono }}>
                        NIMBUS
                      </div>
                      <div style={{ color: "rgba(255,255,255,0.2)", fontSize: 10, marginBottom: 8 }}>autonomous software engineering · v1.1.0</div>
                      <div style={{ color: "rgba(255,255,255,0.25)", fontSize: 10 }}>repo{"   "}github.com/acme/api</div>
                      <div style={{ color: "rgba(255,255,255,0.25)", fontSize: 10 }}>branch{"  "}main · <span style={{ color: C.green }}>ready</span></div>
                      <div style={{ marginTop: 10, color: "rgba(255,255,255,0.1)", fontSize: 10 }}>{"────────────────────────"}</div>
                      <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 6 }}>
                        <span style={{ color: C.gold, fontSize: 11 }}>nimbus</span>
                        <span style={{ color: "rgba(255,255,255,0.2)" }}>›</span>
                        <span style={{ display: "inline-block", width: 6, height: 12, background: "rgba(255,255,255,0.5)", animation: "blink 1s step-end infinite" }} />
                      </div>
                    </div>
                  </div>
                </div>
                <div style={{ padding: "22px 22px 24px" }}>
                  <p style={{ fontFamily: sans, fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 8 }}>Terminal</p>
                  <p style={{ fontFamily: sans, fontSize: 13, color: C.muted, lineHeight: 1.65, marginBottom: 18 }}>Run agents in any terminal. Interactive REPL with live diffs, voice input, session replay, and ambient watch mode.</p>
                  <div style={{ background: "#111", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 8, padding: "8px 14px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <code style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.5)" }}>pip install nimbus-ai</code>
                    <span style={{ fontFamily: mono, fontSize: 10, color: "rgba(255,255,255,0.2)" }}>↗</span>
                  </div>
                </div>
              </div>
            </FadeUp>

            {/* VS Code card */}
            <FadeUp delay={80}>
              <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, overflow: "hidden", background: "#0d0d0d", display: "flex", flexDirection: "column", height: "100%" }}>
                <div style={{ background: "#0a0a0a", padding: "20px 18px 0", minHeight: 240, overflow: "hidden" }}>
                  <div style={{ background: "#0c0c0c", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px 8px 0 0", overflow: "hidden" }}>
                    <WinBar title="Nimbus" />
                    <div style={{ padding: "12px 14px", fontFamily: mono, fontSize: 11 }}>
                      {([
                        { label: "Clone",     done: true,  active: false },
                        { label: "Index",     done: true,  active: false },
                        { label: "Plan",      done: true,  active: false },
                        { label: "Implement", done: false, active: true  },
                        { label: "Verify",    done: false, active: false },
                        { label: "PR",        done: false, active: false },
                      ] as { label: string; done: boolean; active: boolean }[]).map((p, i) => (
                        <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                          <div style={{ width: 6, height: 6, borderRadius: "50%", background: p.done ? C.green : p.active ? C.gold : "rgba(255,255,255,0.1)", flexShrink: 0 }} />
                          <span style={{ fontSize: 11, color: p.done ? "rgba(255,255,255,0.4)" : p.active ? "#FAFAFA" : "rgba(255,255,255,0.15)" }}>{p.label}</span>
                          {p.active && <span style={{ fontSize: 10, color: C.gold }}>writing files...</span>}
                        </div>
                      ))}
                      <div style={{ marginTop: 10, padding: "6px 10px", background: "rgba(255,255,255,0.03)", borderRadius: 5, border: "1px solid rgba(255,255,255,0.06)" }}>
                        <span style={{ color: C.green, fontSize: 10 }}>write </span>
                        <span style={{ color: "rgba(255,255,255,0.4)", fontSize: 10 }}>src/middleware/auth.ts +18</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div style={{ padding: "22px 22px 24px" }}>
                  <p style={{ fontFamily: sans, fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 8 }}>VS Code / Cursor</p>
                  <p style={{ fontFamily: sans, fontSize: 13, color: C.muted, lineHeight: 1.65, marginBottom: 18 }}>Right-click any file and run Nimbus. Phase timeline and live logs stream directly in the editor panel.</p>
                  <a href="https://github.com/arpjw/nimbus-vscode" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", alignItems: "center", gap: 6, fontFamily: sans, fontSize: 13, fontWeight: 500, color: C.bg, background: C.text, padding: "8px 18px", borderRadius: 999, textDecoration: "none" }}>
                    Install extension →
                  </a>
                </div>
              </div>
            </FadeUp>

            {/* Web card */}
            <FadeUp delay={160}>
              <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, overflow: "hidden", background: "#0d0d0d", display: "flex", flexDirection: "column", height: "100%" }}>
                <div style={{ background: "#0a0a0a", padding: "20px 18px 0", minHeight: 240, overflow: "hidden" }}>
                  <div style={{ background: "#0c0c0c", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px 8px 0 0", overflow: "hidden" }}>
                    <WinBar title="get-nimbus.com/dashboard" />
                    <div style={{ padding: "12px 14px", fontFamily: sans, fontSize: 11 }}>
                      {([
                        { task: "migrate auth to JWT",          status: "done",    time: "2m ago" },
                        { task: "add rate limiting to /upload", status: "done",    time: "18m ago" },
                        { task: "generate integration tests",   status: "running", time: "now" },
                        { task: "OWASP security audit",          status: "queued",  time: "..." },
                      ] as { task: string; status: string; time: string }[]).map((t, i) => (
                        <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 6px", borderRadius: 5, marginBottom: 3, background: t.status === "running" ? "rgba(196,169,106,0.05)" : "transparent", border: t.status === "running" ? "1px solid rgba(196,169,106,0.1)" : "1px solid transparent" }}>
                          <div style={{ width: 6, height: 6, borderRadius: "50%", flexShrink: 0, background: t.status === "done" ? C.green : t.status === "running" ? C.gold : "rgba(255,255,255,0.1)" }} />
                          <span style={{ fontSize: 11, color: t.status === "done" ? "rgba(255,255,255,0.35)" : t.status === "running" ? "#FAFAFA" : "rgba(255,255,255,0.2)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.task}</span>
                          <span style={{ fontFamily: mono, fontSize: 9, color: "rgba(255,255,255,0.2)", flexShrink: 0 }}>{t.time}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div style={{ padding: "22px 22px 24px" }}>
                  <p style={{ fontFamily: sans, fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 8 }}>Web</p>
                  <p style={{ fontFamily: sans, fontSize: 13, color: C.muted, lineHeight: 1.65, marginBottom: 18 }}>Trigger tasks from your browser, phone, or Slack. Dashboard shows live task history, memory, and PR results.</p>
                  <a href="https://get-nimbus.com/dashboard" style={{ display: "inline-flex", alignItems: "center", gap: 6, fontFamily: sans, fontSize: 13, fontWeight: 500, color: C.bg, background: C.text, padding: "8px 18px", borderRadius: 999, textDecoration: "none" }}>
                    Open dashboard →
                  </a>
                </div>
              </div>
            </FadeUp>

            {/* Chrome Extension card */}
            <FadeUp delay={240}>
              <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, overflow: "hidden", background: "#0d0d0d", display: "flex", flexDirection: "column", height: "100%" }}>
                <div style={{ background: "#0a0a0a", padding: "20px 18px 0", minHeight: 240, overflow: "hidden" }}>
                  <div style={{ background: "#0c0c0c", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px 8px 0 0", overflow: "hidden" }}>
                    <WinBar title="github.com / acme / api / pull / 52" />
                    <div style={{ padding: "12px 14px", fontFamily: mono, fontSize: 11 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                        <div style={{ width: 16, height: 16, borderRadius: 4, background: "rgba(10,10,10,0.9)", border: "1px solid rgba(255,255,255,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                          <span style={{ color: "#FAFAFA", fontWeight: 800, fontSize: 9 }}>N</span>
                        </div>
                        <span style={{ color: C.muted, fontSize: 11 }}>Review with Nimbus</span>
                        <span style={{ marginLeft: "auto", color: C.gold, fontSize: 10 }}>clicked</span>
                      </div>
                      {[
                        { label: "submitted", done: true },
                        { label: "indexing", done: true },
                        { label: "reviewing", active: true },
                        { label: "commenting", done: false },
                      ].map((p, i) => (
                        <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                          <div style={{ width: 6, height: 6, borderRadius: "50%", background: p.done ? C.green : (p as any).active ? C.gold : "rgba(255,255,255,0.1)", flexShrink: 0 }} />
                          <span style={{ fontSize: 11, color: p.done ? "rgba(255,255,255,0.4)" : (p as any).active ? "#FAFAFA" : "rgba(255,255,255,0.15)" }}>{p.label}</span>
                          {(p as any).active && <span style={{ fontSize: 10, color: C.gold }}>analyzing diff...</span>}
                        </div>
                      ))}
                      <div style={{ marginTop: 10, padding: "6px 10px", background: "rgba(255,255,255,0.03)", borderRadius: 5, border: "1px solid rgba(255,255,255,0.06)" }}>
                        <span style={{ color: C.gold, fontSize: 10 }}>review </span>
                        <span style={{ color: "rgba(255,255,255,0.4)", fontSize: 10 }}>posted as PR comment</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div style={{ padding: "22px 22px 24px" }}>
                  <p style={{ fontFamily: sans, fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 8 }}>Chrome Extension</p>
                  <p style={{ fontFamily: sans, fontSize: 13, color: C.muted, lineHeight: 1.65, marginBottom: 18 }}>One button on every GitHub PR and issue. Review any PR or implement any issue without leaving your browser.</p>
                  <a href="https://github.com/arpjw/nimbus-chrome" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", alignItems: "center", gap: 6, fontFamily: sans, fontSize: 13, fontWeight: 500, color: C.bg, background: C.text, padding: "8px 18px", borderRadius: 999, textDecoration: "none" }}>
                    Install extension →
                  </a>
                </div>
              </div>
            </FadeUp>
          </div>
        </div>
      </section>

      <div style={divider} />

      {/* FEATURE 1 */}
      <section style={{ padding: isMobile ? "60px 20px" : "120px 28px" }}>
        <div style={{ maxWidth: W, margin: "0 auto", display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1.5fr", gap: isMobile ? 32 : 80, alignItems: "center" }}>
          <FadeUp>
            <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>Issues → pull requests</p>
            <h2 style={{ fontFamily: serif, fontSize: 36, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 16, color: C.text }}>
              {"Agents turn ideas"}
              <br />
              <em style={{ fontStyle: "italic" }}>into code.</em>
            </h2>
            <p style={{ fontFamily: sans, fontSize: 15, color: C.muted, lineHeight: 1.7, marginBottom: 22 }}>
              Describe a task. Nimbus clones the repo, retrieves context, plans, implements, verifies, and opens a pull request.
            </p>
            <a href="https://docs.get-nimbus.com" style={{ fontFamily: sans, fontSize: 14, color: C.gold, textDecoration: "none" }}>Learn about agentic development →</a>
          </FadeUp>
          <FadeUp delay={100}><Stage><PRDemo /></Stage></FadeUp>
        </div>
      </section>

      <div style={divider} />

      {/* FEATURE 2 */}
      <section style={{ padding: isMobile ? "60px 20px" : "120px 28px", background: "#080808" }}>
        <div style={{ maxWidth: W, margin: "0 auto", display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1.5fr 1fr", gap: isMobile ? 32 : 80, alignItems: "center" }}>
          <div style={{ order: isMobile ? 2 : 1 }}>
            <FadeUp><Stage><MemoryDemo /></Stage></FadeUp>
          </div>
          <div style={{ order: isMobile ? 1 : 2 }}>
            <FadeUp delay={100}>
              <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>Persistent memory</p>
              <h2 style={{ fontFamily: serif, fontSize: 36, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 16, color: C.text }}>
                {"Gets smarter"}
                <br />
                <em style={{ fontStyle: "italic" }}>every run.</em>
              </h2>
              <p style={{ fontFamily: sans, fontSize: 15, color: C.muted, lineHeight: 1.7, marginBottom: 22 }}>
                After every task, Nimbus writes a memory entry capturing conventions, patterns, and outcomes. Future tasks retrieve this context automatically.
              </p>
              <a href="https://docs.get-nimbus.com/terminal/memory" style={{ fontFamily: sans, fontSize: 14, color: C.gold, textDecoration: "none" }}>Learn about codebase memory →</a>
            </FadeUp>
          </div>
        </div>
      </section>

      <div style={divider} />

      {/* FEATURE 3 */}
      <section style={{ padding: isMobile ? "60px 20px" : "120px 28px" }}>
        <div style={{ maxWidth: W, margin: "0 auto", display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1.5fr", gap: isMobile ? 32 : 80, alignItems: "center" }}>
          <FadeUp>
            <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>In every tool, at every step</p>
            <h2 style={{ fontFamily: serif, fontSize: 36, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 16, color: C.text }}>
              {"Runs in your terminal,"}
              <br />
              <em style={{ fontStyle: "italic" }}>responds in Slack.</em>
            </h2>
            <p style={{ fontFamily: sans, fontSize: 15, color: C.muted, lineHeight: 1.7, marginBottom: 22 }}>
              {"Comment "}
              <code style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.6)", background: "rgba(255,255,255,0.06)", padding: "1px 6px", borderRadius: 4 }}>/nimbus</code>
              {" on any GitHub issue or PR. Trigger from Slack. Nimbus runs wherever your team already works."}
            </p>
            <a href="https://docs.get-nimbus.com/integrations/slack" style={{ fontFamily: sans, fontSize: 14, color: C.gold, textDecoration: "none" }}>Learn about integrations →</a>
          </FadeUp>
          <FadeUp delay={100}><Stage><SlackDemo /></Stage></FadeUp>
        </div>
      </section>

      <div style={divider} />

      {/* CAPABILITY CARDS */}
      <section style={{ padding: isMobile ? "60px 20px" : "120px 28px", background: "#080808" }}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <FadeUp>
            <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 12 }}>Stay on the frontier</p>
          </FadeUp>
          <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(3,1fr)", gap: 1, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 12, overflow: "hidden" }}>
            {([
              { h: "Use the best model for every task", b: "Claude Opus for planning, Claude Sonnet for implementation. Auto mode picks the right model per phase.", l: "Explore models" },
              { h: "Complete codebase understanding", b: "voyage-code-2 embeddings fused with BM25 via RRF. AST-aware chunking. Multi-repo workspace support.", l: "Learn about retrieval" },
              { h: "Develop enduring software", b: "Self-improving reviewer learns from PR feedback. 20 built-in agents for security, testing, docs, and performance. MIT licensed.", l: "Explore agents" },
            ] as { h: string; b: string; l: string }[]).map((card, i) => (
              <FadeUp key={i} delay={i * 60}>
                <div style={{ background: C.bg, padding: "28px" }}>
                  <h3 style={{ fontFamily: sans, fontSize: 14, fontWeight: 600, marginBottom: 10, lineHeight: 1.35, color: "rgba(255,255,255,0.7)" }}>{card.h}</h3>
                  <p style={{ fontFamily: sans, fontSize: 13, color: "rgba(255,255,255,0.35)", lineHeight: 1.7, marginBottom: 14 }}>{card.b}</p>
                  <a href="https://docs.get-nimbus.com" style={{ fontFamily: sans, fontSize: 13, color: "rgba(255,255,255,0.3)", textDecoration: "none" }}>{card.l} →</a>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      <div style={divider} />

      {/* CHANGELOG */}
      <section id="changelog" style={{ padding: isMobile ? "60px 20px" : "120px 28px" }}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <FadeUp>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 36 }}>
              <h2 style={{ fontFamily: serif, fontSize: 28, fontWeight: 400, letterSpacing: "-0.015em" }}>Changelog</h2>
              <a href="https://github.com/arpjw/nimbus/commits/main" target="_blank" rel="noopener noreferrer" style={{ fontFamily: sans, fontSize: 13, color: C.faint, textDecoration: "none" }}>See all →</a>
            </div>
          </FadeUp>
          <FadeUp delay={60}>
            <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr 1fr" : "repeat(4,1fr)", gap: isMobile ? 8 : 10 }}>
              {([
                { v: "1.2", d: "Apr 26, 2026", t: "nimbus chat, diff, search, pre-commit hooks" },
                { v: "1.2", d: "Apr 26, 2026", t: "Chrome Extension, GitHub Actions, SDKs" },
                { v: "1.1", d: "Apr 26, 2026", t: "Interactive terminal + 20 built-in agents" },
                { v: "1.0", d: "Apr 25, 2026", t: "Self-improving PR reviewer + GitHub App" },
              ] as { v: string; d: string; t: string }[]).map((entry, i) => (
                <div key={i} style={{ border: "1px solid rgba(255,255,255,0.06)", borderRadius: 10, padding: "18px 20px", background: "#080808" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                    <span style={{ fontFamily: mono, fontSize: 10, color: C.faint, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)", padding: "2px 8px", borderRadius: 999 }}>v{entry.v}</span>
                    <span style={{ fontFamily: mono, fontSize: 10, color: "rgba(255,255,255,0.2)" }}>{entry.d}</span>
                  </div>
                  <p style={{ fontFamily: sans, fontSize: 13, fontWeight: 500, color: C.muted, lineHeight: 1.4 }}>{entry.t}</p>
                </div>
              ))}
            </div>
          </FadeUp>
        </div>
      </section>

      <div style={divider} />

      {/* CTA */}
      <section style={{ padding: isMobile ? "80px 20px" : "160px 28px" }}>
        <FadeUp>
          <div style={{ maxWidth: W, margin: "0 auto", textAlign: "center" }}>
            <h2 style={{ fontFamily: serif, fontSize: isMobile ? 38 : 56, fontWeight: 400, letterSpacing: "-0.025em", lineHeight: 1.05, color: C.text, marginBottom: 40 }}>
              {"Try Nimbus "}
              <em style={{ fontStyle: "italic" }}>now.</em>
            </h2>
            <div style={{ display: "flex", gap: 12, justifyContent: "center", marginBottom: 20, flexDirection: isMobile ? "column" : "row", alignItems: "center" }}>
              <a href="/download" style={{ fontFamily: sans, fontSize: 15, fontWeight: 600, color: C.bg, background: C.text, padding: "13px 32px", borderRadius: 999, textDecoration: "none" }}>Get started free ↓</a>
              <a href="https://docs.get-nimbus.com" style={{ fontFamily: sans, fontSize: 15, fontWeight: 500, color: C.muted, padding: "13px 24px", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 999, textDecoration: "none" }}>Read the docs</a>
            </div>
            <p style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.2)" }}>pip install nimbus-ai · Free tier · No credit card required</p>
          </div>
        </FadeUp>
      </section>

      <div style={divider} />

      {/* FOOTER */}
      <footer style={{ padding: isMobile ? "40px 20px" : "52px 28px" }}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "2fr 1fr 1fr 1fr", gap: isMobile ? 32 : 48, marginBottom: 40 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
                <div style={{ width: 18, height: 18, borderRadius: 4, background: C.text, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span style={{ color: C.bg, fontWeight: 800, fontSize: 9, fontFamily: sans }}>N</span>
                </div>
                <span style={{ fontFamily: serif, fontStyle: "italic", fontSize: 16, color: C.text }}>Nimbus</span>
              </div>
              <p style={{ fontFamily: sans, fontSize: 13, color: "rgba(255,255,255,0.3)", lineHeight: 1.65, maxWidth: 220 }}>Autonomous software engineering. From task description to merged pull request.</p>
            </div>
            {([
              { title: "Product", links: [["Dashboard", "https://get-nimbus.com/dashboard"], ["Marketplace", "https://get-nimbus.com/marketplace"], ["Prism", "https://get-nimbus.com/prism"], ["Mobile App", "https://get-nimbus.com/app"], ["API", "https://api.get-nimbus.com/docs"]] },
              { title: "Resources", links: [["Docs", "https://docs.get-nimbus.com"], ["Changelog", "#changelog"], ["PyPI", "https://pypi.org/project/nimbus-ai"], ["Status", "https://api.get-nimbus.com/health"]] },
              { title: "Connect", links: [["GitHub", "https://github.com/arpjw/nimbus"], ["Chrome Extension", "https://github.com/arpjw/nimbus-chrome"], ["VS Code", "https://github.com/arpjw/nimbus-vscode"], ["aryasomu.com", "https://aryasomu.com"]] },
            ] as { title: string; links: [string, string][] }[]).map(col => (
              <div key={col.title}>
                <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.2)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>{col.title}</p>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {col.links.map(([label, href]) => (
                    <a key={label} href={href} style={{ fontFamily: sans, fontSize: 13, color: "rgba(255,255,255,0.35)", textDecoration: "none" }}>{label}</a>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", paddingTop: 20, borderTop: "1px solid rgba(255,255,255,0.05)" }}>
            <p style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.2)" }}>© 2026 Nimbus · MIT License</p>
            <p style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.2)" }}>Built by <a href="https://aryasomu.com" style={{ color: "rgba(255,255,255,0.3)", textDecoration: "none" }}>Arya Somu</a></p>
          </div>
        </div>
      </footer>
    </div>
  );
}
