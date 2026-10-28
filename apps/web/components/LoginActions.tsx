"use client";

import { signIn } from "next-auth/react";

export function LoginActions({ development }: { development: boolean }) {
  if (!development) {
    return (
      <button className="primary-button" type="button" onClick={() => signIn("keycloak", { callbackUrl: "/" })}>
        Continue with institutional identity
      </button>
    );
  }
  return (
    <div className="login-actions">
      <button className="primary-button" type="button" onClick={() => signIn("development", { identity: "admin", callbackUrl: "/" })}>
        Sign in as local administrator
      </button>
      <button className="secondary-button" type="button" onClick={() => signIn("development", { identity: "member", callbackUrl: "/" })}>
        Sign in as local researcher
      </button>
      <button className="secondary-button" type="button" onClick={() => signIn("development", { identity: "viewer", callbackUrl: "/" })}>
        Sign in as local viewer
      </button>
      <p className="development-warning">Development only · no application password is created.</p>
    </div>
  );
}
