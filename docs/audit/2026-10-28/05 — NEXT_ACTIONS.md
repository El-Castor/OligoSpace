# 05 — Prochaines actions

- Date : 2026-10-28 · Statut : **proposition de l'audit, soumise à validation utilisateur**.
- Sources : `01` à `04` de ce dossier. Les identifiants D-xx renvoient au doc 04 § 2, les
  critères au doc 03 § 5.
- Légende épistémique : voir `01 — PROJECT_STATE_AUDIT.md`. Les efforts sont **[INFÉRÉS]**.
- Mode d'exécution :
  - **Autonome** : un agent peut exécuter l'action sans arbitrage ; les règles du dépôt
    s'appliquent (commit seulement si demandé, pas de push sans accord).
  - **Validation humaine** : l'action exige un accord explicite ou une entrée externe.

```
current_task: none defined
next_action: awaiting user prioritization
```

Les actions ci-dessous sont **recommandées** et non approuvées. Aucune n'est engagée.

## 1. Top 5

| # | Action | Résultat attendu | Critère d'acceptation vérifiable | Mode |
|---|---|---|---|---|
| 1 | **Sécuriser le plan 005** (D-01). Il faut d'abord relire le diff ; ajouter `.serena/` au `.gitignore` (D-17) ; faire un commit atomique sur `codex/scientific-jobs-primer3` ; puis pousser avec upstream. | Le travail non commité (environ 49 entrées dans `git status`) est versionné et sauvegardé à distance. | `git status --short` est vide, hors `docs/audit/` si ce dossier est volontairement exclu. `git rev-parse @{u}` répond. `git log origin/codex/scientific-jobs-primer3 -1` montre le commit. | **Validation humaine** : commit et push explicitement autorisés |
| 2 | **Établir l'état CI réel** (D-03), via l'interface web GitHub ou après installation autorisée de `gh`. Il faut aussi vérifier si une PR 002–004 existe : le message de `stash@{0}` en mentionne une. | Statut CI connu pour `main` et chaque branche `codex/*` ; état des PR connu. | Tableau branche → dernier run → statut, consigné dans `docs/audit/`. Toute branche rouge a une cause identifiée. | **Validation humaine** : installer `gh` ou fournir l'accès |
| 3 | **Intégrer 002→005 dans `main`** (D-02), par PR ou par fast-forward selon la décision D3, après la CI verte. | `main` reflète l'état réel du produit. | `git merge-base --is-ancestor <commit plan 005> origin/main` réussit. La CI est verte sur `main`. Les migrations 0001→0004 passent sur une base vierge. | **Validation humaine** : merge |
| 4 | **Base de test dédiée et E2E isolée** (D-04, D-05). Un service ou projet Compose de test fournit `OLIGOSPACE_TEST_DATABASE_URL`. Playwright tourne sur cet environnement et le rapport est archivé. | Les 6 tests d'intégration s'exécutent. L'E2E n'écrit plus dans la base de dev. | `make test` donne 0 test ignoré. Le rapport Playwright HTML est archivé, en artefact CI ou sous `docs/audit/`. La base de dev est inchangée : le nombre de lignes des tables principales est identique avant et après. | **Autonome** (implémentation) ; validation humaine pour le changement de Compose |
| 5 | **Clore les gates du plan 005** (D-06). Il reste l'E2E Chromium des jobs Primer3, y compris les états d'erreur, et le test d'interruption/reprise avec arrêt du worker puis de Redis. | Les jobs scientifiques sont prouvés robustes ; le plan 005 peut passer en `completed/`. | Les specs `scientific-jobs.spec.ts` passent. Un job interrompu finit en `succeeded` ou en `failed` explicite, sans doublon (vérifié en base). La provenance (algorithme, version, paramètres, horodatage) est affichée. Le plan 005 est déplacé avec son résultat. | **Autonome** ; l'arrêt de conteneurs se fait sur l'environnement de test isolé uniquement |

Ordre imposé : 1 → 2 → 3 → 4 → 5. Seule l'action 2 peut démarrer en parallèle de l'action 1.

## 2. Correctifs obligatoires avant tout nouveau développement fonctionnel

Ils sont tous P0 et proviennent du doc 04. Aucune fonctionnalité V1 (inventaire, commandes,
export, import) ne doit commencer avant leur clôture.

| ID | Correctif | Critère d'acceptation | Mode | Effort |
|---|---|---|---|---|
| D-01 | Commit et push du plan 005 | Voir Top 5 #1 | Humain | 0,5 j |
| D-02 / D-03 | Fusion dans `main` et CI verte | Voir Top 5 #2 et #3 | Humain | 1–1,5 j |
| D-04 / D-05 | Base de test et E2E isolée | Voir Top 5 #4 | Autonome | 2–3 j |
| D-06 | Gates du plan 005 | Voir Top 5 #5 | Autonome | 2–3 j |
| D-09 | Visibilité sur recherche et suggestions | Tests négatifs 4 portées × rôles sur liste, détail, recherche et suggestions, tous verts ; toute fuite trouvée est corrigée et couverte par un test de non-régression | Autonome | 2–3 j |
| D-15 | Remettre `STATUS.md`, `BACKLOG.md` et `CHANGELOG.md` en cohérence (base en 0004, nombre de specs, état du plan 005), **par ajout daté** et sans réécrire l'historique | Aucune contradiction entre STATUS et l'exécution réelle (doc 01 § 7) | Autonome, après D-02 | 0,5 j |

