"use client";
import { useEffect, useState, useRef, ReactNode } from "react";
import { Github } from "lucide-react";

const serif = "var(--font-serif, 'Georgia', serif)";
const sans  = "var(--font-sans, system-ui, sans-serif)";
const mono  = "var(--font-mono, monospace)";

const C = {
  bg:      "#0A0A0A",
  surface: "#111111",
  border:  "rgba(255,255,255,0.06)",
  border2: "rgba(255,255,255,0.1)",
  text:    "#FAFAFA",
  muted:   "rgba(255,255,255,0.5)",
  faint:   "rgba(255,255,255,0.25)",
  gold:    "#c4a96a",
  green:   "#6aab7a",
  term:    "#0c0c0c",
};

/* ─── Fade on scroll ─── */
function FadeUp({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [vis, setVis] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVis(true); obs.disconnect(); } }, { threshold: 0.1 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return (
    <div ref={ref} style={{ opacity: vis ? 1 : 0, transform: vis ? "translateY(0)" : "translateY(24px)", transition: `opacity 0.6s ease ${delay}ms, transform 0.6s ease ${delay}ms` }}>
      {children}
    </div>
  );
}

/* ─── Terminal ─── */
const LINES = [
  { d: 0,    t: "$ nimbus run 'migrate auth to JWT'",         c: C.text },
  { d: 700,  t: "",                                            c: "" },
  { d: 800,  t: "  cloning   github.com/acme/api",            c: "rgba(255,255,255,0.2)" },
  { d: 1400, t: "  indexing  847 files · 12,304 chunks",      c: "rgba(255,255,255,0.2)" },
  { d: 2100, t: "  planning  via claude opus...",              c: "rgba(255,255,255,0.2)" },
  { d: 2900, t: "",                                            c: "" },
  { d: 3000, t: "  plan",                                      c: "rgba(255,255,255,0.4)" },
  { d: 3200, t: "  ├─ modify  src/middleware/auth.ts",         c: "rgba(255,255,255,0.3)" },
  { d: 3350, t: "  ├─ modify  src/routes/login.ts",           c: "rgba(255,255,255,0.3)" },
  { d: 3500, t: "  └─ create  src/lib/jwt.ts",                c: "rgba(255,255,255,0.3)" },
  { d: 3700, t: "",                                            c: "" },
  { d: 3800, t: "  confidence  ████████░░  92%  ·  low ambiguity", c: C.gold },
  { d: 4400, t: "  Proceed with 3 changes? [y/N] y",          c: "rgba(255,255,255,0.5)" },
  { d: 5000, t: "",                                            c: "" },
  { d: 5100, t: "  write  src/lib/jwt.ts                +42", c: C.green },
  { d: 5400, t: "  write  src/middleware/auth.ts        +18", c: C.green },
  { d: 5700, t: "  write  src/routes/login.ts           +9",  c: C.green },
  { d: 6200, t: "",                                            c: "" },
  { d: 6300, t: "  tsc ✓   eslint ✓",                         c: "rgba(255,255,255,0.4)" },
  { d: 6800, t: "  PR #47 opened  ↗  acme/api/pull/47",       c: C.text },
  { d: 7400, t: "  done in 18.4s",                            c: "rgba(255,255,255,0.3)" },
];

