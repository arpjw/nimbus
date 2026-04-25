import Link from "next/link";
import { ArrowRight, Github } from "lucide-react";
import { HeroTerminal } from "@/components/landing/Hero";
import { Features } from "@/components/landing/Features";
import { Workflow } from "@/components/landing/Workflow";

export default function Landing() {
  return (
    <div className="min-h-screen">

      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 backdrop-blur-md bg-bg/80">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-sm bg-accent flex items-center justify-center">
              <span className="font-sans font-black text-bg text-xs">N</span>
            </div>
            <span className="font-sans font-bold text-sm tracking-tight">Nimbus</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#features" className="font-body text-sm text-muted hover:text-text transition-colors">Features</a>
            <a href="#workflow" className="font-body text-sm text-muted hover:text-text transition-colors">Workflow</a>
            <a
              href="https://github.com/arpjw/nimbus"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 font-body text-sm text-muted hover:text-text transition-colors"
            >
              <Github size={14} />
              GitHub
            </a>
            <Link
              href="/dashboard"
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-accent text-bg text-sm font-semibold font-sans hover:bg-accent/90 transition-colors"
            >
              Launch <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6 grid-bg mesh-gradient relative overflow-hidden">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-2 gap-16 items-start">

            {/* Left copy */}
            <div className="animate-in pt-4">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-accent/20 bg-accent/5 mb-8">
                <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-accent" />
                <span className="font-mono text-xs text-accent">Powered by Claude + Voyage AI</span>
              </div>

              <h1 className="font-sans font-black text-6xl leading-[1.05] tracking-tight mb-6">
                Autonomous
                <br />
                software
                <br />
                <span className="text-accent text-glow">engineering.</span>
              </h1>

              <p className="font-body text-muted text-lg leading-relaxed mb-10 max-w-sm">
                Multi-repo SWE agent with hybrid RAG, Claude Code CLI integration,
                and a self-reviewing PR loop. Ships code. Responds to reviews.
              </p>

              <div className="flex items-center gap-4">
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 px-6 py-3 rounded-xl bg-accent text-bg font-sans font-bold text-sm hover:bg-accent/90 transition-all glow-accent"
                >
                  Open Dashboard <ArrowRight size={16} />
                </Link>
                <a
                  href="https://github.com/arpjw/nimbus"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-6 py-3 rounded-xl border border-border text-text font-sans font-medium text-sm hover:border-border-bright transition-colors"
                >
                  <Github size={16} /> View Source
                </a>
              </div>

              <div className="mt-10 flex items-center gap-6 font-mono text-xs text-muted">
                <span><span className="text-accent">voyage-code-2</span> embeddings</span>
                <span><span className="text-info">BM25 + RRF</span> hybrid search</span>
                <span><span className="text-warning">Multi-repo</span> workspaces</span>
              </div>
            </div>

            {/* Right terminal */}
            <div className="animate-in" style={{ animationDelay: "200ms" }}>
              <HeroTerminal />
            </div>
          </div>
        </div>

        {/* Decorative line */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
      </section>

      <Features />
      <Workflow />

      {/* CTA */}
      <section className="py-24 px-6 border-t border-border">
        <div className="max-w-5xl mx-auto text-center">
          <p className="font-mono text-accent text-xs tracking-widest uppercase mb-4">Get started</p>
          <h2 className="font-sans font-black text-5xl mb-4">
            Ship code.<br />Not just diffs.
          </h2>
          <p className="font-body text-muted text-lg mb-10 max-w-md mx-auto">
            Clone the repo, add your API keys, and point Nimbus at your first PR task in under five minutes.
          </p>
          <div className="flex items-center justify-center gap-4">
            <a
              href="https://github.com/arpjw/nimbus"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-accent text-bg font-sans font-bold hover:bg-accent/90 transition-all glow-accent"
            >
              <Github size={16} /> Clone on GitHub
            </a>
            <Link
              href="/dashboard"
              className="flex items-center gap-2 px-6 py-3 rounded-xl border border-border text-text font-sans font-medium hover:border-border-bright transition-colors"
            >
              Open Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-6">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-sm bg-accent flex items-center justify-center">
              <span className="font-sans font-black text-bg text-[10px]">N</span>
            </div>
            <span className="font-mono text-xs text-muted">Nimbus © 2026 · MIT License</span>
          </div>
          <div className="flex items-center gap-4 font-mono text-xs text-muted">
            <a href="https://github.com/arpjw/nimbus" className="hover:text-text transition-colors">GitHub</a>
            <a href="/docs" className="hover:text-text transition-colors">Docs</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
