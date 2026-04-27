"use client";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";

export const dynamic = 'force-dynamic';

const sans  = "var(--font-sans,system-ui,sans-serif)";
const mono  = "var(--font-mono,monospace)";
const serif = "var(--font-serif,'Georgia',serif)";
const API   = process.env.NEXT_PUBLIC_API_URL || "https://api.get-nimbus.com";

const C = {
  bg: "#0A0A0A", text: "#FAFAFA", muted: "rgba(255,255,255,0.5)",
  faint: "rgba(255,255,255,0.2)", gold: "#c4a96a", green: "#6aab7a",
  border: "rgba(255,255,255,0.07)", surface: "#0d0d0d",
};

interface VelocityData {
  period_days: number;
  current: {
    total_tasks: number;
    success_rate: number;
    prs_opened: number;
    avg_duration_minutes: number;
    estimated_hours_saved: number;
    estimated_cost_usd: number;
    by_type: Record<string, number>;
  };
  deltas: {
    total_tasks: number | null;
    success_rate: number | null;
    prs_opened: number | null;
    hours_saved: number | null;
  };
}

function StatCard({ label, value, unit, delta }: { label: string; value: string | number; unit?: string; delta?: number | null }) {
  const deltaColor = delta && delta > 0 ? C.green : delta && delta < 0 ? "#e06c75" : C.faint;
  const deltaSign = delta && delta > 0 ? "+" : "";
  return (
    <div style={{ border: `1px solid ${C.border}`, borderRadius: 12, padding: "22px 24px", background: C.surface }}>
      <p style={{ fontFamily: mono, fontSize: 10, color: C.faint, letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 12 }}>{label}</p>
      <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginBottom: 8 }}>
        <span style={{ fontFamily: serif, fontSize: 36, fontWeight: 400, color: C.text, letterSpacing: "-0.02em" }}>{value}</span>
        {unit && <span style={{ fontFamily: mono, fontSize: 13, color: C.muted }}>{unit}</span>}
      </div>
      {delta !== null && delta !== undefined && (
        <span style={{ fontFamily: mono, fontSize: 11, color: deltaColor }}>
          {deltaSign}{delta} vs last period
        </span>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  const { data: session } = useSession();
  const [data, setData] = useState<VelocityData | null>(null);
  const [timeline, setTimeline] = useState<{ date: string; total: number; successful: number; prs: number }[]>([]);
  const [period, setPeriod] = useState(30);
  const [loading, setLoading] = useState(true);
  const workspaceId = (session as any)?.nimbusUserId || "";

  useEffect(() => {
    if (!workspaceId) return;
    const load = async () => {
      setLoading(true);
      try {
        const token = (session as any)?.nimbusToken;
        const headers = { Authorization: `Bearer ${token}` };
        const [v, t] = await Promise.all([
          fetch(`${API}/analytics/velocity?workspace_id=${workspaceId}&period_days=${period}`, { headers }).then(r => r.json()),
          fetch(`${API}/analytics/velocity/timeline?workspace_id=${workspaceId}&period_days=${period}`, { headers }).then(r => r.json()),
        ]);
        setData(v);
        setTimeline(Array.isArray(t) ? t : []);
      } catch {}
      setLoading(false);
    };
    load();
  }, [workspaceId, period, session]);

  return (
    <div style={{ background: C.bg, minHeight: "100vh", color: C.text, fontFamily: sans }}>
      <nav style={{ height: 56, borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", padding: "0 28px", justifyContent: "space-between", background: "rgba(10,10,10,0.9)", backdropFilter: "blur(16px)", position: "sticky", top: 0, zIndex: 50 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
          <a href="/" style={{ display: "flex", alignItems: "center", gap: 8, textDecoration: "none" }}>
            <div style={{ width: 22, height: 22, borderRadius: 5, background: C.text, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ color: C.bg, fontWeight: 800, fontSize: 12 }}>N</span>
            </div>
            <span style={{ fontFamily: serif, fontStyle: "italic", fontSize: 17, color: C.text }}>Nimbus</span>
          </a>
          {([ ["Dashboard", "/dashboard"], ["Analytics", "/dashboard/analytics"], ["Health", "/dashboard/health"] ] as [string, string][]).map(([l, h]) => (
            <a key={l} href={h} style={{ fontFamily: sans, fontSize: 14, color: h === "/dashboard/analytics" ? C.text : C.muted, textDecoration: "none", fontWeight: h === "/dashboard/analytics" ? 500 : 400 }}>{l}</a>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {[7, 30, 90].map(d => (
            <button key={d} onClick={() => setPeriod(d)}
              style={{ fontFamily: mono, fontSize: 12, padding: "5px 12px", borderRadius: 6, background: period === d ? "rgba(255,255,255,0.08)" : "transparent", border: `1px solid ${period === d ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.06)"}`, color: period === d ? C.text : C.muted, cursor: "pointer" }}>
              {d}d
            </button>
          ))}
        </div>
      </nav>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "48px 28px" }}>
        <div style={{ marginBottom: 36 }}>
          <h1 style={{ fontFamily: serif, fontSize: 32, fontWeight: 400, letterSpacing: "-0.02em", marginBottom: 6 }}>Engineering Velocity</h1>
          <p style={{ fontFamily: sans, fontSize: 15, color: C.muted }}>What Nimbus shipped in the last {period} days.</p>
        </div>

        {loading ? (
          <p style={{ fontFamily: mono, fontSize: 13, color: C.faint }}>loading...</p>
        ) : data ? (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 32 }}>
              <StatCard label="Tasks completed" value={data.current.total_tasks} delta={data.deltas.total_tasks} />
              <StatCard label="PRs opened" value={data.current.prs_opened} delta={data.deltas.prs_opened} />
              <StatCard label="Success rate" value={data.current.success_rate} unit="%" delta={data.deltas.success_rate} />
              <StatCard label="Hours saved" value={data.current.estimated_hours_saved} unit="hrs" delta={data.deltas.hours_saved} />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12, marginBottom: 32 }}>
              <StatCard label="Avg task duration" value={data.current.avg_duration_minutes} unit="min" />
              <StatCard label="Estimated cost" value={`$${data.current.estimated_cost_usd}`} />
              <div style={{ border: `1px solid ${C.border}`, borderRadius: 12, padding: "22px 24px", background: C.surface }}>
                <p style={{ fontFamily: mono, fontSize: 10, color: C.faint, letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 12 }}>Tasks by type</p>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {Object.entries(data.current.by_type).slice(0, 5).map(([type, count]) => (
                    <div key={type} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontFamily: mono, fontSize: 12, color: C.muted }}>{type}</span>
                      <span style={{ fontFamily: mono, fontSize: 12, color: C.gold }}>{count as number}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {timeline.length > 0 && (
              <div style={{ border: `1px solid ${C.border}`, borderRadius: 12, padding: "24px", background: C.surface, marginBottom: 24 }}>
                <p style={{ fontFamily: mono, fontSize: 10, color: C.faint, letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 20 }}>Daily tasks</p>
                <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 80 }}>
                  {timeline.slice(-30).map((day, i) => {
                    const maxTasks = Math.max(...timeline.map(d => d.total), 1);
                    const height = Math.max((day.total / maxTasks) * 80, 2);
                    return (
                      <div key={i} title={`${day.date}: ${day.total} tasks`}
                        style={{ flex: 1, height, background: C.gold, opacity: 0.7, borderRadius: "2px 2px 0 0", minWidth: 4 }} />
                    );
                  })}
                </div>
              </div>
            )}
          </>
        ) : (
          <div style={{ textAlign: "center", padding: "60px 0" }}>
            <p style={{ fontFamily: mono, fontSize: 13, color: C.faint }}>No data yet.</p>
            <p style={{ fontFamily: sans, fontSize: 14, color: C.faint, marginTop: 8 }}>Run some Nimbus tasks and come back.</p>
          </div>
        )}
      </div>
    </div>
  );
}
