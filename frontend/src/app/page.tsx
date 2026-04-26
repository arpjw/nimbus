"use client";
import { useEffect, useState, useRef, ReactNode } from "react";
import { Github, ArrowRight } from "lucide-react";

/* ─── Color tokens ─── */
const C = {
  bg:      "#0A0A0A",
  surface: "#141414",
  border:  "rgba(255,255,255,0.06)",
  border2: "rgba(255,255,255,0.1)",
  text:    "#FAFAFA",
  muted:   "rgba(255,255,255,0.5)",
  faint:   "rgba(255,255,255,0.25)",
  accent:  "rgba(255,255,255,0.08)",
  gold:    "#c4a96a",
  green:   "#6aab7a",
  term:    "#0c0b08",
  termBdr: "#2a2518",
};

const serif = "var(--font-serif, 'Georgia', serif)";
const sans  = "var(--font-sans, system-ui, sans-serif)";
const mono  = "var(--font-mono, monospace)";

/* ─── Fade-up animation on scroll ─── */
function FadeUp({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVisible(true); obs.disconnect(); } }, { threshold: 0.1 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return (
    <div ref={ref} style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(30px)", transition: `opacity 0.6s ease ${delay}ms, transform 0.6s ease ${delay}ms` }}>
      {children}
    </div>
  );
}

/* ─── Terminal ─── */
const TERM_LINES = [
  { d: 0,    t: "$ nimbus run 'migrate auth to JWT'",        c: C.text },
  { d: 700,  t: "",                                           c: "" },
  { d: 800,  t: "  cloning   github.com/acme/api",           c: "rgba(255,255,255,0.2)" },
  { d: 1400, t: "  indexing  847 files · 12,304 chunks",     c: "rgba(255,255,255,0.2)" },
  { d: 2100, t: "  planning  via claude opus...",             c: "rgba(255,255,255,0.2)" },
  { d: 2900, t: "",                                           c: "" },
  { d: 3000, t: "  plan",                                     c: "rgba(255,255,255,0.4)" },
  { d: 3200, t: "  ├─ modify  src/middleware/auth.ts",        c: "rgba(255,255,255,0.3)" },
  { d: 3350, t: "  ├─ modify  src/routes/login.ts",          c: "rgba(255,255,255,0.3)" },
  { d: 3500, t: "  └─ create  src/lib/jwt.ts",               c: "rgba(255,255,255,0.3)" },
  { d: 3700, t: "",                                           c: "" },
  { d: 3800, t: "  Proceed with 3 changes? [y/N] y",         c: "rgba(255,255,255,0.5)" },
  { d: 4400, t: "",                                           c: "" },
  { d: 4500, t: "  implementing...",                          c: "rgba(255,255,255,0.2)" },
  { d: 4900, t: "  read   src/middleware/auth.ts",           c: "rgba(255,255,255,0.15)" },
  { d: 5100, t: "  write  src/lib/jwt.ts",                  c: "rgba(255,255,255,0.15)" },
  { d: 5300, t: "  write  src/middleware/auth.ts",           c: "rgba(255,255,255,0.15)" },
  { d: 5900, t: "",                                           c: "" },
  { d: 6000, t: "  tsc ✓   eslint ✓",                        c: C.green },
  { d: 6500, t: "  self-review · approve",                   c: C.green },
  { d: 7000, t: "  PR #47 opened  ↗  acme/api/pull/47",     c: C.green },
  { d: 7700, t: "",                                           c: "" },
  { d: 7800, t: "  done in 18.4s",                           c: "rgba(255,255,255,0.3)" },
];

