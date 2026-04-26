import { signIn } from "@/auth";

const serif = "var(--font-serif,'Georgia',serif)";
const sans  = "var(--font-sans,system-ui,sans-serif)";
const mono  = "var(--font-mono,monospace)";

export default function LoginPage() {
  return (
    <div style={{ background: "#0A0A0A", minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: sans }}>
      <div style={{ width: "100%", maxWidth: 380, padding: "0 24px" }}>

        <div style={{ display: "flex", alignItems: "center", gap: 10, justifyContent: "center", marginBottom: 48 }}>
          <div style={{ width: 26, height: 26, borderRadius: 6, background: "#FAFAFA", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: "#0A0A0A", fontWeight: 800, fontSize: 14, fontFamily: sans }}>N</span>
          </div>
          <span style={{ fontFamily: serif, fontStyle: "italic", fontSize: 20, color: "#FAFAFA" }}>Nimbus</span>
        </div>

        <div style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, padding: "36px 32px", background: "#0d0d0d" }}>
          <h1 style={{ fontFamily: serif, fontSize: 24, fontWeight: 400, color: "#FAFAFA", textAlign: "center", marginBottom: 8 }}>
            Sign in
          </h1>
          <p style={{ fontFamily: sans, fontSize: 14, color: "rgba(255,255,255,0.4)", textAlign: "center", marginBottom: 28 }}>
            to your Nimbus account
          </p>

          <form action={async () => {
            "use server";
            await signIn("github", { redirectTo: "/dashboard" });
          }}>
            <button type="submit" style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 12, background: "#FAFAFA", color: "#0A0A0A", border: "none", borderRadius: 9, padding: "12px 20px", fontFamily: sans, fontSize: 15, fontWeight: 600, cursor: "pointer" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
              </svg>
              Continue with GitHub
            </button>
          </form>

          <p style={{ fontFamily: mono, fontSize: 11, color: "rgba(255,255,255,0.2)", textAlign: "center", marginTop: 20, lineHeight: 1.6 }}>
            By signing in you agree to our{" "}
            <a href="/terms" style={{ color: "rgba(255,255,255,0.3)", textDecoration: "none" }}>Terms</a>
            {" "}and{" "}
            <a href="/privacy" style={{ color: "rgba(255,255,255,0.3)", textDecoration: "none" }}>Privacy Policy</a>
          </p>
        </div>

        <p style={{ fontFamily: sans, fontSize: 13, color: "rgba(255,255,255,0.2)", textAlign: "center", marginTop: 20 }}>
          <a href="/" style={{ color: "rgba(255,255,255,0.3)", textDecoration: "none" }}>Back to get-nimbus.com</a>
        </p>
      </div>
    </div>
  );
}
