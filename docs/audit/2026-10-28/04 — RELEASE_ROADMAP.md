# 04 — Feuille de route de release

- Date : 2026-10-28 · Statut : **proposition de l'audit, soumise à validation utilisateur**.
- Sources : `02 — INITIAL_PLAN_GAP_ANALYSIS.md` (matrice, priorités), `03 — MVP_RELEASE_SCOPE.md`.
- Légende épistémique : voir `01 — PROJECT_STATE_AUDIT.md`.
- **Toutes les estimations d'effort sont [INFÉRÉES], en jours-personne d'un développeur
  connaissant le dépôt, avec une confiance faible (±40 %).** Elles excluent les délais
  d'attente des décisions humaines et des entrées institutionnelles.

## 1. Contenu des versions

| Version | Contenu | Critère de sortie |
|---|---|---|
| **MVP** (pilote interne) | Socle vérifié des plans 001–004, jobs Primer3 sécurisés (plan 005), cycle de vie, visibilité, audit et sauvegarde/restauration démontrés. Voir doc 03. | Les 10 critères du doc 03 § 5, chacun prouvé par une exécution archivée, plus la validation par un utilisateur pilote. |
| **V1** (production institutionnelle) | MVP, plus : OIDC institutionnel (AUTH-001), antimalware (ATTACH-002), inventaire physique (INV-*), commandes (ORDER-*), export contrôlé (EXPORT-*), import Excel en écriture (IMPORT-003/004), sauvegarde objets (BACKUP-002), déploiement sur l'hôte cible (BACKUP-005) et monitoring. | Déploiement sur l'hôte cible ; restauration enregistrée ; import réel approuvé par le propriétaire des données ; recette utilisateur sur les flux stock et commande. |
| **V2** (analyse génomique) | Mapping génomique persistant (GENOME-002/003, BIO-002), spécificité BLAST (BIO-005), GeneOligoViewer (VIEW-*), pull INRAE (BACKUP-004), éléments P2. | Références FASTA/GFF et bases BLAST gouvernées fournies et versionnées ; chaque résultat porte algorithme, version, paramètres, référence et horodatage. |

## 2. Blocages et dette technique

### P0 — à lever avant le MVP

