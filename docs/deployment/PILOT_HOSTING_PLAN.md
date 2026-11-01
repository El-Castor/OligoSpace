# Plan préparatoire d’hébergement du pilote OligoSpace

Date initiale : 2026-10-31. Révision PR #16 : 2026-11-01.
Statut : **stratégie générale approuvée ; prérequis applicatifs à qualifier**.
Ce document est l’unique livrable hébergement de cette étape. Aucune installation,
connexion au Mac mini, modification réseau ou création de service de production
n’a été effectuée dans cette étape. Les informations historiques fournies par
l’utilisateur ne sont pas des vérifications actuelles réalisées par l’agent.

## 1. Architecture recommandée

Conserver l’architecture Compose de l’ADR-0005 : Caddy → Next.js/FastAPI,
PostgreSQL, Redis, worker/scheduler scientifiques, MinIO et Keycloak. Sur macOS,
les conteneurs Linux s’exécutent dans la VM du moteur Docker ; sur Linux ils
s’exécutent directement avec un moteur compatible Compose v2.

Deux projets Compose indépendants, `oligospace-dev` et `oligospace-pilot`, restent
la cible logique d’isolation, **sans présumer leur exécution simultanée** sur les
16 Go du Mac mini. Ils isolent les ressources applicatives mais partagent
le noyau de la VM, le disque, le moteur et les ressources de la machine : une
panne du Mac ou un redémarrage Docker interrompt les deux. Si une continuité forte
est requise pendant les mises à jour du moteur, prévoir deux hôtes ; cette
exigence ne peut pas être satisfaite par deux projets Compose seuls.

```text
MacBook WARP ── Cloudflare Zero Trust existant ── Mac mini
                                           │ entrée HTTPS pilote contrôlée
                                    Caddy pilote
                                     ├─ Next.js → API
                                     ├─ Keycloak OIDC
                                     └─ API → PostgreSQL / MinIO / Redis
                                                 ↑ worker + scheduler

Développeur local ── boucle locale ── Caddy dev → pile dev indépendante
Sauvegarde pilote chiffrée ── stockage hors hôte autorisé ── restauration de test
```

Seul le proxy pilote reçoit le trafic utilisateur, exclusivement depuis le réseau
privé retenu. Ne publier ni PostgreSQL, ni Redis, ni MinIO/sa console, ni les
interfaces administratives Keycloak. Prévoir un chemin administratif séparé,
autorisé aux seuls exploitants ; filtrer les routes d’administration au proxy,
pas uniquement les ports. Le réseau privé complète l’authentification OIDC et les
permissions de l’API ; il ne les remplace pas.

### Écart entre dépôt actuel et cible

`compose.yml` est une base de développement : images applicatives `latest`,
construction locale, seed déterministe, Keycloak `start-dev`, authentification de
développement par défaut et exposition du port proxy sans adresse de liaison.
**Ne pas le lancer tel quel comme pilote**, même avec un autre nom de projet.
Les fichiers pilote et les contrôles décrits ici restent à implémenter lors d’une
étape autorisée. L’isolation E2E existante (`compose.e2e.yml`) reste dédiée aux tests.

Prévoir une définition pilote explicite, validée et sans héritage involontaire de
ports, de seeds ou de montages du code dev. Une base commune plus des fichiers
dev/pilote est possible si leur configuration fusionnée est systématiquement
contrôlée. Le pilote n’utilise que `image:` avec des digests approuvés, sans
`build:` ni bind mount du dépôt. Le développement garde sa construction locale.

## 2. Prérequis à vérifier ultérieurement

| Domaine | Vérification avant mise en service |
|---|---|
| Matériel | Apple Silicon et 16 Go RAM, d’après l’utilisateur ; versions macOS/moteur, mémoire réellement disponible et état SSD à relever ultérieurement |
| Capacité | Mesurer charge macOS/autres comptes, VM, Keycloak, PostgreSQL et jobs ; aucune garantie de deux piles complètes parallèles ni de build local pendant le pilote |
| Disque | Environ 66 Gio libres historiquement, pas une mesure actuelle ; réserver données des autres utilisateurs, images/releases, objets, logs, builds et restauration avec marge approuvée |
| Énergie | Reprise après coupure, politique de veille, accès console, onduleur si requis |
| Logiciels | Moteur Docker compatible macOS/architecture, conditions de licence institutionnelles, Compose v2, build multiarchitecture sur une chaîne de construction adaptée |
| Accès | Cloudflare Zero Trust/WARP déjà déclarés ; politique applicative, MFA, révocation, droits d’administration et récupération hors bande à qualifier |
| Identité | Nom HTTPS stable, résolution depuis clients et conteneurs, realm et clients OIDC, administrateurs et comptes scientifiques réels |
| Sauvegarde | Destination distincte du Mac, clés de chiffrement récupérables séparément, autorisations de transfert INRAE, rétention et RPO/RTO approuvés |
| Linux cible | Architecture, stockage, versions Docker/Compose, règles INRAE pour VPN, DNS, PKI, SSO, flux sortants et sauvegardes |

