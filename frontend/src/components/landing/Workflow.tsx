const PHASES = [
  { n: "01", label: "Clone", detail: "Creates isolated workspace, checks out target branch", color: "text-info" },
  { n: "02", label: "Index", detail: "Voyage-code-2 embeddings + BM25 corpus over all files", color: "text-info" },
  { n: "03", label: "Plan", detail: "Claude Opus generates a file-level change plan via RAG", color: "text-warning" },
  { n: "04", label: "Implement", detail: "Claude Sonnet executes plan via agentic tool-use loop", color: "text-warning" },
  { n: "05", label: "Verify", detail: "Runs pytest / tsc / eslint / cargo — loops on failure", color: "text-accent" },
  { n: "06", label: "Review", detail: "Self-reviews diff, posts critique, responds to comments", color: "text-accent" },
  { n: "07", label: "PR", detail: "Pushes branch and opens PR against default branch", color: "text-accent" },
];

export function Workflow() {
  return (
    <section className="py-24 px-6 border-t border-border" id="workflow">
      <div className="max-w-5xl mx-auto">
        <p className="font-mono text-accent text-xs tracking-widest uppercase mb-4">Workflow</p>
        <h2 className="font-sans text-4xl font-bold mb-12">7-phase execution.</h2>

        <div className="relative">
          <div className="absolute left-[52px] top-6 bottom-6 w-px bg-border" />
          <div className="space-y-2">
            {PHASES.map((p, i) => (
              <div key={p.n} className="flex items-start gap-6 group">
                <div className="flex-shrink-0 w-[104px] flex items-center justify-end gap-4">
                  <span className="font-mono text-xs text-muted/50 w-6 text-right">{p.n}</span>
                  <div className={`w-2.5 h-2.5 rounded-full border-2 flex-shrink-0 z-10
                    ${p.color === "text-info" ? "border-info bg-info/20" : ""}
                    ${p.color === "text-warning" ? "border-warning bg-warning/20" : ""}
                    ${p.color === "text-accent" ? "border-accent bg-accent/20" : ""}
                  `} />
                </div>
                <div className={`flex-1 py-4 px-5 rounded-lg border border-transparent
                  group-hover:border-border group-hover:bg-surface transition-all duration-200`}>
                  <div className="flex items-baseline gap-3">
                    <span className={`font-sans font-semibold text-base ${p.color}`}>{p.label}</span>
                    <span className="font-body text-sm text-muted">{p.detail}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
