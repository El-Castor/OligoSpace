import type { AttachmentSummary } from "@/lib/api";

export function AttachmentList({ attachments }: { attachments: AttachmentSummary[] }) {
  if (!attachments.length) {
    return <div className="empty"><strong>No evidence files</strong>Uploaded evidence will remain private and quarantined until malware scanning marks it clean.</div>;
  }
  return (
    <div className="association-list">
      {attachments.map((attachment) => (
        <div className="association-item" key={attachment.public_id}>
          <span className="badge">{attachment.publication_status}</span>
          <div>
            <strong>{attachment.original_filename}</strong>
            <small>{attachment.public_id} · {attachment.content_type} · {attachment.size_bytes} bytes</small>
            <small>SHA-256 {attachment.sha256}</small>
          </div>
          <small>Scan: {attachment.scan_status}. No download is exposed while quarantined.</small>
        </div>
      ))}
    </div>
  );
}
