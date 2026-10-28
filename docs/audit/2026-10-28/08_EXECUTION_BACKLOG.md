# 08 — Backlog d'exécution par lots

- Date : 2026-10-28 · Statut : **proposition**. Aucun lot n'est approuvé ni engagé.
- Les efforts sont **[INFÉRÉS]**, en jours-personne (j). Un lot dépasse rarement 3 j et
  ne dépasse jamais 5 j.
- Règles communes à tous les lots :
  - appliquer `AGENTS.md` ;
  - lancer `make format lint typecheck test` avant toute remise ;
  - toute modification de schéma passe par une révision Alembic ;
  - ne jamais toucher au classeur Excel source ;
  - ne jamais commiter de secret ;
  - mettre à jour STATUS, BACKLOG et CHANGELOG par ajout daté ;
  - ne commiter, pousser ou fusionner qu'avec autorisation.

```
current_task: none defined
next_action: awaiting user prioritization
```

## Vue d'ensemble

| Lot | Titre | Dépend de | Effort | Parallélisable avec |
|---|---|---|---|---|
| R0-01 | Sécuriser le plan 005 localement | — | 0,5–1 j | R0-06 |
| R0-02 | Intégration Git (portes G1–G4) | R0-01 | 0,5 j | — |
| R0-03 | Tests d'intégration en CI ; `make test` sans test ignoré | R0-02 (G2) | 1–1,5 j | R0-04 |
| R0-04 | E2E isolée de la base de dev | R0-02 (G2) | 1,5–2 j | R0-03 |
| R0-05 | Cohérence STATUS, BACKLOG et CHANGELOG | R0-02 | 0,5 j | R0-03, R0-04 |
| R0-06 | Outillage mémoire et nettoyage du stash | Accords D12 et G5 | 0,25 j | Tous |
| R1-01 | Gates du plan 005 | R0-04 | 2–3 j | R1-03, R1-05 |
| R1-02 | E2E du cycle de vie | R0-04 | 2 j | R1-03 |
| R1-03 | Matrice négative des assays | R0-03 | 1 j | R1-01, R1-02 |
| R1-04 | Visibilité de la recherche et des suggestions | R0-03 | 2–3 j | R1-01 |
| R1-05 | Couverture d'audit et non-fuite | R0-03 | 1–2 j | R1-01, R1-02 |
| R1-06 | Upload désactivé (D2 = b) | D2 | 0,5 j | Tous |
| R1-07 | Export CSV minimal | D9, R1-04 | 1–2 j | R1-08 |
| R1-08 | Sauvegarde et restauration | D4 (VM) | 2–3 j | R1-01 à R1-05 |
| R1-09 | Sécurité de session TLS | D4 (VM) | 1–2 j | R1-08 |
| R1-10 | Données pilote | D10, R1-02 | 0,5 j | — |
| R1-11 | Recette pilote | Tous les lots R1 | 0,5–1 j | — |

---

## R0 — Stabilisation et intégration (4–6 j)

### R0-01 — Sécuriser le plan 005 localement *(lot prêt à exécuter)*

**Objectif.** Rendre le travail du plan 005 commitable en toute sécurité, sans rien
écrire dans Git ni sur le dépôt distant.

**Composants.**
- `.gitignore`
- les fichiers du plan 005 :
  - `apps/api/` : migration `0004`, puis `routes`, `models`, `repositories`, `schemas` et
    `services` `scientific*`
  - `services/bioinfo-worker/`
  - `apps/web/` : `scientific-jobs/`, `Primer3JobSection` et `ScientificJobAutoRefresh`
  - `docs/`

**Dépendances.** Aucune.

**Étapes exécutables par un agent de développement :**

1. **Relevé initial.**
   - Lancer `git status --short | wc -l`. Le résultat attendu est 50 entrées.
   - Lancer `git stash list`.
   - Ne rien modifier à ce stade.
2. **Ignorer les artefacts locaux.**
   - Ajouter à `.gitignore`, dans la section des outils locaux, la ligne `.serena/`.
   - Ne pas ajouter `playwright-report/` : la sortie va dans `/tmp` (`playwright.config.ts`).
