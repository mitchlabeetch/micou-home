# Guide Complet des 50 Services Yunohost Recommandés pour micou.org
## Évaluation détaillée pour projets sociaux, artistiques et activistes

---

## TABLE DES MATIÈRES

1. [Communication (8 services)](#section-1-communication)
2. [Gestion Documentaire (8 services)](#section-2-gestion-documentaire)
3. [Médias et Création (7 services)](#section-3-médias-et-création)
4. [Productivité et Organisation (7 services)](#section-4-productivité)
5. [Publication et Web (6 services)](#section-5-publication-web)
6. [Éducation et Formation (4 services)](#section-6-éducation)
7. [Vie Privée et Sécurité (4 services)](#section-7-sécurité)
8. [Réseaux Sociaux Fédérés (3 services)](#section-8-réseaux-sociaux)
9. [Outils Spécialisés (3 services)](#section-9-outils-spécialisés)

---

## LÉGENDE DES ÉVALUATIONS

### Difficulté Setup
- ⭐ (1/10) : Très facile - Configuration en quelques clics
- ⭐⭐⭐ (3/10) : Facile - Guidé, peu de paramètres
- ⭐⭐⭐⭐⭐ (5/10) : Moyen - Quelques réglages techniques
- ⭐⭐⭐⭐⭐⭐⭐ (7/10) : Difficile - Connaissances système nécessaires
- ⭐⭐⭐⭐⭐⭐⭐⭐⭐ (9/10) : Expert - Configuration complexe

### Ressources Serveur (pour 30 utilisateurs réguliers)
- 🟢 Légère : < 1GB RAM
- 🟡 Moyenne : 1-2GB RAM
- 🟠 Élevée : 2-4GB RAM
- 🔴 Très élevée : > 4GB RAM

---

## SECTION 1: COMMUNICATION

### 1. Element (Matrix/Synapse)

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Messagerie instantanée sécurisée |
| **Description** | Client/serveur pour protocole Matrix - messagerie décentralisée fédérée |
| **Licence** | Apache 2.0 |
| **Langues** | 30+ (FR, EN, DE, ES, etc.) |
| **Site** | https://element.io |
| **Fondateurs** | Matthew Hodgson & Amandine Le Pape |

**DESCRIPTION LONGUE**
Element est l'interface d'accès au protocole Matrix, un standard ouvert pour la communication décentralisée. Chaque organisation peut héberger son propre serveur (Synapse) tout en communiquant avec le réseau mondial Matrix. Offre chiffrement E2E vérifié, appels vidéo de groupe, partage fichiers, messages éphémères, et ponts vers WhatsApp/Signal/Telegram.

**POSSIBILITÉS**
- Communication sécurisée groupes activistes
- Coordination événements sans surveillance
- Communautés thématiques fédérées
- Archivage structuré conversations
- Ponts vers autres réseaux

**EXEMPLES DE PROJETS**
1. *Collectif artistique (15 pers)* : Coordination exposition itinérante, partage croquis, réunions hebdo
2. *Association environnementale* : Chantiers nettoyage, localisations temps réel, documentation photo
3. *Festival (50 bénévoles)* : Salons thématiques logistique/programmation/communication

**PROBLÈMES CONNUS**
- Courbe apprentissage utilisateurs WhatsApp
- Lenteur appareils anciens
- Délai messages fédérés occasionnels
- Configuration E2EE complexe novices
- Historique difficile nouveaux appareils
- Confusion fédération
- Notifications décalées iOS

**AVANTAGES (7+)**
1. Chiffrement E2E audité et vérifié
2. Aucune dépendance commerciale
3. Fédération milliers serveurs
4. Applications mobiles natives
5. Support bots et intégrations
6. Groupes illimités
7. Contrôle total données
8. Messages éphémères

**INCONVÉNIENTS (7+)**
1. Interface moins polie Signal
2. Consommation batterie élevée
3. Notifications décalées
4. Éducation utilisateurs nécessaire
5. Recherche historique limitée mobile
6. Confusion fédération
7. Moins adoption générale
8. Configuration initiale technique

**AVIS UTILISATEURS**: 4.2/5 - Très apprécié communautés tech/activistes

**REMPLACE**: WhatsApp, Signal, Telegram, Slack, Teams

**DIFFICULTÉ**
- Admin: ⭐⭐⭐⭐⭐⭐⭐ (7/10)
- Utilisateur: ⭐⭐⭐ (3/10)

**COMPTES INVITE**: ✅ Oui - Admin crée et distribue identifiants

**RESSOURCES (RAM/Stockage)**
| 5 users | 10 users | 15 users | 30 users |
|---------|----------|----------|----------|
| 512MB/2GB | 1GB/5GB | 1.5GB/8GB | 2.5GB/15GB |

**STATUT**: Entièrement gratuit

---

### 2. Mattermost

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Communication d'équipe professionnelle |
| **Description** | Alternative open-source à Slack avec canaux thématiques |
| **Licence** | MIT (Team) / AGPL (Enterprise) |
| **Langues** | 20+ |
| **Site** | https://mattermost.com |
| **Fondateur** | Ian Tien |

**DESCRIPTION LONGUE**
Plateforme collaboration conçue pour organisations nécessitant contrôle total communications. Structurée canaux thématiques avec threads, réactions, intégrations. Interface très proche Slack facilitant migration.

**POSSIBILITÉS**
- Organisation structurée projets complexes
- Intégration outils développement
- Communication asynchrone organisée
- Archives exportables
- Workflows automatisés

**EXEMPLES DE PROJETS**
1. *Coopérative production (20 pers)* : Production, livraisons, comptabilité
2. *Collectif journalisme* : Rédaction collaborative enquêtes, sources
3. *Association quartier* : Événements, adhésions, communication

**PROBLÈMES CONNUS**
- Interface lourde petits groupes
- Applications mobiles lentes
- Courbe apprentissage non-tech
- Configuration LDAP complexe
- Mises à jour ajustements
- Consommation ressources élevée
- Notifications excessives

**AVANTAGES**
1. Interface familière type Slack
2. Threading efficace
3. Export données complet
4. Hautement personnalisable
5. Communication asynchrone
6. Permissions fines
7. Webhooks intégrations
8. Support LDAP/SAML

**INCONVÉNIENTS**
1. Ressource-intensive
2. Notifications excessives
3. Moins adapté informel
4. Configuration complexe
5. Mobile gourmand batterie
6. Mise en page dense
7. Support payant coûteux
8. Maintenance régulière

**AVIS**: 4.5/5 - Très apprécié entreprise/collectifs organisés

**REMPLACE**: Slack, Microsoft Teams, Discord Pro

**DIFFICULTÉ**: Admin 8/10 | Utilisateur 5/10

**COMPTES INVITE**: ✅ Oui

**RESSOURCES**
| 5 | 10 | 15 | 30 |
|---|----|----|----|
| 512MB/1GB | 1GB/3GB | 1.5GB/5GB | 2GB/10GB |

---

### 3. Discourse

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Forum communautaire moderne |
| **Description** | Plateforme discussion timeline infinie, modération communautaire |
| **Licence** | GPL v2 |
| **Langues** | 90+ |
| **Site** | https://www.discourse.org |
| **Fondateur** | Jeff Atwood |

**DESCRIPTION LONGUE**
Plateforme discussion moderne réinventant le forum. Timeline infinie, likes constructifs, modération communautaire. Utilisée Mozilla, GitHub, communautés open-source.

**POSSIBILITÉS**
- Construction communautés durables
- Support collaboratif
- Décisions démocratiques sondages
- Documentation vivante
- Discussions asynchrones

**EXEMPLES**
1. *Communauté artistique (200 pers)* : Techniques, rencontres
2. *Association consommateurs* : Entraide, actions collectives
3. *Projet citoyen* : Débat aménagements urbains

**PROBLÈMES**: Communauté active nécessaire, installation complexe Ruby, emails fréquents, intimidant, maintenance, coût hébergement, adoption Facebook difficile

**AVANTAGES**: Interface moderne, recherche excellente, badges, SEO, plugins, mise en page claire

**INCONVÉNIENTS**: Communauté critique, complexité technique, consommation mémoire, courbe apprentissage, chambres écho

**AVIS**: 4.6/5 - Standard industrie forums

**REMPLACE**: Facebook Groups, Reddit, phpBB

**DIFFICULTÉ**: Admin 9/10 | Utilisateur 6/10

**COMPTES INVITE**: ✅ Oui - Invitation email

**RESSOURCES**
| 5 | 10 | 15 | 30 |
|---|----|----|----|
| 1GB/5GB | 1.5GB/10GB | 2GB/15GB | 3GB/30GB |

---

### 4. Jitsi Meet

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Visioconférence |
| **Description** | Solution visioconférence chiffrée, sans inscription |
| **Licence** | Apache 2.0 |
| **Langues** | 40+ |
| **Site** | https://jitsi.org |
| **Fondateur** | Emil Ivov |

**DESCRIPTION**: Visioconférence E2E, salles instantanées sans inscription, partage écran, jusqu'à 75 participants (35 recommandés).

**EXEMPLES**: Association migrants (interprètes), collectif féministe (groupes parole), festival cinéma (projections+débats)

**PROBLÈMES**: Qualité variable, CPU élevé, écho audio, interface austère, pare-feu, pas enregistrement natif

**AVANTAGES**: Sans inscription, E2E, pas limite temps, navigateur, app légère, streaming YouTube, raise hand

**INCONVÉNIENTS**: Qualité inférieure Zoom instable, pas sondages, pare-feu entreprise, Jibri pour enregistrement, bruit fond

**AVIS**: 4.3/5

**REMPLACE**: Zoom, Google Meet, Teams

**DIFFICULTÉ**: Admin 6/10 | Utilisateur 1/10 (Très facile!)

**COMPTES INVITE**: ✅ Oui - Liens directs

**RESSOURCES**: 2GB/10GB pour 30 users

---

### 5. Mobilizon

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Gestion événements fédérée |
| **Description** | Plateforme décentralisée organisation événements |
| **Licence** | AGPL v3 |
| **Contributeur** | Framasoft |
| **Site** | https://mobilizon.org |

**DESCRIPTION**: Événements par Framasoft, respect vie privée, export données, fédération ActivityPub.

**RESSOURCES**: 1GB/5GB pour 30 users

**AVIS**: 4.0/5

---

### 6. Zulip

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Chat organisé par sujets |
| **Description** | Plateforme chat avec threads par sujet, hybride email/chat |
| **Licence** | Apache 2.0 |
| **Site** | https://zulip.com |

**DESCRIPTION**: Chat avec organisation par sujets (topics) plutôt que canaux. Excellent pour suivre plusieurs conversations parallèles. Utilisé par Rust, Python, etc.

**EXEMPLES**: Collectif recherche (discussions parallèles), association (multiprojets), festival (logistique complexe)

**AVANTAGES**: Organisation par sujets, recherche puissante, intégrations, mobile performant, latex/markdown

**INCONVÉNIENTS**: Paradigme différent à apprendre, interface dense, moins connu, adoption utilisateurs

**RESSOURCES**: 2GB/10GB (30 users)

---

### 7. Bénévalibre

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Gestion bénévolat |
| **Description** | Logiciel gestion et valorisation du bénévolat associatif |
| **Licence** | AGPL |
| **Origine** | France |

**DESCRIPTION**: Spécialement conçu pour associations gérant du bénévolat. Suivi heures, compétences, missions, valorisation bénévoles.

**EXEMPLES**: Festival (bénévoles), association culturelle (suivi engagement), centre social (valorisation)

**RESSOURCES**: 512MB/2GB (30 users)

---

### 8. Agorakit

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Groupware citoyen |
| **Description** | Outil collaboration pour groupes citoyens |
| **Licence** | GPL |
| **Site** | https://agorakit.org |

**DESCRIPTION**: Groupware conçu pour citoyens s'organiser. Calendrier, fichiers, discussions, cartographie, notifications.

**EXEMPLES**: Collectif quartier, association transition, groupement agriculteurs

**RESSOURCES**: 1GB/5GB

---

## SECTION 2: GESTION DOCUMENTAIRE

### 9. Nextcloud

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Cloud personnel |
| **Description** | Suite cloud complète: fichiers, bureautique, calendrier, contacts |
| **Licence** | AGPL v3 |
| **Site** | https://nextcloud.com |
| **Fondateur** | Frank Karlitschek |

**DESCRIPTION**: Suite cloud complète alternative Google/Dropbox. Fichiers, collabora (docs/spreadsheets), calendrier, contacts, deck (kanban), 100+ apps.

**RESSOURCES**: 3GB/30GB+ (30 users actifs)

**AVIS**: 4.6/5 - Incontournable

---

### 10. CryptPad

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Bureautique chiffrée |
| **Description** | Suite bureautique collaborative zero-knowledge |
| **Licence** | AGPL v3 |
| **Site** | https://cryptpad.org |
| **Contributeur** | XWiki (France) |

**DESCRIPTION**: Suite bureautique E2E zero-knowledge. Serveur ne peut pas lire contenu. Documents, spreadsheets, sondages, whiteboard.

**EXEMPLES**: Rédaction manifestes, planification sensibles, sondages anonymes

**RESSOURCES**: 1GB/5GB (30 users)

---

### 11. BookStack

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Documentation/Wiki |
| **Description** | Plateforme documentation organisée étagères/livres/chapitres |
| **Licence** | MIT |
| **Site** | https://www.bookstackapp.com |

**DESCRIPTION**: Wiki orienté documentation. Organisation hiérarchique: étagères > livres > chapitres > pages. Interface claire, WYSIWYG.

**RESSOURCES**: 1GB/5GB

---

### 12. HedgeDoc (CodiMD)

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Édition collaborative Markdown |
| **Description** | Éditeur markdown collaboratif temps réel |
| **Licence** | AGPL |
| **Site** | https://hedgedoc.org |

**DESCRIPTION**: Édition collaborative markdown temps réel. Parfait prise notes réunions, documentation rapide.

**RESSOURCES**: 512MB/2GB

---

### 13. DokuWiki

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Wiki sans base de données |
| **Description** | Wiki léger basé fichiers texte |
| **Licence** | GPL v2 |

**DESCRIPTION**: Wiki simple, fichiers texte (pas de base données). Très portable, fiable, extensible plugins.

**RESSOURCES**: 256MB/1GB

---

### 14. AppFlowy

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Workspace Notion-like |
| **Description** | Alternative Notion open-source |
| **Licence** | AGPL |
| **Site** | https://appflowy.io |

**DESCRIPTION**: Alternative Notion. Notes, bases données, kanban, calendrier. Local-first, chiffrement optionnel.

**RESSOURCES**: 1GB/5GB

---

### 15. Paperless-ngx

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Gestion documents |
| **Description** | Numérisation et archivage documents intelligent |
| **Licence** | GPL v3 |

**DESCRIPTION**: OCR automatique, classement documents, recherche plein texte. Idéal paperless.

**RESSOURCES**: 2GB/20GB+

---

### 16. Grist

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Spreadsheet base données |
| **Description** | Alternative Airtable, spreadsheets relationnelles |
| **Licence** | Apache 2.0 |
| **Site** | https://getgrist.com |

**DESCRIPTION**: Spreadsheet + base données. Formules Python, relations tables, vues flexibles.

**RESSOURCES**: 1GB/5GB

---

## SECTION 3: MÉDIAS ET CRÉATION

### 17. PeerTube

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Hébergement vidéo |
| **Description** | Plateforme vidéo décentralisée fédérée |
| **Licence** | AGPL v3 |
| **Contributeur** | Framasoft |
| **Site** | https://joinpeertube.org |

**DESCRIPTION**: YouTube décentralisé. WebTorrent P2P, fédération ActivityPub, pas d'algorithmes.

**RESSOURCES**: 4GB/100GB+ (dépend stockage vidéo)

---

### 18. Pixelfed

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Partage photos |
| **Description** | Instagram fédéré, chronologique, pas d'algorithmes |
| **Licence** | AGPL v3 |

**DESCRIPTION**: Instagram éthique. Fédération ActivityPub, feed chronologique, pas tracking.

**RESSOURCES**: 1.5GB/20GB+

---

### 19. Funkwhale

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Musique et podcasts |
| **Description** | Plateforme audio fédérée |
| **Licence** | AGPL v3 |

**DESCRIPTION**: Spotify/Podcast fédéré. Artistes partagent directement, Creative Commons.

**RESSOURCES**: 1.5GB/50GB+

---

### 20. Audiobookshelf

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Livres audio |
| **Description** | Serveur livres audio et podcasts |
| **Licence** | GPL v3 |

**DESCRIPTION**: Gestion collection livres audio, podcasts. Apps mobiles, sync progression.

**RESSOURCES**: 1GB/20GB+

---

### 21. Piwigo

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Galerie photos |
| **Description** | Galerie photo web pour photographes |
| **Licence** | GPL v2 |
| **Site** | https://piwigo.org |

**DESCRIPTION**: Galerie photo professionnelle. Albums, tags, visiteurs, e-commerce.

**RESSOURCES**: 1GB/30GB+

---

### 22. Excalidraw

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Dessin collaboratif |
| **Description** | Tableau blanc dessin style croquis |
| **Licence** | MIT |
| **Site** | https://excalidraw.com |

**DESCRIPTION**: Dessin collaboratif style "croquis main". Parfait brainstorming visuel.

**RESSOURCES**: 512MB/1GB

---

### 23. Stylo

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Édition scientifique |
| **Description** | Éditeur articles scientifiques markdown |
| **Licence** | GPL |
| **Origine** | Canada/France |

**DESCRIPTION**: Où écrire articles scientifiques markdown. Export HTML, PDF, XML.

**RESSOURCES**: 512MB/2GB

---

## SECTION 4: PRODUCTIVITÉ ET ORGANISATION

### 24. Wekan

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Kanban |
| **Description** | Tableaux Kanban style Trello |
| **Licence** | MIT |
| **Site** | https://wekan.github.io |

**DESCRIPTION**: Trello open-source. Tableaux, listes, cartes, étiquettes, dates.

**RESSOURCES**: 1GB/5GB (30 users)

---

### 25. Leantime

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Gestion projet |
| **Description** | Project management pour startups/innovateurs |
| **Licence** | AGPL |
| **Site** | https://leantime.io |

**DESCRIPTION**: Gestion projet complète. Idées, recherche, roadmap, sprints, retros.

**RESSOURCES**: 1.5GB/5GB

---

### 26. Baserow

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Base données no-code |
| **Description** | Alternative Airtable open-source |
| **Licence** | MIT |
| **Site** | https://baserow.io |

**DESCRIPTION**: Base données no-code. Tables, vues (grid, gallery, form), relations, API.

**RESSOURCES**: 1.5GB/5GB

---

### 27. Actual

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Finances personnelles |
| **Description** | Gestion budget local-first |
| **Licence** | MIT |
| **Site** | https://actualbudget.com |

**DESCRIPTION**: YNAB open-source. Budget enveloppes, synchro, rapports.

**RESSOURCES**: 512MB/1GB

---

### 28. Kimai2

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Suivi temps |
| **Description** | Application suivi temps multi-utilisateurs |
| **Licence** | MIT |
| **Site** | https://www.kimai.org |

**DESCRIPTION**: Feuilles temps. Projets, clients, facturation, rapports.

**RESSOURCES**: 512MB/2GB

---

### 29. Akaunting

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Comptabilité |
| **Description** | Logiciel comptabilité en ligne |
| **Licence** | GPL |
| **Site** | https://akaunting.com |

**DESCRIPTION**: Comptabilité complète. Factures, dépenses, rapports, multi-devises.

**RESSOURCES**: 1GB/5GB

---

### 30. Crab Fit

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Planification horaires |
| **Description** | Trouver créneaux horaires communs |
| **Licence** | GPL |

**DESCRIPTION**: Doodle éthique. Disponibilités visuelles, sans compte.

**RESSOURCES**: 256MB/1GB

---

## SECTION 5: PUBLICATION WEB

### 31. WordPress

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | CMS |
| **Description** | Système gestion contenu le plus populaire |
| **Licence** | GPL v2 |
| **Site** | https://wordpress.org |

**DESCRIPTION**: CMS incontournable. Blogs, sites, e-commerce (WooCommerce), millions thèmes/plugins.

**RESSOURCES**: 1.5GB/10GB+

---

### 32. WriteFreely

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Blogging fédéré |
| **Description** | Plateforme blog minimaliste fédérée |
| **Licence** | AGPL |
| **Site** | https://writefreely.org |

**DESCRIPTION**: Blog épuré, fédération ActivityPub. Écriture sans distraction.

**RESSOURCES**: 512MB/2GB

---

### 33. 13ft

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Contournement paywalls |
| **Description** | Contourner les paywalls de presse |
| **Licence** | AGPL |

**DESCRIPTION**: Alternative 12ft.io auto-hébergée. Accès articles payants (légal gris).

**RESSOURCES**: 128MB/500MB

---

### 34. Ladder

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Contournement paywalls |
| **Description** | Bypass paywalls comme 12ft.io |
| **Licence** | MIT |

**DESCRIPTION**: Similaire 13ft, contournement paywalls.

**RESSOURCES**: 128MB/500MB

---

### 35. Shaarli

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Signets sociaux |
| **Description** | Partage liens avec tags et notes |
| **Licence** | zlib/libpng |

**DESCRIPTION**: Delicious auto-hébergé. Bookmarks, tags, notes, partage.

**RESSOURCES**: 256MB/1GB

---

### 36. Wiki.js

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Wiki moderne |
| **Description** | Wiki puissant et extensible |
| **Licence** | AGPL |
| **Site** | https://js.wiki |

**DESCRIPTION**: Wiki moderne avec éditeur visuel, markdown, graphiques, authentification.

**RESSOURCES**: 1.5GB/5GB

---

## SECTION 6: ÉDUCATION ET FORMATION

### 37. Moodle

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | LMS |
| **Description** | Plateforme apprentissage en ligne |
| **Licence** | GPL v3 |
| **Site** | https://moodle.org |

**DESCRIPTION**: LMS complet. Cours, quiz, devoirs, forums, badges.

**RESSOURCES**: 2GB/20GB+

---

### 38. BigBlueButton

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Visio éducative |
| **Description** | Visioconférence pour enseignement en ligne |
| **Licence** | LGPL |
| **Site** | https://bigbluebutton.org |

**DESCRIPTION**: Visio éducation. Salles breakout, sondages, tableau blanc, enregistrement.

**RESSOURCES**: 4GB/20GB+

---

### 39. Digisteps

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Parcours éducatifs |
| **Description** | Créer parcours éducatifs simples |
| **Licence** | AGPL |
| **Origine** | France |

**DESCRIPTION**: Parcours pédagogiques étape par étape. Progression, évaluation.

**RESSOURCES**: 512MB/2GB

---

### 40. LibreBooking

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Réservation ressources |
| **Description** | Réservation salles, équipements |
| **Licence** | GPL |

**DESCRIPTION**: Gestion réservations. Salles, équipements, calendriers.

**RESSOURCES**: 512MB/2GB

---

## SECTION 7: VIE PRIVÉE ET SÉCURITÉ

### 41. Vaultwarden

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Gestion mots de passe |
| **Description** | Serveur Bitwarden RS léger |
| **Licence** | GPL v3 |
| **Site** | https://github.com/dani-garcia/vaultwarden |

**DESCRIPTION**: Bitwarden auto-hébergé léger. Mots de passe, notes sécurisées, partage famille.

**RESSOURCES**: 256MB/1GB

---

### 42. Pi-hole

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Blocage publicités |
| **Description** | Bloqueur DNS réseau complet |
| **Licence** | EUPL v1.2 |
| **Site** | https://pi-hole.net |

**DESCRIPTION**: Bloque publicités/trackers au niveau réseau. Protection tous appareils.

**RESSOURCES**: 512MB/2GB

---

### 43. 2FAuth

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | 2FA |
| **Description** | Gestionnaire codes 2FA |
| **Licence** | AGPL |

**DESCRIPTION**: Authy/GA alternatif. Codes TOTP, organisation, import/export.

**RESSOURCES**: 256MB/500MB

---

### 44. PrivateBin

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Pastebin chiffré |
| **Description** | Pastebin zero-knowledge |
| **Licence** | zlib/libpng |
| **Site** | https://privatebin.info |

**DESCRIPTION**: Pastebin chiffré navigateur. Zero-knowledge, expiration, auto-destruction.

**RESSOURCES**: 128MB/1GB

---

## SECTION 8: RÉSEAUX SOCIAUX FÉDÉRÉS

### 45. Mastodon

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Microblogging |
| **Description** | Twitter décentralisé fédéré |
| **Licence** | AGPL v3 |
| **Site** | https://joinmastodon.org |
| **Fondateur** | Eugen Rochko |

**DESCRIPTION**: Twitter éthique. 500 caractères, fédération, pas d'algorithme, pas de pub.

**RESSOURCES**: 2GB/20GB+

---

### 46. Lemmy

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Agrégateur liens |
| **Description** | Reddit fédéré |
| **Licence** | AGPL |
| **Site** | https://join-lemmy.org |

**DESCRIPTION**: Reddit décentralisé. Communautés, votes, fédération, modération.

**RESSOURCES**: 1.5GB/10GB+

---

### 47. Bonfire

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Réseau social fédéré |
| **Description** | Réseau social modulaire fédéré |
| **Licence** | AGPL |

**DESCRIPTION**: Réseau social flexible. Extensions, communautés, fédération ActivityPub.

**RESSOURCES**: 1.5GB/5GB

---

## SECTION 9: OUTILS SPÉCIALISÉS

### 48. n8n

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Automatisation |
| **Description** | Workflow automation (Zapier alternative) |
| **Licence** | fair-code |
| **Site** | https://n8n.io |

**DESCRIPTION**: Automatisation workflows. 400+ intégrations, webhook, scheduler.

**RESSOURCES**: 1GB/2GB

---

### 49. LanguageTool

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Correction linguistique |
| **Description** | Correcteur grammaire/style multilingue |
| **Licence** | LGPL |
| **Site** | https://languagetool.org |

**DESCRIPTION**: Grammarly auto-hébergé. Grammaire, style, 20+ langues.

**RESSOURCES**: 2GB/5GB (avec ngrams)

---

### 50. Kiwix

| Attribut | Valeur |
|----------|--------|
| **Catégorie** | Accès hors-ligne |
| **Description** | Lecteur contenu Wikipedia hors-ligne |
| **Licence** | GPL v3 |
| **Site** | https://www.kiwix.org |

**DESCRIPTION**: Wikipedia/ressources hors-ligne. Accès sans internet.

**RESSOURCES**: 512MB/10GB+ (dépend contenu)

---

## TABLEAU RÉCAPITULATIF

| # | Service | Type | Diff. Admin | RAM 30u | Stockage | Invite | Licence |
|---|---------|------|-------------|---------|----------|--------|---------|
| 1 | Element | Chat | 7/10 | 2.5GB | 15GB | ✅ | Apache 2.0 |
| 2 | Mattermost | Chat | 8/10 | 2GB | 10GB | ✅ | MIT |
| 3 | Discourse | Forum | 9/10 | 3GB | 30GB | ✅ | GPL v2 |
| 4 | Jitsi | Visio | 6/10 | 2GB | 10GB | ✅ | Apache 2.0 |
| 5 | Mobilizon | Événements | 5/10 | 1GB | 5GB | ✅ | AGPL |
| 6 | Zulip | Chat | 7/10 | 2GB | 10GB | ✅ | Apache 2.0 |
| 7 | Bénévalibre | Bénévolat | 5/10 | 512MB | 2GB | ✅ | AGPL |
| 8 | Agorakit | Groupware | 5/10 | 1GB | 5GB | ✅ | GPL |
| 9 | Nextcloud | Cloud | 6/10 | 3GB | 30GB | ✅ | AGPL v3 |
| 10 | CryptPad | Bureautique | 5/10 | 1GB | 5GB | ✅ | AGPL v3 |
| 11 | BookStack | Wiki | 4/10 | 1GB | 5GB | ✅ | MIT |
| 12 | HedgeDoc | Markdown | 4/10 | 512MB | 2GB | ✅ | AGPL |
| 13 | DokuWiki | Wiki | 3/10 | 256MB | 1GB | ✅ | GPL v2 |
| 14 | AppFlowy | Workspace | 5/10 | 1GB | 5GB | ✅ | AGPL |
| 15 | Paperless-ngx | Documents | 6/10 | 2GB | 20GB | ✅ | GPL v3 |
| 16 | Grist | Database | 5/10 | 1GB | 5GB | ✅ | Apache 2.0 |
| 17 | PeerTube | Vidéo | 8/10 | 4GB | 100GB+ | ✅ | AGPL v3 |
| 18 | Pixelfed | Photos | 6/10 | 1.5GB | 20GB+ | ✅ | AGPL v3 |
| 19 | Funkwhale | Audio | 6/10 | 1.5GB | 50GB+ | ✅ | AGPL v3 |
| 20 | Audiobookshelf | Livres audio | 4/10 | 1GB | 20GB+ | ✅ | GPL v3 |
| 21 | Piwigo | Galerie | 5/10 | 1GB | 30GB+ | ✅ | GPL v2 |
| 22 | Excalidraw | Dessin | 3/10 | 512MB | 1GB | ✅ | MIT |
| 23 | Stylo | Scientifique | 4/10 | 512MB | 2GB | ✅ | GPL |
| 24 | Wekan | Kanban | 5/10 | 1GB | 5GB | ✅ | MIT |
| 25 | Leantime | Projet | 6/10 | 1.5GB | 5GB | ✅ | AGPL |
| 26 | Baserow | Database | 5/10 | 1.5GB | 5GB | ✅ | MIT |
| 27 | Actual | Budget | 4/10 | 512MB | 1GB | ✅ | MIT |
| 28 | Kimai2 | Temps | 4/10 | 512MB | 2GB | ✅ | MIT |
| 29 | Akaunting | Compta | 5/10 | 1GB | 5GB | ✅ | GPL |
| 30 | Crab Fit | Planning | 3/10 | 256MB | 1GB | ✅ | GPL |
| 31 | WordPress | CMS | 4/10 | 1.5GB | 10GB+ | ✅ | GPL v2 |
| 32 | WriteFreely | Blog | 4/10 | 512MB | 2GB | ✅ | AGPL |
| 33 | 13ft | Paywall | 2/10 | 128MB | 500MB | N/A | AGPL |
| 34 | Ladder | Paywall | 2/10 | 128MB | 500MB | N/A | MIT |
| 35 | Shaarli | Signets | 3/10 | 256MB | 1GB | ✅ | zlib |
| 36 | Wiki.js | Wiki | 6/10 | 1.5GB | 5GB | ✅ | AGPL |
| 37 | Moodle | LMS | 7/10 | 2GB | 20GB+ | ✅ | GPL v3 |
| 38 | BigBlueButton | Visio édu | 8/10 | 4GB | 20GB+ | ✅ | LGPL |
| 39 | Digisteps | Parcours | 4/10 | 512MB | 2GB | ✅ | AGPL |
| 40 | LibreBooking | Réservation | 4/10 | 512MB | 2GB | ✅ | GPL |
| 41 | Vaultwarden | Passwords | 3/10 | 256MB | 1GB | ✅ | GPL v3 |
| 42 | Pi-hole | DNS | 4/10 | 512MB | 2GB | N/A | EUPL |
| 43 | 2FAuth | 2FA | 3/10 | 256MB | 500MB | ✅ | AGPL |
| 44 | PrivateBin | Paste | 2/10 | 128MB | 1GB | N/A | zlib |
| 45 | Mastodon | Social | 7/10 | 2GB | 20GB+ | ✅ | AGPL v3 |
| 46 | Lemmy | Forum | 6/10 | 1.5GB | 10GB+ | ✅ | AGPL |
| 47 | Bonfire | Social | 6/10 | 1.5GB | 5GB | ✅ | AGPL |
| 48 | n8n | Automation | 6/10 | 1GB | 2GB | ✅ | fair-code |
| 49 | LanguageTool | Correction | 6/10 | 2GB | 5GB | ✅ | LGPL |
| 50 | Kiwix | Hors-ligne | 3/10 | 512MB | 10GB+ | N/A | GPL v3 |

---

## STACKS RECOMMANDÉES PAR TYPE DE PROJET

### Collectif Artistique (5-15 personnes)
- **Communication**: Element ou Zulip
- **Fichiers**: Nextcloud
- **Documentation**: BookStack
- **Gestion projet**: Wekan
- **Présence**: WriteFreely + Pixelfed
- **Visio**: Jitsi

### Association Environnementale (10-30 personnes)
- **Communication**: Mattermost
- **Événements**: Mobilizon
- **Documentation**: CryptPad
- **Vidéo**: PeerTube
- **Formulaires**: LibreForms

### Festival (50+ bénévoles)
- **Communication**: Mattermost + Jitsi
- **Planning**: Leantime
- **Billetterie**: Formulaires LiberaForms
- **Site**: WordPress
- **Médias**: Nextcloud

### Recherche Citoyenne
- **Documentation**: HedgeDoc + Wiki.js
- **Données**: Baserow
- **Communication**: Discourse
- **Sensible**: CryptPad
- **Archivage**: ArchiveBox

---

## NOTES FINALES

### Critères de Sélection
Tous services respectent:
- ✅ Code source ouvert
- ✅ Auto-hébergement possible
- ✅ Pas de collecte données publicitaires
- ✅ Export données possible
- ✅ Communauté active

### Ressources Minimum Serveur
Pour héberger confortablement 10-15 services parmi cette liste:
- **CPU**: 4 cores
- **RAM**: 8GB minimum (16GB recommandé)
- **Stockage**: 200GB SSD minimum
- **Bande passante**: 100Mbps symétrique

### Mises à Jour
Tous ces services sont régulièrement mis à jour via Yunohost. Planifier:
- Maintenance hebdomadaire (sécurité)
- Sauvegardes quotidiennes
- Tests restauration mensuels

---

*Document créé pour micou.org - 50 services évalués*
