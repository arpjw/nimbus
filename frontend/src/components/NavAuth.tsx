import { auth } from "@/auth";

const sans = "var(--font-sans,system-ui,sans-serif)";

export default async function NavAuth() {
  const session = await auth();

  if (session) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <a href="/dashboard" style={{ fontFamily: sans, fontSize: 14, color: "rgba(255,255,255,0.5)", textDecoration: "none" }}>Dashboard</a>
        <div style={{ width: 28, height: 28, borderRadius: "50%", overflow: "hidden", border: "1px solid rgba(255,255,255,0.1)" }}>
          {(session as any).nimbusAvatarUrl ? (
            <img src={(session as any).nimbusAvatarUrl} alt="avatar" width={28} height={28} style={{ display: "block" }} />
          ) : (
            <div style={{ width: 28, height: 28, background: "#c4a96a", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ fontFamily: sans, fontSize: 11, fontWeight: 700, color: "#0A0A0A" }}>
                {(session as any).nimbusUsername?.[0]?.toUpperCase()}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
      <a href="/login" style={{ fontFamily: sans, fontSize: 14, color: "rgba(255,255,255,0.5)", textDecoration: "none" }}>Sign in</a>
      <a href="/download" style={{ fontFamily: sans, fontSize: 14, fontWeight: 600, color: "#0A0A0A", background: "#FAFAFA", padding: "8px 20px", borderRadius: 999, textDecoration: "none" }}>Download</a>
    </div>
  );
}
