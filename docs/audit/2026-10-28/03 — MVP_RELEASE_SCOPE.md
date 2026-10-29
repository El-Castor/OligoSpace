# 03 — Périmètre de la release MVP

- Date : 2026-10-28 · Statut : **proposition de l'audit, soumise à validation utilisateur**.
- Sources : `docs/PRODUCT_SPEC.md` (« MVP boundary »), `02 — INITIAL_PLAN_GAP_ANALYSIS.md`
  (matrice, colonne Priorité), plans 001–005.
- Légende épistémique : voir `01 — PROJECT_STATE_AUDIT.md`.

## 1. Définition proposée

Le MVP est **un registre scientifique collaboratif sûr et récupérable**, utilisable par une
équipe pilote. Il doit permettre de :

- enregistrer et retrouver oligos, cibles, assays, runs et validations avec leur provenance ;
- calculer un QC Primer3 traçable ;
- garantir que les droits d'accès sont appliqués côté serveur ;
- garantir que les données survivent à un incident.

Ce périmètre reprend la « MVP boundary » de la spec. Les éléments que la spec demande de « ne
pas présenter comme complet » (runs, validations, pièces jointes, jobs scientifiques) y entrent
avec des limites explicites (§ 4).

## 2. Inclus dans le MVP

### 2.1 Socle déjà vérifié (non-régression seulement)
Les 31 exigences « Vérifié » des plans 001–004 : identité/RBAC, registre, oligos (normalisation,
QC, anti-doublons), assays (rôles, versions), espaces de travail, admin, preuves d'expérience.
**Reste à faire** : rejouer la suite E2E complète sur l'état fusionné **[DÉCLARÉ → à EXÉCUTER]**.

### 2.2 À terminer (P0, 17 exigences)

| Bloc | IDs | Reste à faire | Dépendance |
|---|---|---|---|
| Jobs Primer3 sécurisés | BIO-003, BIO-006, BIO-007 | Commit ; E2E Chromium finale ; test de reprise worker/Redis ; E2E des états d'erreur ; tests d'intégration sur base de test dédiée | Aucune (autonome) |
| Cycle de vie des objets | OLIGO-007, TARGET-003, ASSAY-007, PROJECT-001 | E2E déprécier/archiver et réutilisation | Fusion 002–004 |
| Intégrité des règles assay | ASSAY-004 | Matrice de tests négatifs complète | — |
| Visibilité et session | AUTH-004, AUTH-005 | Matrice 4 portées sur recherche/export ; revue cookies/refresh/CORS | Hôte réel pour AUTH-005 complet |
| Recherche sûre | SEARCH-003 | Aucune fuite de visibilité via suggestions/export | AUTH-004 |
| Audit | AUDIT-001, AUDIT-002 | Couvrir import/export ; revue des sérialiseurs restants | — |
| Récupérabilité | BACKUP-001, BACKUP-003 | Sauvegarde pgBackRest acceptée ; restauration prod-like enregistrée | Hôte cible (prod-like) |
| Identité institutionnelle | AUTH-001 | Flux OIDC institutionnel qualifié en navigateur | **Décision D1** + entrées institutionnelles |
| Pièces jointes sûres | ATTACH-002 | Scan antimalware **ou** désactivation de l'upload | **Décision D2** |

## 3. Exclu du MVP (V1 ou V2)

| Domaine | IDs | Raison |
|---|---|---|
| Inventaire physique, lots, emplacements, QR | INV-* | Non commencé ; spec : phase ultérieure |
| Commandes | ORDER-* | Non commencé ; dépend de l'inventaire |
| Export contrôlé | EXPORT-* | Non commencé ; dépend d'AUDIT-001 et d'AUTH-004 |
| Import Excel en écriture | IMPORT-003/004 | Bloqué par la revue du propriétaire des données |
| Mapping génomique, BLAST, GeneOligoViewer | GENOME-002/003, BIO-002/005, VIEW-* | Références et bases gouvernées non fournies |
| Exploitation avancée | BACKUP-002/004/005, monitoring | Entrées institutionnelles absentes |

