const PHASES = [
  { n: "01", label: "Clone",        detail: "Isolated workspace. Feature branch." },
  { n: "02", label: "Index",        detail: "voyage-code-2 embeddings and BM25 over all source files, persisted to ChromaDB." },
  { n: "03", label: "Plan",         detail: "Claude Opus retrieves relevant context and generates a file-level change plan." },
  { n: "04", label: "Implement",    detail: "Claude Sonnet executes the plan through an agentic read-write tool-use loop." },
  { n: "05", label: "Verify",       detail: "Test suite, type checker, linter. On failure, the plan is reformulated with error context." },
  { n: "06", label: "Review",       detail: "Diff retrieved. Structured self-critique posted to the PR. Human comments monitored and addressed." },
  { n: "07", label: "Pull request", detail: "Branch pushed. PR opened against the default branch." },
];

export function Workflow() {
  return (
    <section className="py-24 px-6 border-t border-border" id="workflow">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-baseline gap-8 mb-16">
          <h2 className="font-display text-5xl font-medium italic" style={{ color: "#7A6B5E" }}>Seven phases</h2>
          <div className="flex-1 h-px bg-border" />
        </div>

        <div className="space-y-0 max-w-3xl">
          {PHASES.map((p) => (
            <div key={p.n} className="group grid grid-cols-12 gap-6 py-7 border-b border-border last:border-0">
              <div className="col-span-1 pt-0.5">
                <span className="font-mono text-xs text-faint">{p.n}</span>
              </div>
              <div className="col-span-3">
                <span className="font-display text-2xl font-medium group-hover:text-red transition-colors duration-150">
                  {p.label}
                </span>
              </div>
              <div className="col-span-8">
                <p className="text-muted text-sm leading-relaxed pt-1">{p.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