3. **Scan de secrets** sur les fichiers modifiés et non suivis.
   - Lancer, par exemple :
     ```
     git diff --name-only; git ls-files --others --exclude-standard
     ```
   - Rechercher ensuite les motifs `password|secret|token|api[_-]?key|BEGIN .*PRIVATE`.
   - Examiner en particulier :
     - `compose.yml`
     - `database/seeds/initial.sql`
     - `apps/api/src/oligospace_api/core/config.py`
     - `envs/*.yml`
   - Résultat attendu : aucune valeur réelle. Seules des références `${VAR}` ou des
     valeurs de développement documentées sont acceptables.
   - Vérifier que `.env` est ignoré, avec `git check-ignore .env`.
   - **Ne jamais afficher le contenu de `.env`.**
4. **Relecture du diff**, fichier par fichier, avec `git diff --stat` puis `git diff <fichier>`.
   - Vérifier que chaque fichier modifié relève du périmètre du plan 005. Les candidats
     non évidents sont `LoginActions.tsx`, `auth.ts`, `e2e/helpers.ts` et `oligos.spec.ts`.
   - Si un fichier sort de ce périmètre : **ne pas le corriger**. Le lister dans le
     rapport avec une proposition de commit séparé.
5. **Validation déterministe.**
   - Lancer `make format`.
   - Comparer `git diff --stat` avant et après : le formatage ne doit produire aucun diff
     inattendu.
   - Lancer ensuite `make lint`, `make typecheck`, `make test` et `make compose-config`.
   - Consigner pour chaque commande le code de sortie, le nombre de tests passés, échoués
     et ignorés.
6. **Migration.**
   - Lancer `make test-integration`. La cible utilise `postgres-test`, un conteneur
     jetable supprimé ensuite.
   - Si le temps le permet, faire un aller-retour `upgrade head → downgrade 0003 → upgrade head`,
     **uniquement** sur `postgres-test`.
   - **Interdit : toute migration sur la base de dev.**
7. **Stash.**
   - Comparer `git show stash@{0}:docs/exec-plans/active/005-persistent-scientific-jobs-primer3-analysis.md`
     avec le fichier courant.
   - Indiquer si le stash contient un contenu absent de l'arbre de travail.
   - **Ne pas supprimer** le stash.
8. **Préparer, sans les exécuter**, les commandes des trois commits (voir doc 07, § 2,
   étape 2), avec la liste exacte des fichiers de chaque commit.
9. **Rapport.**
   - Les résultats des étapes 1 à 8.
   - Les anomalies trouvées.
   - Les correctifs appliqués : uniquement des corrections minimales qui rendent les tests
     du plan 005 verts. Tout autre correctif est signalé, pas appliqué.

**Tests.** Ceux de l'étape 5 et `make test-integration`.

**Critères d'acceptation.**
- `.serena/` n'apparaît plus dans `git status`.
- Aucun secret n'a été trouvé, ou chaque occurrence est justifiée.
- `make lint`, `typecheck`, `test` et `compose-config` ont le code de sortie 0.
- `make test-integration` passe, ou ses échecs sont expliqués.
- Le plan de commits est prêt.
- **Aucun commit, push, merge ni suppression** n'a eu lieu.

**Effort.** 0,5–1 j.

**Risques.**
- Des tests du plan 005 sont rouges : on corrige dans le périmètre, ou on remonte le
  problème.
- Le diff contient des fichiers hors plan : on prévoit un commit séparé.
- Docker est indisponible localement : on le signale, sans bloquer les étapes 1 à 5.

**Parallélisation.** Possible avec R0-06.

### R0-02 — Intégration Git

**Objectif.** Faire en sorte que `main` reflète les plans 002 à 005.

**Étapes.** La séquence du doc 07, § 2 :

| Étape | Porte |
|---|---|
| Commits | G1 |
| Push | G2 |
| Merge de la PR #1, en merge commit | G3 |
| Ouverture de la PR #2 | — |
| Merge de la PR #2 | G4 |

**Tests.** CI verte sur la PR #2, puis sur `main`.

**Critère d'acceptation.** `git merge-base --is-ancestor <commit 005> origin/main` réussit.

**Effort.** 0,5 j, plus le délai des validations.

**Risque.** Un squash accidentel (voir doc 07).

### R0-03 — Tests d'intégration en CI (D-04)

**Objectif.** Exécuter réellement les tests d'intégration PostgreSQL, en local et en CI.

**Changements.**
- Dans `.github/workflows/ci.yml`, créer un job `integration` avec un service `postgres:17`.
- Ce job exporte `OLIGOSPACE_TEST_DATABASE_URL` et lance `pytest tests/integration`.
- Documenter la variable dans `docs/` et dans le `Makefile`. `make test` doit soit échouer
  explicitement si la variable manque, soit déléguer à `make test-integration`.

**Tests.** Les 6 tests d'intégration existants, plus `test_scientific_routes.py`.

