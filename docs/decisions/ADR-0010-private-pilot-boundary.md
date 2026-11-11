# ADR-0010 — Private pilot security boundary

Status: proposed for code review; no real activation authorized.

Reuse the independent Compose template, production PostgreSQL-backed Keycloak,
private Caddy TLS termination and existing OIDC/scientific/backup controllers.
Only private443 is published. Application/data networks are internal; API/Web
use the canonical Caddy alias and explicit trust, so broad egress is removed.
Keep provider administration off ingress, preserve application/admin authorization,
replace untrusted proxy headers and use a real external certificate/key/CA.

All compatible services are non-root with bounded CPU/RAM/PIDs/logs and controlled
stop/restart. Caddy needs only NET_BIND_SERVICE due its official file capability;
Keycloak needs a writable root for production augmentation. Scientific roles and
calculations are unchanged. No new long-running framework/service is introduced.

Alternative: inherit development Compose or bootstrap identities/runtime builds;
rejected because separation and reproducibility would be implicit. Alternative:
fix AUTH-B6 in this lot; deferred because it is separable and real activation is
already prohibited. No revocation cache is introduced. Unknown preflight inputs
stay NOT_VERIFIED, mandatory release/owner/AUTH-B6 conditions stay BLOCKED.

Synthetic fixtures may use local immutable Docker IDs and disposable S3; neither
constitutes approved registry artifacts or supplier adoption. Real installation,
DNS/TLS/Cloudflare, vault/offhost/RPO/RTO/capacity and human acceptance remain
separate owner decisions. Revisit for approved federation/egress needs, changed
supplier/images/topology or authorization of DEPLOY-06 after all mandatory gates.
