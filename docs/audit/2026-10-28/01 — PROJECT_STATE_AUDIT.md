# 01 — Audit de l'état du projet OligoSpace

- Date de l'audit : 2026-10-28
- Branche auditée : `codex/scientific-jobs-primer3` (HEAD `381b0f4`)
- Nature : audit non destructif — aucun code applicatif modifié, aucun commit, aucun push.
- Hiérarchie des preuves : exécuté > tests > code > docs > mémoires.

Légende épistémique : **[EXÉCUTÉ]** observé pendant cet audit · **[DÉCLARÉ]** affirmé
par la documentation du dépôt sans réexécution · **[CODE]** déduit de l'implémentation ·
**[INFÉRÉ]** déduction de l'auditeur · **[INCONNU]**.

## 1. Sources consultées

| Source | Résultat |
|---|---|
| ResearchBrain (Basic Memory, projet `research-memory`) | **Indisponible** (MCP `CONNECT_TIMEOUT`, deux tentatives). Aucune note projet ni checkpoint consulté. |
| Mémoires Serena | Vides. |
| GitHub (`gh`) | CLI non installé : statut CI et PR **[INCONNU]**. |
| Git local | Historique, branches, stash, diff de l'arbre de travail. |
| Docs du dépôt | `AGENTS.md`, `ARCHITECTURE.md`, `docs/PRODUCT_SPEC.md`, `docs/DATA_MODEL.md`, `docs/SECURITY.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/project/{STATUS,BACKLOG,CHANGELOG}.md`, ADR 0001–0005, plans 001–005. |
| Runtime local | `docker compose ps`, journaux 24 h, état Alembic, table `scientific_jobs` (lecture seule), santé via Caddy. |
| Skills dépôt `.claude/skills/` | Absent. |

## 2. État Git **[EXÉCUTÉ]**

- Historique linéaire : `e802d61` (plan 001) → `5773452` (002) → `de51e6f` (003) → `381b0f4` (004).
- `main` pointe sur `e802d61` uniquement. **Les plans 002–004 ne sont pas fusionnés dans `main`**
  (présents sur des branches `codex/*` poussées).
- **Le plan 005 n'existe que dans l'arbre de travail** : 30 fichiers modifiés (+921/−126) et
  20 fichiers non suivis (migration `0004_scientific_jobs.py`, routes/services/schemas
  `scientific`, composants web Primer3, specs E2E, `docs/PRIMER3_QUALIFICATION.md`, plan 005 actif).
  La branche courante n'a **pas d'upstream** : ce travail est exposé à une perte.
