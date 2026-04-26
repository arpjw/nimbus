"use client";
import { useState } from "react";

const sans  = "var(--font-sans,system-ui,sans-serif)";
const serif = "var(--font-serif,'Georgia',serif)";

export default function NavMobile() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setOpen(!open)}
        style={{ background: "none", border: "none", cursor: "pointer", padding: "4px", display: "flex", flexDirection: "column", gap: 5 }}
        aria-label="Menu"
      >
        <span style={{ display: "block", width: 20, height: 1.5, background: open ? "transparent" : "rgba(255,255,255,0.7)", transition: "all 0.2s" }} />
        <span style={{ display: "block", width: 20, height: 1.5, background: "rgba(255,255,255,0.7)", transform: open ? "rotate(45deg) translateY(0px)" : "none", transition: "all 0.2s" }} />
        <span style={{ display: "block", width: 20, height: 1.5, background: "rgba(255,255,255,0.7)", transform: open ? "rotate(-45deg) translateY(-6.5px)" : "none", transition: "all 0.2s" }} />
      </button>

      {open && (
        <div style={{ position: "fixed", inset: 0, background: "#0A0A0A", zIndex: 200, display: "flex", flexDirection: "column", padding: "80px 32px 32px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {([["Product", "/#product"], ["Docs", "https://docs.get-nimbus.com"], ["GitHub", "https://github.com/arpjw/nimbus"], ["Download", "/download"]] as [string, string][]).map(([l, h]) => (
              <a key={l} href={h} onClick={() => setOpen(false)}
                style={{ fontFamily: serif, fontStyle: "italic", fontSize: 32, fontWeight: 400, color: "#FAFAFA", textDecoration: "none", padding: "12px 0", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                {l}
              </a>
            ))}
          </div>
          <div style={{ marginTop: "auto" }}>
            <a href="/login"
              style={{ display: "block", fontFamily: sans, fontSize: 15, fontWeight: 600, color: "#0A0A0A", background: "#FAFAFA", padding: "14px 28px", borderRadius: 999, textDecoration: "none", textAlign: "center" }}>
              Sign in with GitHub
            </a>
          </div>
        </div>
      )}
    </>
  );
}
