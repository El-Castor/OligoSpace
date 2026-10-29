# 06 — Périmètre MVP révisé et consolidation de l'audit

- Date : 2026-10-28 · Statut : **proposition, soumise à validation utilisateur (D5)**.
- Sources : docs `01` à `05` de ce dossier, plus les vérifications complémentaires
  du 2026-10-28 : API GitHub publique, `Makefile`, `apps/web/playwright.config.ts`,
  `.github/workflows/ci.yml` et `git stash show`.
- Ce document **complète** les docs 01–05 sans les réécrire. Les corrections sont listées
  au § 5.
- Légende épistémique (voir doc 01) :
  - **[EXÉCUTÉ]** : constaté par une commande ;
  - **[CODE]** : lu dans le code ;
  - **[DÉCLARÉ]** : affirmé par la documentation ;
  - **[INFÉRÉ]** : déduit ;
  - **[INCONNU]** : non établi.

```
current_task: none defined
next_action: awaiting user prioritization
```

## 1. Cohérence du décompte des 99 exigences

Le décompte se recoupe de deux façons, et les deux totalisent bien 99 **[CODE]**, à partir
de la matrice du doc 02 et de `docs/REQUIREMENTS_TRACEABILITY.md`.

| Vue | Répartition | Total |
|---|---|---|
| Par état d'avancement | 69 commencées + 27 planifiées + 3 bloquées | 99 |
| Par priorité restante | 31 déjà vérifiées + 17 P0 + 39 P1 + 12 P2 | 99 |

Les états d'avancement sont **cumulatifs** et non exclusifs :

```
69 commencées ⊇ 40 implémentées ou mieux ⊇ 31 vérifiées ⊇ ≈ 19 utilisables
```

Il ne faut donc pas additionner 31 + 40 + 69 ; c'est la source d'ambiguïté du doc 02.

Trois notions doivent rester séparées :

| Notion | Définition retenue | Nombre |
|---|---|---|
| **Implémentée** | Du code existe et couvre l'exigence | 40 **[CODE]** |
| **Validée** | Un test automatisé ou une exécution prouve le comportement | 31 **[DÉCLARÉ]**, dont une partie **[EXÉCUTÉ]** pendant l'audit (tests unitaires et CI verte) |
| **Utilisable** | Un utilisateur scientifique peut accomplir la tâche de bout en bout dans l'UI, sur une instance stable, sans aide développeur | ≈ 19 **[INFÉRÉ]**, aucune n'est **[EXÉCUTÉ]** par un utilisateur réel |

Limite : aucune recette utilisateur n'a eu lieu. Le chiffre « utilisable » reste donc une
inférence. Il deviendra une mesure seulement à la recette pilote (R1-11).

## 2. Périmètre exact des 17 exigences P0

| Exigence | Sujet | Action (doc 04) | Lot (doc 08) |
|---|---|---|---|
| AUTH-001 | Authentification OIDC institutionnelle | D-13 | **R2** (voir note) |
| AUTH-004 | Visibilité par portée et rôle | D-09 | R1-04 |
| AUTH-005 | Sécurité de session (cookies, CORS, expiration) | D-12 | R1-09 |
| PROJECT-001 | Cycle de vie des projets | D-07 | R1-02 |
| TARGET-003 | Cycle de vie des cibles | D-07 | R1-02 |
| OLIGO-007 | Dépréciation et archivage d'oligo, réutilisation interdite | D-07 | R1-02 |
| ASSAY-007 | Cycle de vie des assays | D-07 | R1-02 |
| ASSAY-004 | Règles de composition d'assay | D-08 | R1-03 |
| ATTACH-002 | Pièces jointes sûres | D-14 | R1-06 (option b) |
| SEARCH-003 | Recherche et suggestions respectant la visibilité | D-09 | R1-04 |
| BIO-003 | Jobs Primer3 persistants et idempotents | D-06 | R1-01 |
| BIO-006 | Reprise après interruption (worker, Redis) | D-06 | R1-01 |
| BIO-007 | Provenance des résultats calculés | D-06 | R1-01 |
| AUDIT-001 | Journal d'audit des mutations | D-10 | R1-05 |
| AUDIT-002 | Absence de fuite dans l'audit | D-10 | R1-05 |
| BACKUP-001 | Sauvegarde complète | D-11 | R1-08 |
| BACKUP-003 | Restauration testée sur instance vierge | D-11 | R1-08 |

**Note sur AUTH-001.** Si D1 = a (pilote sur Keycloak local), AUTH-001 n'est pas requis
pour le pilote. Il le reste pour la V1. Le pilote couvre donc **16 P0 sur 17**, et c'est
un choix explicite, non un oubli.

