# App Organigramme - Backend Django

Cette application Django fournit une API REST publique pour la gestion de l'organigramme de l'entreprise SAR. Elle est conçue pour être utilisée exclusivement par le frontend Next.js à l'adresse `http://localhost:3000/organigramme`.

## 🎯 Objectif

Créer une API REST totalement indépendante et publique (aucune authentification requise) pour fournir les données d'organigramme au frontend Next.js.

## 🏗️ Structure du Module

### Modèles

#### Direction
- `id` (auto) - Identifiant unique
- `name` - Nom complet de la direction (ex: "Ressources Humaines")
- `slug` - Identifiant unique en minuscules pour les filtres (ex: "rh")
- `created_at` - Date de création
- `updated_at` - Date de mise à jour

#### Agent
- `id` (auto) - Identifiant unique
- `first_name` - Prénom
- `last_name` - Nom
- `job_title` - Poste ou fonction
- `directions` - Relation ManyToMany vers Direction (un agent peut appartenir à plusieurs directions)
- `email` - Email professionnel
- `phone_fixed` - Téléphone fixe
- `phone_mobile` - Téléphone mobile
- `employee_id` - Matricule unique
- `manager` - Clé étrangère vers Agent, nullable (le DG n'a pas de manager)
- `created_at` - Date de création
- `updated_at` - Date de mise à jour

## 🔗 Endpoints API

### 1. Liste des agents
**GET** `/api/organigramme/agents/`

**Paramètres de requête :**
- `direction=<slug>` - Filtre sur direction spécifique
- `search=<texte>` - Recherche sur prénom, nom, poste ou email

**Exemple de réponse :**
```json
[
  {
    "id": 1,
    "first_name": "Aminata",
    "last_name": "Diop",
    "full_name": "Aminata Diop",
    "initials": "AD",
    "job_title": "Directrice Générale",
    "directions": [{"id": 1, "name": "Ressources Humaines", "slug": "rh"}],
    "email": "aminata.diop@sar.sn",
    "phone_fixed": "33 123 4567",
    "phone_mobile": "77 123 4567",
    "employee_id": "DG-001",
    "manager": null,
    "manager_name": null
  }
]
```

### 2. Détail d'un agent
**GET** `/api/organigramme/agents/<id>/`

Retourne toutes les informations de l'agent, y compris directions et manager.

### 3. Liste des directions
**GET** `/api/organigramme/directions/`

Retourne toutes les directions disponibles pour le filtre du frontend.

**Exemple de réponse :**
```json
[
  {"id": 1, "name": "Ressources Humaines", "slug": "rh"},
  {"id": 2, "name": "Informatique", "slug": "informatique"},
  {"id": 3, "name": "Administration", "slug": "administration"}
]
```

### 4. Arborescence complète
**GET** `/api/organigramme/tree/`

Retourne la hiérarchie complète (DG > Managers > Employés) avec les subordonnés imbriqués.

### 5. Recherche avancée
**GET** `/api/organigramme/agents/search/`

**Paramètres de requête :**
- `direction=<slug>` - Filtre par direction
- `search=<texte>` - Recherche textuelle
- `manager=<id>` - Filtre par manager

### 6. Subordonnés d'un agent
**GET** `/api/organigramme/agents/<id>/subordinates/`

Retourne tous les subordonnés directs d'un agent.

### 7. Agents d'une direction
**GET** `/api/organigramme/directions/<slug>/agents/`

Retourne tous les agents d'une direction spécifique.

## 🚀 Installation et Configuration

### 1. Lancer les migrations
```bash
python manage.py makemigrations organigramme
python manage.py migrate
```

### 2. Charger les données de test
```bash
python manage.py loaddata organigramme/fixtures/sample_data.json
```

### 3. Démarrer le serveur
```bash
python manage.py runserver
```

## 📊 Données de Test

Les fixtures incluent :
- **4 directions** : RH, Informatique, Administration, Finance
- **12 agents** avec hiérarchie complète :
  - 1 Directrice Générale (sans manager)
  - 3 Directeurs (DSI, DRH, DAF)
  - 8 Employés avec différents niveaux

### Hiérarchie des données de test :
```
Aminata Diop (DG)
├── Mamadou Fall (DSI)
│   ├── Aïcha Ba (Chef de Projet IT)
│   │   └── Souleymane Gueye (Développeur Senior)
│   └── Cheikh Wade (Analyste Système)
├── Fatou Sarr (DRH)
│   ├── Khadija Diallo (Responsable Recrutement)
│   └── Awa Faye (Responsable Formation)
└── Ibrahima Ndiaye (DAF)
    ├── Modou Thiam (Comptable Principal)
    ├── Mariama Cissé (Assistante Administrative)
    └── Papa Sow (Contrôleur de Gestion)
```

## 🔧 Configuration CORS

L'application est configurée pour accepter les requêtes depuis :
- `http://localhost:3000`
- `http://127.0.0.1:3000`

## 📝 Exemples d'utilisation

### Filtrer par direction
```bash
curl "http://localhost:8000/api/organigramme/agents/?direction=rh"
```

### Rechercher un agent
```bash
curl "http://localhost:8000/api/organigramme/agents/?search=aminata"
```

### Obtenir l'arborescence complète
```bash
curl "http://localhost:8000/api/organigramme/tree/"
```

## 🎯 Compatibilité Frontend

Cette API est conçue pour être compatible avec le frontend Next.js à l'URL `http://localhost:3000/organigramme`. Les formats de réponse correspondent exactement aux interfaces TypeScript définies dans le frontend.

## 🔒 Sécurité

- **Aucune authentification requise** - API publique
- **CORS configuré** pour localhost:3000 uniquement
- **Pas de pagination** - Retourne tous les résultats
- **Lecture seule** - Aucune modification des données via l'API