function Terminal() {
  const [vis, setVis] = useState<number[]>([]);
  useEffect(() => {
    const t = LINES.map((_, i) => setTimeout(() => setVis(v => [...v, i]), LINES[i].d));
    return () => t.forEach(clearTimeout);
  }, []);
  return (
    <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10, overflow: "hidden", background: C.term }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 16px", borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(255,255,255,0.02)" }}>
        <div style={{ width: 11, height: 11, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
        <div style={{ width: 11, height: 11, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
        <div style={{ width: 11, height: 11, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
        <span style={{ marginLeft: 10, fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.2)" }}>nimbus — zsh</span>
      </div>
      <div style={{ padding: "22px 28px", fontFamily: mono, fontSize: 13, lineHeight: 1.75, minHeight: 360 }}>
        {LINES.map((l, i) => vis.includes(i) ? (
          <div key={i} style={{ color: l.c, minHeight: l.t ? undefined : 12 }}>{l.t}</div>
        ) : null)}
        {vis.length < LINES.length && (
          <span style={{ display: "inline-block", width: 7, height: 13, background: "rgba(255,255,255,0.5)", verticalAlign: "middle", animation: "blink 1s step-end infinite" }} />
        )}
        <style>{`@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}`}</style>
      </div>
    </div>
  );
}

/* ─── Demo frames ─── */
function DemoFrame({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, overflow: "hidden", background: C.surface }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 16px", borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(255,255,255,0.02)" }}>
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
        <span style={{ marginLeft: 10, fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.2)" }}>{title}</span>
      </div>
      {children}
    </div>
  );
}

function PRDemo() {
  return (
    <DemoFrame title="github.com / acme / api / pull / 47">
      <div style={{ padding: "18px 22px" }}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 16 }}>
          <span style={{ fontSize: 11, fontFamily: mono, padding: "2px 10px", borderRadius: 999, border: "1px solid rgba(106,171,122,0.3)", background: "rgba(106,171,122,0.08)", color: C.green, whiteSpace: "nowrap", marginTop: 2 }}>Open</span>
          <div>
            <p style={{ fontSize: 14, fontWeight: 600, color: "#FAFAFA", lineHeight: 1.4, fontFamily: sans }}>Migrate auth middleware to JWT</p>
            <p style={{ fontSize: 12, color: C.muted, marginTop: 4, fontFamily: mono }}>nimbus-bot · 2 minutes ago · 3 files changed</p>
          </div>
        </div>
        {[["src/lib/jwt.ts", "+42", C.green], ["src/middleware/auth.ts", "+18 −31", C.muted], ["src/routes/login.ts", "+9 −4", C.muted]].map(([f, s, col]) => (
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
    </DemoFrame>
  );
}

function MemoryDemo() {
  const entries = [
    { k: "convention", v: "Uses Zod for all request validation. Never Joi." },
    { k: "testing",    v: "pytest only. Fixtures in conftest.py. No unittest." },
    { k: "auth",       v: "JWT + Redis refresh tokens, migrated in PR #47." },
    { k: "patterns",   v: "Functional middleware — avoid class-based handlers." },
  ];
  return (
    <DemoFrame title="nimbus memory · acme/api">
      <div style={{ padding: "14px 18px", display: "flex", flexDirection: "column", gap: 7 }}>
        {entries.map((e, i) => (
          <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start", padding: "9px 10px", borderRadius: 6, border: "1px solid rgba(255,255,255,0.05)", background: "rgba(255,255,255,0.02)" }}>
            <span style={{ fontFamily: mono, fontSize: 10, color: C.gold, background: "rgba(196,169,106,0.08)", border: "1px solid rgba(196,169,106,0.15)", padding: "1px 6px", borderRadius: 4, whiteSpace: "nowrap", marginTop: 2 }}>{e.k}</span>
            <p style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", lineHeight: 1.6, fontFamily: mono }}>{e.v}</p>
          </div>
        ))}
      </div>
    </DemoFrame>
  );
}

function SlackDemo() {
  return (
    <DemoFrame title="Slack — #engineering">
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
            <p style={{ marginBottom: 3 }}><span style={{ color: C.gold, fontWeight: 600 }}>Nimbus</span><span style={{ color: C.faint, background: "rgba(255,255,255,0.04)", fontSize: 9, padding: "1px 5px", borderRadius: 3, marginLeft: 6 }}>APP</span><span style={{ color: C.faint, fontSize: 10, marginLeft: 6 }}>9:14 AM</span></p>
            <p style={{ color: "rgba(255,255,255,0.6)", lineHeight: 1.9 }}>On it. Cloning <span style={{ color: "rgba(255,255,255,0.8)" }}>acme/api</span>...<br />PR opened <span style={{ color: C.gold }}>github.com/acme/api/pull/52</span><br /><span style={{ color: "rgba(255,255,255,0.3)" }}>Self-review: APPROVE · done in 22.7s</span></p>
          </div>
        </div>
      </div>
    </DemoFrame>
  );
}

/* ─── Navbar ─── */
function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", fn);
    return () => window.removeEventListener("scroll", fn);
  }, []);
  return (
    <nav style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 100, height: 56, borderBottom: `1px solid ${scrolled ? "rgba(255,255,255,0.06)" : "transparent"}`, background: scrolled ? "rgba(10,10,10,0.85)" : "transparent", backdropFilter: scrolled ? "blur(16px)" : "none", transition: "all 0.3s ease" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "0 28px", height: "100%", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
            <div style={{ width: 22, height: 22, borderRadius: 5, background: C.text, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ color: C.bg, fontWeight: 800, fontSize: 12, fontFamily: sans }}>N</span>
            </div>
            <span style={{ fontWeight: 400, fontSize: 17, fontStyle: "italic", color: C.text, fontFamily: serif }}>Nimbus</span>
          </div>
          <div style={{ display: "flex", gap: 32 }}>
            {[["Product", "/#product"], ["Docs", "https://docs.get-nimbus.com"], ["GitHub", "https://github.com/arpjw/nimbus"]].map(([l, h]) => (
              <a key={l} href={h} style={{ fontFamily: sans, fontSize: 14, color: C.muted, textDecoration: "none" }}>{l}</a>
            ))}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <a href="https://api.get-nimbus.com/keys/generate" style={{ fontFamily: sans, fontSize: 14, color: C.muted, textDecoration: "none" }}>Sign in</a>
          <a href="https://api.get-nimbus.com/keys/generate" style={{ fontFamily: sans, fontSize: 14, fontWeight: 600, color: C.bg, background: C.text, padding: "8px 20px", borderRadius: 999, textDecoration: "none" }}>Get started</a>
        </div>
      </div>
    </nav>
  );
}

const W = 1100;
const sec = (extra = {}) => ({ padding: "120px 28px", ...extra });
const divider = { height: 1, background: "rgba(255,255,255,0.05)", maxWidth: W, margin: "0 auto" };

export default function Page() {
  return (
    <div style={{ background: C.bg, color: C.text, minHeight: "100vh", fontFamily: sans, overflowX: "hidden" }}>
      <Navbar />

      {/* ── HERO ── */}
      <section style={{ paddingTop: 140, paddingBottom: 0, paddingLeft: 28, paddingRight: 28 }}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <div style={{ maxWidth: 520, marginBottom: 56 }}>
            <h1 style={{ fontFamily: serif, fontSize: 40, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 20, color: C.text }}>
              Autonomous software engineering,{" "}
              <em style={{ fontStyle: "italic" }}>stratified.</em>
            </h1>
            <p style={{ fontFamily: sans, fontSize: 16, color: C.muted, lineHeight: 1.65, marginBottom: 32 }}>
              Nimbus plans, implements, and reviews code against real repositories — entirely on its own. From task description to merged PR.
            </p>
            <a href="https://api.get-nimbus.com/keys/generate"
              style={{ display: "inline-flex", alignItems: "center", gap: 8, fontFamily: sans, fontSize: 15, fontWeight: 600, color: C.bg, background: C.text, padding: "12px 28px", borderRadius: 999, textDecoration: "none" }}>
              Get started free ↓
            </a>
          </div>
          <Terminal />
        </div>
      </section>

      {/* ── LOGOS ── */}
      <div style={{ borderTop: "1px solid rgba(255,255,255,0.05)", borderBottom: "1px solid rgba(255,255,255,0.05)", padding: "28px 28px", marginTop: 72 }}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.18)", textAlign: "center", marginBottom: 24, letterSpacing: "0.07em", textTransform: "uppercase" }}>Works with your stack</p>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 44, flexWrap: "wrap" }}>
            {[
              { name: "GitHub",    slug: "github" },
              { name: "Linear",    slug: "linear" },
              { name: "Slack",     slug: "slack" },
              { name: "Railway",   slug: "railway" },
              { name: "VS Code",   slug: "visualstudiocode" },
              { name: "PagerDuty", slug: "pagerduty" },
              { name: "Anthropic", slug: "anthropic" },
            ].map(({ name, slug }) => (
              <div key={name} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, opacity: 0.35 }}>
                <img
                  src={`https://cdn.simpleicons.org/${slug}/ffffff`}
                  alt={name}
                  width={22}
                  height={22}
                />
                <span style={{ fontFamily: mono, fontSize: 10, color: "rgba(255,255,255,0.5)", letterSpacing: "0.04em" }}>{name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>


      {/* ── USE NIMBUS EVERYWHERE ── */}
      <section style={{ padding: "100px 28px" }}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <FadeUp>
            <h2 style={{ fontFamily: serif, fontSize: 34, fontWeight: 400, letterSpacing: "-0.02em", marginBottom: 8, color: C.text }}>
              Use Nimbus everywhere you work
            </h2>
            <p style={{ fontFamily: sans, fontSize: 16, color: C.muted, marginBottom: 48 }}>
              A unified engineering agent across every surface.
            </p>
          </FadeUp>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12 }}>

            {/* Card 1: Terminal */}
            <FadeUp delay={0}>
              <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, overflow: "hidden", background: "#0d0d0d", display: "flex", flexDirection: "column" }}>
                {/* Screenshot area */}
                <div style={{ background: "#0a0a0a", padding: "20px 18px 0", borderBottom: "1px solid rgba(255,255,255,0.06)", minHeight: 240, position: "relative", overflow: "hidden" }}>
                  <div style={{ background: "#0c0c0c", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px 8px 0 0", overflow: "hidden" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "8px 12px", background: "rgba(255,255,255,0.02)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
                      <span style={{ fontFamily: mono, fontSize: 10, color: "rgba(255,255,255,0.2)", marginLeft: 8 }}>nimbus — zsh</span>
                    </div>
                    <div style={{ padding: "14px 16px", fontFamily: mono, fontSize: 11, lineHeight: 1.8 }}>
                      <div style={{ color: "#c4a96a", fontSize: 10, marginBottom: 6 }}>
                        {"  ██╗   ██╗██╗███╗   ███╗"}<br/>
                        {"  ╚██╗ ██╔╝██║████╗ ████║"}<br/>
                        {"   ╚████╔╝ ██║██╔████╔██║"}
                      </div>
                      <div style={{ color: "rgba(255,255,255,0.2)", fontSize: 10, marginBottom: 8 }}>autonomous software engineering · v1.1.0</div>
                      <div style={{ color: "rgba(255,255,255,0.25)", fontSize: 10 }}>repo &nbsp;&nbsp; github.com/acme/api</div>
                      <div style={{ color: "rgba(255,255,255,0.25)", fontSize: 10 }}>branch &nbsp;main · 847 files <span style={{ color: "#6aab7a" }}>ready</span></div>
                      <div style={{ marginTop: 10, color: "rgba(255,255,255,0.15)", fontSize: 10 }}>────────────────────────</div>
                      <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 6 }}>
                        <span style={{ color: "#c4a96a", fontSize: 11 }}>nimbus</span>
                        <span style={{ color: "rgba(255,255,255,0.2)", fontSize: 11 }}>›</span>
                        <span style={{ display: "inline-block", width: 6, height: 12, background: "rgba(255,255,255,0.5)", animation: "blink 1s step-end infinite" }} />
                      </div>
                    </div>
                  </div>
                </div>
                {/* Card body */}
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

            {/* Card 2: VS Code */}
            <FadeUp delay={80}>
              <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, overflow: "hidden", background: "#0d0d0d", display: "flex", flexDirection: "column" }}>
                <div style={{ background: "#0a0a0a", padding: "20px 18px 0", borderBottom: "1px solid rgba(255,255,255,0.06)", minHeight: 240, overflow: "hidden" }}>
                  <div style={{ background: "#0c0c0c", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px 8px 0 0", overflow: "hidden" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "8px 12px", background: "rgba(255,255,255,0.02)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
                      <span style={{ fontFamily: mono, fontSize: 10, color: "rgba(255,255,255,0.2)", marginLeft: 8 }}>Nimbus</span>
                    </div>
                    <div style={{ padding: "12px 14px", fontFamily: mono, fontSize: 11 }}>
                      {/* Phase timeline */}
                      {[
                        { label: "Clone", done: true },
                        { label: "Index", done: true },
                        { label: "Plan", done: true },
                        { label: "Implement", active: true },
                        { label: "Verify", done: false },
                        { label: "PR", done: false },
                      ].map((p, i) => (
                        <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                          <div style={{ width: 6, height: 6, borderRadius: "50%", background: p.done ? "#6aab7a" : p.active ? "#c4a96a" : "rgba(255,255,255,0.1)", flexShrink: 0 }} />
                          <span style={{ fontSize: 11, color: p.done ? "rgba(255,255,255,0.4)" : p.active ? "#FAFAFA" : "rgba(255,255,255,0.15)" }}>{p.label}</span>
                          {p.active && <span style={{ fontSize: 10, color: "#c4a96a" }}>writing files...</span>}
                        </div>
                      ))}
                      <div style={{ marginTop: 10, padding: "6px 10px", background: "rgba(255,255,255,0.03)", borderRadius: 5, border: "1px solid rgba(255,255,255,0.06)" }}>
                        <span style={{ color: "#6aab7a", fontSize: 10 }}>write </span>
                        <span style={{ color: "rgba(255,255,255,0.4)", fontSize: 10 }}>src/middleware/auth.ts +18</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div style={{ padding: "22px 22px 24px" }}>
                  <p style={{ fontFamily: sans, fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 8 }}>VS Code / Cursor</p>
                  <p style={{ fontFamily: sans, fontSize: 13, color: C.muted, lineHeight: 1.65, marginBottom: 18 }}>Right-click any file and run Nimbus. Phase timeline and live logs stream directly in the editor panel.</p>
                  <a href="https://github.com/arpjw/nimbus-vscode" target="_blank" rel="noopener noreferrer"
                    style={{ display: "inline-flex", alignItems: "center", gap: 6, fontFamily: sans, fontSize: 13, fontWeight: 500, color: C.bg, background: C.text, padding: "8px 18px", borderRadius: 999, textDecoration: "none" }}>
                    Install extension →
                  </a>
                </div>
              </div>
            </FadeUp>

            {/* Card 3: Web */}
            <FadeUp delay={160}>
              <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, overflow: "hidden", background: "#0d0d0d", display: "flex", flexDirection: "column" }}>
                <div style={{ background: "#0a0a0a", padding: "20px 18px 0", borderBottom: "1px solid rgba(255,255,255,0.06)", minHeight: 240, overflow: "hidden" }}>
                  <div style={{ background: "#0c0c0c", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px 8px 0 0", overflow: "hidden" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "8px 12px", background: "rgba(255,255,255,0.02)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: "rgba(255,255,255,0.1)" }} />
                      <span style={{ fontFamily: mono, fontSize: 10, color: "rgba(255,255,255,0.2)", marginLeft: 8 }}>get-nimbus.com/dashboard</span>
                    </div>
                    <div style={{ padding: "12px 14px", fontFamily: sans, fontSize: 11 }}>
                      {/* Task list */}
                      {[
                        { task: "migrate auth to JWT", status: "done", time: "2m ago" },
                        { task: "add rate limiting to /upload", status: "done", time: "18m ago" },
                        { task: "generate integration tests", status: "running", time: "now" },
                        { task: "security audit — OWASP", status: "queued", time: "—" },
                      ].map((t, i) => (
                        <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 6px", borderRadius: 5, marginBottom: 3, background: t.status === "running" ? "rgba(196,169,106,0.05)" : "transparent", border: t.status === "running" ? "1px solid rgba(196,169,106,0.1)" : "1px solid transparent" }}>
                          <div style={{ width: 6, height: 6, borderRadius: "50%", flexShrink: 0, background: t.status === "done" ? "#6aab7a" : t.status === "running" ? "#c4a96a" : "rgba(255,255,255,0.1)" }} />
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
                  <a href="https://get-nimbus.com/dashboard"
                    style={{ display: "inline-flex", alignItems: "center", gap: 6, fontFamily: sans, fontSize: 13, fontWeight: 500, color: C.bg, background: C.text, padding: "8px 18px", borderRadius: 999, textDecoration: "none" }}>
                    Open dashboard →
                  </a>
                </div>
              </div>
            </FadeUp>

          </div>
        </div>
      </section>

      <div style={divider} />

      {/* ── FEATURE 1: Issues → PRs ── */
      <section id="product" style={sec()}>
        <div style={{ maxWidth: W, margin: "0 auto", display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: 80, alignItems: "center" }}>
          <FadeUp>
            <div>
              <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>Issues → pull requests</p>
              <h2 style={{ fontFamily: serif, fontSize: 36, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 16, color: C.text }}>
                Agents turn ideas<br /><em style={{ fontStyle: "italic" }}>into code.</em>
              </h2>
              <p style={{ fontFamily: sans, fontSize: 15, color: C.muted, lineHeight: 1.7, marginBottom: 22 }}>
                Describe a task. Nimbus clones the repo, retrieves context, plans, implements, verifies, and opens a pull request — without you touching a file.
              </p>
              <a href="https://docs.get-nimbus.com" style={{ fontFamily: sans, fontSize: 14, color: C.gold, textDecoration: "none" }}>Learn about agentic development →</a>
            </div>
          </FadeUp>
          <FadeUp delay={100}>
            <div style={{ background: "#141210", borderRadius: 16, padding: "28px", border: "1px solid rgba(255,255,255,0.07)" }}>
              <PRDemo />
            </div>
          </FadeUp>
        </div>
      </section>

      <div style={divider} />

      {/* ── FEATURE 2: Memory ── */}
      <section style={sec({ background: "#080808" })}>
        <div style={{ maxWidth: W, margin: "0 auto", display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 80, alignItems: "center" }}>
          <FadeUp>
            <div style={{ background: "#141210", borderRadius: 16, padding: "28px", border: "1px solid rgba(255,255,255,0.07)" }}>
              <MemoryDemo />
            </div>
          </FadeUp>
          <FadeUp delay={100}>
            <div>
              <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>Persistent memory</p>
              <h2 style={{ fontFamily: serif, fontSize: 36, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 16, color: C.text }}>
                Gets smarter<br /><em style={{ fontStyle: "italic" }}>every run.</em>
              </h2>
              <p style={{ fontFamily: sans, fontSize: 15, color: C.muted, lineHeight: 1.7, marginBottom: 22 }}>
                After every task, Nimbus writes a memory entry capturing conventions, patterns, and outcomes. Future tasks retrieve this context automatically.
              </p>
              <a href="https://docs.get-nimbus.com/terminal/memory" style={{ fontFamily: sans, fontSize: 14, color: C.gold, textDecoration: "none" }}>Learn about codebase memory →</a>
            </div>
          </FadeUp>
        </div>
      </section>

      <div style={divider} />

      {/* ── FEATURE 3: Integrations ── */}
      <section style={sec()}>
        <div style={{ maxWidth: W, margin: "0 auto", display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: 80, alignItems: "center" }}>
          <FadeUp>
            <div>
              <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>In every tool, at every step</p>
              <h2 style={{ fontFamily: serif, fontSize: 36, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 16, color: C.text }}>
                Runs in your terminal,<br /><em style={{ fontStyle: "italic" }}>responds in Slack.</em>
              </h2>
              <p style={{ fontFamily: sans, fontSize: 15, color: C.muted, lineHeight: 1.7, marginBottom: 22 }}>
                Comment <code style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.6)", background: "rgba(255,255,255,0.06)", padding: "1px 6px", borderRadius: 4 }}>/nimbus</code> on any GitHub issue or PR. Trigger from Slack. Nimbus runs wherever your team already works.
              </p>
              <a href="https://docs.get-nimbus.com/integrations/slack" style={{ fontFamily: sans, fontSize: 14, color: C.gold, textDecoration: "none" }}>Learn about integrations →</a>
            </div>
          </FadeUp>
          <FadeUp delay={100}>
            <div style={{ background: "#141210", borderRadius: 16, padding: "28px", border: "1px solid rgba(255,255,255,0.07)" }}>
              <SlackDemo />
            </div>
          </FadeUp>
        </div>
      </section>

      <div style={divider} />

      {/* ── CAPABILITY CARDS ── */}
      <section style={sec({ background: "#080808" })}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <FadeUp>
            <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 12 }}>Stay on the frontier</p>
          </FadeUp>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 1, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 12, overflow: "hidden" }}>
            {[
              { h: "Use the best model for every task", b: "Claude Opus for planning, Claude Sonnet for implementation. Or auto — Nimbus picks the right model for each phase.", l: "Explore models" },
              { h: "Complete codebase understanding", b: "voyage-code-2 embeddings fused with BM25 via Reciprocal Rank Fusion. AST-aware chunking. Multi-repo workspace support.", l: "Learn about retrieval" },
              { h: "Develop enduring software", b: "Self-improving reviewer learns from PR feedback. 20 built-in agents — security, testing, docs, performance. MIT licensed.", l: "Explore agents" },
            ].map((card, i) => (
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

      {/* ── CHANGELOG ── */}
      <section id="changelog" style={sec()}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <FadeUp>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 36 }}>
              <h2 style={{ fontFamily: serif, fontSize: 28, fontWeight: 400, letterSpacing: "-0.015em" }}>Changelog</h2>
              <a href="https://github.com/arpjw/nimbus/commits/main" target="_blank" rel="noopener noreferrer" style={{ fontFamily: sans, fontSize: 13, color: C.faint, textDecoration: "none" }}>See all →</a>
            </div>
          </FadeUp>
          <FadeUp delay={60}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10 }}>
              {[
                { v: "1.1", d: "Apr 26, 2026", t: "Interactive terminal + 20 built-in agents" },
                { v: "1.1", d: "Apr 26, 2026", t: "PyPI package — pip install nimbus-ai" },
                { v: "1.0", d: "Apr 25, 2026", t: "Slack, Linear, automations shipped" },
                { v: "1.0", d: "Apr 25, 2026", t: "Self-improving PR reviewer" },
              ].map((entry, i) => (
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

      {/* ── CTA ── */}
      <section style={{ padding: "160px 28px" }}>
        <FadeUp>
          <div style={{ maxWidth: W, margin: "0 auto", textAlign: "center" }}>
            <h2 style={{ fontFamily: serif, fontSize: 56, fontWeight: 400, letterSpacing: "-0.025em", lineHeight: 1.05, color: C.text, marginBottom: 40 }}>
              Try Nimbus <em style={{ fontStyle: "italic" }}>now.</em>
            </h2>
            <div style={{ display: "flex", gap: 12, justifyContent: "center", marginBottom: 20 }}>
              <a href="https://api.get-nimbus.com/keys/generate" style={{ fontFamily: sans, fontSize: 15, fontWeight: 600, color: C.bg, background: C.text, padding: "13px 32px", borderRadius: 999, textDecoration: "none" }}>Get started free ↓</a>
              <a href="https://docs.get-nimbus.com" style={{ fontFamily: sans, fontSize: 15, fontWeight: 500, color: C.muted, padding: "13px 24px", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 999, textDecoration: "none" }}>Read the docs</a>
            </div>
            <p style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.2)" }}>pip install nimbus-ai · Free tier · No credit card required</p>
          </div>
        </FadeUp>
      </section>

      <div style={divider} />

      {/* ── FOOTER ── */}
      <footer style={{ padding: "52px 28px" }}>
        <div style={{ maxWidth: W, margin: "0 auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 48, marginBottom: 40 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
                <div style={{ width: 18, height: 18, borderRadius: 4, background: C.text, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span style={{ color: C.bg, fontWeight: 800, fontSize: 9, fontFamily: sans }}>N</span>
                </div>
                <span style={{ fontFamily: serif, fontStyle: "italic", fontSize: 16, color: C.text }}>Nimbus</span>
              </div>
              <p style={{ fontFamily: sans, fontSize: 13, color: "rgba(255,255,255,0.3)", lineHeight: 1.65, maxWidth: 220 }}>Autonomous software engineering. From task description to merged pull request.</p>
            </div>
            {[
              { title: "Product", links: [["Dashboard", "https://get-nimbus.com/dashboard"], ["Prism", "https://get-nimbus.com/prism"], ["Mobile App", "https://get-nimbus.com/app"], ["API", "https://api.get-nimbus.com/docs"]] },
              { title: "Resources", links: [["Docs", "https://docs.get-nimbus.com"], ["Changelog", "#changelog"], ["PyPI", "https://pypi.org/project/nimbus-ai"], ["Status", "https://api.get-nimbus.com/health"]] },
              { title: "Connect", links: [["GitHub", "https://github.com/arpjw/nimbus"], ["VS Code", "https://github.com/arpjw/nimbus-vscode"], ["aryasomu.com", "https://aryasomu.com"]] },
            ].map(col => (
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
