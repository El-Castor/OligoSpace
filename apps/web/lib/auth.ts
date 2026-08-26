import type { NextAuthOptions } from "next-auth";
import KeycloakProvider from "next-auth/providers/keycloak";

const issuer = process.env.KEYCLOAK_ISSUER ?? "http://keycloak:8080/realms/oligospace";

export const authOptions: NextAuthOptions = {
  providers: [
    KeycloakProvider({
      clientId: process.env.KEYCLOAK_CLIENT_ID ?? "oligospace-web",
      clientSecret: process.env.KEYCLOAK_CLIENT_SECRET ?? "development-only-change-me",
      issuer,
    }),
  ],
  session: { strategy: "jwt", maxAge: 8 * 60 * 60 },
  pages: { signIn: "/login" },
  callbacks: {
    async jwt({ token, account }) {
      if (account?.access_token) token.accessToken = account.access_token;
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      return session;
    },
  },
};

export const developmentAuth = process.env.AUTH_MODE === "development";