**Critères d'acceptation.**
- Le job CI `integration` est vert.
- Il rapporte 0 test ignoré.
- Un test volontairement cassé fait échouer la CI (vérification ponctuelle).

**Effort.** 1–1,5 j.

**Risque.** Le temps de CI augmente.

### R0-04 — E2E isolée (D-05)

**Objectif.** Faire tourner Playwright sur une pile dédiée, sans jamais toucher la base
de dev.

**Changements.**
- Lancer `make test-e2e` sous un projet Compose distinct (`-p oligospace-e2e`), avec ses
  propres volumes et sa propre base, et le détruire à la fin.
- Archiver le rapport Playwright : en artefact CI, ou dans un dossier daté hors du dépôt.
- Soit ajouter un job CI E2E, soit documenter la procédure locale, selon le coût.

**Tests.** Les 7 specs, dont `scientific-jobs.spec.ts`.

**Critères d'acceptation.**
- Les specs sont vertes.
- Les comptes de lignes des tables principales de la base de dev sont identiques avant et
  après l'exécution.
- Le rapport est archivé.

**Effort.** 1,5–2 j.

**Risques.**
- Keycloak met du temps à démarrer en CI.
- Des conflits de ports peuvent survenir avec la pile de dev.

### R0-05 — Cohérence documentaire (D-15)

**Objectif.** Rendre `STATUS.md`, `BACKLOG.md` et `CHANGELOG.md` exacts.

**Changements.**
- Indiquer la tête de migration 0004, 7 specs et l'état du plan 005.
- Intégrer les corrections C-01 à C-11 du doc 06.
- Procéder **par ajout daté**, sans réécrire l'historique.

**Critère d'acceptation.** Aucune contradiction entre STATUS et l'exécution réelle.

**Effort.** 0,5 j.

### R0-06 — Outillage

**Objectif.** Rétablir la continuité de la mémoire de projet.

**Changements.**
- Après l'accord D12 : corriger la commande MCP de Basic Memory, puis mettre à jour le
  checkpoint par MCP.
- Après l'accord G5 : supprimer `stash@{0}`.

**Critère d'acceptation.** L'outil MCP `search_notes` répond, et le nouveau checkpoint
est visible.

**Effort.** 0,25 j.

---

## R1 — Pilote scientifique utilisable (13–19 j de développement, plus la recette)

### R1-01 — Gates du plan 005 (D-06)

Couvre BIO-003, BIO-006 et BIO-007.

**Changements.**
- Écrire l'E2E Chromium des jobs Primer3 : succès, échec de validation, échec du worker.
- Écrire le test d'interruption et de reprise : arrêter le worker, puis Redis, **sur la
  pile E2E isolée uniquement**.
- Vérifier l'idempotence (plan 005, § 24).
- Vérifier l'affichage de la provenance : algorithme, version 2.6.1, paramètres,
  horodatage.
- Déplacer le plan 005 vers `completed/` avec son résultat.

**Critères d'acceptation.**
- Un job interrompu finit en `succeeded` ou en `failed` explicite, sans doublon, vérifié
  par SQL.
- Les specs sont vertes.

**Effort.** 2–3 j.

**Risque.** Une reprise non déterministe. Repli prévu par D11 : masquer Primer3.

### R1-02 — E2E du cycle de vie (D-07)

Couvre PROJECT-001, TARGET-003, OLIGO-007 et ASSAY-007.

**Changements.** Écrire des specs pour déprécier et archiver chaque entité, et pour
vérifier que la réutilisation d'un identifiant est refusée.

**Critères d'acceptation.**
- Les specs sont vertes.
- Une entrée d'audit existe pour chaque transition.

**Effort.** 2 j.

### R1-03 — Matrice négative des assays (D-08)

Couvre ASSAY-004.

**Changements.** Écrire au moins un test négatif par règle, au niveau API.

**Critère d'acceptation.** Une matrice règle → test, toute verte.

**Effort.** 1 j.

### R1-04 — Visibilité (D-09)

Couvre AUTH-004 et SEARCH-003.

**Changements.** Écrire des tests d'intégration pour 4 portées × rôles, sur la liste, le
détail, la recherche et les suggestions.

**Critères d'acceptation.**
- Tous les tests sont verts.
- Toute fuite trouvée est corrigée et couverte par un test de non-régression.

**Effort.** 2–3 j.

**Risque.** Une fuite structurelle. Elle donne lieu à un lot de correctif dédié, à
réestimer.

