# Qualification du MVP — dossier préparatoire pour revue

Date : 2026-11-01. Référence applicative : `main` au merge commit
`9852bdd704dc2658dd2941eeae8adb56f8ddc759` (UI-06, PR #15).
**Statut : stratégie générale approuvée, corrections documentaires PR #16 ;
qualification applicative et ouverture non autorisées ni attestées.**
Aucun nouveau développement fonctionnel ou d’hébergement.

## 1. Périmètre et méthode

Ce dossier prépare la qualification du pilote scientifique déjà prévu par les
lots R1-08 à R1-11. Il ne relance pas l'audit général de 2026-10-28 et ne crée pas
de nouvelle roadmap. Il distingue preuve acquise, limite connue et recette à
exécuter après revue. Le catalogue produit complet n'est pas le périmètre livré.

Sources relues : `ARCHITECTURE.md`, `PRODUCT_SPEC.md`, `SECURITY.md`,
`REQUIREMENTS_TRACEABILITY.md`, ADR-0003/0005/0006, Plan 006 terminé, rapports
R1-03/05/06/07 et UI-02–06, `compose.yml`, `compose.e2e.yml`, Makefile,
`.github/workflows/ci.yml`, scripts de sauvegarde et de restauration. Le plan
d'exploitation reste centralisé dans
[PILOT_HOSTING_PLAN.md](../deployment/PILOT_HOSTING_PLAN.md), notamment §8.

Aucun hôte distant, Mac mini, équipement réseau ou service de production n'a été
contacté/configuré dans cette étape. Aucun secret, fichier Excel source, donnée scientifique réelle
ou volume n'a été modifié. L'exécution future des protocoles exige une autorisation
distincte ; approuver ce document ne prouve pas leur succès.

### Contexte hôte et réseau corrigé sur déclaration utilisateur

Mac mini Apple Silicon, **16 Go RAM**, espace libre historiquement proche de
**66 Gio**, autres comptes utilisateurs dont les données doivent être préservées.
Cloudflare Zero Trust existe déjà : tunnel `mac-mini-maison` annoncé Healthy
lors de vérifications antérieures, route privée `192.168.1.31/32`, WARP sur
MacBook et SSH distant testé avec succès. Ce sont des informations fournies par
l’utilisateur, non revérifiées ici ; elles supersèdent l’hypothèse antérieure
d’un accès Tailscale à installer. Le succès SSH/réseau privé ne prouve pas le proxy
HTTPS ni OIDC applicatif. Tailscale reste une alternative, sans substitution.

Restent non vérifiés : DNS et chaîne TLS sur client/hôte/conteneurs, origine
canonique/callbacks/issuer, restrictions réseau/ports/LAN et révocation d’un accès
déjà établi, comptes OIDC et récupération des accès. Pas de présomption de double
pile Docker simultanée : mesurer mémoire/swap/disque au repos et en pic, marge et
croissance en préservant les autres utilisateurs. Le §2 du plan fixe ce contrôle ;
si marge insuffisante, déporter dev/build ou planifier la pile dev arrêtée, sans
modifier le pilote ni supprimer des données.

## 2. Intégration et preuves disponibles

| Élément | Preuve observée | Portée de la conclusion |
|---|---|---|
| UI-06 approuvé | Autorisation utilisateur visuelle et fonctionnelle ; head exact `535454ef6a12de0815dec8ef21546695625fb9a8` | Autorise uniquement cette fusion |
| PR #15 | 12 CheckRuns `COMPLETED/SUCCESS`, `CLEAN/MERGEABLE`, fusion par merge commit `9852bdd704dc2658dd2941eeae8adb56f8ddc759` | Intégration effective, sans squash/rebase/force push |
| Synchronisation | `main` fast-forward vers `origin/main` au même SHA | Sources suivies identiques après fusion ; images personnelles `assests/` non suivies conservées |
| Qualité après fusion | `make format lint typecheck test PYTHON_RUNNER=container`, exit 0 | 52 API + 14 worker + 8 web = 74 unitaires ; 198 PostgreSQL exclus de cette invocation |
| Validation UI-06 antérieure à fusion | 198 PostgreSQL avec aller-retour migration ; 29 Chromium ; build et qualité verts | Exécutés sur le head intégré, pas une recette du futur hôte |
| Comparaisons UI-06 | Mêmes lignes PostgreSQL, empreinte avant/après `8502b8e5b29708c3e7eec8139de7da29` | Valeurs conservées, résultat QC et paire, échec réel et historique ; voir rapport UI-06 |
| Reprise des jobs | [Preuves Plan 005](PLAN_005_RECOVERY_EVIDENCE.md) et tests de fencing | Qualification historique isolée ; pas de nouvelle campagne de panne sur le futur pilote |

CI de la PR : <https://github.com/El-Castor/OligoSpace/pull/15>.
Les 12 contrôles correspondent à six jobs exécutés sur push et pull_request,
pas à douze suites différentes. Le workflow CI actuel n'exécute pas Chromium :
ses 29 parcours sont une preuve locale isolée distincte. La CI du merge sur
`main` a également réussi : [run 41300133863](https://github.com/El-Castor/OligoSpace/actions/runs/41300133863),
commit `9852bdd704dc2658dd2941eeae8adb56f8ddc759`, six jobs réussis.

La protection de `main` renvoie « Branch not protected » et les rulesets sont
vides au contrôle de fusion. Aucun réglage n'a été changé ni contourné ; les
contrôles ont été vérifiés explicitement. L'adoption éventuelle de protections
formelles reste une décision séparée.

## 3. Matrice de qualification du périmètre pilote

| Domaine / exigences | Acquis documenté | Complément requis pour ouvrir le pilote |
|---|---|---|
| Registre et collaboration — OLIGO/TARGET/ASSAY, AUTH-003/004, SEARCH-003 | R1-04 portée/rôles/révocation, R1-03 intégrité des associations et versions, R1-02 cycles de vie ; tests PostgreSQL et navigateur | Rejouer avec trois identités OIDC et le jeu curé ; comparer données persistées, accès directs et erreurs, pas seulement les statuts HTTP |
| Recherche, suggestions, conflits | Deux fuites d'identifiants corrigées ; filtres et totaux testés | Vérifier après révocation qu'aucun identifiant privé ne réapparaît dans recherche, choix d'association, compteur ou export ; le conflit générique de doublon reste une limite connue |
| Audit — AUDIT-001/002 | Matrice mutation/audit, corrélation et faits sensibles, activité filtrée par visibilité actuelle | Vérifier les événements attendus et l'absence de payload sensible sur le jeu de recette ; aucun jugement « 100 % produit » pour les modules non livrés |
| Calcul — BIO-003/004/006/007 | QC Primer3 2.6.1, paire Forward/Reverse, snapshot/version/provenance, erreurs réelles ; Wallace distinct | Même outil et paramètres sur chaque architecture retenue, résultats bruts et tolérances justifiées, reprise sans second résultat ni perte d'audit |
| Pièces jointes — décision D2/R1-06 | Uploads désactivés par défaut et refusés en production même avec opt-in ; objets existants conservés en quarantaine | Confirmer notice UI, refus backend sans nouvelle écriture et préservation des anciens objets ; aucun téléchargement/publication ou scanner prétendument livré |
| Export — décision D9/R1-07 | CSV oligos visible/filtré/audité, UTF-8 BOM, échappement et protection formules, provenance stockée | Parser le fichier réel avec Unicode, valeurs nulles/zéro, contrôles de permissions et limites 1 000 lignes / 8 MiB ; pas d'export FASTA/XLSX/assays revendiqué |
| UI-02 à UI-06 | Navigation, surfaces, tables compactes, formulaires, workflows ; clavier et cinq largeurs | Recette humaine, lecteur d'écran et appareils tactiles ; contraste échantillonné ≠ certification WCAG |
| Identité — AUTH-001/005, R1-09 | Frontière OIDC, garde API production, session développement testée | Parcours HTTPS Keycloak réel : connexion, renouvellement, expiration, logout, compte désactivé, issuer/audience, CORS/cookies, MFA ; auth développement interdite |
| Récupérabilité — BACKUP-001–005, R1-08 | Scripts partiels et plan | Restauration complète isolée PostgreSQL + Keycloak + objets + configuration et secrets récupérables ; RPO/RTO mesurés puis acceptés |
| Déploiement — DEPLOY-001–003 | Images et Compose de développement, migrations/builds | Release immuable, définition pilote dédiée, isolation dev/pilote, TLS privé, droits de service et redémarrage qualifiés |
| Données / acceptation — R1-10/11 | Preview Excel en lecture seule ; séparation identité biologique/rôle/stock | Propriétaire valide données/provenance et mapping ; trois comptes et procès-verbal scientifique. Aucun import implicite |

Ne sont pas des conditions implicitement « terminées » : inventaire/commandes/QR,
GeneOligoViewer, persistance complète du mapping, ingestion de références gouvernées,
BLAST, scanner de pièces jointes ou export multi-format. Tout élargissement du
pilote à ces capacités demande une décision explicite et des preuves spécifiques.

## 4. Écarts documentaires et risques à faire examiner

**Réserves de la première revue indépendante traitées dans les documents :**
le plan §8.4 sépare désormais installation vierge (bases prêtes avant migration,
sans backup/release antérieurs supposés) et mise à jour (préchargement, stabilisation,
santé des bases, backup incluant Keycloak/objets, migration unique, recette/retour).
Son §9 raccorde les gates à SECURITY.md ; cette correction documentaire ne prouve
pas leur réalisation. Les sections 2/4/5 détaillent capacité réelle, Cloudflare
existant et stockage objet ; aucun composant n’a été changé.

### Stockage objet : contrôle public préalable, pas de changement de fournisseur

La référence utilisée reste `minio/minio:RELEASE.2025-09-07T16-13-09Z` dans
`compose.yml`. Le plan §5 consigne les sources publiques consultées : source Git
exacte disponible, API Docker Hub 404 et registres Docker Hub/Quay 401 lors de la
lecture du tag/manifest. **Disponibilité téléchargeable, digest et ARM64 non
confirmés**, sans conclure à une disparition de tout artefact. Le dépôt officiel
annonce ne plus être maintenu ; un tag historique n’est pas une politique de
correctifs. Ces observations ne concernent aucun cache local ou Mac mini.

Bloquant avant pilote : artefact reproductible et provenance/version/digest,
support ARM64, scans/maintenance acceptés, compatibilité du SDK S3 existant et
restauration des objets avec clés/contenu/content-type/checksums. Les options
source MinIO figée ou offre AIStor ont une existence publique vérifiée, **pas une
compatibilité opérationnelle validée**. Une construction interne implique sa
maintenance ; le Dockerfile historique hérite de `latest` et n’est pas une recette
reproductible prête. Toute adoption/migration demande décision, tests et retour
arrière ; aucun fournisseur, format disque, objet ou endpoint n’est changé ici.

### Gates de sécurité et traitement des reports

La matrice complète du plan §9 couvre modèle de menace, MFA/comptes, OIDC réel,
TLS/origine, secrets/rotation, privilèges, scans images/dépendances, RLS, incident,
restauration/récupération des accès et isolation/refus hors périmètre. Elle sépare
**prouvé** (preuve datée et portée exacte), **non vérifié**, **bloquant**, **report
demandé**, **report explicitement accepté**. Les tests fonctionnels existants ne
qualifient pas les contrôles opérationnels. À ce stade aucun report n’est demandé
ou accepté par ce dossier ; les gates non réalisés restent bloquants avant
ouverture. Pour RLS notamment, le backlog « plus tard » ne vaut pas dérogation à
SECURITY.md : réaliser ou obtenir une décision habilitée, compensée, datée et
réexaminable. L’approbation de la stratégie générale ne constitue pas ce report.

### Autres limites conservées

1. **Traçabilité vieillissante.** `REQUIREMENTS_TRACEABILITY.md` dit encore que
   l'export n'existe pas et marque EXPORT-001/003 « Planned ». R1-07 prouve un
   sous-ensemble CSV, sans prouver les autres formats. Les anciennes entrées de
   STATUS/BACKLOG sont historiques. Ce dossier ne réécrit pas rétroactivement les
   statuts ; leur réconciliation ciblée est proposée à la revue.
2. **Critères historiques conditionnels.** Les critères du 2026-10-28 sont une
   proposition comportant une option de report OIDC. Ne pas considérer cette
   option comme une autorisation actuelle d'auth développement à distance :
   `SECURITY.md` et le plan d'hébergement exigent OIDC en production.
3. **Compose non pilote.** `latest`, `build:`, seed de démo dépendant de l'API,
   Keycloak `start-dev`, credentials partagés et liaison de port non restreinte
   restent observables dans la base. Un simple changement de nom de projet ou
   `AUTH_MODE` ne produit pas un déploiement qualifié.
4. **Sauvegarde incomplète.** `create-backup.sh` ne couvre que PostgreSQL applicatif
   et `restore-test.sh` ne fait que restaurer une base jetable et compter deux
   tables. Ni chiffrement/transfert hors hôte complet, ni recette Keycloak/objets
   n'est prouvé. Le smoke de `BACKUP_RESTORE.md` qui parle de récupérer une pièce
   jointe doit être adapté à D2 : contrôler l'intégrité côté stockage privé sans
   inventer un téléchargement dans l'application.
5. **Dette asynchrone explicite.** Pas de renouvellement de lease, claim token non
   tourné par tentative et réutilisation du task ID Celery : risques Plan 005
   conservés. Avant utilisation réelle de Primer3, faire accepter les limites de
   durée/concurrence et le protocole de reprise, ou soumettre une correction
   séparée. Ce dossier ne désactive ni ne réécrit ces mécanismes.
6. **Preuves visuelles locales.** Les captures UI-06 sont dans
   `/private/tmp/oligospace-ui06/{before,after}`. Ce chemin temporaire n'est pas
   une archive durable : archiver les preuves approuvées dans un emplacement
   contrôlé avec index/checksums lors de la qualification de release.

## 5. Campagne proposée après revue, sans exécution ici

Chaque ligne produit un rapport lié au commit, aux digests d'images, à la version
de schéma, à la plateforme et à la date UTC. Aucun secret ni donnée réelle dans
les logs partagés. Un échec conserve son résultat ; il n'est pas remplacé par une
capture statique ou un succès HTTP.

| Étape existante | Action / environnement | Preuve de sortie et règle d'arrêt | Responsable à désigner |
|---|---|---|---|
| Socle technique | Sur clone isolé de la release : format/lint/typecheck/unitaires, PostgreSQL, build et tous les Chromium | Versions, sorties et échecs/skips expliqués ; arrêt si un contrôle requis échoue | Développement |
| R1-09 | Recette OIDC/TLS sur cible de qualification autorisée ; trois comptes, scopes distincts, révocation | Login/refresh/logout/désactivation et vérification des données accessibles ; refus hors accès privé, sans exposer de jeton | Exploitation + responsable identité |
| R1-08 | Restaurer un backup complet sur volumes vides d'une pile distincte, sans écraser la source | IDs/comptages/associations/audits/objets/provenance intègres ; RPO/RTO mesurés ; arrêt si perte inexpliquée | Exploitation |
| R1-10 | Jeu réduit curé par le propriétaire, provenance et permissions explicites | Approbation écrite des sources et du mapping ; si import souhaité, preview approuvée et autorisation distincte avant écriture | Propriétaire scientifique |
| R1-11 | Trois scientifiques/comptes : rechercher/réutiliser, créer target/oligo/assay, QC/paire, run/validation, cycle de vie, CSV et refus viewer | Persistences après reload, historique/audit et valeurs scientifiques vérifiés ; PV listant anomalies et exclusions | Responsable scientifique |
| Bascule pilote | Appliquer uniquement le plan revu et les opérations ensuite autorisées | Manifeste de release, recette et restauration acceptés, décision go/no-go nominative | Utilisateur + exploitation |

Les tests E2E doivent employer leur configuration explicite et un projet jetable
qui ne partage aucun volume ni secret avec dev/pilote. Le Makefile actuel appelle
`down --volumes` dans `test-e2e` : ne pas reprendre cette commande dans une procédure
où la suppression de volumes est interdite ; prévoir un teardown ciblé sans ce
flag. Ne pas lancer ces recettes par défaut contre `.env` ou une base utilisateur.

## 6. Décision à prendre après revue

**Constat : le périmètre fonctionnel intégré dispose de preuves automatisées et
d'une validation graphique utilisateur ; le pilote hébergé n'est pas qualifié.**
Ce constat n'est ni un refus scientifique ni une acceptation d'exploitation.

- [ ] Confirmer le périmètre pilote et ses exclusions, notamment D2/D9 (stratégie
  générale approuvée ; recette/exclusions opérationnelles encore à signer).
- [ ] Désigner responsables et jeu de recette pour R1-08 à R1-11.
- [ ] Approuver RPO/RTO, rétention, accès privé et identité ; aucune valeur proposée
  ne devient une exigence approuvée sans décision.
- [ ] Arbitrer la dette asynchrone et les limites scientifiques avant usage réel.
- [ ] Revoir le plan reproductible §8 du document d'hébergement.
- [ ] Valider les gates SECURITY.md (§9), la source/maintenance MinIO et la marge
  RAM/disque réelle ; aucun report de sécurité implicite.
- [ ] Autoriser séparément le prochain lot d'implémentation ou de qualification.

Aucune de ces cases n'est cochée par la fusion de UI-06. Prochaine action : revue
de ce dossier et du plan ; pas de nouvelle modification fonctionnelle entre-temps.