**Note sur ATTACH-002.** Avec l'option b, l'exigence est satisfaite par **désactivation**
de l'upload. Elle ne l'est pas par l'analyse antivirus, qui arrive en R2 (option a).

Hors matrice, l'intégration (D-01/D-02), la CI d'intégration et l'E2E isolée (D-04/D-05)
sont des **préalables techniques** à toutes les P0. Ils forment la release R0.

## 3. Classification scientifique du périmètre pilote

Principe : le pilote doit permettre à une équipe de **concevoir, enregistrer, qualifier,
retrouver et tracer** des oligos sur des données réelles. Tout ce qui sert ce cycle est
indispensable. Ce qui sert la logistique du laboratoire peut attendre.

| Élément | Classement | Justification | Condition de sortie pilote |
|---|---|---|---|
| Registre d'oligos | **Indispensable pilote** | C'est l'objet central ; identifiants publics stables et cycle de vie **[CODE]** | OLIGO-007 couvert en E2E (R1-02) |
| Séquences et cibles | **Indispensable pilote** | Pas d'oligo interprétable sans sa cible ; la provenance scientifique en dépend | TARGET-003 en E2E (R1-02) |
| Projets et workspaces | **Indispensable pilote** | C'est la frontière de visibilité ; sans eux, pas de collaboration sûre | AUTH-004 et SEARCH-003 verts (R1-04) |
| Expériences | **Indispensable pilote** | Elles relient l'oligo au résultat expérimental, livrées au plan 004 **[CODE]** ; sans elles le registre n'est qu'un catalogue | Audit couvert (R1-05) ; scénario de démonstration du doc 03 § 6 |
| Jobs et résultats Primer3 | **Indispensable pilote, sous condition** | C'est la seule analyse calculée du pilote ; elle est implémentée mais non commitée et ses gates ne sont pas clos | Gates D-06 (R1-01) ; à défaut, Primer3 est masqué dans l'UI et sort du pilote |
| Recherche d'oligos | **Indispensable pilote** | La réutilisation des oligos existants est la valeur première du registre | Tests négatifs de visibilité (R1-04) |
| Export simple | **Conditionné à arbitrage** (D9) | Sans sortie, les données sont captives et l'usage réel est freiné ; mais EXPORT-* n'est pas commencé | Recommandation : **inclure** un export CSV minimal des résultats visibles, audité (R1-07, 1–2 j). L'export contrôlé complet arrive en R2 |
| Import et réutilisation de l'existant | **Conditionné à arbitrage** (D7, D10) | Un pilote sur base vide a peu de valeur ; mais l'import en écriture est bloqué par la revue du propriétaire des données | Recommandation : saisie manuelle d'un **sous-ensemble curé** (20–50 oligos) pour le pilote (R1-10), puis import contrôlé en R2 après D7 |
| Inventaire et stock | **Reportable** (R2) | Logistique, non nécessaire pour qualifier ou retrouver un oligo ; INV-* n'est pas commencé ; 8–12 j | — |

Ce classement évite deux écueils :
- un périmètre trop minimal : la recherche, les expériences et l'export minimal sont gardés ;
- un report sans fin : chaque élément reporté a une release cible et un lot dans le doc 08.

## 4. Travail réel de livraison et estimations

Les efforts sont **[INFÉRÉS]**. Un jour-personne (j) correspond à 1 développeur, 1 jour,
tests compris.

| Release | Contenu | Effort | Calendrier, 1 développeur | Calendrier, 2 flux |
|---|---|---|---|---|
| **R0** Stabilisation et intégration | Sécuriser 005, intégrer `main`, CI d'intégration, E2E isolée, cohérence documentaire | 4–6 j | 1–1,5 semaine | 1 semaine (dépend des validations humaines G1–G4) |
| **R1** Pilote scientifique utilisable | Gates 005, cycle de vie, assays, visibilité, audit, pièces jointes b, export minimal, sauvegarde, session, données pilote, recette | 13–19 j de développement, plus 0,5–1 j de recette | 3–4 semaines | 2–3 semaines |
| **R0 + R1** | Pilote interne | **≈ 17–25 j** | **4–5 semaines** | **3–4 semaines** |
| **R2** Fonctionnalités métier | OIDC institutionnel, ClamAV, import en écriture, inventaire, commandes, export étendu, EXPTYPE | ≈ 26–41 j | 6–9 semaines | 4–6 semaines |
| **R3** Production et modules avancés | RLS, rate limiting et monitoring, durcissement prod ; puis BLAST/mapping, GeneOligoViewer, pull INRAE | 11–18 j, puis 20–35 j pour les modules | 3–4 semaines, puis 5–8 semaines | Selon les références fournies |