### R1-05 — Audit (D-10)

Couvre AUDIT-001 et AUDIT-002.

**Changements.**
- Écrire un test paramétré : chaque mutation du périmètre MVP doit produire une entrée
  d'audit.
- Vérifier l'absence de champs sensibles dans les payloads d'audit.

**Effort.** 1–2 j.

### R1-06 — Pièces jointes, option b (D-14b)

Couvre ATTACH-002.

**Changements.**
- L'API refuse l'upload : réponse 403 ou 501 avec un message explicite.
- L'UI masque l'upload ou explique pourquoi il est indisponible.
- Écrire un test API.

**Effort.** 0,5 j.

### R1-07 — Export CSV minimal *(sous réserve de D9)*

**Changements.**
- Exporter en CSV les résultats de recherche **visibles** de l'utilisateur.
- Chaque export crée une entrée d'audit.
- Les colonnes sont documentées.

**Critères d'acceptation.**
- Le test de visibilité réutilise R1-04 : aucune ligne non visible dans l'export.
- L'entrée d'audit est présente.

**Effort.** 1–2 j.

### R1-08 — Sauvegarde et restauration (D-11)

Couvre BACKUP-001 et BACKUP-003.

**Pré-requis.** La VM D4.

**Changements.**
- Sauvegarder PostgreSQL, MinIO et le realm Keycloak.
- Restaurer sur une instance vierge.

**Critères d'acceptation.**
- Le runbook a été exécuté.
- La durée est mesurée, ainsi que le RPO et le RTO.
- Les objets du scénario de démonstration sont retrouvés.

**Effort.** 2–3 j.

### R1-09 — Session TLS (D-12)

Couvre AUTH-005.

**Pré-requis.** La VM D4.

**Critères d'acceptation.**
- Les cookies portent `Secure`, `HttpOnly` et `SameSite`.
- CORS est limité à l'origine.
- L'expiration est vérifiée.

**Effort.** 1–2 j.

### R1-10 — Données pilote *(sous réserve de D10)*

**Changements.** Rédiger un guide de saisie d'un sous-ensemble curé de 20 à 50 oligos.
Le choix des oligos revient au propriétaire des données. **Aucune donnée scientifique
n'est inventée.**

**Effort.** 0,5 j.

### R1-11 — Recette pilote

**Changements.** Un utilisateur scientifique exécute le scénario du doc 03, § 6, avec
3 comptes.

**Critère d'acceptation.** Un procès-verbal signé, archivé dans `docs/`.

**Effort.** 0,5–1 j, **humain uniquement**.

---

## R2 — Fonctionnalités métier complémentaires (≈ 26–41 j)

| Lot | Contenu | Dépend de | Effort |
|---|---|---|---|
| R2-01 | OIDC institutionnel (D-13, AUTH-001) | Paramètres institutionnels fournis | 2–3 j |
| R2-02 | ClamAV asynchrone et quarantaine (D-14a) | R1-06 | 2–3 j |
| R2-03 | Import en écriture, partie 1 : sous-ensemble validé et idempotence | D7 | 3–4 j |
| R2-04 | Import en écriture, partie 2 : rapport d'écarts et reprise | R2-03 | 2–4 j |
| R2-05 | Inventaire, partie 1 : modèle de lots et de tubes, migration | R1 clos | 3–4 j |
| R2-06 | Inventaire, partie 2 : mouvements et seuils | R2-05 | 3–4 j |
| R2-07 | Inventaire, partie 3 : QR et étiquettes | R2-06 | 2–4 j |
| R2-08 | Commandes, partie 1 : demandes et validation | R2-05 | 3–5 j |
| R2-09 | Commandes, partie 2 : réception liée aux lots | R2-08, R2-06 | 3–5 j |
| R2-10 | Export étendu (EXPORT-*) | R1-07 | 2–3 j |
| R2-11 | Métadonnées EXPTYPE (D-19) | — | 1–2 j |

## R3 — Production consolidée et modules avancés

| Lot | Contenu | Effort |
|---|---|---|
| R3-01 | RLS PostgreSQL (D-16) | 3–5 j |
| R3-02 | Rate limiting et monitoring (D-18) | 3–5 j |
| R3-03 | Durcissement prod, partie 1 : déploiement et secrets | 2–4 j |
| R3-04 | Durcissement prod, partie 2 : exploitation et alerting | 3–4 j |
| R3-05+ | BLAST et mapping sur références gouvernées, GeneOligoViewer, pull INRAE | 20–35 j, à découper une fois les références fournies |