function Terminal() {
  const [vis, setVis] = useState<number[]>([]);
  useEffect(() => {
    const t = TERM_LINES.map((_, i) => setTimeout(() => setVis(v => [...v, i]), TERM_LINES[i].d));
    return () => t.forEach(clearTimeout);
  }, []);
  return (
    <div style={{ border: `1px solid ${C.border2}`, borderRadius: 16, overflow: "hidden", background: C.term }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "12px 18px", borderBottom: `1px solid ${C.border}`, background: "rgba(255,255,255,0.03)" }}>
        <div style={{ width: 11, height: 11, borderRadius: "50%", background: "rgba(255,255,255,0.08)" }} />
        <div style={{ width: 11, height: 11, borderRadius: "50%", background: "rgba(255,255,255,0.08)" }} />
        <div style={{ width: 11, height: 11, borderRadius: "50%", background: "rgba(255,255,255,0.08)" }} />
        <span style={{ marginLeft: 10, fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.18)" }}>nimbus — zsh</span>
      </div>
      <div style={{ padding: "24px 28px", fontFamily: mono, fontSize: 13, lineHeight: 1.75, minHeight: 380 }}>
        {TERM_LINES.map((l, i) => vis.includes(i) ? (
          <div key={i} style={{ color: l.c, minHeight: l.t ? undefined : 12 }}>{l.t}</div>
        ) : null)}
        {vis.length < TERM_LINES.length && (
          <span style={{ display: "inline-block", width: 7, height: 13, background: C.muted, verticalAlign: "middle", animation: "blink 1s step-end infinite" }} />
        )}
        <style>{`@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}`}</style>
      </div>
    </div>
  );
}

/* ─── Demo Windows ─── */
function DemoFrame({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{ border: `1px solid ${C.border2}`, borderRadius: 16, overflow: "hidden", background: C.surface }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "11px 16px", borderBottom: `1px solid ${C.border}`, background: "rgba(255,255,255,0.02)" }}>
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: "rgba(255,255,255,0.08)" }} />
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: "rgba(255,255,255,0.08)" }} />
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: "rgba(255,255,255,0.08)" }} />
        <span style={{ marginLeft: 10, fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.18)" }}>{title}</span>
      </div>
      {children}
    </div>
  );
}

function PRDemo() {
  return (
    <DemoFrame title="github.com / acme / api / pull / 47">
      <div style={{ padding: "20px 24px" }}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 18 }}>
          <span style={{ fontSize: 11, fontWeight: 600, padding: "2px 10px", borderRadius: 999, border: "1px solid rgba(106,171,122,0.3)", background: "rgba(106,171,122,0.08)", color: C.green, whiteSpace: "nowrap", marginTop: 2, fontFamily: mono }}>Open</span>
          <div>
            <p style={{ fontSize: 14, fontWeight: 500, color: C.text, lineHeight: 1.4, fontFamily: sans }}>[Nimbus] Migrate auth to JWT with refresh token support</p>
            <p style={{ fontSize: 12, color: C.muted, marginTop: 4, fontFamily: mono }}>nimbus-bot · 2 minutes ago · 3 files changed</p>
          </div>
        </div>
        {[["src/lib/jwt.ts", "+42", C.green], ["src/middleware/auth.ts", "+18 −31", C.muted], ["src/routes/login.ts", "+9 −4", C.muted]].map(([f, s, c]) => (
          <div key={f} style={{ display: "flex", justifyContent: "space-between", padding: "7px 12px", borderRadius: 8, border: `1px solid ${C.border}`, background: "rgba(255,255,255,0.02)", marginBottom: 6 }}>
            <span style={{ fontFamily: mono, fontSize: 12, color: C.muted }}>{f}</span>
            <span style={{ fontFamily: mono, fontSize: 12, color: c }}>{s}</span>
          </div>
        ))}
        <div style={{ border: `1px solid ${C.border}`, borderRadius: 10, overflow: "hidden", marginTop: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 14px", background: "rgba(255,255,255,0.02)", borderBottom: `1px solid ${C.border}` }}>
            <div style={{ width: 16, height: 16, borderRadius: 4, background: "rgba(196,169,106,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ color: C.gold, fontWeight: 700, fontSize: 9 }}>N</span>
            </div>
            <span style={{ fontSize: 12, color: C.muted, fontFamily: mono }}>nimbus-bot · 1 minute ago</span>
          </div>
          <div style={{ padding: "12px 14px", fontFamily: mono, fontSize: 12, lineHeight: 1.7, background: "rgba(0,0,0,0.2)" }}>
            <p style={{ color: C.faint }}>## Self-Review</p>
            <p style={{ color: C.faint }}>&nbsp;</p>
            <p style={{ color: C.green }}>**Verdict**: APPROVE</p>
            <p style={{ color: C.faint }}>&nbsp;</p>
            <p style={{ color: C.faint }}>JWT with Redis refresh tokens. 47 tests pass.</p>
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
      <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 8 }}>
        {entries.map((e, i) => (
          <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: "10px 12px", borderRadius: 8, border: `1px solid ${C.border}`, background: "rgba(255,255,255,0.02)" }}>
            <span style={{ fontFamily: mono, fontSize: 10, color: C.gold, background: "rgba(196,169,106,0.08)", border: "1px solid rgba(196,169,106,0.15)", padding: "1px 7px", borderRadius: 4, whiteSpace: "nowrap", marginTop: 2 }}>{e.k}</span>
            <p style={{ fontSize: 12, color: C.muted, lineHeight: 1.6, fontFamily: mono }}>{e.v}</p>
          </div>
        ))}
      </div>
    </DemoFrame>
  );
}

