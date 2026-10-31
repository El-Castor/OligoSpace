import { apiGetOptional } from "@/lib/api";

type FormAction = (formData: FormData) => void | Promise<void>;

export async function AttachmentUploadForm({ action, error }: { action: FormAction; error?: string }) {
  const policy = await apiGetOptional<{ uploads_enabled: boolean }>("/laboratory/upload-policy");
  if (!policy?.uploads_enabled) return <div className="notice" role="status">Evidence uploads are disabled for the pilot. Existing evidence is retained.</div>;
  return (
    <form className="attachment-form" action={action}>
      {error ? <div className="notice" role="alert">{error}</div> : null}
      <label className="field">
        <span>Evidence file</span>
        <input name="file" type="file" required accept=".pdf,.png,.jpg,.jpeg,.csv,.tsv,.txt,.xlsx" />
      </label>
      <button className="secondary-button" type="submit">Upload to quarantine</button>
      <small>Maximum 10 MiB. Files are private and cannot be downloaded until a malware scanner marks them clean.</small>
    </form>
  );
}