Ces domaines ne doivent pas apparaître dans l'interface du MVP comme fonctionnels. Les
`PlannedPage` existants doivent rester clairement marqués « prévu ».

## 4. Limites déclarées du MVP

- Les jobs scientifiques se limitent à Primer3 : QC d'un oligo et compatibilité d'une paire.
  Aucun résultat de spécificité ni de mapping n'est produit ni affiché.
- Runs et validations enregistrent des preuves. **Ils ne remplacent ni un ELN ni un LIMS.**
- Sans décision D2 favorable au scan, l'upload de pièces jointes est désactivé.
- Sans décision D1 favorable à l'OIDC institutionnel, le MVP reste un **pilote interne sur
  Keycloak local** et n'est pas une mise en production.

## 5. Critères d'acceptation de la release MVP

Chaque critère doit être prouvé **par exécution archivée** (rapport ou journal versionné sous
`docs/audit/` ou artefact CI), et non par simple déclaration.

1. **Intégration** : `main` contient les plans 001–005 ; la CI est verte sur `main`.
2. **Qualité statique** : `make lint`, `make typecheck` et `make test` passent, **y compris les
   tests d'intégration** avec `OLIGOSPACE_TEST_DATABASE_URL` sur une base de test dédiée
   (0 test ignoré).
3. **E2E** : la suite Playwright Chromium via Caddy passe sur un environnement isolé de la base
   de dev ; le rapport HTML est archivé.
4. **Jobs** :
   - un job Primer3 interrompu (worker ou Redis arrêté) est repris ou marqué en échec
     explicite, sans doublon (idempotence) ;
   - chaque résultat affiche algorithme, version, paramètres et horodatage.
5. **Visibilité** :
   - pour les 4 portées de visibilité × rôles, aucune lecture non autorisée n'est possible via
     l'API, la recherche ou les suggestions ;
   - des tests négatifs le démontrent.
6. **Cycle de vie** : déprécier/archiver un oligo, une cible, un assay ou un projet est audité,
   réversible selon les règles, et l'objet reste traçable.
7. **Audit** : toute mutation du périmètre MVP produit une entrée d'audit sans fuite de champ
   sensible.
8. **Récupérabilité** : une sauvegarde complète puis une restauration sur une instance vierge
   sont exécutées et chronométrées. La procédure est consignée dans un runbook, et le RPO/RTO
   mesuré est noté.
9. **Sécurité session** : cookies `Secure`/`HttpOnly`/`SameSite`, CORS restreint et expiration
   de session sont vérifiés sur l'hôte cible.
10. **Validation utilisateur** : le scénario de démonstration (§ 6) est exécuté par un
    utilisateur scientifique pilote. **Ce critère n'est remplaçable par aucun test automatisé.**

## 6. Scénario de démonstration

Les acteurs sont 3 comptes : *contributeur*, *lecteur* (autre équipe) et *admin*.

1. Le contributeur se connecte, puis crée un projet et une cible.
2. Il saisit un oligo dont la séquence est mal formatée. La normalisation s'applique et un
   avertissement de doublon apparaît sur une séquence existante.
3. Il lance un **QC Primer3**. Le job passe de « en file » à « réussi », et le résultat affiche
   sa provenance (Primer3 2.6.1, paramètres, horodatage).
4. Il crée un assay (amorce sens/antisens, sonde) et lance la compatibilité de la paire.
5. Il enregistre un run et une validation avec preuve. La pièce jointe dépend de la décision D2.
6. La recherche retrouve l'oligo. Le *lecteur* d'une autre équipe ne voit pas l'objet privé,
   ni en liste, ni en recherche, ni en suggestion.
7. Le contributeur archive l'oligo, puis l'admin consulte la piste d'audit complète.
8. L'admin démontre une restauration de sauvegarde et retrouve les objets créés.

```
current_task: none defined
next_action: awaiting user prioritization
```
