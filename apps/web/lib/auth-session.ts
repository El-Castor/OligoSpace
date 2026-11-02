import type { JWT } from "next-auth/jwt";

interface ProviderConfig {
  issuer: string;
  clientId: string;
  clientSecret: string;
}

function failedSession(token: JWT): JWT {
  return {
    ...token,
    accessToken: undefined,
    logoutRefreshToken: token.refreshToken ?? token.logoutRefreshToken,
    refreshToken: undefined,
    accessTokenExpires: 0,
    error: "RefreshAccessTokenError",
  };
}

function providerRequest(config: ProviderConfig, fields: Record<string, string>): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ client_id: config.clientId, client_secret: config.clientSecret, ...fields }),
    cache: "no-store",
    redirect: "error",
    signal: AbortSignal.timeout(5000),
  };
}

export async function refreshSessionToken(
  token: JWT,
  config: ProviderConfig,
  fetcher: typeof fetch = fetch,
): Promise<JWT> {
  if (!token.refreshToken) return failedSession(token);
  try {
    const response = await fetcher(`${config.issuer.replace(/\/$/, "")}/protocol/openid-connect/token`,
      providerRequest(config, { grant_type: "refresh_token", refresh_token: token.refreshToken }));
    const refreshed: unknown = await response.json();
    if (!response.ok || !refreshed || typeof refreshed !== "object") return failedSession(token);
    const value = refreshed as Record<string, unknown>;
    if (typeof value.access_token !== "string" || !value.access_token ||
        typeof value.expires_in !== "number" || !Number.isFinite(value.expires_in) || value.expires_in <= 0 ||
        (value.refresh_token !== undefined && (typeof value.refresh_token !== "string" || !value.refresh_token))) {
      return failedSession(token);
    }
    return {
      ...token,
      accessToken: value.access_token,
      accessTokenExpires: Date.now() + value.expires_in * 1000,
      refreshToken: typeof value.refresh_token === "string" ? value.refresh_token : token.refreshToken,
      logoutRefreshToken: typeof value.refresh_token === "string" ? value.refresh_token : token.refreshToken,
      error: undefined,
    };
  } catch {
    // Neither provider response bodies nor credential-bearing errors are logged.
    return failedSession(token);
  }
}

export async function endProviderSession(
  token: JWT,
  config: ProviderConfig,
  fetcher: typeof fetch = fetch,
): Promise<boolean> {
  const credential = token.refreshToken ?? token.logoutRefreshToken;
  if (!credential) return false;
  try {
    const response = await fetcher(`${config.issuer.replace(/\/$/, "")}/protocol/openid-connect/logout`,
      providerRequest(config, { refresh_token: credential }));
    return response.ok;
  } catch {
    return false;
  }
}

export function validLogoutRequest(origin: string | null, contentType: string | null, configuredOrigin: string): boolean {
  try {
    return origin === new URL(configuredOrigin).origin &&
      contentType?.split(";", 1)[0].trim().toLowerCase() === "application/json";
  } catch {
    return false;
  }
}