function SlackDemo() {
  return (
    <DemoFrame title="Slack — #engineering">
      <div style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 18, fontFamily: mono, fontSize: 12 }}>
        <div style={{ display: "flex", gap: 12 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(106,171,122,0.12)", border: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <span style={{ color: C.green, fontWeight: 700, fontSize: 11 }}>K</span>
          </div>
          <div>
            <p style={{ marginBottom: 4 }}>
              <span style={{ color: C.text, fontWeight: 600 }}>kira</span>
              <span style={{ color: C.faint, fontSize: 10, marginLeft: 8 }}>9:14 AM</span>
            </p>
            <p style={{ color: C.muted }}>/nimbus fix the rate limiting bug on /api/upload</p>
          </div>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(196,169,106,0.08)", border: "1px solid rgba(196,169,106,0.15)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <span style={{ color: C.gold, fontWeight: 700, fontSize: 11 }}>N</span>
          </div>
          <div>
            <p style={{ marginBottom: 4 }}>
              <span style={{ color: C.gold, fontWeight: 600 }}>Nimbus</span>
              <span style={{ color: C.faint, background: "rgba(255,255,255,0.05)", fontSize: 9, padding: "1px 5px", borderRadius: 3, marginLeft: 6, marginRight: 6 }}>APP</span>
              <span style={{ color: C.faint, fontSize: 10 }}>9:14 AM</span>
            </p>
            <p style={{ color: C.muted, lineHeight: 1.8 }}>
              On it. Cloning <span style={{ color: "rgba(255,255,255,0.6)" }}>acme/api</span>...<br />
              PR opened <span style={{ color: C.gold }}>github.com/acme/api/pull/52</span><br />
              <span style={{ color: C.faint }}>Self-review: APPROVE · done in 22.7s</span>
            </p>
          </div>
        </div>
      </div>
    </DemoFrame>
  );
}

/* ─── Section divider ─── */
function Divider() {
  return <div style={{ height: 1, background: C.border, maxWidth: 1200, margin: "0 auto" }} />;
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
    <nav style={{
      position: "fixed", top: 0, left: 0, right: 0, zIndex: 100,
      height: 64,
      borderBottom: `1px solid ${scrolled ? C.border : "transparent"}`,
      background: scrolled ? "rgba(10,10,10,0.85)" : "transparent",
      backdropFilter: scrolled ? "blur(12px)" : "none",
      transition: "all 0.3s ease",
    }}>
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 32px", height: "100%", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 22, height: 22, borderRadius: 5, background: C.text, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: C.bg, fontWeight: 800, fontSize: 12, fontFamily: sans }}>N</span>
          </div>
          <span style={{ fontFamily: serif, fontSize: 18, fontStyle: "italic", color: C.text }}>Nimbus</span>
        </div>

        {/* Nav links */}
        <div style={{ display: "flex", gap: 32 }}>
          {[["Product", "#product"], ["Prism", "/prism"], ["API", "https://api.get-nimbus.com/docs"], ["Changelog", "#changelog"], ["GitHub", "https://github.com/arpjw/nimbus"]].map(([l, h]) => (
            <a key={l} href={h} style={{ fontFamily: sans, fontSize: 14, fontWeight: 500, color: C.muted, textDecoration: "none", transition: "color 0.2s" }}>{l}</a>
          ))}
        </div>

        {/* CTAs */}
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <a href="https://api.get-nimbus.com/keys/generate"
            style={{ fontFamily: sans, fontSize: 14, fontWeight: 500, color: C.muted, textDecoration: "none", padding: "7px 16px", border: `1px solid ${C.border}`, borderRadius: 8, transition: "all 0.2s" }}>
            Sign in
          </a>
          <a href="https://api.get-nimbus.com/keys/generate"
            style={{ fontFamily: sans, fontSize: 14, fontWeight: 500, color: C.bg, background: C.text, padding: "7px 18px", borderRadius: 8, textDecoration: "none", display: "flex", alignItems: "center", gap: 6 }}>
            Get started <ArrowRight size={13} />
          </a>
        </div>
      </div>
    </nav>
  );
}

