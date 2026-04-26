"use client";
import { useEffect, useState } from "react";

const sans  = "var(--font-sans,system-ui,sans-serif)";
const mono  = "var(--font-mono,monospace)";
const serif = "var(--font-serif,'Georgia',serif)";
const API   = process.env.NEXT_PUBLIC_API_URL || "https://api.get-nimbus.com";

const C = {
  bg: "#0A0A0A", text: "#FAFAFA", muted: "rgba(255,255,255,0.5)",
  faint: "rgba(255,255,255,0.25)", gold: "#c4a96a", green: "#6aab7a",
  border: "rgba(255,255,255,0.07)", surface: "#0d0d0d",
};

interface Skill {
  name: string;
  description: string;
  tags?: string;
  install_count?: number;
  star_count?: number;
  author_username?: string;
  version?: string;
}

export default function MarketplacePage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSkills = async () => {
      setLoading(true);
      try {
        const r = await fetch(`${API}/marketplace/skills?q=${encodeURIComponent(query)}&limit=50`);
        if (r.ok) setSkills(await r.json());
      } catch {}
      setLoading(false);
    };
    const t = setTimeout(fetchSkills, 300);
    return () => clearTimeout(t);
  }, [query]);

  return (
    <div style={{ background: C.bg, color: C.text, minHeight: "100vh", fontFamily: sans }}>
      <nav style={{ position: "sticky", top: 0, zIndex: 50, height: 56, background: "rgba(10,10,10,0.9)", backdropFilter: "blur(16px)", borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", padding: "0 28px", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
          <a href="/" style={{ display: "flex", alignItems: "center", gap: 8, textDecoration: "none" }}>
            <div style={{ width: 22, height: 22, borderRadius: 5, background: C.text, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ color: C.bg, fontWeight: 800, fontSize: 12 }}>N</span>
            </div>
            <span style={{ fontFamily: serif, fontStyle: "italic", fontSize: 17, color: C.text }}>Nimbus</span>
          </a>
          <span style={{ fontFamily: mono, fontSize: 11, color: C.faint, letterSpacing: "0.06em", textTransform: "uppercase" }}>Skill Marketplace</span>
        </div>
        <a href="/login" style={{ fontFamily: sans, fontSize: 13, fontWeight: 600, color: C.bg, background: C.text, padding: "7px 18px", borderRadius: 999, textDecoration: "none" }}>Publish a skill</a>
      </nav>

      <div style={{ maxWidth: 900, margin: "0 auto", padding: "60px 28px" }}>
        <h1 style={{ fontFamily: serif, fontSize: 38, fontWeight: 400, letterSpacing: "-0.02em", marginBottom: 12, color: C.text }}>
          Skill Marketplace
        </h1>
        <p style={{ fontFamily: sans, fontSize: 16, color: C.muted, marginBottom: 36, maxWidth: 480 }}>
          Community-published skills for Nimbus. Install any skill with{" "}
          <code style={{ fontFamily: mono, fontSize: 13, color: "rgba(255,255,255,0.6)", background: "rgba(255,255,255,0.06)", padding: "1px 6px", borderRadius: 4 }}>
            nimbus skills install &lt;name&gt;
          </code>
        </p>

        <input
          type="text"
          placeholder="Search skills..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          style={{ width: "100%", background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: "12px 18px", fontFamily: mono, fontSize: 14, color: C.text, outline: "none", marginBottom: 32, boxSizing: "border-box" }}
        />

        {loading ? (
          <p style={{ fontFamily: mono, fontSize: 13, color: C.faint }}>loading...</p>
        ) : skills.length === 0 ? (
          <div style={{ textAlign: "center", padding: "60px 0" }}>
            <p style={{ fontFamily: mono, fontSize: 13, color: C.faint }}>no skills found</p>
            <p style={{ fontFamily: sans, fontSize: 14, color: C.faint, marginTop: 8 }}>
              Be the first to publish one with{" "}
              <code style={{ fontFamily: mono, fontSize: 12 }}>nimbus skills publish</code>
            </p>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(280px,1fr))", gap: 12 }}>
            {skills.map(s => (
              <div key={s.name} style={{ border: `1px solid ${C.border}`, borderRadius: 12, padding: "20px 22px", background: C.surface }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                  <span style={{ fontFamily: mono, fontSize: 13, fontWeight: 600, color: C.gold }}>{s.name}</span>
                  <span style={{ fontFamily: mono, fontSize: 10, color: C.faint }}>{s.version || "1.0.0"}</span>
                </div>
                <p style={{ fontFamily: sans, fontSize: 13, color: C.muted, lineHeight: 1.6, marginBottom: 14 }}>{s.description}</p>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", gap: 8 }}>
                    {s.tags?.split(",").slice(0, 2).map(t => (
                      <span key={t} style={{ fontFamily: mono, fontSize: 10, color: C.faint, background: "rgba(255,255,255,0.04)", border: `1px solid ${C.border}`, padding: "2px 7px", borderRadius: 4 }}>{t.trim()}</span>
                    ))}
                  </div>
                  <span style={{ fontFamily: mono, fontSize: 11, color: C.faint }}>↓{s.install_count || 0}</span>
                </div>
                {s.author_username && (
                  <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.2)", marginTop: 10 }}>by {s.author_username}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
