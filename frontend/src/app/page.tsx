import Link from "next/link";
import { ArrowRight, Github } from "lucide-react";
import { HeroTerminal } from "@/components/landing/Hero";
import { Features } from "@/components/landing/Features";
import { Workflow } from "@/components/landing/Workflow";

const TICKER_ITEMS = [
  "voyage-code-2 embeddings",
  "AST-aware chunking",
  "BM25 keyword retrieval",
  "Reciprocal Rank Fusion",
  "Claude Opus planning",
  "Claude Sonnet implementation",
  "Parallel multi-agent execution",
  "Persistent codebase memory",
  "Iterative verification",
  "Diff preview gate",
  "Self-reviewing PR loop",
  "GitHub App integration",
  "Issue-to-PR pipeline",
  "Test generation",
  "Hosted at api.get-nimbus.com",
  "CLI — nimbus run",
];

export default function Landing() {
  const tickers = [...TICKER_ITEMS, ...TICKER_ITEMS];

  return (
    <div className="min-h-screen bg-bg">

      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-bg/95 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-6 h-12 flex items-center justify-between">
          <span className="font-display italic text-xl font-medium tracking-tight">Nimbus</span>
          <div className="flex items-center gap-7">
            <a href="#features" className="text-sm text-muted hover:text-text transition-colors">Features</a>
            <a href="#workflow" className="text-sm text-muted hover:text-text transition-colors">Workflow</a>
            <a
              href="https://api.get-nimbus.com/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-muted hover:text-text transition-colors"
            >
              API
            </a>
            <a
              href="https://github.com/arpjw/nimbus"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-sm text-muted hover:text-text transition-colors"
            >
              <Github size={13} /> GitHub
            </a>
            <Link
              href="/dashboard"
              className="flex items-center gap-1.5 text-sm font-medium text-bg bg-text hover:bg-brown px-4 py-1.5 rounded-sm transition-colors"
            >
              Dashboard <ArrowRight size={12} />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-0 px-6 relative overflow-hidden">

        {/* Large decorative background letter */}
        <div
          aria-hidden="true"
          className="absolute right-0 top-0 select-none pointer-events-none"
          style={{ lineHeight: 1 }}
        >
          <span
            className="font-display font-medium"
            style={{ fontSize: "580px", color: "rgba(180,168,152,0.10)", letterSpacing: "-0.04em" }}
          >
            N
          </span>
        </div>

        <div className="max-w-5xl mx-auto relative">

          {/* Label */}
          <p className="font-mono text-[11px] text-faint uppercase tracking-widest mb-8">
            Nimbus &mdash; 2026
          </p>

          <div className="grid grid-cols-2 gap-16 items-start">

            {/* Left */}
            <div className="space-y-10">
              <h1 className="font-display font-medium leading-[1.0] tracking-tight" style={{ fontSize: "82px" }}>
                Autonomous<br />
                software<br />
                <em className="italic font-medium" style={{ color: "#8E2D2D" }}>engineering.</em>
              </h1>

              <p className="text-muted text-base leading-relaxed max-w-[340px]">
                Nimbus plans, implements, and reviews code against real repositories &mdash;
                entirely on its own. Powered by Claude and Voyage AI.
              </p>

              <div className="flex items-center gap-3">
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 px-5 py-2.5 bg-text text-bg text-sm font-medium hover:bg-brown rounded-sm transition-colors"
                >
                  Open Dashboard
                </Link>
                <a
                  href="https://github.com/arpjw/nimbus"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-5 py-2.5 border border-border text-sm text-text hover:border-border-dark rounded-sm transition-colors"
                >
                  <Github size={13} /> View source
                </a>
              </div>
            </div>

            {/* Right — terminal */}
            <div>
              <HeroTerminal />
            </div>
          </div>

          {/* Stats bar */}
          <div className="grid grid-cols-3 gap-0 mt-16 border-t border-border">
            {[
              { label: "Embedding model", value: "voyage-code-2", sub: "AST-aware, purpose-built for code" },
              { label: "Retrieval", value: "BM25 + RRF", sub: "Keyword + semantic fusion" },
              { label: "Hosted at", value: "api.get-nimbus.com", sub: "Free tier, no setup required" },
            ].map((s, i) => (
              <div key={s.label} className={`py-8 ${i > 0 ? "pl-8 border-l border-border" : ""} ${i < 2 ? "pr-8" : ""}`}>
                <p className="font-mono text-[10px] text-faint uppercase tracking-widest mb-2">{s.label}</p>
                <p className="font-display text-3xl font-medium mb-1">{s.value}</p>
                <p className="text-sm text-muted">{s.sub}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Ticker */}
      <div className="border-y border-border overflow-hidden py-3 bg-surface">
        <div className="animate-marquee">
          {tickers.map((item, i) => (
            <span
              key={i}
              className="font-mono text-[11px] text-faint uppercase tracking-widest px-8 whitespace-nowrap"
            >
              {item}
              <span className="ml-8 text-border-dark">·</span>
            </span>
          ))}
        </div>
      </div>

      <Features />

      {/* Pull quote */}
      <div className="border-t border-b border-border py-20 px-6 bg-surface">
        <div className="max-w-5xl mx-auto grid grid-cols-12 gap-8 items-start">
          <div className="col-span-1">
            <span className="font-display font-medium text-[96px] leading-none text-border-dark">&ldquo;</span>
          </div>
          <div className="col-span-11 pt-6">
            <blockquote className="font-display text-4xl font-medium leading-tight max-w-3xl" style={{ color: "#3A2E24" }}>
              The gap between writing code and shipping code
              is where most effort disappears. Nimbus closes it.
            </blockquote>
          </div>
        </div>
      </div>

      <Workflow />

      {/* CTA */}
      <section className="py-24 px-6 border-t border-border bg-surface">
        <div className="max-w-5xl mx-auto grid grid-cols-2 gap-20 items-start">
          <div>
            <p className="font-mono text-[10px] text-faint uppercase tracking-widest mb-6">Get started</p>
            <h2 className="font-display font-medium leading-tight mb-6" style={{ fontSize: "56px" }}>
              Operational<br />
              <em className="italic" style={{ color: "#8E2D2D" }}>in minutes.</em>
            </h2>
            <p className="text-muted text-[15px] leading-relaxed max-w-sm">
              Clone the repository, configure your API keys, and point Nimbus
              at a target repository with a task description.
            </p>
            <div className="flex items-center gap-3 mt-8">
              <a
                href="https://github.com/arpjw/nimbus"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-5 py-2.5 bg-text text-bg text-sm font-medium hover:bg-brown rounded-sm transition-colors"
              >
                <Github size={13} /> View on GitHub
              </a>
              <Link
                href="/dashboard"
                className="flex items-center gap-2 px-5 py-2.5 border border-border text-sm hover:border-border-dark rounded-sm transition-colors"
              >
                Dashboard
              </Link>
            </div>
          </div>

          <div>
            <p className="font-mono text-[10px] text-faint uppercase tracking-widest mb-4">Quick start</p>
            <div
              className="font-mono text-[13px] leading-relaxed border border-border rounded-sm px-5 py-4"
              style={{ background: "#16120D", color: "#C8BFB0" }}
            >
              <p style={{ color: "#5C5040" }}># install the CLI</p>
              <p>pip install -e ./backend</p>
              <p>&nbsp;</p>
              <p style={{ color: "#5C5040" }}># or use the hosted backend</p>
              <p>nimbus run "add rate limiting" \</p>
              <p>{"  "}--backend https://api.get-nimbus.com \</p>
              <p>{"  "}--api-key nk_...</p>
              <p>&nbsp;</p>
              <p style={{ color: "#5C5040" }}># generate a free API key</p>
              <p>curl -X POST \</p>
              <p>{"  "}https://api.get-nimbus.com/keys/generate</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-6">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="font-display italic text-lg font-medium">Nimbus</span>
            <span className="text-faint font-mono text-[11px]">MIT License · 2026</span>
          </div>
          <div className="flex items-center gap-6 font-mono text-[11px] text-faint">
            <a href="https://github.com/arpjw/nimbus" className="hover:text-muted transition-colors">GitHub</a>
            <a href="https://arpjw.github.io" className="hover:text-muted transition-colors">arpjw.github.io</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
