"use client";
import Link from "next/link";
import { ArrowRight, Github } from "lucide-react";

const serif = "var(--font-serif, 'Georgia', serif)";
const sans  = "var(--font-sans, system-ui, sans-serif)";
const mono  = "var(--font-mono, monospace)";

const STEPS = [
  {
    n: "01",
    label: "Paste your spec",
    desc: "Drop in a PRD, a Confluence doc, a Figma description, or just plain English. Anything that describes what you want to build.",
  },
  {
    n: "02",
    label: "Claude Opus parses it",
    desc: "Prism sends your spec to Claude Opus, which breaks it into discrete, scoped implementation tasks — each achievable in one pull request, ordered by dependency.",
  },
  {
    n: "03",
    label: "Review and edit",
    desc: "The parsed task list is shown to you before anything runs. Edit descriptions, reassign skills, reorder tasks, delete what you don't need, add what's missing.",
  },
  {
    n: "04",
    label: "Nimbus executes",
    desc: "Once you approve, Prism queues the tasks to Nimbus in dependency order. PRs open one by one as each task completes. You track progress in real time.",
  },
];

const EXAMPLES = [
  {
    input: "Add user authentication with email/password signup, JWT login, and an admin panel for managing accounts.",
    tasks: [
      { id: 1, text: "Create User and AdminUser models with SQLModel", deps: [] },
      { id: 2, text: "Add bcrypt password hashing utilities", deps: [1] },
      { id: 3, text: "Implement POST /auth/register and POST /auth/login", deps: [1, 2] },
      { id: 4, text: "Add JWT middleware for protected routes", deps: [3] },
      { id: 5, text: "Implement GET /admin/users and POST /admin/users/{id}/deactivate", deps: [1, 4] },
      { id: 6, text: "Write test suite for all auth endpoints", deps: [3, 4, 5], skill: "add-tests" },
    ],
  },
];

