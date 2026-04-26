import { Suspense } from "react";
import NavAuth from "@/components/NavAuth";
import NavScrollEffect from "@/components/NavScrollEffect";
import NavMobile from "@/components/NavMobile";

const serif = "var(--font-serif,'Georgia',serif)";
const sans  = "var(--font-sans,system-ui,sans-serif)";
const W     = 1100;
const C     = { bg: "#0A0A0A", text: "#FAFAFA", muted: "rgba(255,255,255,0.5)" };

export default function Navbar() {
  return (
    <>
      <NavScrollEffect />
      <nav id="main-nav" style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 100, height: 56, borderBottom: "1px solid transparent", background: "transparent", backdropFilter: "none", transition: "all 0.3s ease" }}>
        <div style={{ maxWidth: W, margin: "0 auto", padding: "0 28px", height: "100%", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
              <div style={{ width: 22, height: 22, borderRadius: 5, background: C.text, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: C.bg, fontWeight: 800, fontSize: 12, fontFamily: sans }}>N</span>
              </div>
              <span style={{ fontWeight: 400, fontSize: 17, fontStyle: "italic", color: C.text, fontFamily: serif }}>Nimbus</span>
            </div>
            <div className="nav-desktop-links" style={{ display: "flex", gap: 32 }}>
              {([["Product", "/#product"], ["Docs", "https://docs.get-nimbus.com"], ["Marketplace", "/marketplace"], ["GitHub", "https://github.com/arpjw/nimbus"], ["Download", "/download"]] as [string, string][]).map(([l, h]) => (
                <a key={l} href={h} style={{ fontFamily: sans, fontSize: 14, color: C.muted, textDecoration: "none" }}>{l}</a>
              ))}
            </div>
          </div>
          <div className="nav-auth-desktop">
            <Suspense fallback={<a href="/login" style={{ fontFamily: sans, fontSize: 14, color: C.muted, textDecoration: "none" }}>Sign in</a>}>
              <NavAuth />
            </Suspense>
          </div>
          <div className="nav-mobile-menu" style={{ display: "none" }}>
            <NavMobile />
          </div>
        </div>
      </nav>
    </>
  );
}