- `stash@{0}` : ne contient que le document du plan 005.
- `.serena/` non suivi (configuration d'outil, à ignorer ou exclure).

## 3. État runtime local **[EXÉCUTÉ]**

- 9 conteneurs actifs depuis ~10 jours ; `api`, `postgres`, `redis` en état *healthy*.
- Santé via Caddy (`http://oligospace.localhost:8080/api/v1/health/ready`) : `{"status":"ready"}`.
- Base locale à la révision Alembic `0004` (migration du plan 005 appliquée, alors que son code
  n'est pas commité).
- `scientific_jobs` : 8 jobs `succeeded`, tous du 2026-09-07
  (`oligo_primer3_qc` ×6, `assay_primer3_pair_compatibility` ×2). Ceci prouve qu'un chemin
  bout-en-bout API → Redis → worker → DB a fonctionné au moins une fois ; cela ne prouve ni la
  validation UI, ni la reprise sur incident.
- Journaux 24 h : 0 erreur.
- Aucun rapport Playwright (`playwright-report/`, `test-results/`) sur disque : **la dernière
  exécution E2E n'est pas démontrable localement**.

## 4. Vérifications exécutées pendant l'audit

| Commande | Résultat | Commentaire |
|---|---|---|
| `make compose-config` | **PASS** **[EXÉCUTÉ]** | |
| `PYTHON_RUNNER=container make lint` | **PASS** **[EXÉCUTÉ]** | ruff API + worker, eslint web ; sur l'arbre de travail (plan 005 inclus). |
| `PYTHON_RUNNER=container make typecheck` | **PASS** **[EXÉCUTÉ]** | mypy API (50 fichiers), worker (3), `tsc --noEmit` web (exit 0). |
| `make test` (sans `OLIGOSPACE_TEST_DATABASE_URL`) | **PASS partiel** **[EXÉCUTÉ]** | API : 25 passés, **6 ignorés** (tests d'intégration route, dont `test_scientific_routes.py`, non exécutés faute de base de test dédiée) ; worker : 7 passés ; web : `registry-format.test.mjs` exit 0. |
| `make format` | Non exécuté | Réécrit des fichiers : interdit par le périmètre de l'audit. |
| `make test-e2e` | Non exécuté | Reconstruit les images et écrit dans la base de dev partagée : non conforme à « aucune modification de données ». |

Ces résultats prouvent la cohérence statique et unitaire du code actuel ; ils ne constituent
**pas** une validation utilisateur ni une preuve d'intégration (les 6 tests de routes et l'E2E
n'ont pas tourné).

Dernières preuves déclarées **[DÉCLARÉ]** (`STATUS.md`, `CHANGELOG.md`, plan 005) :
- 2026-09-02 : 21 tests API, 7 specs Chromium via Caddy (plans 003–004).
- Plan 005 : 25 tests unitaires API, 7 tests worker, migration 0004 ; **E2E Chromium finale,
  test de reprise worker/Redis et revue de traçabilité non réalisés** (cases non cochées du plan).

## 5. Inventaire par couche

### Backend (FastAPI) **[CODE]**
- Domaines livrés : identité/RBAC, utilisateurs, équipes, projets, organismes, génomes (identité),
  cibles, oligos (normalisation, QC calculé, anti-doublons), types d'expérience, assays (rôles,
  amplicon, versions), runs, validations, pièces jointes (MinIO), recherche, audit, imports (prévisualisation).
- Plan 005 (non commité) : modèle `scientific_jobs`, file Celery, contrat de job, routes
  `/scientific`, idempotence/provenance.
- Absent : commandes, inventaire, lots, emplacements, QR, export, mapping persistant.

### Frontend (Next.js) **[CODE]**
- Pages registre, détail oligo/assay, espaces de travail, admin, preuves d'expérience.
- Plan 005 : `Primer3JobSection`, `ScientificJobAutoRefresh`, `app/scientific-jobs/`.
- Inventaire/commandes : `PlannedPage` (placeholder). Pas de GeneOligoViewer.

### Base de données **[EXÉCUTÉ + CODE]**
- PostgreSQL 17, Alembic 0001→0004. 0004 non commitée. Pas de RLS (backlog).
- Seeds de référence dans `database/seeds/initial.sql` (modifié, non commité).

### Infrastructure **[CODE + EXÉCUTÉ]**
- Compose : postgres, redis, minio, keycloak, api, web, worker, beat, caddy. CI GitHub définie
  (`.github/workflows/ci.yml`), statut **[INCONNU]**.
- Non livré : déploiement de production, sauvegarde pgBackRest acceptée, restauration enregistrée,
  monitoring, antimalware, OIDC institutionnel, rate limiting.

## 6. Indicateurs d'avancement (dénominateur : 99 exigences de `REQUIREMENTS_TRACEABILITY.md`)

| Indicateur | Nombre | % | Nature |
|---|---:|---:|---|
| Vérifié (statut déclaré) | 31 | 31,3 % | [DÉCLARÉ] |
| Implémenté ou mieux (Vérifié + Implémenté) | 40 | 40,4 % | [DÉCLARÉ] |
| Entamé (Vérifié + Implémenté + En cours) | 69 | 69,7 % | [DÉCLARÉ] |
| Planifié (non commencé) | 27 | 27,3 % | [DÉCLARÉ] |
| Bloqué | 3 | 3,0 % | [DÉCLARÉ] |
| Utilisable en navigateur (Vérifié **et** preuve E2E Caddy) | 19 | 19,2 % | [INFÉRÉ] de la colonne preuve |
| Partiellement utilisable (En cours/Implémenté avec E2E partielle) | 17 | 17,2 % | [INFÉRÉ] |

Ces pourcentages ne sont pas pondérés par l'effort. Les preuves datent de septembre 2026 et
n'ont pas été rejouées pendant l'audit. Le nombre de commits n'est pas utilisé.

## 7. Incohérences documentaires relevées

1. `STATUS.md` daté du 2026-09-07 ; son pied indique la base en 0003 alors que la base est en 0004.
2. `DEPLOY-002` cite « 6 specs Caddy », `STATUS.md` en cite 7.
3. `STATUS.md`/`CHANGELOG.md` décrivent le plan 005 comme avancé alors que rien n'est commité.
4. `main` ne contient que le plan 001 : toute documentation de `main` est en retard de 3 plans.

## 8. Synthèse

Le projet dispose d'un **registre scientifique cœur démontré en navigateur** (plans 001–004) et
d'un **moteur de jobs Primer3 fonctionnel mais non sécurisé** (plan 005 non commité, gates finaux
non passés). Les domaines inventaire/commandes/viewer/export et l'exploitation production
(sauvegarde, restauration, OIDC institutionnel, antimalware) ne sont pas commencés ou sont bloqués
par des entrées institutionnelles. Le risque immédiat principal est la **perte du travail non
commité** ; le second est **l'écart entre `main` et l'état réel**.

```
current_task: none defined
next_action: awaiting user prioritization
```
