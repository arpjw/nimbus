import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Nimbus",
  description: "Autonomous software engineering",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Nimbus",
  },
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      background: "#0A0A0A",
      minHeight: "100dvh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      color: "#FAFAFA",
      fontFamily: "var(--font-jakarta), system-ui, sans-serif",
    }}>
      {children}
    </div>
  );
}
