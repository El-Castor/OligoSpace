import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface User {
    role?: string;
    developmentIdentity?: boolean;
  }

  interface Session {
    accessToken?: string;
    developmentIdentity?: boolean;
    error?: "RefreshAccessTokenError";
    user?: {
      id: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
      role?: string;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
    role?: string;
    developmentIdentity?: boolean;
    error?: "RefreshAccessTokenError";
  }
}
