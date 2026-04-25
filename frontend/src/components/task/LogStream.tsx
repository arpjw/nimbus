"use client";
import { useEffect, useRef } from "react";
import type { LogLine } from "@/types";
import { PHASE_LABELS } from "@/types";

interface Props {
  logs: LogLine[];
  connected: boolean;
}

const LINE_COLORS: Record<LogLine["type"], string> = {
  agent: "text-text/70",
  tool:  "text-accent/80",
  error: "text-danger",
  done:  "text-accent font-semibold",
  info:  "text-muted",
};

const LINE_PREFIX: Record<LogLine["type"], string> = {
  agent: "   ",
  tool:  " → ",
  error: "[!]",
  done:  "[✓]",
  info:  "   ",
};

export function LogStream({ logs, connected }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

  return (
    <div className="flex flex-col h-full">
      {/* Status bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-surface-raised">
        <span className="font-mono text-xs text-muted">execution log</span>
        <div className="flex items-center gap-2">
          <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-accent animate-pulse-accent" : "bg-muted"}`} />
          <span className="font-mono text-xs text-muted">{connected ? "live" : "disconnected"}</span>
          <span className="font-mono text-xs text-muted/50">· {logs.length} events</span>
        </div>
      </div>

      {/* Log body */}
      <div className="flex-1 overflow-y-auto bg-surface font-mono text-xs">
        {logs.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-muted/40">
            Waiting for agent...
          </div>
        ) : (
          <>
            {logs.map((line, i) => {
              const prevPhase = i > 0 ? logs[i - 1].phase : null;
              const showPhaseHeader = line.phase !== prevPhase && line.phase !== "queued";
              return (
                <div key={line.id}>
                  {showPhaseHeader && (
                    <div className="px-4 py-2 mt-2 flex items-center gap-2 border-b border-border/30 bg-surface-raised/50">
                      <span className="text-muted/50 uppercase tracking-widest text-[10px]">
                        {PHASE_LABELS[line.phase] ?? line.phase}
                      </span>
                    </div>
                  )}
                  <div className={`log-line ${line.type} flex gap-2`}>
                    <span className="text-muted/40 select-none w-6 text-right flex-shrink-0">
                      {LINE_PREFIX[line.type]}
                    </span>
                    <span className={LINE_COLORS[line.type]}>
                      {line.message}
                    </span>
                  </div>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </>
        )}
      </div>
    </div>
  );
}
