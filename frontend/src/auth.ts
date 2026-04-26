import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account?.provider === "github" && profile) {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "https://api.get-nimbus.com"}/auth/github`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              github_id: String((profile as any).id),
              github_username: (profile as any).login,
              github_email: profile.email,
              github_avatar_url: (profile as any).avatar_url,
            }),
          }
        );
        if (res.ok) {
          const data = await res.json();
          token.nimbusToken = data.token;
          token.nimbusUserId = data.user_id;
          token.nimbusUsername = data.username;
          token.nimbusAvatarUrl = data.avatar_url;
          token.nimbusPlan = data.plan;
          token.nimbusApiKey = data.api_key;
        }
      }
      return token;
    },
    async session({ session, token }) {
      (session as any).nimbusToken = token.nimbusToken;
      (session as any).nimbusUserId = token.nimbusUserId;
      (session as any).nimbusUsername = token.nimbusUsername;
      (session as any).nimbusAvatarUrl = token.nimbusAvatarUrl;
      (session as any).nimbusPlan = token.nimbusPlan;
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
  session: { strategy: "jwt" },
});
