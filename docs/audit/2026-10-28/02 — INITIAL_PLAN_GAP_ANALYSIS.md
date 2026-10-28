# 02 — Analyse d'écart avec le plan initial

- Date : 2026-10-28 · Référence : `docs/PRODUCT_SPEC.md` (exigences et « MVP boundary »),
  `docs/REQUIREMENTS_TRACEABILITY.md` (99 exigences), plans d'exécution 001–005.
- Légende épistémique : voir `01 — PROJECT_STATE_AUDIT.md`.

## 1. Méthode

- **Référence initiale.** Le plan initial est la spécification produit et le plan 001. La
  colonne « Priorité initiale » est **[INFÉRÉE]** : la spec ne numérote pas de priorités par
  exigence. Elle classe en *Jalon MVP* ce que le plan 001 et la « MVP boundary » placent dans
  le premier livrable. Elle classe en *Phase ultérieure* ce que la spec renvoie explicitement à
  plus tard (inventaire, commandes, viewer, export, mapping génomique) ou demande de « ne pas
  présenter comme complet » (runs, validations, pièces jointes, sauvegarde, jobs scientifiques).
- **État du code** : statut déclaré dans `REQUIREMENTS_TRACEABILITY.md` **[DÉCLARÉ]**, recoupé
  par l'inventaire du code (doc 01, § 5) **[CODE]**.
- **Validation** : preuve déclarée dans la matrice de traçabilité. Elle n'a **pas** été rejouée
  pendant l'audit, sauf lint, typecheck et tests unitaires (doc 01, § 4).
- **Intégration** :
  - `main + branches` : présent depuis le plan 001.
  - `Branche codex/*` : livré par les plans 002–004, poussé mais non fusionné dans `main`.
  - `Arbre de travail non commité` : plan 005.
- **Utilisable** :
  - *Oui* : Vérifié **et** preuve E2E navigateur via Caddy (2026-09).
  - *Partiel* : E2E partielle.
  - *API/unitaire seulement* : vérifié sans parcours navigateur.
  - *Non démontré* : code présent sans preuve d'usage.
  - *Non* : non commencé ou bloqué.
- **Priorité (reste à faire)** : proposition de cet audit, **soumise à validation utilisateur**.
  - P0 : requis pour un MVP sûr.
  - P1 : V1.
  - P2 : différable.
  - — : déjà vérifié (non-régression seulement).

## 2. Indicateurs (dénominateur 99)

| Dimension | Valeurs |
|---|---|
| État du code | Vérifié 31 · Implémenté 9 · En cours 29 · Planifié 27 · Bloqué 3 |
| Utilisable | Oui 19 · Partiel 17 · API/unitaire 12 · Non démontré 21 · Non 30 |
| Priorité initiale (inférée) | Jalon MVP 51 · Phase ultérieure 27 · Phase ultérieure « ne pas présenter comme complet » 21 |
| Priorité proposée du reste | P0 17 · P1 39 · P2 12 · — (vérifié) 31 |

Lecture : environ **un tiers** des exigences est vérifié, et **moins d'un cinquième** est
démontré utilisable en navigateur. Aucune preuve navigateur n'a moins de 7 semaines.

## 3. Matrice de traçabilité

