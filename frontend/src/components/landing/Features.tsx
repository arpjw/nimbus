import { GitPullRequest, Brain, Search, Terminal, RefreshCw, Layers } from "lucide-react";

const FEATURES = [
  {
    icon: Brain,
    title: "Voyage-code-2 RAG",
    desc: "Purpose-built code embeddings fused with BM25 via Reciprocal Rank Fusion. Understands symbol names, function signatures, and architecture patterns — not just text similarity.",
    span: "col-span-2",
    accent: true,
  },
  {
    icon: Layers,
    title: "Multi-Repo Workspaces",
    desc: "Index multiple repositories into a single workspace. Retrieve context across codebases to handle tasks that span service boundaries.",
    span: "col-span-1",
  },
  {
    icon: Terminal,
    title: "Claude Code Integration",
    desc: "Delegates complex subtasks to the Claude Code CLI agent, combining high-level planning with native shell tool-use for maximum coverage.",
    span: "col-span-1",
  },
  {
    icon: GitPullRequest,
    title: "Tighter PR Loop",
    desc: "After creating a PR, Nimbus self-reviews its own diff, posts a structured critique, then monitors for human comments and responds with technical precision.",
    span: "col-span-2",
    accent: true,
  },
  {
    icon: RefreshCw,
    title: "Iterative Verification",
    desc: "Runs your actual test suite, type checker, and linter. Loops back into planning on failure — not just retrying the same broken code.",
    span: "col-span-1",
  },
  {
    icon: Search,
    title: "Real-Time Streaming",
    desc: "Every tool call, plan step, and verification result streams to the dashboard via WebSocket. Watch the agent think.",
    span: "col-span-1",
  },
];

export function Features() {
  return (
    <section className="py-24 px-6" id="features">
      <div className="max-w-5xl mx-auto">
        <p className="font-mono text-accent text-xs tracking-widest uppercase mb-4">Capabilities</p>
        <h2 className="font-sans text-4xl font-bold mb-2">Built different.</h2>
        <p className="text-muted font-body text-lg mb-12 max-w-xl">
          Not a wrapper around an existing agent. A ground-up architecture designed for multi-repo, production-grade automation.
        </p>

        <div className="grid grid-cols-3 gap-4">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <div
                key={f.title}
                className={`${f.span} rounded-xl border p-6 card-hover cursor-default
                  ${f.accent
                    ? "border-accent/20 bg-surface-raised/80"
                    : "border-border bg-surface"
                  }`}
              >
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-4
                  ${f.accent ? "bg-accent/10" : "bg-border"}`}>
                  <Icon size={18} className={f.accent ? "text-accent" : "text-muted"} />
                </div>
                <h3 className="font-sans font-semibold text-lg mb-2">{f.title}</h3>
                <p className="font-body text-muted text-sm leading-relaxed">{f.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