Hypothèses calendaires : la VM prod-like (D4) est disponible **au plus tard en semaine 2
de R1**, et les validations humaines G1–G4 sont rendues sous 48 h. Chaque semaine de
retard sur D4 décale R1 d'autant, car R1-08 et R1-09 sont sur le chemin critique.

Écart avec le doc 04, scénario A (15–21 j) : R0+R1 ajoute l'export minimal (1–2 j), les
données pilote (0,5 j), la recette (0,5–1 j) et le câblage CI d'intégration et d'E2E,
absent du doc 04. Il retire D-03, désormais résolu (0,5 j).

## 5. Corrections apportées aux docs 01–05

Les corrections sont ajoutées ici ; les documents d'origine ne sont pas modifiés.

| # | Doc | Énoncé initial | Correction | Preuve |
|---|---|---|---|---|
| C-01 | 04, 05 | D-03 : l'état de la CI est inconnu | **Résolu.** Tous les check-runs sont verts sur `e802d61`, `5773452`, `de51e6f` et `381b0f4`. La PR #1 (`codex/experiment-runs-validation` → `main`) est ouverte, avec `mergeable_state: clean` | **[EXÉCUTÉ]** API GitHub publique |
| C-02 | 05 | D6 : installer `gh` | **Obsolète.** L'API REST publique suffit en lecture. L'écriture (merge, PR) passe par l'interface web ou un outil authentifié | **[EXÉCUTÉ]** |
| C-03 | 05 | « environ 49 entrées » dans `git status` | **50 entrées** : 30 modifiées et 20 non suivies, dont `docs/audit/` et `.serena/` | **[EXÉCUTÉ]** |
| C-04 | 01, 04 | La CI couvre l'essentiel | **Lacune nouvelle** : `ci.yml` n'a **aucun job** de tests d'intégration PostgreSQL ni d'E2E Playwright | **[CODE]** `.github/workflows/ci.yml` |
| C-05 | 04, 05 | D-04/D-05 : base de test à créer | Le service Compose `postgres-test` et les cibles `make test-integration` et `make test-e2e` **existent déjà**. Il reste à les brancher en CI, à faire que `make test` cesse d'ignorer des tests, et à isoler l'E2E : `test-e2e` démarre le `caddy` principal et écrit donc probablement dans la base de dev **[INFÉRÉ]**. Effort D-04/D-05 révisé : 2,5–3,5 j | **[CODE]** `Makefile` |
| C-06 | 01 | STATUS : base de données en 0003 | La tête réelle est **0004** (`0004_scientific_jobs.py`, non suivie). `STATUS.md` est en retard | **[EXÉCUTÉ]** |
| C-07 | 01 | Nombre de specs E2E | `STATUS.md` en annonce 6, le dépôt en contient **7**, y compris `scientific-jobs.spec.ts`, non suivie | **[EXÉCUTÉ]** |
| C-08 | 04 | Scénario A : 10–14 jours ouvrés | Valable seulement avec au moins 2 personnes et une VM disponible immédiatement. Avec 1 développeur, compter **4–5 semaines** pour R0+R1 | **[INFÉRÉ]** |
| C-09 | 04 | V1 : 52–80 j | Les lignes du tableau totalisent 44–68 j. L'écart (≈ 8–12 j) correspond à D-16/D-18 et D-19, cités hors tableau. Le total reste plausible, mais il n'est **pas** la somme des lignes affichées | **[CODE]** doc 04 § 3 |
| C-10 | — | Checkpoint Basic Memory « 2026-09-03 — Plan 005 Activated » | **Périmé** : il indique que l'implémentation n'a pas commencé, alors qu'elle est quasi complète dans l'arbre de travail. À mettre à jour par MCP (R0-06) | **[EXÉCUTÉ]** recherche CLI en lecture |
| C-11 | 05 | Le stash peut contenir du travail | `stash@{0}` ne contient **que** le document du plan 005 (+679 lignes), remplacé par la version de l'arbre de travail. Un diff est requis avant toute suppression | **[EXÉCUTÉ]** `git stash show` |

## 6. Décisions nouvelles introduites par ce document

| # | Question | Recommandation |
|---|---|---|
| D9 | Export CSV minimal dans le pilote | **Oui** (R1-07) |
| D10 | Données du pilote : saisie manuelle d'un sous-ensemble curé, ou attente de l'import (D7) | **Saisie manuelle** ; import en R2 |
| D11 | Primer3 hors pilote si les gates D-06 échouent | **Oui** : masquer plutôt que retarder le pilote |
