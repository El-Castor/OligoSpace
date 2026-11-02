# DEPLOY-02 — Synthèse décisionnelle (2026-11-02)

**Conclusion : fusion encore bloquée.** PR18 unique, brouillon ; aucune nouvelle
remédiation engagée. Revue du head `0b12667`, preuves détaillées dans le
[rapport consolidé](DEPLOY_02_TARGETED_REVIEW.md).

**Debian — 44 occurrences HIGH = neuf CVE distinctes.** Les neuf pages du tracker
ont été revérifiées : aucun correctif publié pour **trixie utilisée** ; huit ont
un correctif unstable, SQLite reste ouvert aussi dans sid. Pas de greffe sid.
17 paquets présents sur reconstructions1cca325 ; aucune innocuité ni identité historique prouvée.

| CVE (préfixe CVE-) | Précondition et appréciation dans notre configuration |
|---|---|
| 2026-76642 | Hooks de montage privilégiés : scénario local plausible si montage autorisé ; chemin applicatif non démontré. |
| 2026-78408 | `nsenter --join-cgroup` privilégié sur cible hostile : risque opérateur plausible ; usage non observé dans le code examiné. |
| 2026-78409 | Montage fstab/subdir et noyau compatibles : preuves insuffisantes, contradiction de version amont/tracker non résolue. |
| 2026-78410 | Bind mount privilégié, chemin source modifiable : scénario local conditionnel ; configuration exploitable non démontrée. |
| 2026-54369 | Appel ACL privilégié sur chemin contrôlé : plausible si ces deux conditions existent ; graphe d'appels incomplet. |
| 2026-119373 | SQLite FTS5, données et requête hostiles : pas de parcours identifié ; PostgreSQL utilisé, Python sondé lie SQLite Conda, copie Debian présente. Couverture insuffisante. |
| 2026-16742 | Utilisateur géré par systemd-homed : seules bibliothèques système observées ; service vulnérable non établi, exclusion non prouvée. |
| 2025-69720 | Entrée hostile traitée par `infocmp` : paquet ncurses-bin présent ; invocation et présence du fichier spécifique non établies. |
| 2026-9538 | Archive::Tar traitant une archive hostile : uploads désactivés, aucun appel identifié ; présence du module et usages indirects non établis. |

Sources par CVE et versions : [table Debian détaillée](DEPLOY_02_TARGETED_REVIEW.md#1-neuf-vulnérabilités-distinctes-et-non44).
Ces appréciations sont conditionnelles, aucun avis n'est déclaré inoffensif.

**Stockage : recommander SeaweedFS4.52 au digest qualifié**, conditionnellement.
Apache2.0 ; activité amont observée, notices/dépendances et veille à valider.
Go-jose corrigé ; six restaurations passent. Restent trois UNKNOWN :
[x/net Parse](https://pkg.go.dev/vuln/GO-2026-6860)/[Render](https://pkg.go.dev/vuln/GO-2026-6866) (correctif0.62.0),
[OpenPGP](https://pkg.go.dev/vuln/GO-2026-5932) non maintenu/sans correctif.
Atteignabilité, licences et provenance non acceptées. Garage2.5.0 reste alternative
AGPLv3 : obligations de redistribution/modification, réserve mono-serveur,
HIGH source rustls-webpki, inventaire runtime/provenance insuffisants malgré
binaires conformes à la distribution. Aucune adoption ni modification du Compose.

**Fusion versus release.** Fonctions, PostgreSQL, Chromium, Primer3 et contrats S3
validés. GitHub revérifié le2026-11-02 au head0b12667 : jobs terminés, scans API/worker/fournisseurs/source et
historiques rouges ; `MERGEABLE` mais `UNSTABLE`. API GitHub : main non protégée,
aucun required check configuré/ruleset retourné. Aucun contrôle modifié/contourné.
Les exigences actuelles de conservation des findings bloquants restent applicables :
**fusion conditionnée à résolution ou décision explicite approuvée du périmètre
d'acceptation pour intégration du code**, puis revue des statuts au SHA final.
Une éventuelle acceptation de fusion ne qualifierait aucune image pour release.
OIDC/TLS/MFA/RLS, moindre privilège worker, restauration, capacité réelle et choix
fournisseur sont des gates de **release/déploiement** de [SECURITY](../SECURITY.md),
pas des défauts fonctionnels démontrés imposant une refonte de DEPLOY-02.

**Acceptation proposée, non accordée.** Fiche par CVE/groupe homogène et digest :
preuves, scénario/impact, incertitudes, non-correction supportée, périmètre
« fusion seulement » ou « release », compensations et risque résiduel.
Responsable technique à nommer ; approbation propriétaire et RSSI compétent pour
usage institutionnel. Réexamen proposé **2026-11-16**, anticipé sur correctif,
exploitation connue ou changement d'exposition. Compensations à vérifier :
non-root/no-new-privileges, capacités minimales, aucun montage privilégié/socket
Docker, stockage privé, limites mémoire/temps, uploads désactivés, surveillance
et restauration. Les sondes CI ne prouvent pas ces protections du pilote.
Aucun ignore scanner ni dérogation ; décision écrite requise avant fusion,
autorisation distincte avant release. **Arrêt pour décision utilisateur.**
