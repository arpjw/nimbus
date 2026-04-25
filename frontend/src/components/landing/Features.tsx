const FEATURES = [
  {
    n: "01",
    label: "Retrieval",
    title: "Hybrid\ncode search",
    desc: "Voyage AI's voyage-code-2 embeddings fused with BM25 keyword matching via Reciprocal Rank Fusion. Captures semantic intent and exact symbol names simultaneously — across one repository or many.",
    wide: true,
  },
  {
    n: "02",
    label: "Planning",
    title: "Grounded\nplans",
    desc: "Claude Opus reasons over retrieved context to produce a file-level change plan before a single line is written.",
    wide: false,
  },
  {
    n: "03",
    label: "Implementation",
    title: "Agentic\ntool-use loop",
    desc: "Claude Sonnet reads current file contents, writes targeted changes, and verifies its output — iterating rather than generating in a single pass.",
    wide: false,
  },
  {
    n: "04",
    label: "Verification",
    title: "Your actual\ntest suite",
    desc: "Runs pytest, tsc, eslint, or cargo. On failure, reformulates the plan with error output as context and tries again.",
    wide: false,
  },
  {
    n: "05",
    label: "Review",
    title: "Self-review\nand response",
    desc: "After opening a PR, Nimbus retrieves its own diff, posts a structured critique, then monitors for human comments and responds with technical precision.",
    wide: true,
  },
  {
    n: "06",
    label: "Scope",
    title: "Multi-repo\nworkspaces",
    desc: "Index multiple repositories into one workspace. Retrieve context across service boundaries for tasks that span codebases.",
    wide: false,
  },
];

export function Features() {
  return (
    <section className="py-24 px-6" id="features">
      <div className="max-w-5xl mx-auto">

        {/* Section header */}
        <div className="flex items-baseline gap-8 mb-16">
          <h2
            className="font-display font-medium italic"
            style={{ fontSize: "52px", color: "#7A6B5E" }}
          >
            What it does
          </h2>
          <div className="flex-1 h-px bg-border" />
        </div>

        {/* Row 1: wide + narrow */}
        <div className="grid grid-cols-3 gap-px bg-border mb-px">
          {/* Wide — spans 2 */}
          <FeatureCell f={FEATURES[0]} span={2} tall />
          <FeatureCell f={FEATURES[1]} span={1} tall />
        </div>

        {/* Row 2: narrow + narrow + wide */}
        <div className="grid grid-cols-3 gap-px bg-border mb-px">
          <FeatureCell f={FEATURES[2]} span={1} />
          <FeatureCell f={FEATURES[3]} span={1} />
          <FeatureCell f={FEATURES[4]} span={1} />
        </div>

        {/* Row 3: full */}
        <div className="grid grid-cols-3 gap-px bg-border">
          <FeatureCell f={FEATURES[5]} span={3} horizontal />
        </div>
      </div>
    </section>
  );
}

function FeatureCell({
  f,
  span,
  tall,
  horizontal,
}: {
  f: (typeof FEATURES)[0];
  span: number;
  tall?: boolean;
  horizontal?: boolean;
}) {
  return (
    <div
      className="bg-bg relative overflow-hidden group"
      style={{
        gridColumn: `span ${span}`,
        padding: "40px 44px",
        minHeight: tall ? "280px" : horizontal ? "auto" : "240px",
      }}
    >
      {/* Giant decorative number */}
      <div
        aria-hidden="true"
        className="absolute select-none pointer-events-none font-display font-medium"
        style={{
          fontSize: horizontal ? "180px" : "200px",
          lineHeight: 1,
          color: "rgba(180,168,152,0.13)",
          right: horizontal ? "auto" : "-12px",
          left: horizontal ? "auto" : "auto",
          bottom: "-20px",
          ...(horizontal ? { right: "32px", bottom: "-16px" } : {}),
        }}
      >
        {f.n}
      </div>

      <div className={`relative z-10 ${horizontal ? "flex items-start gap-16" : "flex flex-col justify-between h-full"}`}>
        {/* Top: label */}
        <div>
          <span className="font-mono text-[10px] uppercase tracking-widest text-faint block mb-6">
            {f.label}
          </span>

          <h3
            className="font-display font-medium leading-tight"
            style={{
              fontSize: horizontal ? "36px" : span === 2 ? "44px" : "32px",
              whiteSpace: "pre-line",
            }}
          >
            {f.title}
          </h3>
        </div>

        {/* Desc */}
        <p
          className="text-muted leading-relaxed"
          style={{
            fontSize: "14px",
            maxWidth: horizontal ? "520px" : "100%",
            marginTop: horizontal ? 0 : "20px",
          }}
        >
          {f.desc}
        </p>
      </div>

      {/* Hover accent line */}
      <div
        className="absolute bottom-0 left-0 right-0 h-px transition-all duration-300 group-hover:opacity-100 opacity-0"
        style={{ background: "#8E2D2D" }}
      />
    </div>
  );
}
