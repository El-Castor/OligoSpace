# 07 — Stratégie d'intégration Git

- Date : 2026-10-28 · Statut : **plan proposé**. Aucune opération Git d'écriture n'a été
  effectuée.
- Toute étape marquée **G*n*** exige une autorisation explicite de l'utilisateur.
- Légende épistémique : voir doc 01.

```
current_task: none defined
next_action: awaiting user prioritization
```

## 1. État constaté [EXÉCUTÉ]

```
origin/main ── e802d61  plan 001 (MVP foundation)
                  │
               5773452  plan 002 (core registry)
                  │
               de51e6f  plan 003 (identity, workspaces, admin)
                  │
               381b0f4  plan 004 (experiment evidence)  ← codex/experiment-runs-validation (poussée, PR #1)
                  │                                     ← codex/scientific-jobs-primer3 (HEAD, sans upstream)
                  ⋮
            [arbre de travail] plan 005 non commité : 30 fichiers modifiés et 20 non suivis
```

L'historique est **linéaire** : aucune divergence et aucun conflit possible entre les
plans 002 à 005. Les vérifications suivantes ont été faites par l'API GitHub publique :

- **PR #1** « feat: integrate Plans 002–004… » est ouverte, avec `mergeable_state: clean`.
- La CI est verte sur les quatre commits.
- `stash@{0}` contient uniquement une version antérieure du document du plan 005.

**Risque principal : le plan 005 n'existe que dans l'arbre de travail local.** Une erreur
de manipulation ou une perte du poste le ferait disparaître. C'est la raison pour
laquelle R0-01 passe avant tout le reste.

## 2. Séquence d'intégration

| Étape | Action | Commande ou moyen | Porte | Vérification |
|---|---|---|---|---|
| 1 | Sécuriser 005 localement : ignorer `.serena/`, relire le diff, scanner les secrets, lancer `make format lint typecheck test compose-config` | Lot R0-01 (doc 08) | — (aucune écriture Git) | Rapport R0-01 |
| 2 | Créer 3 commits sur `codex/scientific-jobs-primer3` : `chore: ignore local agent artifacts`, `feat: add persistent scientific jobs with Primer3 analysis`, `docs: add takeover audit` (D8) | `git add` ciblé fichier par fichier, sans `git add -A` | **G1** | `git status --short` vide ; `git show --stat` sur chaque commit ; `.env` absent |
| 3 | Pousser la branche 005 | `git push -u origin codex/scientific-jobs-primer3` | **G2** | `git rev-parse @{u}` répond ; CI déclenchée |
| 4 | Fusionner la PR #1 (002–004) dans `main` | Interface web GitHub, **« Create a merge commit »** ou fast-forward. **Jamais « Squash » ni « Rebase and merge »** | **G3** | `main` contient `381b0f4` ; CI verte sur `main` |
| 5 | Ouvrir la PR #2 `codex/scientific-jobs-primer3` → `main` | Interface web GitHub | — (lecture de son contenu par l'utilisateur) | Le diff ne montre **que** les 3 commits de l'étape 2 |
| 6 | Fusionner la PR #2 | Interface web, merge commit | **G4**, CI verte, R0-03 conseillé avant | `git merge-base --is-ancestor <commit 005> origin/main` |
| 7 | Supprimer `stash@{0}` | Après `git diff stash@{0}^ stash@{0} -- docs/exec-plans/` comparé au fichier courant | **G5** | `git stash list` vide |
| 8 | Supprimer les branches distantes fusionnées (facultatif) | Interface web | **G6** | — |

**Pourquoi jamais de squash à l'étape 4.** Un squash de la PR #1 créerait sur `main` un
commit au contenu identique à 002–004, mais au SHA différent. La branche 005 contient
déjà `5773452`, `de51e6f` et `381b0f4`. La PR #2 afficherait alors à nouveau 002–004 et
risquerait des conflits fictifs. Un merge commit ou un fast-forward conserve les SHA.

**Variante D3 = b (fast-forward direct).** Les étapes 4 à 6 se résument alors à :

```
git push origin codex/scientific-jobs-primer3:main
```

Cette commande pousse 002–005 en une fois. Elle est plus rapide, mais elle supprime la
revue et la CI par étape. Elle n'est **pas recommandée**.

## 3. Ordre et parallélisme

- Les étapes 1 → 2 → 3 sont strictement séquentielles.
- L'étape 4 peut avoir lieu **avant** l'étape 2 : la PR #1 est indépendante et déjà verte.
  C'est le seul gain de parallélisme possible.
- Le lot R0-03 (CI d'intégration) se développe sur une branche issue de 005 après
  l'étape 3. Ses commits peuvent rejoindre la PR #2 avant l'étape 6.

## 4. Retour arrière

| Situation | Remède | Destructif ? |
|---|---|---|
| Mauvais fichier dans un commit local (avant G2) | `git reset --soft HEAD~1`, puis recommencer | Non : l'arbre de travail est conservé. Demande malgré tout une autorisation |
| Secret poussé (après G2) | Révoquer le secret **d'abord**, puis purger l'historique | Oui : action d'urgence avec accord explicite |
| CI rouge sur `main` après G3 ou G4 | `git revert -m 1 <merge>` via une PR | Non |
| Migration 0004 défaillante | `alembic downgrade 0003`, déjà couvert par le job CI `migration` (aller-retour) **[CODE]** | Non sur une base vierge. **Interdit** sur une base contenant des données sans sauvegarde préalable |

## 5. Continuité documentaire : Basic Memory et Serena

| Outil | État | Cause | Contournement | Correctif proposé |
|---|---|---|---|---|
| Basic Memory MCP | **En échec** : `CONNECT_TIMEOUT` à 30 s, constaté de nouveau le 2026-10-28 **[EXÉCUTÉ]** | `uvx basic-memory` met environ 26 s à démarrer ; le binaire direct `~/.local/bin/basic-memory` v0.24.1 démarre en environ 2 s **[EXÉCUTÉ]** | La recherche CLI en lecture seule fonctionne. Aucune écriture hors MCP, conformément aux règles | Remplacer la commande du serveur MCP dans `~/.claude.json` par `/Users/clpichot/.local/bin/basic-memory mcp --project research-memory`, puis redémarrer. **Exige votre accord (D12)** |
| Serena | Configuré et fonctionnel, **aucune mémoire** **[EXÉCUTÉ]** | Projet jamais onboardé | Les outils symboliques sont utilisables | Ignorer `.serena/` (R0-01). L'onboarding est facultatif |
| Checkpoint Basic Memory | Périmé (correction C-10, doc 06) | — | Ce dossier `docs/audit/` fait foi | Mettre à jour via MCP après le correctif, dans le lot R0-06 |

Ces lacunes **ne bloquent pas** la reprise. Les dépôts restent la source de vérité.
