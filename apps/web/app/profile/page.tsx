import { ScientificFormFrame } from "@/components/ScientificFormFrame";
import { SubmitButton } from "@/components/SubmitButton";
import { PageHeader } from "@/components/PageHeader";
import { updateProfile } from "@/app/workspace/actions";
import { apiGet, type CurrentUser } from "@/lib/api";

export default async function ProfilePage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; updated?: string }>;
}) {
  const { error, updated } = await searchParams;
  const user = await apiGet<CurrentUser>("/me");
  return (
    <>
      <PageHeader eyebrow="Identity" title="Your profile" description="Your OIDC subject remains immutable. Profile changes are stored in OligoSpace and audited." />
      {updated ? <div className="success-notice" role="status">Profile updated and audited.</div> : null}
      <ScientificFormFrame action={updateProfile} error={error} legend={false}>

        <div className="profile-summary">
          <div className="profile-avatar" aria-hidden="true">{user.initials}</div>
          <div><strong>{user.display_name}</strong><span>{user.email}</span><small>{user.organization_name} · {user.role.replaceAll("_", " ")}</small></div>
        </div>
        <div className="form-grid">
          <label className="field"><span>Display name</span><input name="display_name" required maxLength={160} defaultValue={user.display_name} /></label>
          <label className="field"><span>Email</span><input value={user.email} readOnly /></label>
          <label className="field"><span>First name</span><input name="first_name" maxLength={120} defaultValue={user.first_name ?? ""} /></label>
          <label className="field"><span>Last name</span><input name="last_name" maxLength={120} defaultValue={user.last_name ?? ""} /></label>
          <label className="field field-wide"><span>Avatar URL</span><input name="avatar_url" type="url" defaultValue={user.avatar_url ?? ""} /></label>
          <div className="field"><span>Identity provider</span><code>{user.identity_provider}</code></div>
          <div className="field"><span>External identity ID</span><code>{user.external_identity_id}</code></div>
        </div>
        <div className="form-actions"><SubmitButton className="primary-button">Save profile</SubmitButton></div>
      </ScientificFormFrame>
    </>
  );
}