| # | Élément | Cause | Preuve | Composants | Dépendances | Correctif | Effort | Risque de régression |
|---|---|---|---|---|---|---|---|---|
| D-01 | **Plan 005 non commité, branche sans upstream** | Développement mené sans commit intermédiaire | `git status` : 30 fichiers modifiés, 20 non suivis ; aucun upstream **[EXÉCUTÉ]** | API, web, worker, docs, migration 0004 | Aucune | Commit atomique, puis push vers `origin/codex/scientific-jobs-primer3` après validation utilisateur | 0,5 j | Faible |
| D-02 | **`main` en retard de 3 plans** | Plans 002–004 livrés sur des branches, jamais fusionnés | `main` = `e802d61` **[EXÉCUTÉ]** | Tout le dépôt | D-01, décision utilisateur | Fusion (fast-forward possible, historique linéaire) de 002→005 dans `main`, puis CI verte | 0,5–1 j | Moyen : migrations 0002–0004 à rejouer sur une base vierge |
| D-03 | **Statut CI inconnu** | `gh` absent ; statut non consulté | `gh: command not found` **[EXÉCUTÉ]** | `.github/workflows/ci.yml` | Installation de `gh` (autorisation requise) ou consultation web | Vérifier la CI sur chaque branche, réparer si elle est rouge | 0,5 j (+ correctifs **[INCONNU]**) | Faible |
| D-04 | **Tests d'intégration ignorés** | Pas de `OLIGOSPACE_TEST_DATABASE_URL` | 6 tests ignorés **[EXÉCUTÉ]** | `apps/api/tests/integration` | Base de test dédiée | Créer une base de test isolée (service Compose dédié ou base séparée), puis l'utiliser dans `make test` et en CI | 1 j | Faible |
| D-05 | **E2E sur la base de dev partagée, rapports non archivés** | `make test-e2e` écrit dans la base de dev ; `playwright-report/` n'est pas conservé | Aucun rapport sur disque **[EXÉCUTÉ]** | `apps/web/e2e`, Compose | D-04 (modèle d'isolation) | Projet Compose E2E isolé ; artefact CI ou archive sous `docs/audit/` | 1–2 j | Moyen : les helpers E2E supposent certaines seeds |
| D-06 | **Gates finaux du plan 005 non passés** | Plan interrompu | Cases non cochées du plan 005 **[DÉCLARÉ]** | Worker, API `scientific`, composants Primer3 | D-01, D-04, D-05 | E2E Chromium finale ; test de reprise worker/Redis ; E2E des états d'erreur ; revue de qualification Primer3 | 2–3 j | Moyen : idempotence sur incident jamais testée |
| D-07 | Cycle de vie non prouvé en E2E | E2E déprécier/archiver absente | Matrice : OLIGO-007, TARGET-003, ASSAY-007, PROJECT-001 **[DÉCLARÉ]** | API, web | D-02 | Specs E2E : archiver, déprécier, réutilisation interdite, audit | 2 j | Faible |
| D-08 | Règles d'assay incomplètement testées | Matrice de tests négatifs partielle | ASSAY-004 « En cours » **[DÉCLARÉ]** | API assays | — | Compléter les tests négatifs (rôles, amplicon, versions) | 1 j | Faible |
| D-09 | Visibilité non couverte sur recherche/suggestions | Matrice 4 portées appliquée aux lectures, pas à la recherche ni aux suggestions | AUTH-004, SEARCH-003 **[DÉCLARÉ]** | API recherche, dépôts | D-04 | Tests négatifs 4 portées × rôles sur liste, détail, recherche et suggestions | 2–3 j | Moyen : possibles corrections de requêtes |
| D-10 | Audit incomplet | Imports non couverts ; sérialiseurs non revus | AUDIT-001/002 **[DÉCLARÉ]** | API services, audit | — | Couvrir toutes les mutations du périmètre MVP ; test de non-fuite des champs sensibles | 1–2 j | Faible |
| D-11 | **Sauvegarde/restauration jamais démontrées** | pgBackRest configuré mais aucune sauvegarde acceptée | BACKUP-001/003 **[DÉCLARÉ]** | `infra/`, runbooks | Hôte prod-like | Exécuter sauvegarde complète + restauration sur instance vierge ; mesurer RPO/RTO ; runbook | 2–3 j | Faible (opération hors code) |
| D-12 | Sécurité de session non revue sur hôte réel | Développement en `localhost` HTTP | AUTH-005 **[DÉCLARÉ]** | NextAuth, API CORS, Caddy | Hôte cible TLS | Vérifier cookies `Secure`/`HttpOnly`/`SameSite`, refresh, expiration, CORS | 1–2 j | Moyen |
| D-13 | OIDC institutionnel absent | Entrées SSO non fournies | AUTH-001, BACKUP-005 **[DÉCLARÉ]** | Keycloak, NextAuth | **Décision D1** + entrées institutionnelles | Fédération Keycloak → IdP institutionnel, qualifiée en navigateur | 2–3 j après réception des entrées | Moyen |
| D-14 | Pièces jointes non scannées | Scanner non choisi | ATTACH-002 **[DÉCLARÉ]** | API attachments, MinIO | **Décision D2** | Option a : ClamAV en file asynchrone + quarantaine (2–3 j). Option b : désactiver l'upload côté serveur (0,5 j). | 0,5–3 j | Faible (b) ; moyen (a) |

### P1 — avant la V1

| # | Élément | Cause / preuve | Correctif | Effort |
|---|---|---|---|---|
| D-15 | `STATUS.md` périmé (2026-09-07, base indiquée en 0003) ; incohérence 6/7 specs (DEPLOY-002) | Doc 01 § 7 **[EXÉCUTÉ]** | Mettre à jour STATUS/BACKLOG/CHANGELOG après D-01/D-02 | 0,5 j |
| D-16 | Pas de RLS PostgreSQL | Autorisation uniquement applicative ; backlog **[CODE]** | ADR, puis RLS sur les tables à visibilité, en défense en profondeur | 3–5 j |
| D-17 | `.serena/` non suivi | Configuration d'outil locale **[EXÉCUTÉ]** | Ajouter à `.gitignore` | < 0,1 j |
| D-18 | Pas de rate limiting ni de monitoring | Doc 01 § 5 **[CODE]** | Limitation au niveau Caddy/API ; métriques, alertes, journaux centralisés | 3–5 j |
| D-19 | Métadonnées requises des types d'expérience non imposées | EXPTYPE-002 **[DÉCLARÉ]** | Validation serveur des schémas de métadonnées | 1–2 j |
| D-20 | `stash@{0}` (document du plan 005) | Doublon du fichier présent dans l'arbre **[EXÉCUTÉ]** | Le supprimer après le commit D-01, sur validation explicite | < 0,1 j |

