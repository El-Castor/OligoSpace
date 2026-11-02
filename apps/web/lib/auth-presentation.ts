export function accountRecovery(code: string): { title: string; message: string } | null {
  if (["invalid_token", "authentication_required", "development_session_required"].includes(code)) {
    return { title: "Session required", message: "Your session expired or could not be verified. Sign in again or end the current session." };
  }
  if (["account_disabled", "account_not_provisioned", "identity_provider_mismatch"].includes(code)) {
    return { title: "Account access unavailable", message: "This identity is not enabled for this application. Contact an administrator or end the current session before using another identity." };
  }
  return null;
}
