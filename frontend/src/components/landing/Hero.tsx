"use client";
import { useEffect, useState } from "react";

const LINES = [
  { d: 0,    t: "$ nimbus run \\", c: "agent" },
  { d: 400,  t: "    --repo github.com/acme/api \\", c: "agent" },
  { d: 700,  t: "    --task 'migrate auth middleware to JWT'", c: "agent" },
  { d: 1100, t: "", c: "info" },
  { d: 1200, t: "  cloning repository                   0.9s", c: "info" },
  { d: 1900, t: "  indexing 847 files, 12304 chunks     4.1s", c: "info" },
  { d: 2700, t: "  planning via claude opus...", c: "info" },
  { d: 3400, t: "", c: "info" },
  { d: 3500, t: "  plan", c: "tool" },
  { d: 3700, t: "  ├─ modify  src/middleware/auth.ts", c: "tool" },
  { d: 3900, t: "  ├─ modify  src/routes/login.ts", c: "tool" },
  { d: 4100, t: "  └─ create  src/lib/jwt.ts", c: "tool" },
  { d: 4800, t: "", c: "info" },
  { d: 4900, t: "  implementing...", c: "info" },
  { d: 5400, t: "  read   src/middleware/auth.ts", c: "tool" },
  { d: 5700, t: "  write  src/lib/jwt.ts", c: "tool" },
  { d: 6000, t: "  write  src/middleware/auth.ts", c: "tool" },
  { d: 6700, t: "", c: "info" },
  { d: 6800, t: "  tsc ✓  eslint ✓", c: "done" },
  { d: 7300, t: "  self-review · approve", c: "done" },
  { d: 7800, t: "  PR #47 → github.com/acme/api/pull/47", c: "done" },
  { d: 8400, t: "", c: "info" },
  { d: 8500, t: "  done in 18.4s", c: "agent" },
];

export function HeroTerminal() {
  const [visible, setVisible] = useState<number[]>([]);

  useEffect(() => {
    const timers = LINES.map((l, i) =>
      setTimeout(() => setVisible((v) => [...v, i]), l.d)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div
      className="rounded-sm border border-stone-700/40 overflow-hidden flex flex-col"
      style={{ background: "#16120D", height: "440px" }}
    >
      {/* Title bar — fixed */}
      <div className="flex-shrink-0 flex items-center gap-1.5 px-4 py-2.5 border-b border-stone-700/30">
        <span className="w-2.5 h-2.5 rounded-full bg-stone-700/60" />
        <span className="w-2.5 h-2.5 rounded-full bg-stone-700/60" />
        <span className="w-2.5 h-2.5 rounded-full bg-stone-700/60" />
        <span className="ml-2 font-mono text-[11px] text-stone-600">nimbus — zsh</span>
      </div>

      {/* Scrollable log — lines appear inside fixed box, no layout shift */}
      <div className="flex-1 overflow-hidden p-5">
        {LINES.map((l, i) =>
          visible.includes(i) ? (
            <div key={i} className={`log-line ${l.c}`}>{l.t || "\u00A0"}</div>
          ) : null
        )}
        {visible.length < LINES.length && (
          <span className="cursor-blink font-mono text-xs" />
        )}
      </div>
    </div>
  );
}
