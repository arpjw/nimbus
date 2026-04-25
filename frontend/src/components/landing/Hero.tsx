"use client";
import { useEffect, useState } from "react";

const TERMINAL_LINES = [
  { delay: 0,    text: "$ nimbus run --repo github.com/acme/api --task 'migrate auth to JWT'", type: "cmd" },
  { delay: 800,  text: "◈ Cloning repository...                                    [0.8s]", type: "info" },
  { delay: 1600, text: "◈ Building Voyage AI code embeddings (voyage-code-2)...     [4.2s]", type: "info" },
  { delay: 2200, text: "  ↳ 847 files · 12,304 chunks indexed", type: "dim" },
  { delay: 3000, text: "◈ Generating implementation plan (Claude Opus)...", type: "info" },
  { delay: 3800, text: "  [MODIFY] src/middleware/auth.ts — Replace JWT verify logic", type: "plan" },
  { delay: 4000, text: "  [MODIFY] src/routes/login.ts — Update token issuance", type: "plan" },
  { delay: 4200, text: "  [CREATE] src/lib/jwt.ts — Centralized JWT utilities", type: "plan" },
  { delay: 5000, text: "◈ Implementing (iteration 1/5)...", type: "info" },
  { delay: 5400, text: "  [tool] read_file({path: 'src/middleware/auth.ts'})", type: "tool" },
  { delay: 5900, text: "  [tool] write_file({path: 'src/lib/jwt.ts', content: ...})", type: "tool" },
  { delay: 6400, text: "  [tool] write_file({path: 'src/middleware/auth.ts', ...})", type: "tool" },
  { delay: 7200, text: "◈ Verifying — tsc, eslint                                  [PASS]", type: "success" },
  { delay: 8000, text: "◈ Self-review (Claude Sonnet) — verdict: APPROVE", type: "success" },
  { delay: 8600, text: "◈ PR created → github.com/acme/api/pull/47", type: "success" },
  { delay: 9200, text: "✓ Task complete in 18.4s", type: "done" },
];

const COLOR: Record<string, string> = {
  cmd:     "text-text font-medium",
  info:    "text-muted",
  dim:     "text-muted/60",
  plan:    "text-info/80",
  tool:    "text-accent/70",
  success: "text-accent",
  done:    "text-accent font-semibold",
};

export function HeroTerminal() {
  const [visible, setVisible] = useState<number[]>([]);

  useEffect(() => {
    const timers = TERMINAL_LINES.map((line, i) =>
      setTimeout(() => setVisible((v) => [...v, i]), line.delay)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="rounded-xl border border-border bg-surface overflow-hidden shadow-2xl">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-surface-raised">
        <span className="w-3 h-3 rounded-full bg-danger/60" />
        <span className="w-3 h-3 rounded-full bg-warning/60" />
        <span className="w-3 h-3 rounded-full bg-accent/60" />
        <span className="ml-3 font-mono text-xs text-muted">nimbus — zsh</span>
      </div>
      <div className="p-4 font-mono text-xs space-y-1 min-h-[320px]">
        {TERMINAL_LINES.map((line, i) =>
          visible.includes(i) ? (
            <div
              key={i}
              className={`${COLOR[line.type] ?? "text-text"} leading-6 transition-opacity duration-200`}
            >
              {line.text}
            </div>
          ) : null
        )}
        {visible.length < TERMINAL_LINES.length && (
          <span className="cursor-blink text-accent" />
        )}
      </div>
    </div>
  );
}
