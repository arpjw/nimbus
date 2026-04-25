import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import type { Phase } from "@/types";
import { PHASE_ORDER, PHASE_LABELS } from "@/types";

const VISIBLE_PHASES: Phase[] = [
  "cloning", "indexing", "planning", "implementing",
  "verifying", "fixing", "reviewing", "done",
];

function phaseIndex(phase: Phase): number {
  return PHASE_ORDER.indexOf(phase);
}

interface Props { phase: Phase; }

export function PhaseTimeline({ phase }: Props) {
  const current = phaseIndex(phase);
  const failed = phase === "failed";

  return (
    <div className="space-y-0">
      {VISIBLE_PHASES.map((p) => {
        const idx = phaseIndex(p);
        const isDone = current > idx && !failed;
        const isActive = current === idx || (p === "done" && current >= phaseIndex("cleanup") && !failed);
        const isFuture = current < idx;
        const isFailedPhase = failed && current === idx;

        return (
          <div key={p} className="flex items-start gap-3 group">
            <div className="flex flex-col items-center">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5
                ${isDone ? "bg-accent/20 text-accent" : ""}
                ${isActive ? "bg-warning/20 text-warning" : ""}
                ${isFuture ? "bg-border text-muted/30" : ""}
                ${isFailedPhase ? "bg-danger/20 text-danger" : ""}
              `}>
                {isDone && <CheckCircle2 size={13} />}
                {isActive && !failed && <Loader2 size={13} className="animate-spin" />}
                {isFuture && <Circle size={13} />}
                {isFailedPhase && <XCircle size={13} />}
              </div>
              {p !== "done" && (
                <div className={`w-px flex-1 min-h-[24px] mt-0.5
                  ${isDone ? "bg-accent/30" : "bg-border"}`}
                />
              )}
            </div>
            <div className={`py-1 pb-4 ${isFuture ? "opacity-30" : ""}`}>
              <p className={`font-sans text-sm font-medium leading-tight
                ${isDone ? "text-accent" : ""}
                ${isActive ? "text-warning" : ""}
                ${isFuture ? "text-muted" : ""}
                ${isFailedPhase ? "text-danger" : ""}
              `}>
                {PHASE_LABELS[p]}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