Les caractéristiques historiques sont fournies par l’utilisateur, sans audit du
Mac mini. Avant tout lancement futur : mesurer consommation au repos/pic, pression
mémoire/swap, espace réellement libre et croissance (données, logs, cache, images,
sauvegarde/restauration). Définir plafonds et marge avec l’exploitant, puis tester
une pile pilote seule avant toute coexistence. Si la marge est insuffisante :
développement/tests sur le poste actuel ou une autre cible autorisée, builds hors
Mac mini, ou arrêt planifié de la pile dev ; jamais arrêt improvisé du pilote ni
nettoyage des données des autres comptes. Les deux projets ne garantissent aucune
réservation matérielle. Aucun seuil non mesuré n’est présenté comme validé.
Aucun prérequis d’hébergement ne conditionne les tests fonctionnels R1 locaux.

## 3. Configuration future du Mac mini

À exécuter seulement lorsque la machine sera disponible et que la configuration
sera autorisée :

1. Vérifier les prérequis ci-dessus et les règles de l’établissement ; consigner
   les versions réellement retenues et le responsable de l’exploitation.
2. Préparer un compte d’exploitation et un répertoire pilote protégé, distinct du
   checkout de développement. Prévoir le démarrage du moteur et des services
   après reboot macOS ; vérifier le comportement réel après coupure/redémarrage.
3. Vérifier le moteur Docker et l’accès Cloudflare existant avant toute éventuelle
   configuration explicitement autorisée ; ne pas remplacer le tunnel. Fixer les
   plafonds CPU/mémoire de la VM pour préserver macOS ; limiter ensuite les jobs
   concurrents et les ressources des services de développement.
4. Préparer les deux configurations Compose, les secrets séparés, les répertoires
   d’exploitation et un manifeste de release immuable. Contrôler sans les afficher
   les configurations résolues : noms, ports, images, réseaux, volumes et variables.
5. Restaurer des données de recette autorisées dans une pile isolée ; qualifier
   OIDC/TLS, les permissions, les jobs et une restauration complète avant le pilote.
6. Déployer une release testée, migrer explicitement via l’image API de cette
   release et initialiser uniquement les références/comptes approuvés. Le seed dev
   ne doit jamais créer les identités publiques de démonstration dans le pilote.

### Images et portabilité ARM64 / AMD64

Construire API, web et worker depuis un commit précis ; publier des manifests OCI
`linux/arm64` et `linux/amd64` sous une version et un identifiant Git immuables.
Worker et scheduler emploient exactement le même digest ; migration et API aussi.
Conserver le digest de l’index multiarchitecture et ceux des images par plateforme,
les versions PostgreSQL/Keycloak/MinIO et `OLIGOSPACE_BUILD_ID` dans le manifeste.
Ne jamais écraser les tags d’une release ; déployer par digest.

Le Dockerfile worker sélectionne déjà BLAST+ selon `TARGETARCH` et compile
Primer3 2.6.1. Cela ne prouve pas la qualification de toute la pile sur les deux
architectures. Vérifier les manifests des images tierces, la résolution des
environnements Conda, puis construire et tester nativement chaque architecture
(tests PostgreSQL, E2E et résultats Primer3 avec provenance). Une émulation peut
aider à construire, mais ne constitue pas la recette de performance ARM64.
Ne pas recalculer silencieusement les résultats scientifiques pendant une migration.

## 4. Accès distant privé, HTTPS et Keycloak

### Infrastructure déclarée et frontières distinctes

L’utilisateur indique : tunnel Cloudflare `mac-mini-maison`, annoncé Healthy lors
de vérifications antérieures, route privée `192.168.1.31/32`, client WARP sur
MacBook et SSH distant testé avec succès. **Pas de vérification actuelle ici.**
Cloudflare Zero Trust est le point de départ existant à qualifier pour
l’application ; le succès SSH ou l’état du tunnel ne qualifie pas HTTPS/OIDC.

| Couche | Ce qui est déclaré / ce qui reste à prouver |
|---|---|
| SSH d’administration | Test historique réussi ; compte, clés, restrictions et récupération à revérifier lors d’une opération autorisée |
| Réseau privé Cloudflare/WARP | Route hôte /32 déclarée ; règles effectives, identité/appareil, ports autorisés et refus hors périmètre à tester |
| Proxy HTTPS applicatif | Nom DNS, liaison de Caddy, terminaison/renouvellement TLS et en-têtes de confiance non qualifiés |
| Authentification applicative OIDC | Keycloak, sessions et autorisations API séparés de WARP/SSH ; aucune confiance implicite dans l’accès réseau |

La route /32 n’est pas une politique de ports. Prévoir une entrée Caddy privée,
aucun port applicatif interne ou console accessible au client WARP ; vérifier
également les chemins LAN directs et les routes d’administration. Un hostname
public Cloudflare ou une exposition publique n’est ni demandé ni supposé.
La liaison Docker à une interface privée et le chemin VM→issuer doivent être
qualifiés sur la cible, sans présumer que WARP sur le MacBook donne un accès
équivalent aux conteneurs. Si TLS termine en amont de Caddy, fixer un relais de
confiance et vérifier le schéma transmis ; aucun en-tête client arbitraire ne doit
définir l’origine de confiance.

Vérifications futures, sans modifier le réseau à cette étape :

- résolution du même nom canonique depuis MacBook WARP, hôte et conteneurs
  API/web ; issuer, discovery/JWKS et token endpoint joignables avec chaîne TLS
  valide, sans réécriture du `iss` ;
