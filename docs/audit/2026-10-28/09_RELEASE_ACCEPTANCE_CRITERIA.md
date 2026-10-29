# 09 — Critères d'acceptation des releases

- Date : 2026-10-28 · Statut : **proposition**.
- Une release est franchie seulement lorsque **tous** ses critères sont prouvés
  **[EXÉCUTÉ]**. Un document ou un test unitaire seul ne suffit pas.
- Chaque gate produit une preuve archivée : lien CI, rapport ou procès-verbal.

```
current_task: none defined
next_action: awaiting user prioritization
```

## Gate R0 → R1 : stabilisé et intégré

| # | Critère | Preuve attendue |
|---|---|---|
| R0-G1 | Le plan 005 est commité, poussé et fusionné dans `main` | `git merge-base --is-ancestor <commit 005> origin/main` |
| R0-G2 | La CI est verte sur `main`, jobs `integration` et `migration` compris | Lien du run GitHub Actions |
| R0-G3 | Les migrations 0001 → 0004 passent sur une base vierge, avec aller-retour | Job `migration` |
| R0-G4 | `make test` donne 0 test ignoré, ou les tests ignorés sont explicitement délégués à `test-integration` | Sortie de commande |
| R0-G5 | L'E2E est isolée et verte (7 specs) ; la base de dev est inchangée | Rapport archivé, comptes de lignes avant et après |
| R0-G6 | STATUS, BACKLOG et CHANGELOG sont cohérents avec l'exécution réelle | Relecture croisée avec le doc 06, § 5 |
| R0-G7 | `git status` est propre ; aucun secret dans l'historique poussé | Sortie de commande et scan |

## Gate R1 → R2 : pilote scientifique utilisable

Ce gate reprend les 10 critères MVP du doc 03, rendus mesurables.

| # | Critère MVP (doc 03) | Mesure | Lots |
|---|---|---|---|
| 1 | Intégration | Gate R0 franchi | R0 |
| 2 | Qualité statique | `make lint` et `make typecheck` verts en CI | R0-03 |
| 3 | E2E isolée | Toutes les specs vertes sur la pile isolée, y compris le cycle de vie et Primer3 | R0-04, R1-01, R1-02 |
| 4 | Jobs scientifiques | Interruption et reprise sans doublon ; provenance affichée ; ou bien Primer3 masqué (D11) | R1-01 |
| 5 | Visibilité | 0 fuite sur 4 portées × rôles × {liste, détail, recherche, suggestions, export} | R1-04, R1-07 |
| 6 | Cycle de vie | Transitions auditées ; réutilisation d'un identifiant refusée | R1-02, R1-03 |
| 7 | Audit | 100 % des mutations MVP auditées ; 0 champ sensible | R1-05 |
| 8 | Récupérabilité | Restauration sur instance vierge réussie ; RPO et RTO mesurés et acceptés par l'utilisateur | R1-08 |
| 9 | Sécurité de session | Attributs des cookies, CORS et expiration vérifiés sur l'hôte TLS | R1-09 |
| 10 | Validation utilisateur | Scénario du doc 03, § 6 exécuté par un scientifique, avec 3 comptes ; procès-verbal signé | R1-11 |

Exigences complémentaires :
- 16 des 17 P0 sont fermées. AUTH-001 est reporté en R2 si D1 = a.
- L'upload est désactivé et vérifié (ATTACH-002, option b).
- Les données pilote ont été saisies par le propriétaire des données, sans donnée inventée.

## Gate R2 → R3 : fonctionnalités métier

| # | Critère | Preuve |
|---|---|---|
| R2-G1 | AUTH-001 : connexion OIDC institutionnelle sur l'IdP réel | Recette avec un compte institutionnel |
| R2-G2 | ATTACH-002, option a : un fichier EICAR est mis en quarantaine et refusé | Test d'intégration |
| R2-G3 | Import : le sous-ensemble approuvé par le propriétaire est importé de façon idempotente ; le rapport d'écarts est validé | Rapport d'import signé (D7) |
| R2-G4 | Inventaire et commandes : le flux demande → réception → lot → mouvement est couvert en E2E | Specs vertes |
| R2-G5 | Export contrôlé : les formats documentés respectent la visibilité et sont audités | Tests |
| R2-G6 | Aucune régression sur le gate R1 | CI et E2E vertes |
| R2-G7 | Le pilote a fonctionné au moins 4 semaines sans perte de données | Journal d'exploitation [critère proposé] |

## Gate R3 : production consolidée

| # | Critère | Preuve |
|---|---|---|
| R3-G1 | RLS active ; un test de contournement API direct en base est refusé | Tests d'intégration |
| R3-G2 | Rate limiting et monitoring actifs ; une alerte de test est reçue | Capture de l'alerte |
| R3-G3 | Secrets externalisés ; aucun secret par défaut | Revue de configuration |
| R3-G4 | Sauvegardes automatiques ; restauration testée chaque mois | Journal de restauration |
| R3-G5 | Revue de sécurité indépendante sans constat critique ouvert | Rapport |
| R3-G6 | Modules avancés : chaque résultat de mapping ou BLAST porte une référence gouvernée versionnée, ses paramètres et son horodatage ; aucun résultat fabriqué | Tests et revue scientifique |
