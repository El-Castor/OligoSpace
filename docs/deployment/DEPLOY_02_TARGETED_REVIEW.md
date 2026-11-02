# DEPLOY-02 — Rapport final consolidé et recommandation de fusion

Latest [one-page decision review](DEPLOY_02_DECISION.md) distinguishes code integration from release authorization; no risk acceptance granted.

## Périmètre et décision maintenue

Revue demandée du head `1cca325bf6d81f76ac875826c7f5ee068e2c89bc`,
base `75179a52da0d929922c904ff6df06d94eb7a1a67`. Contrôleur testé
`44bb074e317b1fdb147858a87040919cd9d3ce20`,
[CI ciblée41494493319](https://github.com/El-Castor/OligoSpace/actions/runs/41494493319).
[Preuves conservées](../../infra/deployment/evidence/targeted-44bb074-review.json)
et [SBOM source](../../infra/deployment/evidence/garage-2.5.0-source-sbom.cdx.json).
PR18 reste **DRAFT,
non fusionnée**. Cette passe apporte des lectures de qualification et une
consolidation du chantier dans la seule PR18 ; aucun découpage Git/PR n'est exécuté, aucune règle
GitHub ou politique de sécurité modifiée, aucune activation de release.
Aucun Dockerfile produit, paquet installé, API, règle métier, politique d'accès,
Compose pilote ou fournisseur n'est modifié par cette passe. Pas de Mac mini,
Cloudflare, migration réelle, publication d'image ni rotation de secret.

## 1. Neuf vulnérabilités distinctes, et non44

Les44 occurrences HIGH de chacun des quatre scans API/worker ARM64/AMD64 se
regroupent en **9 CVE,6 paquets source Debian et17 paquets binaires**. Les quatre
avis util-linux s'appliquent chacun à9 binaires, soit36 occurrences. Le scanner
reste HIGH ; le triage Debian `no-dsa`/minor/postponed est une autre information,
pas une dérogation ni un motif pour filtrer les résultats.

État du tracker Debian vérifié le2026-11-02. « Correctif unstable » signifie
qu'un paquet source corrigé y existe, **pas** qu'une mise à jour supportée trixie
est disponible ni qu'une greffe de binaires sid serait compatible.

| CVE réellement distincte | Source / version source observée | Binaires concernés par image | État trixie | Correctif Debian unstable | Proposition / risque restant |
|---|---|---:|---|---|---|
| [CVE-2026-76642](https://security-tracker.debian.org/tracker/CVE-2026-76642) | `util-linux 2.41.5-0+deb13u1` | 9 | vulnérable ; no-dsa (Minor issue) | `2.42.3-1` | attendre correctif stable ou backport revu ; ambiguïté de portée pour78409, aucune suppression automatique |
| [CVE-2026-78408](https://security-tracker.debian.org/tracker/CVE-2026-78408) | `util-linux 2.41.5-0+deb13u1` | 9 | vulnérable ; no-dsa (Minor issue) | `2.42.4-1` | attendre correctif stable ou backport revu ; ambiguïté de portée pour78409, aucune suppression automatique |
| [CVE-2026-78409](https://security-tracker.debian.org/tracker/CVE-2026-78409) | `util-linux 2.41.5-0+deb13u1` | 9 | vulnérable ; no-dsa (Minor issue) | `2.42.3-1` | attendre correctif stable ou backport revu ; ambiguïté de portée pour78409, aucune suppression automatique |
| [CVE-2026-78410](https://security-tracker.debian.org/tracker/CVE-2026-78410) | `util-linux 2.41.5-0+deb13u1` | 9 | vulnérable ; no-dsa (Minor issue) | `2.42.3-1` | attendre correctif stable ou backport revu ; ambiguïté de portée pour78409, aucune suppression automatique |
| [CVE-2026-54369](https://security-tracker.debian.org/tracker/CVE-2026-54369) | `acl 2.3.2-2` | 1 | vulnérable ; no-dsa (Will be fixed first in unstable, then point release update; not to be backported by individual patches) | `2.4.0-1` | mise à jour ponctuelle stable annoncée ; pas de backport individuel recommandé par Debian |
| [CVE-2026-119373](https://security-tracker.debian.org/tracker/CVE-2026-119373) | `sqlite3 3.46.1-7+deb13u2` | 1 | vulnérable ; ouvert | `non corrigé dans le tracker` | analyse amont/correctif requis ; absence de version corrigée Debian indiquée |
| [CVE-2026-16742](https://security-tracker.debian.org/tracker/CVE-2026-16742) | `systemd 257.13-1~deb13u1` | 2 | vulnérable ; no-dsa (Minor issue) | `261.2-1` | correctif stable ou backport revu ; changement de branche ABI à éviter |
| [CVE-2025-69720](https://security-tracker.debian.org/tracker/CVE-2025-69720) | `ncurses 6.5+20250216-2` | 3 | vulnérable ; no-dsa (Minor issue) | `6.6+20251231-1` | correctif stable ou backport revu ; compatibilité terminal/bibliothèques |
| [CVE-2026-9538](https://security-tracker.debian.org/tracker/CVE-2026-9538) | `perl 5.40.1-6+deb13u1` | 1 | vulnérable ; postponed (Minor issue; wait for regressions upstream sorted out) | `5.42.3-1` | attendre résolution des régressions amont ou correctif stable ; paquet de base à préserver |

Huit avis ont donc un correctif dans unstable ; les neuf restent ouverts dans
trixie selon les pages consultées. SQLite reste aussi non corrigé dans unstable.
Aucune de ces constatations n'est une preuve d'exploitabilité dans OligoSpace.

Correspondances qui évitent des faux doublons de versions :

- `bsdutils 1:2.41.5-0+deb13u1` et
  `login 1:4.16.0-2+really2.41.5-0+deb13u1` proviennent de
  `util-linux 2.41.5-0+deb13u1` : epoch/wrapper binaire ne sont pas une autre
  vulnérabilité source. [Métadonnées login](https://packages.debian.org/trixie/login),
  [bsdutils](https://packages.debian.org/trixie/bsdutils).
- `libacl1 2.3.2-2+b1` provient de `acl 2.3.2-2` ; le suffixe binNMU `+b1`
  n'est pas une version source. [Métadonnées](https://packages.debian.org/trixie/libacl1).
- Pour `CVE-2026-78409`, le tracker marque trixie2.41.5 vulnérable mais une note
  dit que le code concerné a été ajouté en2.42. La contradiction reste à clarifier
  auprès de Debian/amont ; ce n'est pas un faux positif accepté automatiquement.

## 2. Présence effective, utilisation et limites

Les projections SPDX déjà conservées lient les17 paquets à des images finales
vérifiées, mais une base dpkg/inventaire ne suffit pas à prouver la présence de
chaque fichier ni sa charge effective. La sonde ajoutée lit donc, dans des
conteneurs éphémères non-root, sans réseau, rootfs en lecture seule et sans
capabilities : statuts dpkg, version source déclarée, compte de fichiers
réellement présents, ELF représentatif avec SHA256 et observations `ldd`
sélectionnées pour Python, `_sqlite3`/readline et les exécutables Primer3 présents.
Aucun paquet n'est supprimé ; aucun répertoire privé ni configuration utilisateur
n'est lu. Les absences/erreurs de métadonnées restent explicitement non vérifiées.

Les images sont reconstruites depuis le head revu1cca325 et liées par leur digest
de configuration, RootFS et étiquette source avant la sonde. C'est une observation
sur cette reconstruction : **pas une reproduction bit à bit démontrée des images
historiques**, car apt et certaines résolutions transitives ne sont pas archivés
comme un snapshot de dépôt. Les digests observés et le contrôleur sont conservés
séparément. Une bibliothèque présente peut ne pas apparaître dans les seuls
`ldd` sélectionnés ; une bibliothèque chargée ne prouve pas l'usage du code
vulnérable. Aucune déclaration globale « inatteignable » ou « paquet inutile »
ne découle de ces observations.

Le premier essai (contrôleur47917bb puis9fa4d94) s’est arrêté sur des refus
catégorisés `read-only file system`/`no such file` au lancement via micromamba.
Le contrôleur a2a891a lance directement `/opt/conda/bin/python` déjà installé,
sans activation Conda et sans assouplir read-only/no-network/non-root. Les rapports
portent explicitement `direct_python_without_conda_activation` : les chargements
observés ne prétendent donc pas reproduire tous les hooks d’activation applicatifs.
Les quatre lectures corrigées **réussissent** :

| Image reconstruite depuis1cca325 | Architecture | Paquets installés | Fichiers réguliers listés présents | Paquets avec ELF représentatif |
|---|---|---:|---:|---:|
| API | AMD64 | 17/17 | 852 | 16/17 |
| API | ARM64 | 17/17 | 852 | 16/17 |
| Worker | AMD64 | 17/17 | 852 | 16/17 |
| Worker | ARM64 | 17/17 | 852 | 16/17 |

852 est une somme d'occurrences de fichiers par paquet, pas une mesure garantie
sans doublon de tout le système. ncurses-base apporte notamment des données
terminal, sans ELF représentatif dans la sélection : ce n'est pas une absence
de paquet. Les six versions source relevées par dpkg sont celles du tableau9CVE.
Les trois exécutables Primer3 sont présents dans le worker et absents de l'API,
conformément aux rôles. Les extensions Python examinées lient `libsqlite3` et
`libtinfo` depuis `/opt/conda`, tandis que les copies Debian restent sur disque.
Primer3 charge notamment libc/libm et, pour primer3_core, libstdc++ système.
Ces observations n'inspectent pas tous les processus/hooks ni les chargements
ultérieurs et ne permettent pas une suppression ou une dérogation de sécurité.


## 3. SeaweedFS4.52 : correctif vérifié, qualification et réserves

La [release officielle4.52](https://github.com/seaweedfs/seaweedfs/releases/tag/4.52)
a été publiée le2026-11-02 à11:24:12UTC, sans marqueur prerelease. Tag source
`984eac6a790be89e2a11de175a7413e1e3e32dd3` ; son `go.mod` déclare
`github.com/go-jose/go-jose/v4 v4.1.6`, version corrigée annoncée pour l'avis
HIGH de4.51. La présence dans les sources ne prouve pas celle du binaire.

La disponibilité a changé pendant la revue. À16:25UTC les deux registres
officiels répondaient404 et le workflow amont était queued. Au contrôle17:42UTC,
Docker Hub **et** GHCR exposent le même index et les deux architectures :

| Objet | Digest vérifié |
|---|---|
| Index4.52 des deux registres | `sha256:57877e32bb90073b37dc109b438ba66e84fd5ed9ced5f5c04f56444ef243ce59` |
| Linux AMD64 | `sha256:a54ba35b44895a449f5cdd415999062201b17b9835ec0ffc19ea605b72ffa3d1` |
| Linux ARM64 | `sha256:18a805c81cd574a24571cfbc23ff1cb0bb2b875b1ac028a58c065c15f0c7b3ad` |

Le [workflow amont41436547119](https://github.com/seaweedfs/seaweedfs/actions/runs/41436547119)
est terminé en échec sur `merge (normal)` malgré ces manifestes disponibles.
Le hash des manifestes est vérifié ; la confiance de signature/provenance amont
reste non vérifiée. L'échec de workflow n'est ni masqué ni assimilé à une preuve
que le binaire est incorrect : les scans et tests de ce digest sont distincts.

La variante **de qualification** `seaweedfs-4.52` sélectionne explicitement ce
seul digest. Le défaut4.51, les autres images et le Compose pilote restent
inchangés. Pas de fallback latest/dev, pas de provider switch ni release.
La requalification native lance le scan intégral vuln/secret/licence, vérifie
la version go-jose réellement inventoriée, et exécute les restaurations
SeaweedFS→SeaweedFS, SeaweedFS→Garage et Garage→SeaweedFS sur chaque architecture.
Les métadonnées/SHA256, restarts, refus, logs/ports et cleanup restent obligatoires.
Garage→Garage est inchangé et couvert par les preuves antérieures ; il n'est
pas compté comme un nouveau test4.52. Scans et observation go-jose tournent même
si les contrats S3 ou le build client échouent. Chaque contrôle absent ou finding
résiduel reste bloquant, sans choix fournisseur automatique.

Résultats natifs observés au contrôleur44bb074 :

| Architecture | go-jose réellement inventorié | HIGH go-jose | Autres avis | Licences observées | Restaurations testées |
|---|---|---:|---|---:|---|
| AMD64 | v4.1.6 | 0 | 3 UNKNOWN | 38 | 3/3 passent |
| ARM64 | v4.1.6 | 0 | 3 UNKNOWN | 38 | 3/3 passent |

Les six contrats passent, y compris les métadonnées/types/SHA256 persistés, les
deux restarts, export/restauration indépendante, refus de mauvais credentials,
logs deux flux, ports et cleanup. Le SDK réel7.2.20 et l'adaptateur inchangé sont
exercés. Les preuves OCI du client API reconstruit sont également conservées.
Les scans ont abouti ; ils restent `completed_with_findings`/`gate=failed` :
`GO-2026-5932` dans x/crypto v0.58.0 (aucun correctif indiqué),
`CVE-2026-78661` et `CVE-2026-97045` dans x/net v0.61.0 (correctif indiqué0.62.0).
Aucune baisse artificielle de sévérité ni exclusion : le HIGH de4.51 n'est plus
signalé avec la version corrigée observée, et tous les résiduels sont conservés.
Les275 paquets inventoriés et les38 observations de licences de chaque image
ne constituent ni une certification de redistribution ni une confiance de signature.

Recommander4.52 comme **version candidate corrigée à examiner**, sans adoption
pilote automatique. Les UNKNOWN, licences et provenance restent à décider.
Le défaut4.51 est conservé pour comparaison historique, et le service pilote
MinIO n'est pas repointé. Le digest de configuration AMD64 observé est
`sha256:50924162a651638ef1b7b28c08cf47dd66c28ebecb6f9eb220900e5996f804f8` ;
ARM64 `sha256:f01d2260762bfe0a3b4780b561d716251a1dc3fd3d20dccfa8fde4d95c414104`.


## 4. Garage : source SBOM, binaire distribué et risque restant

La SBOM **source** CycloneDX1.6 conservée décrit542 paquets du Cargo.lock
(dont526 registry), versions/checksums et graphe source, à partir du commit
`586726edb0170bb46f604e84fba09e5659610649` du tag annoté2.5.0.
La SBOM source a été validée contre le schéma officiel CycloneDX1.6 (0erreur),
avec542 références uniques et aucune arête source pendante.
SHA256 Cargo.lock :
`d7d15e571ad5274e849a264a04e08e7e15d49ba42d352cc7325b2847d582e61b`.
Les checksums sont ceux des archives de crates, pas des bibliothèques liées.
Les dépendances build/dev/optionnelles et plateformes sont incluses sans
résolution des features runtime ; les bibliothèques natives embarquées, Nix et
le toolchain ne sont pas complètement inventoriés. Aucune licence externe
n'est devinée. Cette SBOM ne remplace pas une SBOM de l'image ou du binaire.

Le scan du Cargo.lock exact par le même Trivy observe542 paquets source,
**1 HIGH,3 MEDIUM,7 LOW**, toujours bloquants. Le HIGH est
`GHSA-82j2-j2ch-gfr8`, `rustls-webpki 0.101.7`, correctifs indiqués
`0.103.13, 0.104.0-alpha.7`. Ce résultat ne prouve pas que cette version entre
dans le binaire exécuté ; une montée de branche transitive doit être traitée
avec l'amont et ses tests, sans forcer une résolution incompatible.
[L’avis primaire](https://github.com/advisories/GHSA-82j2-j2ch-gfr8) décrit un déni
de service sur traitement de CRL, avec vérification de révocation explicitement
activée et octets CRL influençables par un attaquant. Ces préconditions ne sont
pas démontrées pour Garage ici ; ni la présence runtime ni l’inapplicabilité
ne sont affirmées, et le finding reste bloquant.

Le Dockerfile exact est `FROM scratch` et copie `result/bin/garage`. Le processus
Nix/woodpecker examiné publie le même chemin de sortie comme binaire HTTPS et
image OCI. Les deux binaires extraits des images figées ont été comparés aux
URLs officielles fixes, sans exécuter les octets distribués :

| Architecture | Taille | SHA256 OCI et téléchargement officiel | Résultat |
|---|---:|---|---|
| AMD64 | 69426824 | `2ff667286217cd73ebcb1c03af993822365000441dfe31a80cb64c5189a9dea8` | identiques |
| ARM64 | 65920568 | `69b6040cef428b993500c17dd0d0c1240acf2f3f667b9b05ceba4b9660db4e8c` | identiques |

Le manifeste index, child manifest, config, diff_ids de layers et architecture
ELF sont vérifiés. L'égalité établit une **correspondance de distribution à la
date observée**, pas une signature ni une attestation source→binaire. Le tag
source n'est pas vérifié signé par l'API consultée ; l'index de téléchargement
n'expose pas de checksum signé dans les champs observés. Aucun marqueur `.dep-v0`
n'a été observé par la recherche binaire ; cette recherche seule ne constitue
pas une analyse de sections ELF complète. La couverture Rust/OS des scans images
reste **not_verified**, et « aucune vulnérabilité » serait une conclusion erronée.

Sources primaires exactes :
[Cargo.lock](https://git.deuxfleurs.fr/Deuxfleurs/garage/raw/commit/586726edb0170bb46f604e84fba09e5659610649/Cargo.lock),
[build Nix](https://git.deuxfleurs.fr/Deuxfleurs/garage/src/commit/586726edb0170bb46f604e84fba09e5659610649/nix/compile.nix),
[publication](https://git.deuxfleurs.fr/Deuxfleurs/garage/src/commit/586726edb0170bb46f604e84fba09e5659610649/shell.nix),
[Dockerfile](https://git.deuxfleurs.fr/Deuxfleurs/garage/src/commit/586726edb0170bb46f604e84fba09e5659610649/Dockerfile),
[index officiel](https://garagehq.deuxfleurs.fr/_releases.json).
La provenance authentifiée, une SBOM du build réel, ou une reconstruction
reproductible avec égalité mesurée et inventaire complet restent des preuves à
obtenir. Aucune publication ni compilation d'une nouvelle image Garage n'est faite.

## 5. Organisation finale : une seule PR18

La décision utilisateur annule la proposition précédente de séparation A/B.
Cette proposition n'avait jamais été exécutée : aucun développement n'est perdu,
retiré ou déplacé. Les outils, corrections de sécurité, tests et preuves restent
ensemble dans la branche et la PR18. Aucun nouveau découpage n'est recommandé.
Pour les prochains lots, privilégier une PR cohérente par objectif fonctionnel ou
technique ; ne pas créer plusieurs PR pour des sous-tâches fortement liées sans
bénéfice technique démontré. Cette décision d'organisation ne change aucun gate.

### Fonctions validées et exigences bloquantes

| Domaine | État démontré | Condition encore ouverte |
|---|---|---|
| Application | backend, worker, frontend, migrations, intégration PostgreSQL et Chromium passent au head documentaire cbca2d7 | ne vaut pas autorisation de release |
| Science | comparaison native des résultats Primer3 passe | conserver paramètres, versions et référence validée |
| S3 | huit scénarios historiques 4.51/Garage ; six scénarios supplémentaires 4.52 sur deux architectures passent au contrôleur44bb074 | aucun choix fournisseur ni changement pilote approuvé |
| API/worker OCI | CRITICAL corrigés, secrets finaux absents dans preuves conservées ; web passe sur deux architectures | 44 occurrences HIGH /9 CVE par image, autres niveaux conservés ; correction stable ou décision explicite requise |
| SeaweedFS | correctif go-jose4.52 vérifié, contrats passent | défaut4.51 encore signalé ; 4.52 conserve3 UNKNOWN, licences et confiance provenance à traiter |
| Garage | sourceSBOM et correspondance des distributions établies | HIGH source et autres avis ; inventaire runtime et attestation source→binaire non vérifiés |
| Historique secrets | triage expurgé des exemples publics conservé | jobs scannant les anciennes images restent rouges, pas présentés comme succès |
| Déploiement | aucun déploiement réalisé | OIDC/TLS/RLS, récupération, capacité réelle et autres gates du plan restent non qualifiés |

### CI et protections vérifiées avant toute fusion

Snapshot GitHub au head `cbca2d7748954262fe525cf853d8846991977fe5` :
PR OPEN/DRAFT, `mergeable=MERGEABLE` (absence de conflit),
`mergeStateStatus=UNSTABLE`. Tous les jobs de ce head sont terminés.
Les contrôles applicatifs/foundation, PostgreSQL, Chromium, présence de paquets,
comparaison scientifique et binaires Garage passent. Les quatre scans natifs
API/worker, les quatre scans candidats par défaut, le scan source Garage,
les deux qualifications 4.52 (gates de scan) et les deux scans historiques
restent rouges. Les réussites S3 ne transforment pas ces échecs en succès.

L'API GitHub indique `main.protected=false`, aucune ruleset retournée et aucun
required_status_check configuré dans cette réponse. Ce constat ne rend pas les
gates de sécurité facultatifs et ne remplace pas l'approbation utilisateur.
Aucun contrôle, workflow, statut, protection ou politique n'est désactivé,
renommé pour contournement, forcé ou marqué comme accepté. Aucun merge admin.

### Recommandation explicite

**Corrections encore nécessaires : ne pas fusionner PR18 en l'état.**
L'absence de conflit Git est distincte de l'aptitude de sécurité. Les findings
résiduels et lacunes de couverture doivent être corrigés ou faire l'objet d'une
décision explicite, documentée et approuvée, sans dérogation implicite.
La PR18 reste l'unique PR du chantier, en brouillon et sans fusion automatique.
Après résolution, rejouer les contrôles pertinents au SHA final puis soumettre
la recommandation de fusion à l'utilisateur. Aucun développement nouveau ni
opération d'hébergement n'est engagé par cette consolidation.

## Preuves, contrôles et arrêt

Dernière revue indépendante de cette consolidation : aucun problème important ;
annulation A/B, conservation intégrale dans PR18 et recommandation de non-fusion
vérifiées. Diff documentaire seulement ; les88 tests de qualification repassent.

88 tests locaux de qualification passent, ainsi que Ruff lint/format et les
vérifications de diff. Le contrôle ciblé est rouge sur les findings source Cargo.lock et les scans
4.52 résiduels ; les quatre lectures de paquets, les deux comparaisons
binaires, les six restaurations et les deux observations go-jose passent. Les anciens refus de lecture restent conservés, sans être
promus en succès. La requalification applicative existante reste séparée, et les
findings système/candidats continuent de bloquer la release. La CI applicative
41494493357 et foundation41494493321 du contrôleur44bb074 sont vertes.
Le run natif41494493310 reste rouge sur les quatre scans API/worker ; web et
comparaison des preuves passent. Dans41494493344, Chromium passe et les deux
scans historiques de secrets restent rouges ; ils ne sont pas comptés comme succès.

La revue documentaire des sources Debian, Cargo et SeaweedFS est datée ; la
lecture effective en conteneurs natifs et ses éventuels refus sont conservés
séparément. Aucun test non exécuté ou couverture absente n'est décrit comme passé.
La capacité Mac mini, son réseau et les autres gates OIDC/TLS/RLS/recovery restent
hors de cette passe. PR18 reste DRAFT et le travail s'arrête pour revue.