## 3. Fonctionnalités prioritaires (MVP, après les correctifs)

| ID | Action | Critère d'acceptation | Mode | Effort |
|---|---|---|---|---|
| D-07 | E2E du cycle de vie (déprécier/archiver oligo, cible, assay, projet) | Specs vertes ; entrée d'audit pour chaque transition ; réutilisation interdite vérifiée | Autonome | 2 j |
| D-08 | Matrice de tests négatifs des règles d'assay | Chaque règle d'ASSAY-004 a au moins un test négatif | Autonome | 1 j |
| D-10 | Couverture d'audit et non-fuite des sérialiseurs | Chaque mutation du périmètre MVP produit une entrée d'audit (vérifié par un test) ; aucun champ sensible dans les payloads d'audit | Autonome | 1–2 j |
| D-14 | Pièces jointes selon D2 : option b (désactiver l'upload côté serveur) ou option a (ClamAV) | b : l'API refuse l'upload et l'UI l'indique. a : un fichier EICAR est mis en quarantaine et refusé | Humain (D2), puis autonome | 0,5–3 j |
| D-11 | Sauvegarde complète et restauration sur instance vierge | Runbook exécuté ; durée mesurée ; RPO/RTO notés ; objets du scénario de démonstration retrouvés | Humain (hôte), puis autonome | 2–3 j |
| D-12 | Sécurité de session sur hôte TLS | Cookies `Secure`/`HttpOnly`/`SameSite` constatés ; CORS limité à l'origine ; expiration vérifiée | Humain (hôte), puis autonome | 1–2 j |
| — | Recette pilote (critère 10) | Le scénario du doc 03 § 6 est exécuté par un utilisateur scientifique ; procès-verbal signé | **Humain uniquement** | 0,5–1 j |

## 4. Travaux différables

| Élément | Raison du report | Horizon |
|---|---|---|
| Inventaire, lots, QR (INV-*), commandes (ORDER-*), export (EXPORT-*) | Non commencés ; aucun n'est requis pour le pilote | V1 |
| Import Excel en écriture (IMPORT-003/004) | Bloqué par la revue du propriétaire des données | V1 |
| OIDC institutionnel (D-13) | Entrées institutionnelles absentes ; le scénario A s'en passe | V1 |
| RLS (D-16), rate limiting et monitoring (D-18), métadonnées EXPTYPE (D-19) | Défense en profondeur et exploitation, non bloquantes pour le pilote | V1 |
| Mapping, BLAST, GeneOligoViewer, pull INRAE | Références gouvernées non fournies | V2 |
| Éléments P2 du doc 02 | Valeur marginale avant V1 | V2 |
| Suppression de `stash@{0}` (D-20) | Sans urgence ; uniquement après D-01 et avec accord explicite | Après D-01 |

## 5. Décisions à arbitrer par l'utilisateur

| # | Question | Options | Recommandation de l'audit | Bloque |
|---|---|---|---|---|
| D1 | Identité du MVP | a) pilote sur Keycloak local ; b) attendre l'OIDC institutionnel | **a**, avec D-13 en V1 | Scénario A ou B ; D-13 |
| D2 | Pièces jointes au MVP | a) ClamAV asynchrone ; b) upload désactivé | **b** pour le pilote, **a** en V1 | D-14 |
| D3 | Stratégie d'intégration dans `main` | a) une PR par plan (002–004, puis 005) ; b) fast-forward direct | **a**, pour la revue et la CI par étape | D-02 |
| D4 | Hôte prod-like pour sauvegarde et session | VM interne, hôte cible, ou report | Fournir une VM interne dès que possible : c'est le délai le plus long du chemin critique | D-11, D-12 |
| D5 | Validation du périmètre MVP et du scénario | Accepter, amender ou rejeter les docs 03/04 | — | Tout le reste |
| D6 | Installer `gh` (nouvelle dépendance outil) | Installer, ou consulter la CI via le web | Installer : c'est l'outil de référence du workflow | D-03 |
| D7 | Revue du propriétaire des données sur l'aperçu d'import Excel | Planifier, ou reporter en V1 | Planifier tôt, hors chemin critique MVP | IMPORT-003/004 |
| D8 | Sort de `docs/audit/2026-10-28/` | Le committer avec le plan 005, séparément, ou le garder local | Commit séparé `docs: add takeover audit` | Hygiène Git |

## 6. Prochaine action précise

Après validation de D5, il faut **exécuter le Top 5 #1** :
1. relire le diff du plan 005 ;
2. ajouter `.serena/` au `.gitignore` ;
3. faire un commit atomique sur `codex/scientific-jobs-primer3` ;
4. pousser avec `git push -u origin codex/scientific-jobs-primer3`.

Ce push exige votre autorisation explicite.