/* ─── Main ─── */
export default function Page() {
  return (
    <div style={{ background: C.bg, color: C.text, minHeight: "100vh", overflowX: "hidden", fontFamily: sans }}>
      <Navbar />

      {/* ═══════════════════════════════════════
          SECTION 1 — HERO (centered, large terminal)
      ═══════════════════════════════════════ */}
      <section style={{ paddingTop: 160, paddingBottom: 100, paddingLeft: 32, paddingRight: 32 }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <FadeUp>
            <div style={{ maxWidth: 640, marginBottom: 48 }}>
              <h1 style={{ fontFamily: serif, fontSize: 62, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.1, marginBottom: 24, color: C.text }}>
                Autonomous software engineering,{" "}
                <em style={{ fontStyle: "italic" }}>stratified.</em>
              </h1>
              <p style={{ fontFamily: sans, fontSize: 18, color: C.muted, lineHeight: 1.65, marginBottom: 36 }}>
                Nimbus plans, implements, and reviews code against real repositories — entirely on its own. From task description to merged PR.
              </p>
              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <a href="https://api.get-nimbus.com/keys/generate"
                  style={{ fontFamily: sans, fontSize: 15, fontWeight: 500, color: C.bg, background: C.text, padding: "11px 24px", borderRadius: 10, textDecoration: "none", display: "flex", alignItems: "center", gap: 8 }}>
                  Get started free <ArrowRight size={14} />
                </a>
                <a href="https://github.com/arpjw/nimbus" target="_blank" rel="noopener noreferrer"
                  style={{ fontFamily: sans, fontSize: 15, fontWeight: 500, color: C.muted, padding: "11px 24px", border: `1px solid ${C.border}`, borderRadius: 10, textDecoration: "none", display: "flex", alignItems: "center", gap: 8, transition: "all 0.2s" }}>
                  <Github size={14} /> View source
                </a>
              </div>
            </div>
          </FadeUp>

          {/* Large terminal — 80% viewport width */}
          <FadeUp delay={150}>
            <div style={{ maxWidth: "82%", margin: "0 auto" }}>
              <Terminal />
            </div>
          </FadeUp>
        </div>
      </section>

      <Divider />

      {/* ═══════════════════════════════════════
          SECTION 2 — FEATURE: Issues → PRs
          Layout: text centered above card
      ═══════════════════════════════════════ */}
      <section id="product" style={{ padding: "140px 32px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 3fr", gap: 80, alignItems: "center" }}>
            <FadeUp>
              <div>
                <p style={{ fontFamily: mono, fontSize: 11, color: C.faint, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>Issues → pull requests</p>
                <h2 style={{ fontFamily: serif, fontSize: 40, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 16, color: C.text }}>
                  Agents turn ideas<br /><em style={{ fontStyle: "italic" }}>into code.</em>
                </h2>
                <p style={{ fontFamily: sans, fontSize: 17, color: C.muted, lineHeight: 1.65, marginBottom: 20 }}>
                  Describe a task. Nimbus clones the repo, retrieves context, plans, implements, verifies, and opens a pull request — without you touching a file.
                </p>
                <a href="https://github.com/arpjw/nimbus#readme" style={{ fontFamily: sans, fontSize: 14, color: C.gold, textDecoration: "none" }}>Learn about agentic development →</a>
              </div>
            </FadeUp>
            <FadeUp delay={100}>
              <PRDemo />
            </FadeUp>
          </div>
        </div>
      </section>

      <Divider />

      {/* ═══════════════════════════════════════
          SECTION 3 — FEATURE: Memory
          Layout: text left (40%) | card right (60%)
      ═══════════════════════════════════════ */}
      <section style={{ padding: "140px 32px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", display: "grid", gridTemplateColumns: "2fr 3fr", gap: 80, alignItems: "center" }}>
          <FadeUp>
            <div>
              <p style={{ fontFamily: mono, fontSize: 11, color: C.faint, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>Persistent memory</p>
              <h2 style={{ fontFamily: serif, fontSize: 40, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 16, color: C.text }}>
                Gets smarter<br /><em style={{ fontStyle: "italic" }}>every run.</em>
              </h2>
              <p style={{ fontFamily: sans, fontSize: 17, color: C.muted, lineHeight: 1.65, marginBottom: 20 }}>
                After every task, Nimbus writes a memory entry — conventions, patterns, outcomes. Future tasks retrieve this context automatically.
              </p>
              <a href="https://github.com/arpjw/nimbus#readme" style={{ fontFamily: sans, fontSize: 14, color: C.gold, textDecoration: "none" }}>Learn about codebase memory →</a>
            </div>
          </FadeUp>
          <FadeUp delay={100}>
            <MemoryDemo />
          </FadeUp>
        </div>
      </section>

      <Divider />

      {/* ═══════════════════════════════════════
          SECTION 4 — FEATURE: Integrations
          Layout: card left (60%) | text right (40%)
      ═══════════════════════════════════════ */}
      <section style={{ padding: "140px 32px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", display: "grid", gridTemplateColumns: "3fr 2fr", gap: 80, alignItems: "center" }}>
          <FadeUp>
            <SlackDemo />
          </FadeUp>
          <FadeUp delay={100}>
            <div>
              <p style={{ fontFamily: mono, fontSize: 11, color: C.faint, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>In every tool, at every step</p>
              <h2 style={{ fontFamily: serif, fontSize: 40, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 16, color: C.text }}>
                Runs in your terminal,<br /><em style={{ fontStyle: "italic" }}>responds in Slack.</em>
              </h2>
              <p style={{ fontFamily: sans, fontSize: 17, color: C.muted, lineHeight: 1.65, marginBottom: 20 }}>
                Comment <code style={{ fontFamily: mono, fontSize: 13, color: "rgba(255,255,255,0.6)", background: "rgba(255,255,255,0.05)", padding: "1px 6px", borderRadius: 4 }}>/nimbus</code> on any GitHub issue or PR. Trigger from Slack. Nimbus runs wherever your team already works.
              </p>
              <a href="https://github.com/arpjw/nimbus#readme" style={{ fontFamily: sans, fontSize: 14, color: C.gold, textDecoration: "none" }}>Learn about integrations →</a>
            </div>
          </FadeUp>
        </div>
      </section>

      <Divider />

      {/* ═══════════════════════════════════════
          SECTION 6 — FEATURES GRID
      ═══════════════════════════════════════ */}
      <section style={{ padding: "140px 32px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <FadeUp>
            <p style={{ fontFamily: mono, fontSize: 11, color: C.faint, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 48 }}>Stay on the frontier</p>
          </FadeUp>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
            {[
              {
                label: "Retrieval",
                h: "Hybrid code search",
                b: "voyage-code-2 embeddings fused with BM25 via Reciprocal Rank Fusion. AST-aware chunking via tree-sitter. Multi-repo workspaces.",
                demo: (
                  <div style={{ fontFamily: mono, fontSize: 11, padding: "14px 16px", borderRadius: 8, background: "rgba(0,0,0,0.3)", border: `1px solid ${C.border}`, lineHeight: 1.7 }}>
                    <p style={{ color: C.faint }}>query: "JWT middleware"</p>
                    <p style={{ color: C.faint }}>&nbsp;</p>
                    <p style={{ color: "rgba(255,255,255,0.5)" }}>↗ src/middleware/auth.ts  <span style={{ color: C.gold }}>0.97</span></p>
                    <p style={{ color: "rgba(255,255,255,0.5)" }}>↗ src/lib/tokens.ts      <span style={{ color: C.gold }}>0.91</span></p>
                    <p style={{ color: "rgba(255,255,255,0.5)" }}>↗ src/routes/login.ts   <span style={{ color: C.gold }}>0.88</span></p>
                  </div>
                )
              },
              {
                label: "Verification",
                h: "Your actual test suite",
                b: "Runs pytest, tsc, eslint, or cargo. On failure, reformulates the plan with the error output as context and tries again.",
                demo: (
                  <div style={{ fontFamily: mono, fontSize: 11, padding: "14px 16px", borderRadius: 8, background: "rgba(0,0,0,0.3)", border: `1px solid ${C.border}`, lineHeight: 1.7 }}>
                    <p style={{ color: C.faint }}>running verification...</p>
                    <p style={{ color: C.faint }}>&nbsp;</p>
                    <p style={{ color: C.green }}>  ruff     ✓ pass</p>
                    <p style={{ color: C.green }}>  mypy     ✓ pass</p>
                    <p style={{ color: C.green }}>  pytest   ✓ 47 tests</p>
                  </div>
                )
              },
              {
                label: "Skills",
                h: "Reusable task types",
                b: "nimbus run --skill add-tests, dependency-audit, add-openapi-docs. Built-in skills ship with Nimbus. Define your own and share them.",
                demo: (
                  <div style={{ fontFamily: mono, fontSize: 11, padding: "14px 16px", borderRadius: 8, background: "rgba(0,0,0,0.3)", border: `1px solid ${C.border}`, lineHeight: 1.7 }}>
                    <p style={{ color: C.faint }}>$ nimbus skills list</p>
                    <p style={{ color: C.faint }}>&nbsp;</p>
                    <p style={{ color: "rgba(255,255,255,0.5)" }}>add-tests         built-in</p>
                    <p style={{ color: "rgba(255,255,255,0.5)" }}>add-openapi-docs  built-in</p>
                    <p style={{ color: "rgba(255,255,255,0.5)" }}>dependency-audit  built-in</p>
                  </div>
                )
              },
              {
                label: "Automations",
                h: "Always-on agents",
                b: "Trigger Nimbus from PagerDuty alerts, CI failures, cron schedules, Linear issues, or any webhook. Set it once, let it run.",
                demo: (
                  <div style={{ fontFamily: mono, fontSize: 11, padding: "14px 16px", borderRadius: 8, background: "rgba(0,0,0,0.3)", border: `1px solid ${C.border}`, lineHeight: 1.7 }}>
                    <p style={{ color: C.faint }}>trigger: pagerduty P1</p>
                    <p style={{ color: C.faint }}>&nbsp;</p>
                    <p style={{ color: "rgba(255,255,255,0.5)" }}>→ task queued</p>
                    <p style={{ color: "rgba(255,255,255,0.5)" }}>→ PR #91 opened</p>
                    <p style={{ color: C.green }}>→ incident resolved</p>
                  </div>
                )
              },
            ].map((c, i) => (
              <FadeUp key={i} delay={i * 80}>
                <div style={{ border: `1px solid ${C.border}`, borderRadius: 20, padding: 24, background: C.surface, height: "100%" }}>
                  <p style={{ fontFamily: mono, fontSize: 10, color: C.gold, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 12 }}>{c.label}</p>
                  <h3 style={{ fontFamily: serif, fontSize: 22, fontWeight: 400, marginBottom: 10, lineHeight: 1.3, color: C.text }}>{c.h}</h3>
                  <p style={{ fontFamily: sans, fontSize: 14, color: C.muted, lineHeight: 1.65, marginBottom: 16 }}>{c.b}</p>
                  {c.demo}
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      <Divider />

      {/* ═══════════════════════════════════════
          SECTION 7 — CHANGELOG
      ═══════════════════════════════════════ */}
      <section id="changelog" style={{ padding: "100px 32px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <FadeUp>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 36 }}>
              <h2 style={{ fontFamily: serif, fontSize: 30, fontWeight: 400, letterSpacing: "-0.015em" }}>Changelog</h2>
              <a href="https://github.com/arpjw/nimbus/commits/main" target="_blank" rel="noopener noreferrer" style={{ fontFamily: sans, fontSize: 14, color: C.muted, textDecoration: "none" }}>See all →</a>
            </div>
          </FadeUp>
          <FadeUp delay={80}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
              {[
                { v: "1.1", d: "Apr 26, 2026", t: "Mobile PWA — trigger tasks from phone" },
                { v: "1.1", d: "Apr 26, 2026", t: "Skills system — 5 built-in task types" },
                { v: "1.1", d: "Apr 26, 2026", t: "Automations — cron, webhooks, PagerDuty" },
                { v: "1.1", d: "Apr 26, 2026", t: "Linear + Slack integrations" },
                { v: "1.0", d: "Apr 25, 2026", t: "Web dashboard — tasks, memory, keys" },
                { v: "1.0", d: "Apr 25, 2026", t: "Self-improving PR reviewer" },
                { v: "1.0", d: "Apr 25, 2026", t: "Parallel multi-agent execution" },
                { v: "1.0", d: "Apr 25, 2026", t: "Persistent codebase memory" },
              ].map((c, i) => (
                <div key={i} style={{ border: `1px solid ${C.border}`, borderRadius: 16, padding: "18px 20px", background: C.surface }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                    <span style={{ fontFamily: mono, fontSize: 10, color: C.faint, background: "rgba(255,255,255,0.04)", border: `1px solid ${C.border}`, padding: "2px 8px", borderRadius: 999 }}>v{c.v}</span>
                    <span style={{ fontFamily: mono, fontSize: 10, color: "rgba(255,255,255,0.2)" }}>{c.d}</span>
                  </div>
                  <p style={{ fontFamily: sans, fontSize: 13, fontWeight: 500, color: C.muted, lineHeight: 1.4 }}>{c.t}</p>
                </div>
              ))}
            </div>
          </FadeUp>
        </div>
      </section>

      <Divider />

      {/* ═══════════════════════════════════════
          SECTION 8 — FINAL CTA
      ═══════════════════════════════════════ */}
      <section style={{ padding: "160px 32px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
        <FadeUp>
          <div style={{ textAlign: "center" }}>
            <h2 style={{ fontFamily: serif, fontSize: 56, fontWeight: 400, letterSpacing: "-0.03em", lineHeight: 1.0, color: C.text, marginBottom: 48 }}>
              Try Nimbus <em style={{ fontStyle: "italic" }}>now.</em>
            </h2>
            <div style={{ display: "flex", gap: 12, justifyContent: "center", marginBottom: 48 }}>
              <a href="https://api.get-nimbus.com/keys/generate"
                style={{ fontFamily: sans, fontSize: 15, fontWeight: 500, color: C.bg, background: C.text, padding: "13px 28px", borderRadius: 10, textDecoration: "none", display: "flex", alignItems: "center", gap: 8 }}>
                Get started free <ArrowRight size={14} />
              </a>
              <a href="https://github.com/arpjw/nimbus" target="_blank" rel="noopener noreferrer"
                style={{ fontFamily: sans, fontSize: 15, fontWeight: 500, color: C.muted, padding: "13px 28px", border: `1px solid ${C.border}`, borderRadius: 10, textDecoration: "none", display: "flex", alignItems: "center", gap: 8 }}>
                <Github size={14} /> View source
              </a>
            </div>

            {/* Quick start code block */}
            <div style={{ display: "inline-block", textAlign: "left", background: "rgba(255,255,255,0.03)", border: `1px solid ${C.border}`, borderRadius: 16, padding: "28px 36px", marginBottom: 20 }}>
              <div style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 13, lineHeight: 1.9, color: C.text }}>
                <p style={{ color: "rgba(255,255,255,0.3)" }}># install</p>
                <p>pip install nimbus-ai</p>
                <p>&nbsp;</p>
                <p style={{ color: "rgba(255,255,255,0.3)" }}># set your API keys</p>
                <p>export ANTHROPIC_API_KEY=sk-ant-...</p>
                <p>export VOYAGE_API_KEY=pa-...</p>
                <p>&nbsp;</p>
                <p style={{ color: "rgba(255,255,255,0.3)" }}># launch</p>
                <p>cd your-project &amp;&amp; nimbus</p>
              </div>
            </div>
            <p style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.2)", marginBottom: 8 }}>
              or use the hosted backend
            </p>
            <div style={{ display: "inline-block", textAlign: "left", background: "rgba(255,255,255,0.03)", border: `1px solid ${C.border}`, borderRadius: 12, padding: "16px 24px", marginBottom: 20 }}>
              <div style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 12, lineHeight: 1.9, color: "rgba(255,255,255,0.5)" }}>
                <p>nimbus run &quot;your task&quot; \</p>
                <p>&nbsp;&nbsp;--backend https://api.get-nimbus.com \</p>
                <p>&nbsp;&nbsp;--api-key nk_...</p>
              </div>
            </div>
            <p style={{ marginTop: 8, fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.2)" }}>
              Free tier · 10 tasks/month · No credit card required
            </p>
          </div>
        </FadeUp>
        </div>
      </section>

      <Divider />

      {/* ═══════════════════════════════════════
          SECTION 9 — FOOTER (4 columns)
      ═══════════════════════════════════════ */}
      <footer style={{ padding: "64px 32px 48px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 48, marginBottom: 48 }}>
            {/* Brand */}
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 16 }}>
                <div style={{ width: 20, height: 20, borderRadius: 4, background: C.text, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span style={{ color: C.bg, fontWeight: 800, fontSize: 10, fontFamily: sans }}>N</span>
                </div>
                <span style={{ fontFamily: serif, fontSize: 17, fontStyle: "italic", color: C.text }}>Nimbus</span>
              </div>
              <p style={{ fontFamily: sans, fontSize: 14, color: C.muted, lineHeight: 1.65, maxWidth: 240 }}>
                Autonomous software engineering. From task description to merged pull request.
              </p>
            </div>

            {/* Product */}
            <div>
              <p style={{ fontFamily: mono, fontSize: 11, color: C.faint, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 20 }}>Product</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {[["Dashboard", "/dashboard"], ["Mobile App", "/app"], ["CLI", "https://github.com/arpjw/nimbus#cli"], ["GitHub App", "https://github.com/arpjw/nimbus#github-app-setup"], ["API", "https://api.get-nimbus.com/docs"], ["Changelog", "#changelog"]].map(([l, h]) => (
                  <a key={l} href={h} style={{ fontFamily: sans, fontSize: 14, color: C.muted, textDecoration: "none" }}>{l}</a>
                ))}
              </div>
            </div>

            {/* Resources */}
            <div>
              <p style={{ fontFamily: mono, fontSize: 11, color: C.faint, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 20 }}>Resources</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {[["Docs", "https://github.com/arpjw/nimbus#readme"], ["Status", "https://api.get-nimbus.com/health"], ["License", "https://github.com/arpjw/nimbus/blob/main/LICENSE"]].map(([l, h]) => (
                  <a key={l} href={h} style={{ fontFamily: sans, fontSize: 14, color: C.muted, textDecoration: "none" }}>{l}</a>
                ))}
              </div>
            </div>

            {/* Connect */}
            <div>
              <p style={{ fontFamily: mono, fontSize: 11, color: C.faint, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 20 }}>Connect</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {[["GitHub", "https://github.com/arpjw/nimbus"], ["aryasomu.com", "https://aryasomu.com"], ["SSRN", "https://ssrn.com"]].map(([l, h]) => (
                  <a key={l} href={h} style={{ fontFamily: sans, fontSize: 14, color: C.muted, textDecoration: "none" }}>{l}</a>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom row */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 24, borderTop: `1px solid ${C.border}` }}>
            <p style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.2)" }}>© 2026 Nimbus · MIT License</p>
            <div style={{ display: "flex", gap: 20 }}>
              <a href="https://github.com/arpjw/nimbus" style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.2)", textDecoration: "none" }}>GitHub</a>
              <a href="https://aryasomu.com" style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.2)", textDecoration: "none" }}>aryasomu.com</a>
            </div>
          </div>
        </div>
      </footer>

    </div>
  );
}