- certificat, SNI, renouvellement, origine/callbacks/logout/CORS cohérents ;
- tests négatifs hors WARP, appareil ou identité non autorisés, LAN direct et
  ports internes ; conserver les règles réellement appliquées comme preuve ;
- révoquer identité/appareil ou autorisation de route et tester connexion nouvelle
  **et session déjà ouverte**, puis révoquer le compte OIDC séparément ;
- récupération administrative hors bande sans rétablir un bypass applicatif.

Tailscale reste une alternative à discuter si nécessaire, soumise à décision et
politique institutionnelle ; il n’est ni installé par cette étape, ni prérequis,
ni remplacement automatique de Cloudflare. Tout changement de tunnel est hors
périmètre. Pour Linux INRAE, choisir l’accès privé institutionnel approuvé sans
présumer l’acceptation de Cloudflare ou de Tailscale.

La PKI et le nom privé restent à approuver. Prévoir le renouvellement et la distribution
de la chaîne de confiance aux postes **et aux conteneurs**. Les noms de certificats
publics peuvent être publiés dans les journaux de transparence : faire approuver
le nom choisi. La procédure exacte dépendra du DNS et de la PKI disponibles.

Utiliser la même origine canonique HTTPS pour `APP_ORIGIN`, `NEXTAUTH_URL`, les
redirect/logout URIs Keycloak et l’issuer OIDC ; fixer l’audience API et CORS à
cette configuration. L’API et le web doivent joindre discovery/JWKS et le token
endpoint depuis leurs réseaux Docker : tester cette résolution et cette confiance
TLS, sans substituer un issuer interne différent du `iss` des jetons.

Keycloak utilise son mode de production, sa base persistante et ses credentials
dédiés. Fixer `ENVIRONMENT=production` et le mode OIDC supporté par l’application,
jamais `AUTH_MODE=development`. Supprimer les comptes/mots de passe de démo de
l’import realm pilote, restreindre l’administration et tester MFA, PKCE, refresh,
logout, expiration et désactivation. Vérifier les cookies Secure/HttpOnly/SameSite
au navigateur. Cette qualification n’a pas encore été exécutée.

## 5. Isolation et exploitation des deux environnements

| Ressource | Développement | Pilote |
|---|---|---|
| Projet Compose explicite | `oligospace-dev` | `oligospace-pilot` |
| Code/images | Checkout, builds locaux | Release figée, images par digest |
| Configuration | Fichier dev dédié | Fichier pilote protégé hors Git |
| PostgreSQL | Instance et credentials dev | Instance et credentials pilote ; DB applicative et DB Keycloak, rôles distincts |
| Redis | Instance/volume dev | Instance/volume pilote ; réseau privé |
| MinIO | Instance/objets dev | Instance, credentials et volume pilote |
| Réseaux/volumes | Préfixés par projet | Préfixés par projet, aucun volume externe partagé |
| Ingress | Port distinct lié à localhost | Entrée privée HTTPS qualifiée |
| Keycloak/session | Realm/clients/secrets dev | Realm/clients/secrets/cookies origine pilote |
| Sauvegarde | Données jetables | Sauvegardes chiffrées hors hôte et essais de restauration |

Éviter `container_name`, les volumes avec `name:` global fixe et les réseaux
externes communs. Passer systématiquement un nom de projet, un fichier Compose et
un fichier d’environnement explicites dans le futur lanceur de déploiement ; ne
pas dépendre du répertoire courant ni du `.env` dev. Les alias DNS restent internes
à chaque réseau. Ne jamais lancer `down --volumes`, `docker system prune --volumes`
ou une migration dev sur le pilote. Les tests E2E gardent leur troisième projet
jetable et leurs placeholders, sans credentials pilote.

Le pilote doit rester stable pendant les modifications du code et les builds dev :
aucun bind mount de code, aucune référence `latest`, aucune recréation automatique
sur changement Git. Limiter CPU, mémoire et concurrence dev ; réserver de l’espace
disque et limiter la rotation des logs. Qualifier cette coexistence sous charge.
Les mises à jour du moteur/VM restent des maintenances communes planifiées.

### Contrôle préalable du stockage objet (référence actuelle, non changée)

**Décision DEPLOY-02 du 2026-11-01 :** stockage open source, gratuit, maintenu,
sans licence commerciale ni activation. SeaweedFS est prioritaire, Garage second ;
MinIO historique reste une référence de compatibilité. AIStor est exclu du choix
d’architecture, ce qui remplace les options exploratoires historiques ci-dessous.
La matrice et la recommandation provisoire sont dans
[ADR-0007](../decisions/ADR-0007-pilot-object-storage-gate.md), les preuves dans
[DEPLOY-02](DEPLOY_02_STORAGE_RELEASE_IMAGES.md). Les manifests ARM64/AMD64 des
deux candidats sont vérifiés ; exécution SDK, restauration et consommation restent
bloquées faute de moteur local disponible. Aucun fournisseur final n’est choisi ;
le Compose pilote, les objets et les réseaux restent inchangés.

`compose.yml` référence exactement
`minio/minio:RELEASE.2025-09-07T16-13-09Z`, sans digest. L’intégration existante
utilise le SDK Python MinIO (`services/object_storage.py`) : test/création de
bucket et `put_object` avec clé et content-type. Les objets existants et leurs
checksums restent à conserver même avec les uploads désactivés. S3 compatible ne
prouve ni compatibilité de format disque ni restauration interchangeable.