### P2 — différable

Ce sont les éléments P2 de la matrice du doc 02 : VIEW-002/003/005, GENOME-003, BIO-005,
INV-007, AUDIT-003, EXPORT-003, BACKUP-004, IMPORT-005, TEAM-003, USER-003, VALID-004. Aucun
ne bloque le MVP ni la V1.

## 3. Scénarios

### Scénario A — Plus rapide utilisable : pilote interne

- **Hypothèses** :
  - D1 : pilote sur Keycloak local, pas d'OIDC institutionnel ;
  - D2 : upload de pièces jointes désactivé ;
  - un hôte prod-like est disponible (une VM interne suffit).
- **Contenu** : D-01 à D-12, plus D-14 option b. D-13 est hors scénario.
- **Effort** : **≈ 15–21 j** de développement et de validation, soit environ **10–14 jours
  ouvrés** si certaines tâches avancent en parallèle (D-08 et D-10 en parallèle de D-05/D-06)
  **[INFÉRÉ]**.
- **Résultat** : une équipe pilote utilise le registre et le QC Primer3 sur données réelles,
  avec sauvegarde démontrée. Ce n'est **pas** une production institutionnelle.

### Scénario B — V1 complète

- **Contenu** : le scénario A, plus D-13, D-14 option a, D-15 à D-19, et les domaines V1 :

| Bloc V1 | Effort **[INFÉRÉ]** |
|---|---|
| MVP (scénario A, plus D-13 et D-14 option a) | ≈ 17–25 j |
| Inventaire physique (INV-*) | 8–12 j |
| Commandes (ORDER-*) | 6–10 j |
| Export contrôlé (EXPORT-*) | 3–5 j |
| Import Excel en écriture (IMPORT-003/004) | 5–8 j, après approbation du propriétaire |
| Déploiement prod, monitoring, RLS, rate limiting | 5–8 j, plus D-16/D-18 |
| **Total V1** | **≈ 52–80 j** (dont ≈ 35–55 j au-delà du MVP) |

- **V2** : 20–35 j selon la qualité des références fournies **[INFÉRÉ, confiance très faible]**.

### Chemin critique (commun aux deux scénarios)

```
D-01 commit/push plan 005
  → D-02 fusion 002–005 dans main + D-03 CI verte
    → D-04 base de test dédiée → D-05 E2E isolée et archivée
      → D-06 gates plan 005 ─┐
      → D-07 / D-09 (P0 fonctionnels) ─┤
                                       → D-11 sauvegarde/restauration sur hôte prod-like
                                         → D-12 session sur hôte réel
                                           → [D1/D2] → validation pilote (critère 10)
```

Hors code, les éléments les plus longs du chemin critique sont **[INFÉRÉ]** :
- la mise à disposition d'un hôte prod-like ;
- les décisions D1 et D2 ;
- la disponibilité d'un utilisateur pilote.

## 4. Risques

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Perte du travail non commité du plan 005 | Moyenne | Élevé | D-01 en priorité absolue |
| La CI est rouge sur les branches codex/* | **[INCONNU]** | Moyen | D-03 avant toute fusion |
| La migration 0004 diverge entre la base locale (appliquée) et une base vierge | Faible | Moyen | Rejouer 0001→0004 sur base vierge dans D-04 |
| Fuite de visibilité découverte par D-09 | Moyenne | Élevé | Correctif prioritaire ; tests de non-régression |
| La restauration échoue ou le RTO est inacceptable | **[INCONNU]** | Élevé | D-11 tôt dans le scénario, sur hôte prod-like |
| Les entrées institutionnelles tardent | Élevée | Élevé (V1) | Scénario A découplé de D1 |
| Le périmètre s'élargit avant la sécurisation du MVP | Moyenne | Moyen | Geler les nouvelles fonctionnalités jusqu'à la sortie du MVP |

```
current_task: none defined
next_action: awaiting user prioritization
```
