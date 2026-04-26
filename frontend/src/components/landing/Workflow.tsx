const PHASES = [
  { n: "01", label: "Clone",           detail: "Isolated workspace. Feature branch." },
  { n: "02", label: "Index",           detail: "voyage-code-2 embeddings + BM25 over all source files. AST-aware chunking via tree-sitter." },
  { n: "03", label: "Plan",            detail: "Claude Opus retrieves relevant context and generates a file-level change plan." },
  { n: "04", label: "Approve",         detail: "Plan shown to user. Proceed, reject, or edit before a single line is written.", dim: true },
  { n: "05", label: "Implement",       detail: "Claude Sonnet executes the plan via agentic tool-use. Six or more changes run across parallel workers." },
  { n: "06", label: "Verify",          detail: "Test suite, type checker, linter. On failure, the plan is reformulated with error context and retried." },
  { n: "07", label: "Diff preview",    detail: "Full git diff shown before anything is pushed. One-click approve or reject.", dim: true },
  { n: "08", label: "Review",          detail: "Claude Sonnet retrieves its own diff, posts a structured critique, and responds to human reviewer comments." },
  { n: "09", label: "Pull request",    detail: "Branch pushed. PR opened against the default branch." },
  { n: "10", label: "Memory",          detail: "Task outcome written to per-repo memory. Retrieved on all future tasks for the same codebase." },
];

export function Workflow() {
  return (
    <section className="py-24 px-6 border-t border-border" id="workflow">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-baseline gap-8 mb-16">
          <h2 className="font-display font-medium italic" style={{ fontSize: "52px", color: "#7A6B5E" }}>
            Ten phases
          </h2>
          <div className="flex-1 h-px bg-border" />
        </div>

        <div className="space-y-0 max-w-3xl">
          {PHASES.map((p) => (
            <div key={p.n} className={`group grid grid-cols-12 gap-6 py-7 border-b border-border last:border-0 ${p.dim ? "opacity-60" : ""}`}>
              <div className="col-span-1 pt-0.5">
                <span className="font-mono text-xs text-faint">{p.n}</span>
              </div>
              <div className="col-span-3">
                <span className={`font-display text-2xl font-medium transition-colors duration-150 ${p.dim ? "" : "group-hover:text-red"}`}>
                  {p.label}
                </span>
              </div>
              <div className="col-span-8">
                <p className="text-muted text-sm leading-relaxed pt-1">{p.detail}</p>
              </div>
            </div>
          ))}
        </div>

        <p className="font-mono text-[11px] text-faint mt-8">
          Steps 04 and 07 are optional approval gates — pass --yes to skip both.
        </p>
      </div>
    </section>
  );
}
