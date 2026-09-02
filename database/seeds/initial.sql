-- Idempotent local-development seed. Never use these identities as production credentials.
INSERT INTO organizations (id, name, slug, active)
VALUES ('10000000-0000-0000-0000-000000000001', 'OligoSpace Development', 'development', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (
  id, oidc_subject, identity_provider, email, display_name, first_name, last_name,
  active, global_role, organization_id
)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  '20000000-0000-0000-0000-000000000001',
  'keycloak',
  'admin@oligospace.local',
  'Local administrator',
  'Local',
  'Administrator',
  true,
  'admin',
  '10000000-0000-0000-0000-000000000001'
) , (
  '00000000-0000-0000-0000-000000000002',
  '20000000-0000-0000-0000-000000000002',
  'keycloak',
  'researcher@oligospace.local',
  'Local researcher',
  'Local',
  'Researcher',
  true,
  'member',
  '10000000-0000-0000-0000-000000000001'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO teams (id, organization_id, name, description, active)
VALUES (
  '30000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',
  'Development laboratory',
  'Local development team',
  true
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO team_memberships (team_id, user_id, role)
VALUES
(
  '30000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000001',
  'admin'
),
(
  '30000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000002',
  'member'
)
ON CONFLICT (team_id, user_id) DO NOTHING;

INSERT INTO experiment_types
  (id, name, slug, description, allowed_roles, required_metadata, recommended_validation_fields, active)
VALUES
  (gen_random_uuid(), 'PCR', 'pcr', 'Polymerase chain reaction', '["forward_primer", "reverse_primer"]', '{}', '{"gel_validation": {"type": "boolean"}}', true),
  (gen_random_uuid(), 'RT-PCR', 'rt-pcr', 'Reverse transcription PCR', '["forward_primer", "reverse_primer"]', '{}', '{}', true),
  (gen_random_uuid(), 'qPCR SYBR', 'qpcr-sybr', 'SYBR-based quantitative PCR', '["forward_primer", "reverse_primer"]', '{}', '{"efficiency": {"type": "number"}, "r_squared": {"type": "number"}, "melt_curve_status": {"type": "string"}}', true),
  (gen_random_uuid(), 'qPCR probe', 'qpcr-probe', 'Probe-based quantitative PCR', '["forward_primer", "reverse_primer", "probe"]', '{}', '{"efficiency": {"type": "number"}, "r_squared": {"type": "number"}}', true),
  (gen_random_uuid(), 'Genotyping PCR', 'genotyping-pcr', 'PCR genotyping assay', '["forward_primer", "reverse_primer", "internal_oligo"]', '{}', '{}', true),
  (gen_random_uuid(), 'Sequencing PCR', 'sequencing-pcr', 'PCR for sequencing templates', '["forward_primer", "reverse_primer", "sequencing_primer"]', '{}', '{}', true),
  (gen_random_uuid(), 'Cloning', 'cloning', 'General cloning assay', '["forward_primer", "reverse_primer", "adapter"]', '{}', '{}', true),
  (gen_random_uuid(), 'Gibson assembly', 'gibson-assembly', 'Isothermal Gibson assembly', '["forward_primer", "reverse_primer", "adapter"]', '{}', '{}', true),
  (gen_random_uuid(), 'Golden Gate', 'golden-gate', 'Golden Gate assembly', '["forward_primer", "reverse_primer", "adapter"]', '{}', '{}', true),
  (gen_random_uuid(), 'Site-directed mutagenesis', 'site-directed-mutagenesis', 'Targeted mutagenesis assay', '["forward_primer", "reverse_primer"]', '{}', '{}', true),
  (gen_random_uuid(), 'In situ hybridization / HIS', 'in-situ-hybridization', 'In situ hybridization', '["probe", "template", "forward_primer", "reverse_primer"]', '{}', '{}', true),
  (gen_random_uuid(), 'Probe hybridization', 'probe-hybridization', 'Probe hybridization', '["probe"]', '{}', '{}', true),
  (gen_random_uuid(), 'FISH', 'fish', 'Fluorescence in situ hybridization', '["probe"]', '{}', '{}', true),
  (gen_random_uuid(), 'CRISPR-related oligos', 'crispr', 'CRISPR guide/donor oligos', '["guide", "donor", "other"]', '{}', '{}', true),
  (gen_random_uuid(), 'LAMP', 'lamp', 'Loop-mediated isothermal amplification', '["forward_primer", "reverse_primer", "internal_oligo"]', '{}', '{}', true),
  (gen_random_uuid(), 'Sequencing primers', 'sequencing-primers', 'Sequencing primer design', '["sequencing_primer"]', '{}', '{}', true),
  (gen_random_uuid(), 'Custom', 'custom', 'Administrator-defined custom method', '["other"]', '{}', '{}', true)
ON CONFLICT (slug) DO NOTHING;
