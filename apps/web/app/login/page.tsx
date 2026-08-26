"use client";

import { signIn } from "next-auth/react";

export default function LoginPage() {
  return (
    <div className="login-shell">
      <section className="login-card">
        <p className="eyebrow">Secure laboratory workspace</p>
        <h1>Welcome to OligoSpace.</h1>
        <p>Sign in through the configured identity provider. OligoSpace never stores your password.</p>
        <button className="primary-button" type="button" onClick={() => signIn("keycloak", { callbackUrl: "/" })}>Continue with institutional identity</button>
      </section>
    </div>
  );
}
