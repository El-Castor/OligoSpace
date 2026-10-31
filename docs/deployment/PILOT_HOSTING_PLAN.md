# Plan préparatoire d’hébergement du pilote OligoSpace

Date : 2026-10-31. Statut : **proposition à qualifier sur les futurs hôtes**.
Ce document est l’unique livrable hébergement de cette étape. Aucune installation,
connexion au Mac mini, modification réseau ou création de service de production
n’a été effectuée. Le développement R1 continue indépendamment de sa disponibilité.

## 1. Architecture recommandée

Conserver l’architecture Compose de l’ADR-0005 : Caddy → Next.js/FastAPI,
PostgreSQL, Redis, worker/scheduler scientifiques, MinIO et Keycloak. Sur macOS,
les conteneurs Linux s’exécutent dans la VM du moteur Docker ; sur Linux ils
s’exécutent directement avec un moteur compatible Compose v2.

Deux projets Compose indépendants, `oligospace-dev` et `oligospace-pilot`, sur un
même moteur sont proposés. Ils isolent les ressources applicatives mais partagent
le noyau de la VM, le disque, le moteur et les ressources de la machine : une
panne du Mac ou un redémarrage Docker interrompt les deux. Si une continuité forte
est requise pendant les mises à jour du moteur, prévoir deux hôtes ; cette
exigence ne peut pas être satisfaite par deux projets Compose seuls.

```text
Poste autorisé ── réseau privé Tailscale ── Mac mini
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
pas uniquement les ports. Tailscale complète l’authentification OIDC et les
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
| Matériel | Modèle/CPU réel ARM64 ou Intel, mémoire disponible, espace et état du SSD, support macOS maintenu |
| Capacité | Budget initial proposé : 16 Go de RAM minimum à évaluer, 32 Go préférables pour deux piles et des builds ; valider par mesure avec Keycloak et jobs réels |
| Disque | Réserver les données, objets, images de deux versions, espace de build et de restauration ; dimensionner sur volumes mesurés avec marge, sans supposer la capacité du Mac |
| Énergie | Reprise après coupure, politique de veille, accès console, onduleur si requis |
| Logiciels | Moteur Docker compatible macOS/architecture, conditions de licence institutionnelles, Compose v2, build multiarchitecture sur une chaîne de construction adaptée |
| Accès | Compte d’exploitation, MFA, politique Tailscale approuvée, droits d’administration et de récupération hors bande |
| Identité | Nom HTTPS stable, résolution depuis clients et conteneurs, realm et clients OIDC, administrateurs et comptes scientifiques réels |
| Sauvegarde | Destination distincte du Mac, clés de chiffrement récupérables séparément, autorisations de transfert INRAE, rétention et RPO/RTO approuvés |
| Linux cible | Architecture, stockage, versions Docker/Compose, règles INRAE pour VPN, DNS, PKI, SSO, flux sortants et sauvegardes |

Ces valeurs sont des hypothèses de dimensionnement, pas un audit du Mac mini.
Aucun prérequis d’hébergement ne conditionne les tests fonctionnels R1 locaux.

## 3. Configuration future du Mac mini

À exécuter seulement lorsque la machine sera disponible et que la configuration
sera autorisée :

1. Vérifier les prérequis ci-dessus et les règles de l’établissement ; consigner
   les versions réellement retenues et le responsable de l’exploitation.
2. Préparer un compte d’exploitation et un répertoire pilote protégé, distinct du
   checkout de développement. Prévoir le démarrage du moteur et des services
   après reboot macOS ; vérifier le comportement réel après coupure/redémarrage.
3. Installer/configurer le moteur Docker et l’accès privé approuvés. Fixer les
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

Recommandation : Tailscale sur l’hôte, accès limité par groupes/règles du tailnet
aux utilisateurs et exploitants autorisés. Aucun transfert de port sur la box,
aucune exposition publique et aucun Tailscale Funnel. L’accès dev reste local,
ou réservé explicitement au développeur avec des règles distinctes.

Deux modes sont à qualifier ultérieurement : proxy d’entrée Tailscale local vers
Caddy lié à la boucle locale, ou Caddy lié uniquement à l’adresse privée de l’hôte.
Le second exige de vérifier la liaison de ports Docker Desktop à cette interface ;
ne pas présumer qu’elle fonctionne sur le futur macOS. Choisir un seul mode avant
la recette et vérifier depuis un poste hors tailnet que l’entrée est inaccessible.
L’option proposée par défaut est une terminaison TLS Caddy avec certificat valide
pour le nom privé retenu et transport d’entrée Tailscale contrôlé ; si TLS termine
en amont, propager correctement le schéma et n’accepter les en-têtes proxy que de
ce relais de confiance.

Le certificat peut dépendre du nom tailnet et de sa procédure de délivrance, ou
d’une PKI institutionnelle approuvée. Prévoir le renouvellement et la distribution
de la chaîne de confiance aux postes **et aux conteneurs**. Les noms de certificats
publics peuvent être publiés dans les journaux de transparence : faire approuver
le nom choisi. La procédure exacte dépendra du tailnet et de la PKI disponibles.

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

### Secrets

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

Avant chaque release : checks R1, backup vérifié, capture du manifeste courant,
fenêtre de maintenance, migrations explicites, santé et recette. Un rollback
d’image n’annule pas une migration de schéma : n’utiliser l’ancienne image que si
la compatibilité est prouvée ; sinon restaurer l’ensemble cohérent sous maintenance
et documenter les écritures perdues depuis le point de restauration.

## 6. Migration future vers Linux INRAE

1. Faire approuver la cible Linux, les règles réseau, DNS/TLS/SSO et la destination
   de sauvegarde. Tailscale reste conditionné à la politique INRAE ; si refusé,
   utiliser le VPN ou l’accès privé institutionnel sans publier l’application.
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
- [ ] Configurations dev/pilote résolues contrôlées, volumes/réseaux/ports distincts.
- [ ] Aucun seed de démo, auth dev, build local ou montage du code dans le pilote.
- [ ] Secrets et rôles de service séparés, rotation/récupération testables.
- [ ] Keycloak production, callbacks, issuer/audience, cookies et lifecycle validés.
- [ ] Accès hors tailnet refusé ; consoles et endpoints d’administration restreints.
- [ ] Migrations et données curées autorisées ; aucune importation Excel implicite.
- [ ] Format/lint/typecheck/unitaires, PostgreSQL et E2E validés pour la release.
- [ ] Coexistence dev/pilote testée pendant build et analyse, sans accès croisé.
- [ ] Backup complet chiffré hors hôte restauré sur une instance vide ; RPO/RTO mesurés.
- [ ] Réconciliation des jobs et intégrité des objets/audits/provenances contrôlées.
- [ ] Recette scientifique humaine, responsable, fenêtre de maintenance et rollback définis.
- [ ] Répétition Linux et règles INRAE planifiées avant la migration réelle.

Toutes les cases restent à exécuter. Aucun déploiement n’est attesté par ce document.