Consultations **publiques uniquement**, 2026-11-01, sans Docker/pull/exécution :

| Contrôle | Résultat / limite |
|---|---|
| Source exacte | [Tag GitHub](https://api.github.com/repos/minio/minio/git/ref/tags/RELEASE.2025-09-07T16-13-09Z) présent ; tag annoté `01ce918d8279a20e4706b96a64396146894adee4`, [commit](https://github.com/minio/minio/commit/07c3a429bfed433e49018cb0f78a52145d4bedeb) `07c3a429bfed433e49018cb0f78a52145d4bedeb` |
| Image publiquement accessible | [API Docker Hub du tag](https://hub.docker.com/v2/repositories/minio/minio/tags/RELEASE.2025-09-07T16-13-09Z) : HTTP 404 ; registre Docker Hub avec jeton anonyme de lecture : HTTP 401 ; [API Quay du tag](https://quay.io/api/v1/repository/minio/minio/tag/?specificTag=RELEASE.2025-09-07T16-13-09Z) : HTTP 401. Cela ne démontre pas une disparition universelle ; disponibilité publique non confirmée |
| ARM64 et digest image | Manifest non obtenu : ni digest index/ARM64/AMD64 ni disponibilité d’un binaire ARM64 de ce tag prouvés. Ne pas inventer de digest ou utiliser `latest` en remplacement |
| Maintenance | [Dépôt officiel](https://github.com/minio/minio) annoncé non maintenu et archivé ; README actuel décrit distribution source et anciens binaires non maintenus. Aucune promesse de correctifs pour l’image référencée |
| S3 et persistance | Tests historiques avec MinIO, pas qualification d’un nouvel artefact ; recette upload autorisé en test, clé/contenu/content-type/checksum, restart et restauration d’objets/quarantaine encore requise pour l’image choisie |

Avant toute release : obtenir l’artefact depuis une source autorisée, enregistrer
version/digests/provenance, manifests ARM64/AMD64, scans et responsable de
maintenance ; qualifier l’API existante et la restauration d’un jeu d’objets.
**Bloquant avant pilote tant que cet artefact et sa maintenance ne sont pas
acceptés.** Les tests historiques ou un cache local ne prouvent pas sa future
disponibilité reproductible. Aucun cache/image local n’a été inspecté ici.

Options historiques explorées avant la décision open source ci-dessus,
**pas des candidats retenus ni des remplacements qualifiés** :

- Source exacte MinIO disponible : envisager une construction contrôlée et un
  registre approuvé après autorisation. Responsabilité interne de maintenance,
  dépendances/compilation ARM64, scans et recette complète. Le [Dockerfile du tag](https://github.com/minio/minio/blob/07c3a429bfed433e49018cb0f78a52145d4bedeb/Dockerfile)
  part lui-même de `minio/minio:latest` : il ne résout pas seul le problème et ne
  doit pas être repris comme recette reproductible.
- [AIStor](https://www.min.io/product/aistor), proposé par l’éditeur : existence
  d’une offre S3 vérifiée ; licence, distribution, support ARM64, digest, coût et
  compatibilité des données non validés ici. Adoption uniquement par décision
  explicite avec recette de migration/retour, jamais substitution du tag.
- Un miroir ou une archive institutionnelle du même artefact ne serait admissible
  qu’avec provenance/digest et maintenance établis ; aucune telle archive n’est
  actuellement identifiée. Ce n’est pas une option réputée disponible.

Si aucune option n’est acceptée, conserver le blocage ; pas de migration implicite
vers un autre fournisseur S3, pas de conversion de volume ni suppression d’objets.

### Fourniture et rotation des secrets

Conserver des credentials différents entre environnements et entre services :
PostgreSQL applicatif, migration, worker à privilèges réduits, Keycloak, MinIO,
client OIDC, session NextAuth, sauvegardes. Préférer des fichiers montés en lecture
seule via Compose secrets, issus d’un gestionnaire de secrets approuvé. Compose
secrets ne chiffre pas ces fichiers sur l’hôte : permissions et chiffrement du
disque restent nécessaires. L’application doit d’abord acquérir le support de
lecture de ces fichiers ; ne pas supposer un support universel des suffixes `_FILE`.

En transition, si des variables sont nécessaires, fichier hors Git limité au
compte d’exploitation ; ne pas afficher `compose config` résolu dans les logs,
ni archiver `docker inspect` contenant des secrets. Stocker séparément les clés de
restauration, définir rotation/révocation et procédure de récupération. Aucun
secret réel ni fichier d’environnement pilote n’est livré avec ce plan.

### Sauvegarde, restauration et releases

`docs/BACKUP_RESTORE.md` décrit les objectifs et les modes INRAE. Le script actuel
de sauvegarde PostgreSQL et le scaffold de restauration ne constituent pas une
sauvegarde complète de cette cible. Prévoir :

- dump logique PostgreSQL applicatif **et Keycloak**, rôles/droits nécessaires,
  objets MinIO et métadonnées/versioning, configuration non secrète et manifeste
  de release ; sauvegarde séparée des secrets selon la politique approuvée ;
- point cohérent : suspendre les nouvelles écritures/uploads/soumissions, terminer
  ou stabiliser les jobs, arrêter worker/scheduler avant la capture finale ;
- chiffrement, manifeste de sommes SHA-256 et vérification d’intégrité/authenticité,
  copie hors hôte, rétention et alertes d’échec ; un volume local `backup_data`
  seul ne protège pas contre la perte du Mac ;
- Redis traité comme transport, pas comme source de vérité scientifique : restaurer
  PostgreSQL puis redémarrer la réconciliation sans rejouer une file obsolète ;
- restauration sur volumes vides dans un projet jetable, accès OIDC, comptages,
  UUID/IDs publics, audits, checksums objets, jobs/résultats/provenance, mesure du
  RPO/RTO et rapport avant ouverture du pilote. Les pièces jointes restent privées
  et en quarantaine sans circuit de téléchargement tant que celui-ci n’existe pas.

Point de départ proposé : sauvegarde quotidienne, conservation 30 quotidiennes /
12 mensuelles et test trimestriel, à faire approuver selon les données réelles.
Le WAL/pgBackRest pour PITR est une mise en œuvre ultérieure à qualifier, pas une
capacité revendiquée aujourd’hui.

Avant chaque **mise à jour d’une installation existante** : checks R1, backup vérifié, capture du manifeste courant,
fenêtre de maintenance, migrations explicites, santé et recette. Un rollback
d’image n’annule pas une migration de schéma : n’utiliser l’ancienne image que si
la compatibilité est prouvée ; sinon restaurer l’ensemble cohérent sous maintenance
et documenter les écritures perdues depuis le point de restauration.

## 6. Migration future vers Linux INRAE

1. Faire approuver la cible Linux, les règles réseau, DNS/TLS/SSO et la destination
   de sauvegarde. L’accès Cloudflare existant et l’alternative Tailscale restent
   conditionnés à la politique INRAE ; sinon utiliser le VPN ou l’accès privé
   institutionnel sans publier l’application.
2. Préparer le moteur et les définitions Compose portables ; tirer les mêmes
   digests de release pour l’architecture cible. Commencer avec les mêmes versions
   de services et le même schéma, sans cumuler migration d’hôte et upgrade majeur.
3. Répéter la restauration hors service sur Linux : dumps PostgreSQL et Keycloak,
   restauration des objets avec leurs clés/métadonnées, secrets et issuer maîtrisés.
   Ne pas copier les répertoires bruts PostgreSQL d’une VM macOS vers Linux :
   privilégier dump/restore logique. Préserver IDs, audits et provenance des jobs.
4. Qualifier le login et les permissions, les checksums, les résultats scientifiques
   existants, une nouvelle analyse Primer3 et le dispositif de sauvegarde Linux.
   Si le nom/issuer change, actualiser clients, callbacks et configuration API/web
   ensemble, puis imposer une réauthentification ; tester d’abord ce changement.
5. Geler les écritures sur le Mac, drainer/stabiliser les jobs, arrêter le scheduler
   et les workers source, capturer le backup final cohérent et le restaurer sur
   Linux. Ne jamais faire fonctionner deux instances écrivaines sur des copies
   divergentes. Comparer comptages, identifiants et checksums avant bascule.
6. Basculer l’accès privé/DNS à la cible approuvée, effectuer la recette scientifique
   et mesurer l’interruption. Garder le Mac arrêté ou en lecture seule pendant la
   fenêtre de retour arrière ; fixer un responsable et un délai de validation.
7. En cas d’échec avant réouverture des écritures, rétablir la source inchangée.
   Après écritures sur Linux, un retour exige une nouvelle capture cohérente vers
   le Mac et une procédure de schéma compatible : ne pas revenir à une ancienne
   copie en perdant silencieusement des données. Décommissionner la source après
   validation et confirmation des sauvegardes/rétentions.

## 7. Checklist à exécuter lorsque le Mac sera disponible

- [ ] Disponibilité et autorisation de configuration du Mac confirmées.
- [ ] CPU/RAM/disque, veille, redémarrage et moteur Docker qualifiés.
- [ ] Politique institutionnelle, accès privé, administrateurs et MFA approuvés.
- [ ] Nom HTTPS, renouvellement TLS et résolution clients/conteneurs validés.
- [ ] Manifests/images ARM64 et AMD64 construits, testés et figés par digest.
- [ ] Source/version/digest MinIO, disponibilité ARM64, maintenance et restauration des objets acceptés (§5).
- [ ] Configurations dev/pilote résolues contrôlées, volumes/réseaux/ports distincts.
- [ ] Aucun seed de démo, auth dev, build local ou montage du code dans le pilote.
- [ ] Secrets et rôles de service séparés, rotation/récupération testables.
- [ ] Keycloak production, callbacks, issuer/audience, cookies et lifecycle validés.
- [ ] Accès hors périmètre Cloudflare/WARP refusé, révocation testée ; consoles et endpoints d’administration restreints.
- [ ] Migrations et données curées autorisées ; aucune importation Excel implicite.
- [ ] Format/lint/typecheck/unitaires, PostgreSQL et E2E validés pour la release.
- [ ] Marge RAM/disque mesurée sur les 16 Go et le disque réel, données des autres comptes préservées ; coexistence autorisée seulement si mesurée viable.
- [ ] Backup complet chiffré hors hôte restauré sur une instance vide ; RPO/RTO mesurés.
- [ ] Réconciliation des jobs et intégrité des objets/audits/provenances contrôlées.
- [ ] Recette scientifique humaine, responsable, fenêtre de maintenance et rollback définis.
- [ ] Répétition Linux et règles INRAE planifiées avant la migration réelle.
- [ ] Gates SECURITY.md (§9) prouvés ou dérogation habilitée explicitement acceptée ; aucun report tacite.

Toutes les cases restent à exécuter. Aucun déploiement n’est attesté par ce document.

## 8. Plan de déploiement reproductible — préparation après UI-06

Ajout du 2026-11-01, **à revoir avant toute implémentation**. La référence
applicative intégrée est `9852bdd704dc2658dd2941eeae8adb56f8ddc759` (PR #15).
Le [dossier de qualification MVP](../project/MVP_QUALIFICATION_AUDIT.md) sépare
les preuves acquises des recettes R1-08 à R1-11. Les sections précédentes restent
la référence d'architecture ; cette section précise les livrables et l'ordre des
opérations futures. Aucun fichier Compose pilote, script, workflow de publication,
secret, installation ou service supplémentaire n'est créé par cette préparation.

### 8.1 Choix retenu pour la proposition

Préférer un fichier Compose pilote autonome et validé à une superposition directe
sur `compose.yml` : le risque d'hériter de `build:`, du seed de démo, des ports et
du mode `start-dev` y est moindre. Une base commune pourra être extraite dans un
lot séparé si elle conserve les contrôles de configuration fusionnée. Le pilote
reste un déploiement Compose simple, conforme à l'ADR-0005 ; aucune orchestration
nouvelle. Ce choix est une proposition à approuver, pas une configuration livrée.

Le premier pilote devrait utiliser un Keycloak en mode production avec comptes
réels autorisés ; la fédération institutionnelle dépend de ses entrées propres.
Ne jamais contourner une absence d'IdP en exposant le bypass de développement.

### 8.2 Entrées obligatoires et manifeste de release

Avant de fabriquer une release, obtenir : hôte autorisé/architecture réelle,
nom HTTPS et PKI, politique d'accès privé, realm/client OIDC et audience,
responsables, coffre à secrets, destination de sauvegarde et RPO/RTO approuvés.
Si une entrée manque, noter « bloqué, entrée non fournie » ; ne pas inventer de
nom de serveur, de compte, de certificat ou de secret de production.

Le futur manifeste versionné non secret devra contenir :

| Champ | Contenu vérifiable |
|---|---|
| Sources | SHA complet, version de release immuable, arbre propre, checksum des définitions de déploiement |
| Images applicatives | Référence du registre et digest OCI index + digest ARM64/AMD64 API/web/worker ; migration = image API, scheduler = image worker |
| Dépendances | Digests et versions PostgreSQL/Redis/Keycloak/MinIO/Caddy ; versions Docker/Compose et plateforme qualifiée |
| Science | Primer3 effectif, version/build worker, paramètres et résultats de qualification ; `OLIGOSPACE_BUILD_ID` explicite |
| Données | Révision Alembic source/cible, index/checksums des objets et références présentes ; mise à jour : backup pré-release ; installation vierge : absence d’antécédent consignée, backup initial après création puis restauration avant ouverture |
| Configuration | Origine/issuer/audience, projet Compose, version des paramètres non secrets et références aux versions des secrets, jamais leurs valeurs |
| Validation | Liens CI du SHA exact, rapports PostgreSQL/Chromium et ARM64/AMD64, recette humaine, date et approbateurs |
| Retour arrière | Mise à jour : release précédente et compatibilité de schéma ou backup cohérent ; installation vierge : aucune release précédente, maintien fermé/diagnostic conservant les données ; responsable et fenêtre |

Déployer un digest permet de reproduire l'artefact exécuté ; cela ne démontre pas
une reconstruction bit à bit. Les environnements/dépendances actuels doivent être
inventoriés et contrôlés, sans promettre des verrous transitifs déjà complets.
Un changement de digest ou de configuration après recette invalide l'approbation
du paquet précédent et demande une nouvelle vérification ciblée.

### 8.3 Lots préparatoires proposés, uniquement après revue

| Ordre | Livrable à produire ultérieurement | Critère de validation indépendant |
|---|---|---|
| 1 | Définition pilote dédiée sous `infra/`, configurations non secrètes et contrat des paramètres ; pas de modification métier | `config --quiet`, puis inspection contrôlée sans journaliser les secrets : zéro build/code monté/seed dev, images par digest, ingress privé, réseaux/volumes distincts, auth OIDC/production et uploads off |
| 2 | Chaîne de construction/publication immuable et manifeste | Tests existants sur chaque architecture retenue, version effective Primer3, image API identique à migrate et worker identique à scheduler ; aucun tag écrasé |
| 3 | Rôles de services et fourniture des secrets compatibles avec les applications | Connexions avec privilèges nécessaires seulement ; aucun credential dev/bootstrap conservé ; rotation/récupération répétable, aucune supposition `_FILE` non implémentée |
| 4 | Procédure outillée de backup/restore complète R1-08 | Backup chiffré hors hôte, checksum et authenticité, restauration app + identité + objets sur cible vide, intégrité et RPO/RTO acceptés |
| 5 | Recette R1-09 et isolation dev/pilote sur hôte disponible | TLS/OIDC privé, services internes non exposés, pilote seul sous QC avec marge ; coexistence avec build dev seulement si retenue et mesurée viable, sinon builds déportés ; reboot/restauration testés |
| 6 | Données R1-10 et PV R1-11 puis décision d'ouverture | Sources approuvées, permissions/CSV/historique/science vérifiés par les responsables ; décision go/no-go explicite |

Chaque futur lot conserve sa branche, ses tests, sa PR et la revue adaptée. Les
chemins/artefacts nouveaux de ce tableau sont des livrables attendus, pas des
scripts existants utilisables aujourd'hui. Ne pas exécuter `make dev`, `make seed`,
`make migrate` ou `make backup` comme raccourcis pilote : ces cibles utilisent
actuellement la configuration de développement implicite.

### 8.4 Deux procédures distinctes à qualifier

Préconditions communes : manifeste/images approuvés et préchargés par digest,
contexte moteur/projet/chemins de configuration explicites, gates de sécurité §9,
source de stockage objet acceptée et marge matérielle mesurée. Aucun démarrage ou
changement n'est réalisé dans cette PR. Un seul ordonnanceur et une seule
migration ; jamais de seed/comptes de démonstration.

#### A. Installation vierge — aucune release ni sauvegarde antérieure supposée

1. Vérifier identité de la cible, volumes vides autorisés, permissions, secrets et
   budget RAM/disque ; arrêter si un volume contient des données non identifiées.
   Ne pas initialiser ni nettoyer les fichiers d'autres utilisateurs.
2. Démarrer PostgreSQL et les dépendances nécessaires au bootstrap autorisé
   (Redis/stockage selon la configuration retenue), sans API ouverte aux utilisateurs.
3. Vérifier disponibilité réelle via le compte de bootstrap autorisé et persistance
   des dépendances. Ne pas exiger des comptes applicatifs encore inexistants.
4. Initialiser uniquement bases/rôles autorisés (application et Keycloak distincts),
   propriétaires et droits, puis vérifier les connexions et droits des comptes de
   service avant migration. Ne pas traiter une base existante comme vierge.
5. Exécuter les migrations applicatives **une seule fois** via l'image API retenue
   et le rôle de migration ; attendre le succès et vérifier la révision Alembic.
6. Initialiser l'identité réelle et les références approuvées : démarrer/configurer
   Keycloak production contre sa base prête (évolution interne de schéma gérée par
   la version Keycloak qualifiée), sans comptes de démo. Bootstrap des seules
   données autorisées, provenance conservée ; aucune importation Excel implicite.
7. Démarrer les services applicatifs, puis un scheduler et les workers autorisés,
   après leurs dépendances et migrations ; garder l'entrée utilisateurs fermée.
8. Effectuer la recette R1-09/10/11 et la sauvegarde initiale **après création des
   données**, puis sa restauration isolée R1-08. Ouvrir seulement après toutes les
   preuves/gates acceptées. En cas d'échec du bootstrap, maintenir fermé et
   diagnostiquer sans détruire les volumes ; il n'existe pas de release précédente
   à restaurer. Le premier backup ne remplace pas une recette de restauration.

#### B. Mise à jour — installation existante et santé vérifiée

1. Précharger les images par digest et vérifier manifeste/version précédente,
   intégrité, compatibilité de schéma et procédure de retour arrière qualifiée.
2. Stabiliser les écritures et les jobs sous maintenance qualifiée : fermer les
   nouvelles écritures, drainer/consigner les jobs, arrêter scheduler/workers.
   Stabiliser aussi les mutations Keycloak/objets pour la capture cohérente ; aucun
   mode maintenance applicatif nouveau n'est supposé déjà livré.
3. Vérifier santé et disponibilité des bases existantes, droits et révisions, et
   état du stockage objet ; PostgreSQL reste disponible pour backup et migration.
   En cas d'anomalie, arrêter la mise à jour et conserver les preuves.
4. Réaliser la sauvegarde cohérente application **et Keycloak**, objets,
   configuration et secrets récupérables séparément ; vérifier intégrité et copie
   hors hôte. Conserver le manifeste précédent et la preuve de restauration.
5. Exécuter la migration applicative unique avec l'image API et le rôle dédiés,
   sans seed ni migration concurrente. Si une évolution Keycloak est nécessaire,
   respecter sa procédure/version validée et le backup de sa base ; pas d'upgrade
   majeur implicite. Échec : rester fermé et appliquer le retour arrière revu,
   jamais de downgrade automatique.
6. Démarrer la nouvelle version avec dépendances prêtes et schéma vérifié, un
   scheduler et les workers autorisés. Après **restauration**, ne pas rejouer une
   ancienne file Redis ; la réconciliation s'appuie sur PostgreSQL.
7. Vérifier santé et parcours OIDC, rôles/scopes/révocation, persistance après
   reload, nouveau QC/paire de recette, refus uploads et CSV parsé. Ouvrir après
   PV et décision nominative, sinon revenir aux images précédentes uniquement si
   le schéma est compatible ; à défaut restaurer le paquet cohérent. Quantifier
   les écritures perdues depuis backup et les faire accepter, jamais les masquer.

Dans les deux procédures : données de recette identifiées/autorisées, contrôles
IDs/audits/provenance et absence de doublon, surveillance et récupération des accès
qualifiées. Commandes futures toujours avec contexte/projet/Compose/env explicites.
Aucun `down --volumes`, prune, reset de base ou suppression de données ici.

### 8.5 Répétition, portabilité et go/no-go

Répéter d'abord l'installation à blanc et la restauration dans une pile isolée
autorisée ; conserver les résultats et durées. Qualifier ARM64 et AMD64 avec les
mêmes fixtures scientifiques, paramètres et unités ; documenter les écarts bruts
et leurs tolérances justifiées avant validation, sans réécrire les anciens résultats.
La migration Linux suit §6 : mêmes versions initiales, dump/restore logique,
contrôle OIDC, un seul écrivain et bascule privée autorisée.

**No-go** si auth dev, seed/comptes de démo, exposition réseau imprévue, backup
non restauré, résultat scientifique divergent inexpliqué, permission contournée,
configuration non versionnée ou absence d'approbation scientifique/exploitation.
R1-08/09/10/11 restent ouverts jusqu'à leurs preuves respectives. Prochaine étape :
revue de ce plan et choix explicite du premier lot à autoriser, sans exécution
automatique à la suite de UI-06.

## 9. Matrice des gates de sécurité — avant ouverture, décision traçable

Référence normative : [SECURITY.md](../SECURITY.md), sections Identity and
authorization, Deployment controls, Scientific worker controls, Remaining
hardening. La stratégie générale est approuvée ; cela ne vaut **aucun report
d’exigence de sécurité**. La qualification doit nommer responsable, date, preuve,
portée et décision. Un résultat réseau/SSH historique ne vaut pas preuve OIDC.

Deux dimensions distinctes : **preuve** = prouvé (rapport précis, périmètre/date)
ou non vérifié ; **décision** = bloquant avant ouverture, report demandé ou report
explicitement accepté. Ce dernier exige approbateur habilité, justification,
mesures compensatoires, échéance et déclencheur de réexamen. Sans ces éléments,
le gate demeure bloquant. Aucun report demandé/accepté n’est enregistré par cette
PR ; une demande éventuelle ne constitue pas une acceptation. Les preuves
fonctionnelles héritées ne changent pas le statut des gates d’exploitation.

| Gate / référence SECURITY.md | Preuve disponible et statut | Preuve future requise / décision actuelle |
|---|---|---|
| Modèle de menace — Remaining hardening | Non vérifié pour la topologie Cloudflare/VM/Compose | Flux, actifs, acteurs, frontières de confiance et risques résiduels revus ; bloquant |
| MFA et cycle de vie — Identity, Remaining hardening | Tests locaux RBAC/compte désactivé prouvés dans leur contexte ; politique réelle non vérifiée | Enrôlement/MFA, récupération, désactivation et révocation des sessions/appareils Cloudflare et OIDC testés séparément ; bloquant |
| OIDC réel — Identity | Implémenté et tests dev hérités ; parcours réel non vérifié | PKCE, issuer/audience/signature/expiration, refresh/logout et refus auth dev validés sur l’origine retenue ; bloquant |
| TLS et origine — Deployment controls | Builds/proxy dev prouvés ; HTTPS applicatif non vérifié | DNS hôte/client/conteneurs, certificat/chaîne/renouvellement, callbacks, cookies/CORS et relais de confiance ; bloquant |
| Secrets — Deployment controls, Remaining hardening | Pas de secret ajouté au diff ; rotation réelle non vérifiée | Versions hors Git, suppression bootstrap, accès restreint, rotation et récupération des clés/sessions testées sans logs sensibles ; bloquant |
| Privilèges minimaux — Scientific worker controls | Credential worker partagé observé dans Compose dev ; cible non qualifiée | Rôles application/migration/worker/Keycloak/objets distincts et tests de refus des droits excessifs ; bloquant |
| Scans images/dépendances — Remaining hardening | Non vérifié pour la release retenue ; CI build ≠ scan | Rapports datés par digest et dépendances, triage des vulnérabilités et décision sur risques résiduels par responsable ; bloquant |
| RLS — Remaining hardening | Non livré comme défense en profondeur ; politique applicative testée | Décider mise en œuvre qualifiée ou demander un report argumenté/compensé et daté ; **aucun report accepté**, reste bloquant sans décision explicite |
| Réponse à incident — Remaining hardening | Runbook/exercice opérationnel non vérifié | Responsables/contact, confinement sans perte, révocation des accès, préservation logs/audit, communication et exercice documentés ; bloquant |
| Restauration et récupération des accès — Remaining hardening | Scripts partiels ; restauration complète et accès d’urgence non vérifiés | App/Keycloak/objets restaurés, secrets récupérables séparément, accès hors bande et RPO/RTO mesurés/acceptés ; bloquant |
| Isolation/refus hors périmètre — Deployment controls | SSH et route WARP historiques déclarés ; isolation applicative non vérifiée | Refus WARP non autorisé/hors WARP/LAN/ports internes, consoles privées, isolation dev/pilote et révocation effective ; bloquant |

L’ouverture exige chaque gate prouvé dans sa portée ou un report explicitement
accepté lorsque la politique permet une telle dérogation. Aucune dérogation ne
peut être inventée pour autoriser auth développement à distance, exposition
inattendue ou perte de données. Les exigences que le responsable ne peut pas
déroger doivent être réalisées. Cette matrice prépare la revue ; elle ne change
ni SECURITY.md, ni les politiques ni les composants de sécurité.