| ID | Fonctionnalité | Priorité initiale (inférée) | Source (plans) | État du code | Validation (preuve déclarée) | Intégration | Utilisable | Blocage | Reste à faire | Priorité |
|---|---|---|---|---|---|---|---|---|---|---|
| AUTH-001 | Institutional authentication | Jalon MVP (plan 001) | 001, 003 | Implémenté — `apps/web/lib/auth.ts`, NextAuth route, Keycloak realm | Development login E2E; institutional OIDC browser flow not exercised | Branche codex/* (non fusionnée dans main) | Partiel | Hôte/SSO institutionnel non fournis (BACKUP-005) | Qualifier le flux OIDC institutionnel en navigateur | P0 |
| AUTH-002 | Development authentication | Jalon MVP (plan 001) | 003 | Vérifié — signed development session, production runtime guard | `test_auth.py`; auth/logout/second-identity Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| AUTH-003 | Server-side RBAC | Jalon MVP (plan 001) | 001, 002, 003 | Vérifié — `domain/permissions.py`, registry/workspace services | permission units; PostgreSQL admin/member 403 integration; admin-denial E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| AUTH-004 | Visibility | Jalon MVP (plan 001) | 001, 002, 003 | En cours — visibility queries and scope validation across registry/workspaces | four-scope PostgreSQL integration; complete search/export leakage matrix absent | Branche codex/* (non fusionnée dans main) | Non démontré | — | Couvrir recherche/export avec la matrice 4 portées | P0 |
| AUTH-005 | Session security | Jalon MVP (plan 001) | 001, 003 | En cours — `security/auth.py`, token refresh, secure cookies, CORS, Caddy headers | disabled-account PostgreSQL test and development session E2E; production OIDC absent | Branche codex/* (non fusionnée dans main) | Partiel | — | Revue sécurité session prod (cookies, refresh, CORS) sous hôte réel | P0 |
| USER-001 | User profile | Jalon MVP (plan 001) | 001, 003 | Vérifié — expanded User model, `/me`, profile API/page | PostgreSQL profile test; profile save/reload Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| USER-002 | Account lifecycle | Jalon MVP (plan 001) | 003 | En cours — inactive-user rejection and preserved relational authorship | disabled-account PostgreSQL test; authored-history lifecycle not yet explicit | Branche codex/* (non fusionnée dans main) | Non démontré | — | Tester cycle désactivation + historique d'auteur | P1 |
| USER-003 | User dashboard | Jalon MVP (plan 001) | 001, 003 | En cours — personalized dashboard service/page | dashboard Caddy E2E; later validation/stock actions explicitly unavailable | Branche codex/* (non fusionnée dans main) | Partiel | — | Ajouter actions validation/stock au tableau de bord | P2 |
| TEAM-001 | Team management | Jalon MVP (plan 001) | 003 | En cours — workspace Team CRUD API and admin/team pages | PostgreSQL create and detail tests; activation browser path untested | Branche codex/* (non fusionnée dans main) | Non démontré | — | E2E activation/désactivation équipe | P1 |
| TEAM-002 | Team membership | Jalon MVP (plan 001) | 001, 003 | Vérifié — TeamMembership CRUD, role-aware principal, visibility policy | permission units; PostgreSQL membership/403/visibility; Team Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| TEAM-003 | Team dashboard | Jalon MVP (plan 001) | 003 | En cours — Team detail dashboard and visible resource counts | Caddy Team/project view; validation/inventory summaries unavailable | Branche codex/* (non fusionnée dans main) | Partiel | — | Résumés validation/inventaire | P2 |
| PROJECT-001 | Project lifecycle | Jalon MVP (plan 001) | 003 | En cours — Project CRUD, stable IDs, status, visibility, migration `0002` | PostgreSQL create; Caddy create/detail/reload; archive path untested | Branche codex/* (non fusionnée dans main) | Partiel | — | E2E archivage projet | P0 |
| PROJECT-002 | Project membership | Jalon MVP (plan 001) | 001, 003 | Vérifié — ProjectMembership CRUD and server permission policy | PostgreSQL membership/visibility/403; membership and denial Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| PROJECT-003 | Project context | Jalon MVP (plan 001) | 001, 002, 003 | En cours — project links on Targets/Oligos/Assays and scope-aware forms | core form build/E2E plus Project linked-resource view; later domains absent | Branche codex/* (non fusionnée dans main) | Partiel | — | Contexte projet sur runs/validations/stock | P1 |
| PROJECT-004 | Project dashboard | Jalon MVP (plan 001) | 003 | En cours — Project detail dashboard, participants, linked resources, counts | Project create/membership/reload Caddy E2E; evidence/stock states unavailable | Branche codex/* (non fusionnée dans main) | Partiel | — | Résumés preuves/stock | P1 |
| ORGANISM-001 | Organism catalogue | Jalon MVP (plan 001) | 001, 003 | Implémenté — organism model, admin list/create/update routes and controls | Static/type/build validation; no catalogue mutation E2E | Branche codex/* (non fusionnée dans main) | Partiel | — | E2E mutation catalogue | P1 |
| ORGANISM-002 | Organism reuse | Jalon MVP (plan 001) | 001 | Implémenté — organism foreign keys on target/genome/assay | PostgreSQL schema validation only | main + branches | Non démontré | — | Test d'intégration réutilisation | P1 |
| GENOME-001 | Reference genome identity | Jalon MVP (plan 001) | 001 | Implémenté — `ReferenceGenome` model and migration | PostgreSQL migration validation | main + branches | Non démontré | — | Test API/UI au-delà de la migration | P1 |
| GENOME-002 | Governed references | Jalon MVP (plan 001) | 001, Backlog | En cours — checksum/version fields; mapping services | `test_target_mapping.py`; no governed reference runtime | main + branches | Non démontré | Références FASTA/GFF gouvernées non fournies | Runtime de référence gouverné | P1 |
| GENOME-003 | Reference ingestion | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | Références FASTA/GFF non fournies | Concevoir, implémenter, tester (non commencé) | P2 |
| TARGET-001 | Target registration | Jalon MVP (plan 001) | 002 | Vérifié — target API/services and web create form | PostgreSQL create integration; Caddy create/detail E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| TARGET-002 | Known sequence only | Jalon MVP (plan 001) | 002, Backlog | En cours — target schema/form avoids inference | Sequence normalization tests; source provenance incomplete | Branche codex/* (non fusionnée dans main) | Non démontré | — | Provenance de la source de séquence | P1 |
| TARGET-003 | Target lifecycle | Jalon MVP (plan 001) | 002 | En cours — target search/detail/update/status and audit | Caddy create/detail/edit/reload E2E; deprecate/archive path untested | Branche codex/* (non fusionnée dans main) | Partiel | — | E2E déprécier/archiver | P0 |
| TARGET-004 | Target relationships | Phase ultérieure | Backlog | Planifié — target/assay FK only | Aucune | — | Non | — | Exposer assays/mappings liés | P1 |
| OLIGO-001 | Oligo registration | Jalon MVP (plan 001) | 001, 002 | Vérifié — oligo API/services and web create/detail forms | PostgreSQL route integration; Caddy create/detail/reload E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| OLIGO-002 | Immutable biological identity | Jalon MVP (plan 001) | 002 | Vérifié — update schema forbids sequence; edit form read-only | PostgreSQL PATCH sequence rejection | Branche codex/* (non fusionnée dans main) | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| OLIGO-003 | Normalization and validation | Jalon MVP (plan 001) | 001, 002 | Vérifié — `sequence_analysis.py`, create service | `test_sequence_analysis.py`; PostgreSQL normalization integration | Branche codex/* (non fusionnée dans main) | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| OLIGO-004 | Computed sequence QC | Jalon MVP (plan 001) | 001, 002 | Vérifié — sequence metrics service and detail UI | `test_sequence_analysis.py`; PostgreSQL response validation | Branche codex/* (non fusionnée dans main) | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| OLIGO-005 | QC provenance | Jalon MVP (plan 001) | 001, 002 | Vérifié — `calculation_provenance` and provenance UI | Unit assertions plus PostgreSQL serialized response | Branche codex/* (non fusionnée dans main) | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| OLIGO-006 | Duplicate prevention | Jalon MVP (plan 001) | 001, 002 | Vérifié — duplicate/reverse-complement checks | sequence duplicate unit tests; PostgreSQL exact-duplicate integration | Branche codex/* (non fusionnée dans main) | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| OLIGO-007 | Oligo lifecycle and reuse | Jalon MVP (plan 001) | 002 | En cours — list/search/detail/edit/status routes and pages | PostgreSQL search/update/audit and Caddy list/detail/edit/reload; archive path untested | Branche codex/* (non fusionnée dans main) | Partiel | — | E2E déprécier/archiver + réutilisation | P0 |
| EXPTYPE-001 | Configurable catalogue | Jalon MVP (plan 001) | 001, 003 | Implémenté — model, seed, admin create/update routes and controls | seed/runtime plus static/type/build validation; no mutation E2E | Branche codex/* (non fusionnée dans main) | Partiel | — | E2E mutation admin | P1 |
| EXPTYPE-002 | Method constraints | Jalon MVP (plan 001) | 001, 002 | En cours — assay role validation | PostgreSQL valid-role integration; required metadata not enforced | Branche codex/* (non fusionnée dans main) | Non démontré | — | Imposer les métadonnées requises | P1 |
| EXPTYPE-003 | Catalogue preservation | Jalon MVP (plan 001) | 001, 003 | Implémenté — active filter, admin active-state control, restrictive assay FK | Migration/schema and build validation; deactivation behavior test incomplete | Branche codex/* (non fusionnée dans main) | Non démontré | — | Tester le comportement de désactivation | P1 |
| ASSAY-001 | Assay registration | Jalon MVP (plan 001) | 001, 002 | Vérifié — assay create/search/detail/edit API and pages | PostgreSQL route integration; Caddy create/detail/reload E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| ASSAY-002 | Contextual oligo roles | Jalon MVP (plan 001) | 001, 002 | Vérifié — `AssayOligo`, contextual-role form | PostgreSQL association integration; Forward/Reverse Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| ASSAY-003 | Domain separation | Jalon MVP (plan 001) | 001 | Implémenté — separate Oligo/AssayOligo/Assay models | ADR-0004 and schema validation | main + branches | Non démontré | — | —(contrainte de schéma ; garder ADR-0004) | P1 |
| ASSAY-004 | Association integrity | Jalon MVP (plan 001) | 001, 002 | Implémenté — `_validate_assay_references` | Valid association integration; negative matrix incomplete | Branche codex/* (non fusionnée dans main) | Non démontré | — | Compléter la matrice de tests négatifs | P0 |
| ASSAY-005 | Expected amplicon | Jalon MVP (plan 001) | 002 | Vérifié — expected product/amplicon API and UI | Expected amplicon asserted by Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| ASSAY-006 | Versioned edits | Jalon MVP (plan 001) | 002 | Vérifié — version increment and before/after audit | PostgreSQL version/audit integration | Branche codex/* (non fusionnée dans main) | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| ASSAY-007 | Assay lifecycle | Jalon MVP (plan 001) | 002 | En cours — search/detail/edit/status workflows | PostgreSQL API and Caddy edit/version/reload E2E; archive path untested | Branche codex/* (non fusionnée dans main) | Partiel | — | E2E archivage | P0 |
| EXPRUN-001 | Experiment execution | Phase ultérieure (spec : ne pas présenter comme complet) | 004, Backlog | En cours — `models/laboratory.py`, laboratory API/UI; true OligoLot relation awai | PostgreSQL laboratory integration and experiment-evidence Caddy E2E | Branche codex/* (non fusionnée dans main) | Partiel | — | Relation réelle OligoLot (dépend INV-001) | P1 |
| EXPRUN-002 | Repeatable history | Phase ultérieure (spec : ne pas présenter comme complet) | 004 | Vérifié — repeated run API/UI with Assay version snapshot | PostgreSQL laboratory integration and experiment-evidence Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| EXPRUN-003 | Run provenance | Phase ultérieure (spec : ne pas présenter comme complet) | 004 | Vérifié — immutable run provenance, contextual inputs, attachments | API units, PostgreSQL laboratory integration, experiment-evidence Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| VALID-001 | Contextual validation | Phase ultérieure (spec : ne pas présenter comme complet) | 004 | Vérifié — separate append-oriented `Validation` model/API/UI | PostgreSQL laboratory integration and experiment-evidence Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| VALID-002 | Validation states | Phase ultérieure (spec : ne pas présenter comme complet) | 004 | Vérifié — assay-level or run-context validation with user-entered evidence | API units, PostgreSQL laboratory integration, experiment-evidence Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| VALID-003 | Validation history | Phase ultérieure (spec : ne pas présenter comme complet) | 004 | Vérifié — explicit supersession preserving prior evidence | PostgreSQL laboratory integration and experiment-evidence Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| VALID-004 | Method guidance | Phase ultérieure (spec : ne pas présenter comme complet) | 004 | Vérifié — `ValidationForm` renders ExperimentType measurement guidance | experiment-evidence Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| ATTACH-001 | Attachment metadata | Phase ultérieure (spec : ne pas présenter comme complet) | 004 | Vérifié — private MinIO upload plus PostgreSQL checksum/provenance metadata | PostgreSQL laboratory integration and real-MinIO Caddy E2E | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| ATTACH-002 | Safe file handling | Phase ultérieure (spec : ne pas présenter comme complet) | 004, Backlog | En cours — size/type policy and mandatory pending/quarantine gate; malware scanne | API units, PostgreSQL rejection tests, quarantine Caddy E2E | Branche codex/* (non fusionnée dans main) | Partiel | Scanner antimalware non choisi | Scan antimalware | P0 |
| ATTACH-003 | Evidence retention | Phase ultérieure (spec : ne pas présenter comme complet) | 004 | Vérifié — soft removal retains metadata/object and audit history | PostgreSQL laboratory integration | Branche codex/* (non fusionnée dans main) | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| ORDER-001 | Supplier catalogue | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| ORDER-002 | Purchase orders | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| ORDER-003 | Order items | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| ORDER-004 | Receipt | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| INV-001 | Oligo lots | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| INV-002 | Stock items and aliquots | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| INV-003 | Hierarchical locations | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| INV-004 | Occupancy integrity | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| INV-005 | Immutable inventory events | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| INV-006 | Quantity integrity | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| INV-007 | QR workflows | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P2 |
| INV-008 | Stock alerts | Phase ultérieure | Backlog | Planifié — dashboard placeholders remain null | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| SEARCH-001 | Global search | Phase ultérieure (spec : ne pas présenter comme complet) | 002, 003, 004, Backlog | En cours — global search page/API for core registry, Projects, runs, and validati | PostgreSQL core/evidence search and Caddy global-search E2E; inventory absent | Branche codex/* (non fusionnée dans main) | Partiel | — | Étendre à stock/commandes ; pertinence | P1 |
| SEARCH-002 | Scoped registry search | Jalon MVP (plan 001) | 002 | En cours — registry search and pagination API | PostgreSQL oligo search; filters/sorting incomplete | Branche codex/* (non fusionnée dans main) | Non démontré | — | Filtres et tris | P1 |
| SEARCH-003 | No visibility leakage | Jalon MVP (plan 001) | 002, 003 | En cours — visible-query registry and workspace searches | permission units and four-scope PostgreSQL list matrix; exports absent | Branche codex/* (non fusionnée dans main) | Non démontré | — | Couvrir export/suggestions | P0 |
| SEARCH-004 | Reuse-first discovery | Jalon MVP (plan 001) | 002, Backlog | En cours — exact duplicate conflict | PostgreSQL duplicate test; pre-submit suggestions incomplete | Branche codex/* (non fusionnée dans main) | Non démontré | — | Suggestions pré-soumission | P1 |
| VIEW-001 | GeneOligoViewer data integrity | Phase ultérieure | Backlog | Planifié — mapping service only | Aucune | — | Non | Dépend de BIO-002 | Concevoir, implémenter, tester (non commencé) | P1 |
| VIEW-002 | Transcript selection | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P2 |
| VIEW-003 | Exon/intron structure | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P2 |
| VIEW-004 | Oligo orientation | Phase ultérieure | Backlog | Planifié — strand-aware mapping data only | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| VIEW-005 | Amplicon representation | Phase ultérieure | Backlog | Planifié — assay expected amplicon field only | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P2 |
| VIEW-006 | Ambiguity | Phase ultérieure | Backlog | Planifié — mapping warnings service only | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| BIO-001 | Exact target mapping | Jalon MVP (plan 001) | 001 | Vérifié — `target_mapping.py` | `test_target_mapping.py` forward/reverse/ambiguous cases | main + branches | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| BIO-002 | Mapping persistence | Phase ultérieure | Backlog | Planifié — TargetMapping design only | Aucune | — | Non | Dépend de GENOME-002/003 | Concevoir, implémenter, tester (non commencé) | P1 |
| BIO-003 | Primer3 QC | Phase ultérieure (spec : ne pas présenter comme complet) | 001, 005 | En cours — persistent scientific API/worker and Oligo/Assay UI | `test_scientific_contract.py` real Primer3 fixtures; API and PostgreSQL tests; Caddy E2E p | Arbre de travail non commité (plan 005) | Partiel | Plan 005 non commité ; E2E finale non rejouée | Commiter ; E2E Chromium finale ; revue qualification | P0 |
| BIO-004 | Screening distinction | Jalon MVP (plan 001) | 001, 002 | Vérifié — Wallace service, provenance, UI label | `test_sequence_analysis.py`; PostgreSQL response | Branche codex/* (non fusionnée dans main) | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| BIO-005 | BLAST-ready specificity | Phase ultérieure | 001, Backlog | Implémenté — pinned BLAST+ worker image | image build/version check; governed databases blocked | main + branches | Non démontré | Bases BLAST gouvernées non fournies | Bases BLAST gouvernées + job | P2 |
| BIO-006 | Reproducible jobs | Phase ultérieure (spec : ne pas présenter comme complet) | 005 | En cours — `ScientificJob`/attempt/result, migration 0004, Celery worker/Beat | reversible PostgreSQL migration and API integration; worker/Redis recovery runtime gate pe | Arbre de travail non commité (plan 005) | Non démontré | Plan 005 non commité ; reprise worker/Redis non testée | Commiter ; test reprise worker/Redis | P0 |
| BIO-007 | Honest uncertainty | Phase ultérieure (spec : ne pas présenter comme complet) | 001, 005 | En cours — explicit scientific validation/error states and neutral UI | API boundary tests and worker timeout/output/version tests; rejected-input Caddy E2E pendi | Arbre de travail non commité (plan 005) | Partiel | Plan 005 non commité | Commiter ; E2E états d'erreur | P0 |
| IMPORT-001 | Immutable source | Jalon MVP (plan 001) | 001 | Vérifié — `scripts/migration_excel`, migration report | checksum unchanged before/after preview | main + branches | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| IMPORT-002 | Preview before write | Jalon MVP (plan 001) | 001 | Vérifié — preview/audit/normalization scripts | `test_excel_import.py`; 93/7 preview runtime | main + branches | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| IMPORT-003 | Reviewed write | Phase ultérieure (spec : ne pas présenter comme complet) | Backlog | Bloqué — approval gate documented | Data-owner review not supplied | — | Non | Revue propriétaire des données absente | Revue + approbation propriétaire | P1 |
| IMPORT-004 | Domain decomposition | Phase ultérieure (spec : ne pas présenter comme complet) | 001, Backlog | En cours — preview candidate decomposition/report | `test_excel_import.py`; write decomposition absent | main + branches | Non démontré | — | Décomposition en écriture | P1 |
| IMPORT-005 | Idempotency and lineage | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P2 |
| EXPORT-001 | Registry export | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| EXPORT-002 | Sequence export | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P1 |
| EXPORT-003 | Export security | Phase ultérieure | Backlog | Planifié — audit model only | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P2 |
| AUDIT-001 | Mutation audit | Jalon MVP (plan 001) | 001, 002, 003 | En cours — `AuditEvent`, registry and workspace services | PostgreSQL registry/user/team/project/membership audit integration; later domains absent | Branche codex/* (non fusionnée dans main) | Non démontré | — | Couvrir import/export | P0 |
| AUDIT-002 | Audit evidence | Jalon MVP (plan 001) | 001, 002, 003 | En cours — safe audit helpers and before/after snapshots | workspace/core audit counts and secret-free serializers; correlation ID absent | Branche codex/* (non fusionnée dans main) | Non démontré | — | Revue des sérialiseurs restants | P0 |
| AUDIT-003 | Audit access | Phase ultérieure | Backlog | Planifié | Aucune | — | Non | — | Concevoir, implémenter, tester (non commencé) | P2 |
| DEPLOY-001 | Container deployment | Jalon MVP (plan 001) | 001 | Vérifié — `compose.yml`, pinned Dockerfiles | compose config and production image builds | main + branches | API/unitaire seulement | — | Rejouer en non-régression avant release | — |
| DEPLOY-002 | Public ingress | Jalon MVP (plan 001) | 001, 002, 003 | Vérifié — Caddy, isolated networks, E2E Caddy network namespace | Compose health gates, 6 Caddy specs, host-network smoke on 2026-09-02 | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| DEPLOY-003 | Runtime readiness | Jalon MVP (plan 001) | 002, 003 | Vérifié — status vocabulary, split Playwright E2E, host smoke | Build/API/browser evidence separated; Caddy and host-network smoke passed 2026-09-02 | Branche codex/* (non fusionnée dans main) | Oui (E2E navigateur, 2026-09) | — | Rejouer en non-régression avant release | — |
| BACKUP-001 | PostgreSQL-aware backup | Phase ultérieure (spec : ne pas présenter comme complet) | 001, Backlog | En cours — `infra/backup/create-backup.sh` | script/config only; no accepted backup runtime | main + branches | Non démontré | — | Exécuter une sauvegarde acceptée | P0 |
| BACKUP-002 | Object/reference coverage | Phase ultérieure (spec : ne pas présenter comme complet) | Backlog | Planifié — architecture documentation | Aucune | — | Non | — | Conception objets/références | P1 |
| BACKUP-003 | Restore verification | Phase ultérieure (spec : ne pas présenter comme complet) | 001, Backlog | En cours — `restore-test.sh`, runbook | no recorded successful production-like restore | main + branches | Non démontré | — | Restauration prod-like enregistrée | P0 |
| BACKUP-004 | INRAE pull architecture | Phase ultérieure (spec : ne pas présenter comme complet) | Backlog | Bloqué — documented pull topology | INRAE endpoint/ownership not supplied | — | Non | Endpoint INRAE / responsable non fournis | Conception pull INRAE | P2 |
| BACKUP-005 | Institutional inputs | Phase ultérieure (spec : ne pas présenter comme complet) | Backlog | Bloqué — `SECURITY.md`, deployment/backlog docs | Institutional inputs absent | — | Non | Entrées institutionnelles absentes | Obtenir hôte, SSO/LDAP, endpoint, secrets | P1 |


## 4. Fonctionnalités manquantes (non commencées, 27 « Planifié »)

- **Inventaire physique** (INV-*) : lots, emplacements, mouvements, stock bas, QR. Seul un
  `PlannedPage` placeholder existe **[CODE]**.
- **Commandes** (ORDER-*) : demande, approbation, réception, lien fournisseur.
- **GeneOligoViewer** (VIEW-*) : dépend du mapping génomique (BIO-002), lui-même bloqué par
  l'absence de références FASTA/GFF gouvernées.
- **Export** (EXPORT-*) : exports contrôlés et audités.
- **Exploitation** : sauvegarde objets (BACKUP-002), pull INRAE (BACKUP-004), monitoring,
  antimalware (ATTACH-002), OIDC institutionnel (AUTH-001 en production).

## 5. Bloqués (3) et blocages externes

| ID | Blocage | Nature |
|---|---|---|
| IMPORT-003 | Revue/approbation du propriétaire des données Excel | Humain |
| BACKUP-004 | Endpoint et responsable INRAE non fournis | Institutionnel |
| BACKUP-005 | Hôte, SSO/LDAP, endpoint, secrets non fournis | Institutionnel |

S'y ajoutent des blocages **de fait**, non marqués « Bloqué » dans la matrice :
- GENOME-002/003 et BIO-002/005 : références et bases BLAST gouvernées absentes.
- ATTACH-002 : scanner non choisi.

## 6. Hors périmètre et changements de périmètre

- **Changements de périmètre approuvés : aucun trouvé** **[EXÉCUTÉ — recherche docs/ADR/plans]**.
  Les ADR 0001–0005 sont des décisions d'architecture, pas des réductions de périmètre.
- **Ajouts non prévus au plan initial** : persistance des jobs scientifiques et qualification
  Primer3 (plan 005, ADR 0005, `docs/PRIMER3_QUALIFICATION.md`). L'ajout est cohérent avec
  BIO-003/006/007 de la spec, mais il est avancé avant l'inventaire. C'est un **réordonnancement
  de fait**, non documenté comme décision utilisateur **[INFÉRÉ]**.
- **Hors périmètre (spec)** : ELN complet, LIMS généraliste, conception automatique d'amorces
  au-delà de Primer3. Aucun code détecté dans ces domaines **[CODE]**.

## 7. Écarts de processus

1. Les plans 002–004 sont livrés sur des branches, **pas fusionnés dans `main`**.
2. Le plan 005 a été développé sans commit, avec une migration 0004 appliquée en base locale.
3. Les preuves E2E ne sont pas archivées : aucun rapport Playwright n'est conservé, et les
   preuves n'existent que sous forme déclarative.
4. `STATUS.md` n'a pas été tenu à jour après le 2026-09-07.

```
current_task: none defined
next_action: awaiting user prioritization
```
