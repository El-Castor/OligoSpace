import { LoginActions } from "@/components/LoginActions";
import { developmentAuth } from "@/lib/auth";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  return (
    <div className="login-shell">
      <section className="login-card">
        <p className="eyebrow">Secure laboratory workspace</p>
        <h1>Welcome to OligoSpace.</h1>
        <p>
          {developmentAuth
            ? "Choose an explicit local identity. These sessions use real projected users and permissions from PostgreSQL."
            : "Sign in through the configured identity provider. OligoSpace never stores your password."}
        </p>
        {error ? <div className="notice" role="alert">Authentication failed or expired. Please sign in again.</div> : null}
        <LoginActions development={developmentAuth} />
      </section>
    </div>
  );
}
