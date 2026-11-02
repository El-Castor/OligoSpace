# DEPLOY-02 — Remédiation de sécurité OCI

Latest targeted follow-up: [distinct CVEs, physical package presence, supplier qualification and proposed PR split](DEPLOY_02_TARGETED_REVIEW.md). Historical evidence below retains its original source SHA.

## Périmètre et état de livraison

PR18 reste **DRAFT, non fusionnée**, sans publication, déploiement, accès Mac mini,
modification Cloudflare, migration réelle ni substitution du Compose pilote.
SeaweedFS reste prioritaire, Garage alternatif, MinIO historique de compatibilité,
AIStor exclu. Les gates restent stricts : tout finding résiduel ou contrôle non
vérifié bloque ; aucune ignore-list, suppression de résultat ou dérogation ajoutée.

Code final requalifié : `98a3250339d2e17b59caff28061ac286f8549708`.
[Qualification native41458888349](https://github.com/El-Castor/OligoSpace/actions/runs/41458888349),
[CI applicative41458888116](https://github.com/El-Castor/OligoSpace/actions/runs/41458888116),
[foundation41458887782](https://github.com/El-Castor/OligoSpace/actions/runs/41458887782),
[scans candidats41458887799](https://github.com/El-Castor/OligoSpace/actions/runs/41458887799),
[triage historique et Chromium41458887909](https://github.com/El-Castor/OligoSpace/actions/runs/41458887909).
Les CI applicative et foundation sont vertes. La qualification native reste rouge
sur quatre scans applicatifs résiduels ; les deux jobs web sont verts. Les quatre
scans fournisseurs restent bloquants. Les deux jobs de reconstruction historique
restent rouges, puisqu'ils scannent volontairement les anciennes images vulnérables :
leur classification expurgée ne transforme pas leurs findings en succès.

[Preuves intégrales assainies conservées](../../infra/deployment/evidence/security-98a3250-remediation.json)
au-delà de la rétention Actions : scans, huit rapports S3, douze projections
SBOM/provenance, digests, comparaison scientifique et triage. Aucune image ni
sortie brute n'est publiée. Les commit(s) documentaires ultérieurs sont distincts
du code testé ; leur CI est suivie dans la description de PR18.

## Causes et corrections minimales regroupées

| Groupe | Cause / correction | Risque et vérification |
|---|---|---|
| G1 | Base micromamba Debian13 : upgrade des paquets de sécurité de la distribution ; digest de base conservé | Moyen : libs/utilitaires ; builds natifs, worker, PostgreSQL et vrais résultats Primer3 ; résiduels Debian conservés |
| G2 | PyJWT2.10.1 →2.14.0, majeur2 conservé | Moyen : validation de tokens ; tests permissions/auth/session ; aucune politique OIDC modifiée |
| G3 | python-multipart0.0.20 →0.0.30 | Faible à moyen : parsing HTTP ; uploads restent désactivés ; tests backend |
| G4 | FastAPI0.115.8 →0.135.2 et Starlette0.45.3 →1.3.1, contrainte amont vérifiée | Moyen : passage majeur Starlette explicitement contrôlé, aucune route/schema/action modifiée ; tests API/PostgreSQL/Chromium ; pas de forçage d'un graphe incompatible |
| G5 | Base Node22 Alpine3.23 conservée ; upgrade des correctifs Alpine | Moyen : crypto/TLS ; build/start/navigation et contrats existants |
| G6 | Next/eslint-config-next16.3.3 →16.4.1 ; sharp0.35.5 par override compatible | Moyen : serveur Next, auth/server actions ; build/typage/tests/Chromium ; React inchangé |
| G7 | npm/corepack et leurs dépendances retirés de l'étage web final ; conservés dans tooling/build | Faible : runtime standalone démarre avec node ; aucune fonction scientifique retirée |

Python3.12.8, pip25.0, Biopython1.85, Primer3 **2.6.1**, BLAST **2.17.0**,
compilation/paramètres et règles scientifiques restent inchangés. Les findings
Conda/pip ne sont pas confondus avec ceux de dpkg : changer l'environnement Conda
ne corrigerait pas les paquets Debian hérités. Aucun paquet système n'est supprimé
à l'aveugle pour faire disparaître un avis. Les transactions apt/apk sont datées
par les builds ; la reproductibilité porte sur les digests OCI produits et les
inventaires conservés, pas sur l'immuabilité future des dépôts système.

Sources primaires : [PyJWT2.14](https://pypi.org/project/PyJWT/2.14.0/),
[métadonnées FastAPI0.135.2](https://pypi.org/pypi/fastapi/0.135.2/json),
[Starlette](https://starlette.dev/release-notes/),
[multipart](https://pypi.org/project/python-multipart/),
[Next versions](https://www.npmjs.com/package/next?activeTab=versions),
[correctifs OpenSSL Debian](https://tracker.debian.org/news/1805073/accepted-openssl-357-1deb13u3-source-into-stable-security/),
[OpenSSL Alpine3.23](https://pkgs.alpinelinux.org/packages?branch=v3.23&name=libcrypto3).
Le contrôleur des projections SPDX acceptait160caractères au maximum par
champ : le worker contient une expression `licenseDeclared` de749caractères.
La validation accepte désormais les expressions de licence SPDX bornées à4096
caractères, tout en refusant les URLs et caractères non autorisés. Les champs
restent conservés et liés au digest d’attestation ; aucune licence n’est ignorée.

Les tests observés valident le périmètre testé, pas une exploitabilité universelle.

## Résultats applicatifs et vulnérabilités résiduelles

Comptes d'occurrences paquet/avis par architecture ; ARM64/AMD64 concordent dans
le run final98a3250. Ce ne sont pas des CVE uniques. Tous les niveaux restent
bloquants, pas uniquement HIGH/CRITICAL.

| Image | Critical avant → après | High avant → après | Medium après | Low après | Unknown après | Alertes JWT après |
|---|---:|---:|---:|---:|---:|---:|
| API | 6 →0 | 121 →44 | 79 | 62 | 8 | 0 |
| Web | 4 →0 | 18 →0 | 0 | 0 | 0 | 0 |
| Worker | 5 →0 | 110 →44 | 78 | 61 | 8 | 0 |

Les44 HIGH résiduels API/worker concernent principalement util-linux (quatre avis
sur neuf paquets binaires), ACL, SQLite, systemd/udev, ncurses et Perl. Le rapport
ne donne pas de version corrigée pour ces avis dans la distribution retenue.
[Debian suit encore CVE-2026-76642](https://security-tracker.debian.org/tracker/CVE-2026-76642).
Cela ne prouve pas qu'aucun correctif n'existe dans un autre canal. Un changement
majeur de distribution, une reconstruction interne ou l'acceptation du risque
exigent une décision séparée ; aucun report n'est supposé autorisé.

## Triage des alertes secrets

Deux alertes logiques (API et worker), reproduites sur les deux architectures :
règle `jwt-token`, catégorie de cache de construction pip sous root. Aucun
credential réel, identifiant public ou faux positif n'est déduit du seul compte.
Le cache pip n’est pas nécessaire au runtime : création désactivée et retrait
dans le même étage de construction, sans désinstaller de dépendance applicative.
Les alertes historiques restent conservées ; leur disparition dans les images
finales ne prouve pas qu’elles étaient des faux positifs. Le JSON de Trivy0.76.1 est déjà censuré par
[le scanner amont](https://github.com/aquasecurity/trivy/blob/v0.76.1/pkg/fanal/secret/scanner.go).
Le contrôleur réexamine donc uniquement en RAM le fichier à l'offset exact dans
les layers OCI dont les digests sont vérifiés. La traversée est bornée à100000 entrées,4GiB cumulés et16MiB par fichier.
Whiteouts, liens, ambiguïtés et bornes dépassées laissent le triage non résolu. Aucun chemin arbitraire, offset,
Match, Code, valeur ou claims ne sont exportés. Le rapport expose uniquement des
catégories, booléens et une conclusion expurgée. Les exemples publics ne sont
reconnus qu'après vérification de claims de démonstration et signature de démo ;
les claims seuls ou une date d'expiration ne justifient aucune acceptation.

Résultat au contrôleur98a3250 : les deux reconstructions du head historique2750c78
sont classées **chaînes de documentation publiques**, exemple PyJWT, après
lecture dans le cache pip, décodage des claims de démonstration et vérification
HMAC de la signature de démo. Statut `resolved_in_memory`, sans valeur conservée.
La source est la [documentation PyJWT](https://pyjwt.readthedocs.io/en/stable/usage.html).
Il ne s'agit ni d'un identifiant public isolé ni d'un credential OligoSpace
identifié. La règle Trivy reconnaît correctement une forme JWT ; le triage établit
ici un exemple de documentation, sans accepter les findings des anciennes images.
Le retrait du cache produit **zéro alerte secrète sur les six images finales**.
La reconstruction historique n'est pas une preuve de reproductibilité bit à bit
des anciennes images : code et bases sont fixés, mais la résolution transitive
et les horodatages de build peuvent différer. Les anciens rapports restent intacts.

Si un vrai secret est confirmé ou reste plausible, une rotation et une enquête
sur la distribution des images pourraient être nécessaires ; aucune rotation ni
action sur un système réel n'est autorisée ici. Même un faux positif justifié
reste visible et bloquant tant qu'une politique explicite n'est pas approuvée.

## Scans fournisseurs et redistribution

Scans exacts index/platform/config, natifs ARM64/AMD64, sans socket Docker monté
dans Trivy, sorties brutes en mémoire uniquement. La première exécution échouait
faute d'espace dans le tmpfs256MiB ; les catégories assainies établissent
`no space left on device`. Passage borné à2GiB, rootfs lecture seule, noexec,
capabilities retirées et no-new-privileges conservés. Aucun scan désactivé.

- SeaweedFS4.51 :1 HIGH `CVE-2026-116587`, `go-jose/v4` v4.1.5,
  correctif annoncé4.1.6 ;3 avis UNKNOWN crypto/net ;0 alerte secrète.
  Inventaire274 paquets dont245 composants langages et29 système. Les38
  observations de licences sont des obligations à examiner, pas38 CVE ni une
  preuve automatique d'incompatibilité : GPL/LGPL/MPL et licences permissives
  dans les dépendances. Apache2.0 du projet ne décrit pas seul toute l'image.
- Garage2.5.0 : aucun inventaire de paquets ni OS exploitable par cette exécution
  Trivy. Gate `not_verified`, jamais « zéro vulnérabilité prouvé ». Les dépendances
  Rust embarquées/provenance binaire nécessitent une preuve complémentaire.
  AGPLv3 du projet, notices/source et obligations éventuelles de redistribution
  ou service modifié restent à examiner institutionnellement.

Le [Dockerfile Garage2.5.0](https://raw.githubusercontent.com/deuxfleurs-org/garage/v2.5.0/Dockerfile)
utilise `FROM scratch` et copie un binaire Rust. Le
[Cargo.lock source](https://raw.githubusercontent.com/deuxfleurs-org/garage/v2.5.0/Cargo.lock)
est un inventaire source, sans lien cryptographique vérifié ici avec ce binaire.
Il ne peut pas être présenté comme son SBOM runtime. La
[licence AGPL](https://raw.githubusercontent.com/deuxfleurs-org/garage/v2.5.0/LICENSE)
impose notamment des obligations de redistribution ; la clause réseau13 porte
sur une version modifiée et ne doit pas être présentée comme s'appliquant au seul
usage réseau d'un binaire non modifié.

Les signatures/provenances amont ne sont pas vérifiées : vérification du digest
registre et de la configuration n'est pas une preuve d'identité de signataire.
Aucun fournisseur nouveau/version candidate n'est adopté. Un futur correctif de
SeaweedFS devra être requalifié, sans repointer silencieusement un tag.

## Versions et digests retenus

Bases conservées : micromamba2.4.0
`sha256:10bd2dd2e7bfae77e529c76a71f4126c222d74e99b908abc6e210da9eda0f6af` ;
Node22.23.0-alpine3.23
`sha256:35e2f96595091599e7c1fb0b61049e17d8478997b2aa13db51ad7995299fe55a`.
SeaweedFS4.51 index
`sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8` ;
Garage2.5.0 index
`sha256:677e5b758e4425a325b811c425c026bf35a4bf42f7ddbaa773de3f4fd779a5a5`.
Trivy0.76.1
`sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c`.
Digests applicatifs/platform/config, versions système réellement installées,
SBOM/provenance et base de vulnérabilités sont rattachés au SHA/run des preuves,
jamais à un tag mutable ni au simple résultat de build.

| Image | Architecture | Digest applicatif OCI | Digest de configuration |
|---|---|---|---|
| api | amd64 | `sha256:a91841b8a48046c4f924078becb8dd7aef9ab685f7129f96865256cb4d5230cb` | `sha256:a62d736844ae356477f149aaf8f6c0cafdf901ee3833e447b47c111a8b65c6ae` |
| api | arm64 | `sha256:48b6ff30d47ec6a034fafcb8516108997220bcca59e37100e5a3c5a926f4ef2f` | `sha256:b65ba09cf8487f3e06816f0df547d82d69624cc82c4ef28dacea88ca4d2b8f41` |
| web | amd64 | `sha256:a4fb763b97f4ac36d0509952199024308eaa6fc6fb3166385ab60f6216852e95` | `sha256:a57dc5513af520fb42496d2958c75b992c781c41e9b52a1fc3b049c73672dd21` |
| web | arm64 | `sha256:ed3c6bdff620b3b46f9543c5ceeb4d8a8d5bb48011d0bc430eac4abe131728b7` | `sha256:41e11b348fb2741b88dc0ff82a604348708a320be9b1cde3e9aefee99b1235e7` |
| worker | amd64 | `sha256:3abb4dc1a989d2f491bb6aa368041430eda76a2de444a48300efc3ad55d95533` | `sha256:4a902f208cc3848f76d62160a80beba05cf2de2ed103990c3c21f8912428dbca` |
| worker | arm64 | `sha256:e1a874dd36c1621533bf0855ca3993e3d26fcbe0c42279e7f5abfe26396256be` | `sha256:f9d7bd74f9670173ff79bc239ee65e04ca5dcdee084c8d2e782db09c18cf9845` |

Les douze fichiers conservés sont des **projections assainies** de six SPDX2.3
et six provenances SLSA liés aux sujets OCI vérifiés : métadonnées paquet,
versions/licences et digests des attestations originales. Fichiers, URLs libres,
invocations, arguments et environnements sont exclus. Les projections ne sont
pas les attestations originales verbatim ; ni leur présence ni l’étiquette de
révision ne prouvent une signature ou une origine source de confiance.

## Tests, revue et limites

Tests statiques locaux, format/lint/typage/build, PostgreSQL et migrations sont
vérifiés par leurs contrôles respectifs, sans promouvoir un test ignoré en succès.
Les scans applicatifs, contrats S3 et vrais Primer3 tournent sur Linux natif
ARM64/AMD64. Le comparateur vérifie désormais aussi chaque résultat contre la
référence validée `e0a57dc`, entrées/paramètres/version identiques, neuf valeurs à
tolérance absolue1e-6 ; le run final donne deux deltas maximaux0.0.

Les29 parcours Chromium réussissent au run41458887909, code98a3250, après correction des prérequis. Le tag MinIO
historique est indisponible sur le runner : la recette E2E uploads-disabled retire
uniquement sa dépendance de démarrage dans un override CI temporaire ; aucun
fournisseur n'est substitué. Les images applicatives sont construites avant les
services dépendants ; S3 est testé séparément et les refus d'uploads demeurent
couverts. Aucun parcours de téléchargement inexistant n'est prétendument livré.

Validation locale : **69 tests** de qualification passent, Ruff lint/format,
`git diff --check` et `make compose-config` passent. Le groupe local
`make format lint typecheck test PYTHON_RUNNER=container` s’arrête au prérequis
Docker (accès socket refusé), sans exécution des suites : aucune réussite locale
fictive. Les contrôles applicatifs/build/typage/PostgreSQL et migrations sont
exécutés en CI.

Revue indépendante : chemins arbitraires remplacés par catégories fixes,
couverture OS manquante non assimilée à un succès ; extraction/triage en mémoire
relus sans nouveau problème important. Validation native du triage réalisée au contrôleur98a3250 ; aucun finding important restant dans le contrôleur n’a été confirmé.
Capacité réelle Mac/Docker Desktop, pic mémoire, sauvegarde cohérente app/Keycloak/
objets, OIDC/TLS/RLS et décisions pilote restent hors qualification de ce lot.
Aucune approbation de risque, fournisseur ou fusion n'est implicite.

## Matrice exhaustive HIGH/CRITICAL de référence

Référence `e0a57dc` (mêmes comptes au head revu2750c78), comparée au premier
rescan final `98a3250` (mêmes comptes que `b449f19`). Les deux architectures concordent ; les doublons par image sont
regroupés. Chaque ligne conserve l'avis, composant, versions, origine, présence/
exposition, correction, risque et statut. G1–G7 renvoient aux corrections et
risques documentés plus haut. « Absent au rescan » ne vaut pas preuve
universelle d'inexploitabilité. Aucun finding n'est retiré des rapports originaux.

| Avis | Sévérité | Composant | Image(s), ARM64 et AMD64 | Installée initiale | Finale observée (SPDX) | Corrigée indiquée | Origine | Présence finale / exposition connue | Correction proposée | Risque | Statut |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CVE-2026-102267 | HIGH | PyJWT | api | 2.10.1 | 2.14.0 | 2.14.0 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G2 | G2 | corrigé au rescan |
| CVE-2026-102268 | CRITICAL | PyJWT | api | 2.10.1 | 2.14.0 | 2.14.0 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G2 | G2 | corrigé au rescan |
| CVE-2026-102271 | HIGH | PyJWT | api | 2.10.1 | 2.14.0 | 2.14.0 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G2 | G2 | corrigé au rescan |
| CVE-2026-32597 | HIGH | PyJWT | api | 2.10.1 | 2.14.0 | 2.12.0 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G2 | G2 | corrigé au rescan |
| CVE-2026-48526 | HIGH | PyJWT | api | 2.10.1 | 2.14.0 | 2.13.0 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G2 | G2 | corrigé au rescan |
| GHSA-pxh4-856f-4h89 | HIGH | PyJWT | api | 2.10.1 | 2.14.0 | 2.14.0 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G2 | G2 | corrigé au rescan |
| CVE-2026-102276 | HIGH | brace-expansion | web | 2.0.2 | non présente dans la projection | 5.0.10, 3.0.7, 2.1.5, 1.1.19 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-102278 | HIGH | brace-expansion | web | 2.0.2 | non présente dans la projection | 5.0.11, 3.0.8, 2.1.6, 1.1.20 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-13149 | HIGH | brace-expansion | web | 2.0.2 | non présente dans la projection | 5.0.7, 1.1.16, 2.1.2 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-14257 | HIGH | brace-expansion | web | 2.0.2 | non présente dans la projection | 5.0.8, 3.0.3, 2.1.3, 1.1.17 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-69152 | HIGH | brace-expansion | web | 2.0.2 | non présente dans la projection | 1.1.18, 2.1.4, 3.0.6, 5.0.9 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-53612 | HIGH | bsdutils | api, worker | 1:2.41-5 | 1:2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53613 | HIGH | bsdutils | api, worker | 1:2.41-5 | 1:2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53614 | HIGH | bsdutils | api, worker | 1:2.41-5 | 1:2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53615 | HIGH | bsdutils | api, worker | 1:2.41-5 | 1:2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-76642 | HIGH | bsdutils | api, worker | 1:2.41-5 | 1:2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78408 | HIGH | bsdutils | api, worker | 1:2.41-5 | 1:2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78409 | HIGH | bsdutils | api, worker | 1:2.41-5 | 1:2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78410 | HIGH | bsdutils | api, worker | 1:2.41-5 | 1:2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-41992 | HIGH | gzip | api, worker | 1.13-1 | 1.13-1+deb13u1 | 1.13-1+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-69192 | HIGH | ip-address | web | 10.1.0 | non présente dans la projection | 10.3.1 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-54369 | HIGH | libacl1 | api, worker | 2.3.2-2+b1 | 2.3.2-2+b1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-53612 | HIGH | libblkid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53613 | HIGH | libblkid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53614 | HIGH | libblkid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53615 | HIGH | libblkid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-76642 | HIGH | libblkid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78408 | HIGH | libblkid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78409 | HIGH | libblkid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78410 | HIGH | libblkid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-4878 | HIGH | libcap2 | api, worker | 1:2.75-10+b1 | 1:2.75-10+deb13u1+b3 | 1:2.75-10+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-14456 | HIGH | libcrypto3 | web | 3.5.7-r0 | 3.5.9-r0 | 3.5.8-r0 | système Alpine / base | initiale oui ; finding absent au rescan ; bibliothèque finale ; chemin chargé non établi | G5 | G5 | corrigé au rescan |
| CVE-2026-53612 | HIGH | liblastlog2-2 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53613 | HIGH | liblastlog2-2 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53614 | HIGH | liblastlog2-2 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53615 | HIGH | liblastlog2-2 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-76642 | HIGH | liblastlog2-2 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78408 | HIGH | liblastlog2-2 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78409 | HIGH | liblastlog2-2 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78410 | HIGH | liblastlog2-2 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-53612 | HIGH | libmount1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53613 | HIGH | libmount1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53614 | HIGH | libmount1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53615 | HIGH | libmount1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-76642 | HIGH | libmount1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78408 | HIGH | libmount1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78409 | HIGH | libmount1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78410 | HIGH | libmount1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-103111 | HIGH | libpcre2-8-0 | api, worker | 10.46-1~deb13u1 | 10.46-1~deb13u3 | 10.46-1~deb13u3 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-86145 | HIGH | libpcre2-8-0 | api, worker | 10.46-1~deb13u1 | 10.46-1~deb13u3 | 10.46-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-89157 | HIGH | libpcre2-8-0 | api, worker | 10.46-1~deb13u1 | 10.46-1~deb13u3 | 10.46-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-89161 | HIGH | libpcre2-8-0 | api, worker | 10.46-1~deb13u1 | 10.46-1~deb13u3 | 10.46-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53612 | HIGH | libsmartcols1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53613 | HIGH | libsmartcols1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53614 | HIGH | libsmartcols1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53615 | HIGH | libsmartcols1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-76642 | HIGH | libsmartcols1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78408 | HIGH | libsmartcols1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78409 | HIGH | libsmartcols1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78410 | HIGH | libsmartcols1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-11822 | HIGH | libsqlite3-0 | api, worker | 3.46.1-7 | 3.46.1-7+deb13u2 | 3.46.1-7+deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-11824 | HIGH | libsqlite3-0 | api, worker | 3.46.1-7 | 3.46.1-7+deb13u2 | 3.46.1-7+deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-119373 | HIGH | libsqlite3-0 | api, worker | 3.46.1-7 | 3.46.1-7+deb13u2 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-14456 | HIGH | libssl3 | web | 3.5.7-r0 | 3.5.9-r0 | 3.5.8-r0 | système Alpine / base | initiale oui ; finding absent au rescan ; bibliothèque finale ; chemin chargé non établi | G5 | G5 | corrigé au rescan |
| CVE-2025-15467 | HIGH | libssl3t64 | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.4-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2025-69421 | HIGH | libssl3t64 | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.4-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-14456 | HIGH | libssl3t64 | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.7-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-28387 | HIGH | libssl3t64 | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.5-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-28388 | HIGH | libssl3t64 | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.5-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-28389 | HIGH | libssl3t64 | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.5-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-28390 | HIGH | libssl3t64 | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.5-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-31789 | CRITICAL | libssl3t64 | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.5-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-45447 | HIGH | libssl3t64 | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.6-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-84782 | HIGH | libssl3t64 | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.7-1~deb13u3 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-16742 | HIGH | libsystemd0 | api, worker | 257.9-1~deb13u1 | 257.13-1~deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2025-69720 | HIGH | libtinfo6 | api, worker | 6.5+20250216-2 | 6.5+20250216-2 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-16742 | HIGH | libudev1 | api, worker | 257.9-1~deb13u1 | 257.13-1~deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-53612 | HIGH | libuuid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53613 | HIGH | libuuid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53614 | HIGH | libuuid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53615 | HIGH | libuuid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-76642 | HIGH | libuuid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78408 | HIGH | libuuid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78409 | HIGH | libuuid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78410 | HIGH | libuuid1 | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-53612 | HIGH | login | api, worker | 1:4.16.0-2+really2.41-5 | 1:4.16.0-2+really2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53613 | HIGH | login | api, worker | 1:4.16.0-2+really2.41-5 | 1:4.16.0-2+really2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53614 | HIGH | login | api, worker | 1:4.16.0-2+really2.41-5 | 1:4.16.0-2+really2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53615 | HIGH | login | api, worker | 1:4.16.0-2+really2.41-5 | 1:4.16.0-2+really2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-76642 | HIGH | login | api, worker | 1:4.16.0-2+really2.41-5 | 1:4.16.0-2+really2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78408 | HIGH | login | api, worker | 1:4.16.0-2+really2.41-5 | 1:4.16.0-2+really2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78409 | HIGH | login | api, worker | 1:4.16.0-2+really2.41-5 | 1:4.16.0-2+really2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78410 | HIGH | login | api, worker | 1:4.16.0-2+really2.41-5 | 1:4.16.0-2+really2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-53612 | HIGH | mount | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53613 | HIGH | mount | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53614 | HIGH | mount | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53615 | HIGH | mount | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-76642 | HIGH | mount | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78408 | HIGH | mount | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78409 | HIGH | mount | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78410 | HIGH | mount | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2025-69720 | HIGH | ncurses-base | api, worker | 6.5+20250216-2 | 6.5+20250216-2 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2025-69720 | HIGH | ncurses-bin | api, worker | 6.5+20250216-2 | 6.5+20250216-2 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-94482 | HIGH | next | web | 16.3.3 | 16.4.1 | 15.5.28, 16.4.1 | npm applicatif | initiale oui ; finding absent au rescan ; serveur web ; exploitabilité non établie | G6 | G6 | corrigé au rescan |
| CVE-2026-94483 | HIGH | next | web | 16.3.3 | 16.4.1 | 16.3.8 | npm applicatif | initiale oui ; finding absent au rescan ; serveur web ; exploitabilité non établie | G6 | G6 | corrigé au rescan |
| GHSA-2464-fhr4-w9xw | CRITICAL | next | web | 16.3.3 | 16.4.1 | 15.5.28, 16.4.1 | npm applicatif | initiale oui ; finding absent au rescan ; serveur web ; exploitabilité non établie | G6 | G6 | corrigé au rescan |
| GHSA-673q-mjm6-r5xr | CRITICAL | next | web | 16.3.3 | 16.4.1 | 16.4.1 | npm applicatif | initiale oui ; finding absent au rescan ; serveur web ; exploitabilité non établie | G6 | G6 | corrigé au rescan |
| GHSA-vcvr-r3jv-pc5j | CRITICAL | next | web | 16.3.3 | 16.4.1 | 16.3.6 | npm applicatif | initiale oui ; finding absent au rescan ; serveur web ; exploitabilité non établie | G6 | G6 | corrigé au rescan |
| CVE-2025-15467 | HIGH | openssl-provider-legacy | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.4-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2025-69421 | HIGH | openssl-provider-legacy | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.4-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-14456 | HIGH | openssl-provider-legacy | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.7-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-28387 | HIGH | openssl-provider-legacy | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.5-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-28388 | HIGH | openssl-provider-legacy | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.5-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-28389 | HIGH | openssl-provider-legacy | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.5-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-28390 | HIGH | openssl-provider-legacy | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.5-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-31789 | CRITICAL | openssl-provider-legacy | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.5-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-45447 | HIGH | openssl-provider-legacy | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.6-1~deb13u2 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-84782 | HIGH | openssl-provider-legacy | api, worker | 3.5.4-1~deb13u1 | 3.5.7-1~deb13u3 | 3.5.7-1~deb13u3 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-9496 | HIGH | pacote | web | 19.0.2 | non présente dans la projection | 21.5.1 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-9496 | HIGH | pacote | web | 20.0.1 | non présente dans la projection | 21.5.1 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-13221 | CRITICAL | perl-base | api, worker | 5.40.1-6 | 5.40.1-6+deb13u1 | 5.40.1-6+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-42496 | CRITICAL | perl-base | api, worker | 5.40.1-6 | 5.40.1-6+deb13u1 | 5.40.1-6+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-42497 | HIGH | perl-base | api, worker | 5.40.1-6 | 5.40.1-6+deb13u1 | 5.40.1-6+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-48962 | HIGH | perl-base | api, worker | 5.40.1-6 | 5.40.1-6+deb13u1 | 5.40.1-6+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-57432 | HIGH | perl-base | api, worker | 5.40.1-6 | 5.40.1-6+deb13u1 | 5.40.1-6+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-57433 | HIGH | perl-base | api, worker | 5.40.1-6 | 5.40.1-6+deb13u1 | 5.40.1-6+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-8376 | CRITICAL | perl-base | api, worker | 5.40.1-6 | 5.40.1-6+deb13u1 | 5.40.1-6+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-9538 | HIGH | perl-base | api, worker | 5.40.1-6 | 5.40.1-6+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-33671 | HIGH | picomatch | web | 4.0.3 | UNKNOWN | 4.0.4, 3.0.2, 2.3.2 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-24486 | HIGH | python-multipart | api | 0.0.20 | 0.0.30 | 0.0.22 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G3 | G3 | corrigé au rescan |
| CVE-2026-42561 | HIGH | python-multipart | api | 0.0.20 | 0.0.30 | 0.0.27 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G3 | G3 | corrigé au rescan |
| CVE-2026-53539 | HIGH | python-multipart | api | 0.0.20 | 0.0.30 | 0.0.30 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G3 | G3 | corrigé au rescan |
| GHSA-rgj7-g3m4-5g8c | HIGH | sharp | web | 0.35.3 | 0.35.5 | 0.35.4 | npm applicatif | initiale oui ; finding absent au rescan ; serveur web ; exploitabilité non établie | G6 | G6 | corrigé au rescan |
| GHSA-wq5f-xc86-pv6w | HIGH | sharp | web | 0.35.3 | 0.35.5 | 0.35.5 | npm applicatif | initiale oui ; finding absent au rescan ; serveur web ; exploitabilité non établie | G6 | G6 | corrigé au rescan |
| CVE-2026-48815 | HIGH | sigstore | web | 3.1.0 | non présente dans la projection | 4.1.1 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2025-62727 | HIGH | starlette | api | 0.45.3 | 1.3.1 | 0.49.1 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G4 | G4 | corrigé au rescan |
| CVE-2026-48818 | HIGH | starlette | api | 0.45.3 | 1.3.1 | 1.1.0 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G4 | G4 | corrigé au rescan |
| CVE-2026-54283 | HIGH | starlette | api | 0.45.3 | 1.3.1 | 1.3.1 | pip | initiale oui ; finding absent au rescan ; API HTTP/auth ; exploitabilité non établie | G4 | G4 | corrigé au rescan |
| CVE-2026-59873 | CRITICAL | tar | web | 7.5.11 | UNKNOWN | 7.5.19 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-59874 | HIGH | tar | web | 7.5.11 | UNKNOWN | 7.5.18 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-73566 | HIGH | tar | web | 7.5.11 | UNKNOWN | 7.5.21 | npm de la base / outil global | initiale oui ; finding absent au rescan ; outil embarqué initialement ; usage runtime non requis | G7 | G7 | corrigé au rescan |
| CVE-2026-53612 | HIGH | util-linux | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53613 | HIGH | util-linux | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53614 | HIGH | util-linux | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-53615 | HIGH | util-linux | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | 2.41.5-0+deb13u1 | système Debian / base micromamba | initiale oui ; finding absent au rescan ; paquet final ; charge/utilisation vulnérable non établie | G1 | G1 | corrigé au rescan |
| CVE-2026-76642 | HIGH | util-linux | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78408 | HIGH | util-linux | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78409 | HIGH | util-linux | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-78410 | HIGH | util-linux | api, worker | 2.41-5 | 2.41.5-0+deb13u1 | non indiquée | système Debian / base micromamba | initiale oui ; finale toujours signalée ; paquet final ; charge/utilisation vulnérable non établie | G1 ; suivre le correctif amont | G1 | analyse nécessaire — correctif non indiqué par le rapport |
| CVE-2026-116587 | HIGH | github.com/go-jose/go-jose/v4 | SeaweedFS, ARM64 et AMD64 | v4.1.5 | v4.1.5 | 4.1.6 | Go embarqué | finale oui ; exposition vulnérable non établie | correctif amont / image à requalifier, sans substitution | moyen : authentification/S3 à requalifier | analyse nécessaire, bloquant |