export default function PrismPage() {
  return (
    <div style={{ background: "#0A0A0A", color: "#FAFAFA", minHeight: "100vh", fontFamily: sans, overflowX: "hidden" }}>

      {/* Nav */}
      <nav style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 50, background: "rgba(10,10,10,0.85)", backdropFilter: "blur(20px)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "0 28px", height: 52, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 36 }}>
            <Link href="/" style={{ display: "flex", alignItems: "center", gap: 9, textDecoration: "none" }}>
              <div style={{ width: 20, height: 20, borderRadius: 5, background: "#FAFAFA", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: "#0A0A0A", fontWeight: 800, fontSize: 11, fontFamily: sans }}>N</span>
              </div>
              <span style={{ fontWeight: 400, fontSize: 18, color: "#FAFAFA", fontFamily: serif, fontStyle: "italic" }}>Nimbus</span>
            </Link>
            <div style={{ display: "flex", gap: 28 }}>
              {[["Product", "/#product"], ["Prism", "/prism"], ["API", "https://api.get-nimbus.com/docs"], ["Changelog", "/#changelog"]].map(([l, h]) => (
                <a key={l} href={h}
                  style={{ fontSize: 14, color: l === "Prism" ? "#FAFAFA" : "rgba(255,255,255,0.5)", textDecoration: "none", fontWeight: l === "Prism" ? 500 : 400 }}>
                  {l}
                </a>
              ))}
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <a href="https://github.com/arpjw/nimbus" target="_blank" rel="noopener noreferrer"
              style={{ fontSize: 14, color: "rgba(255,255,255,0.45)", textDecoration: "none", display: "flex", alignItems: "center", gap: 5 }}>
              <Github size={13} /> GitHub
            </a>
            <Link href="/prism/try"
              style={{ fontSize: 13, fontWeight: 500, color: "#0A0A0A", background: "#FAFAFA", padding: "7px 18px", borderRadius: 8, textDecoration: "none" }}>
              Try Prism
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ paddingTop: 120, paddingBottom: 80, paddingLeft: 28, paddingRight: 28 }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <div style={{ maxWidth: 680, marginBottom: 56 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
              <span style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.3)", letterSpacing: "0.08em", textTransform: "uppercase" }}>Nimbus</span>
              <span style={{ color: "rgba(255,255,255,0.15)" }}>·</span>
              <span style={{ fontFamily: mono, fontSize: 11, color: "#c4a96a", letterSpacing: "0.08em", textTransform: "uppercase" }}>Prism</span>
            </div>
            <h1 style={{ fontSize: 54, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.08, marginBottom: 20, color: "#FAFAFA", fontFamily: serif }}>
              Spec to pull requests,<br /><em style={{ fontStyle: "italic" }}>automatically.</em>
            </h1>
            <p style={{ fontSize: 18, color: "rgba(255,255,255,0.5)", lineHeight: 1.65, marginBottom: 32, maxWidth: 520 }}>
              Paste a product spec in plain English. Prism breaks it into a structured, dependency-ordered sequence of Nimbus tasks and executes them — one pull request at a time.
            </p>
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <Link href="/prism/try"
                style={{ fontSize: 15, fontWeight: 500, color: "#0A0A0A", background: "#FAFAFA", padding: "12px 26px", borderRadius: 9, textDecoration: "none", display: "flex", alignItems: "center", gap: 8 }}>
                Try it out <ArrowRight size={14} />
              </Link>
              <a href="https://github.com/arpjw/nimbus" target="_blank" rel="noopener noreferrer"
                style={{ fontSize: 15, color: "rgba(255,255,255,0.35)", textDecoration: "none", display: "flex", alignItems: "center", gap: 5 }}>
                <Github size={13} /> View source
              </a>
            </div>
          </div>

          {/* Live example */}
          <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, overflow: "hidden", background: "#111" }}>
            <div style={{ padding: "16px 22px", borderBottom: "1px solid rgba(255,255,255,0.06)", display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.06em", textTransform: "uppercase" }}>Example</span>
              <span style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.12)" }}>·</span>
              <span style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)" }}>spec → 6 tasks</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0 }}>
              {/* Input */}
              <div style={{ padding: "22px 24px", borderRight: "1px solid rgba(255,255,255,0.06)" }}>
                <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 12 }}>Input</p>
                <p style={{ fontSize: 14, color: "rgba(255,255,255,0.55)", lineHeight: 1.7 }}>
                  {EXAMPLES[0].input}
                </p>
              </div>
              {/* Output tasks */}
              <div style={{ padding: "22px 24px" }}>
                <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.25)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 12 }}>Parsed tasks</p>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {EXAMPLES[0].tasks.map((t) => (
                    <div key={t.id} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                      <span style={{ fontFamily: mono, fontSize: 11, color: "#c4a96a", flexShrink: 0, marginTop: 2 }}>{t.id}</span>
                      <div>
                        <p style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", lineHeight: 1.5 }}>{t.text}</p>
                        <div style={{ display: "flex", gap: 6, marginTop: 3 }}>
                          {t.deps.length > 0 && (
                            <span style={{ fontFamily: mono, fontSize: 10, color: "rgba(255,255,255,0.2)" }}>
                              deps: {t.deps.join(", ")}
                            </span>
                          )}
                          {t.skill && (
                            <span style={{ fontFamily: mono, fontSize: 10, color: "#c4a96a", background: "rgba(196,169,106,0.08)", padding: "1px 6px", borderRadius: 3 }}>
                              {t.skill}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section style={{ padding: "80px 28px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.3)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 48 }}>How it works</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 1, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 10, overflow: "hidden" }}>
            {STEPS.map((s) => (
              <div key={s.n} style={{ background: "#0A0A0A", padding: "28px 26px 32px" }}>
                <div style={{ fontFamily: mono, fontSize: 22, color: "rgba(255,255,255,0.07)", fontWeight: 400, marginBottom: 16 }}>{s.n}</div>
                <h3 style={{ fontFamily: serif, fontSize: 19, fontWeight: 400, marginBottom: 10, color: "#FAFAFA", lineHeight: 1.3 }}>{s.label}</h3>
                <p style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", lineHeight: 1.7 }}>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Prism */}
      <section style={{ padding: "80px 28px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 80, alignItems: "start" }}>
          <div>
            <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.3)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 20 }}>Why Prism</p>
            <h2 style={{ fontFamily: serif, fontSize: 38, fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1.15, marginBottom: 18, color: "#FAFAFA" }}>
              From idea to<br /><em style={{ fontStyle: "italic" }}>merged PRs.</em>
            </h2>
            <p style={{ fontSize: 16, color: "rgba(255,255,255,0.45)", lineHeight: 1.7, marginBottom: 16 }}>
              The skill required to break a product idea into well-scoped engineering tasks is enormous — it takes years of experience to know what "one PR worth of work" looks like, how to sequence dependencies, and what level of description an autonomous agent needs.
            </p>
            <p style={{ fontSize: 16, color: "rgba(255,255,255,0.45)", lineHeight: 1.7 }}>
              Prism handles that decomposition automatically. You describe what you want to build. Claude Opus reasons about the right task boundaries, dependency order, and appropriate skills. Nimbus executes.
            </p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {[
              { label: "For PMs and founders", desc: "Describe a feature in plain English and watch it get implemented without writing a single technical ticket." },
              { label: "For engineers", desc: "Break down large features into a properly sequenced task queue. Review and edit before anything runs." },
              { label: "For teams", desc: "Prism queues tasks in dependency order — schema before routes, routes before tests. Nothing runs out of order." },
            ].map((item) => (
              <div key={item.label} style={{ padding: "20px 22px", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 10, background: "#111" }}>
                <p style={{ fontSize: 14, fontWeight: 500, color: "#FAFAFA", marginBottom: 6 }}>{item.label}</p>
                <p style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", lineHeight: 1.6 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: "100px 28px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <h2 style={{ fontFamily: serif, fontSize: 52, fontWeight: 400, letterSpacing: "-0.025em", lineHeight: 1.1, marginBottom: 36, color: "#FAFAFA" }}>
            Try it <em style={{ fontStyle: "italic" }}>now.</em>
          </h2>
          <p style={{ fontSize: 17, color: "rgba(255,255,255,0.4)", lineHeight: 1.65, marginBottom: 36, maxWidth: 460 }}>
            Paste any spec — a paragraph, a PRD, a list of requirements — and Prism will have tasks queued to Nimbus within seconds.
          </p>
          <Link href="/prism/try"
            style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 15, fontWeight: 500, color: "#0A0A0A", background: "#FAFAFA", padding: "13px 28px", borderRadius: 9, textDecoration: "none" }}>
            Try it out <ArrowRight size={14} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: "1px solid rgba(255,255,255,0.05)", padding: "32px 28px" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Link href="/" style={{ fontFamily: serif, fontSize: 16, fontStyle: "italic", color: "rgba(255,255,255,0.3)", textDecoration: "none" }}>Nimbus</Link>
          <p style={{ fontFamily: mono, fontSize: 12, color: "rgba(255,255,255,0.15)" }}>© 2026 Nimbus · MIT License</p>
        </div>
      </footer>

    </div>
  );
}
