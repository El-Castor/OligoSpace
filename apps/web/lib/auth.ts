import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import KeycloakProvider from "next-auth/providers/keycloak";

import { refreshSessionToken, endProviderSession } from "./auth-session";

const issuer = process.env.KEYCLOAK_ISSUER ?? "http://keycloak:8080/realms/oligospace";
export const developmentAuth = process.env.AUTH_MODE === "development";

const developmentIdentities = {
  admin: {
    id: "00000000-0000-0000-0000-000000000001",
    name: "Local administrator",
    email: "admin@oligospace.local",
    role: "admin",
  },
  member: {
    id: "00000000-0000-0000-0000-000000000002",
    name: "Local researcher",
    email: "researcher@oligospace.local",
    role: "member",
  },
  viewer: {
    id: "00000000-0000-0000-0000-000000000003",
    name: "Local viewer",
    email: "viewer@oligospace.local",
    role: "viewer",
  },
} as const;

const providerConfig = {
  issuer,
  clientId: process.env.KEYCLOAK_CLIENT_ID ?? "oligospace-web",
  clientSecret: process.env.KEYCLOAK_CLIENT_SECRET ?? "",
};

const providers: NextAuthOptions["providers"] = developmentAuth
  ? [
      CredentialsProvider({
        id: "development",
        name: "OligoSpace development identity",
        credentials: { identity: { label: "Identity", type: "text" } },
        async authorize(credentials) {
          const key = credentials?.identity as keyof typeof developmentIdentities | undefined;
          if (!key || !(key in developmentIdentities)) return null;
          return { ...developmentIdentities[key], developmentIdentity: true };
        },
      }),
    ]
  : [
      KeycloakProvider({
        clientId: process.env.KEYCLOAK_CLIENT_ID ?? "oligospace-web",
        clientSecret: process.env.KEYCLOAK_CLIENT_SECRET ?? "",
        issuer,
        checks: ["pkce", "state", "nonce"],
      }),
    ];

export const authOptions: NextAuthOptions = {
  providers,
  useSecureCookies:
    process.env.NEXTAUTH_URL?.startsWith("https://") ?? process.env.NODE_ENV === "production",
  session: { strategy: "jwt", maxAge: 8 * 60 * 60, updateAge: 15 * 60 },
  pages: { signIn: "/login", error: "/login" },
  events: {
    async signOut(message) {
      if (!developmentAuth && "token" in message && message.token) {
        const closed = await endProviderSession(message.token, providerConfig);
        if (!closed) console.warn("OIDC_LOGOUT_NOT_CONFIRMED");
      }
    },
  },
  callbacks: {
    async jwt({ token, account, user }) {
      if (account?.provider === "development") {
        token.role = user.role;
        token.developmentIdentity = true;
        return token;
      }
      if (account?.access_token) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.accessTokenExpires = (account.expires_at ?? 0) * 1000;
        return token;
      }
      if (token.developmentIdentity || !token.accessTokenExpires) return token;
      if (Date.now() < token.accessTokenExpires - 30_000) return token;
      return refreshSessionToken(token, providerConfig);
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.sub ?? "";
        session.user.role = token.role;
      }
      session.accessToken = token.accessToken;
      session.developmentIdentity = Boolean(token.developmentIdentity);
      session.error = token.error;
      return session;
    },
  },
};

export function providerLogoutUrl(): string {
  if (developmentAuth) return "/login";
  const origin = process.env.NEXTAUTH_URL ?? "http://oligospace.localhost:8080";
  const url = new URL(`${issuer.replace(/\/$/, "")}/protocol/openid-connect/logout`);
  url.searchParams.set("client_id", process.env.KEYCLOAK_CLIENT_ID ?? "oligospace-web");
  url.searchParams.set("post_logout_redirect_uri", `${origin}/login`);
  return url.toString();
}
