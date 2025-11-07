# Documentation API Forum

## Vue d'ensemble

Le backend du forum permet aux utilisateurs de :
- Créer et gérer des forums (catégories)
- Créer des conversations (posts) dans un forum avec upload d'image
- Commenter des conversations
- Aimer/désaimer des commentaires

## Endpoints API

### Forums

#### Liste des forums
```
GET /api/forum/forums/
```
Retourne la liste de tous les forums actifs avec leurs statistiques.

**Réponse :**
```json
[
  {
    "id": 1,
    "name": "Annonces Générales",
    "description": "Actualités et communications importantes",
    "image": "/media/forums/forum1.jpg",
    "image_url": "http://localhost:8000/media/forums/forum1.jpg",
    "is_active": true,
    "member_count": 1247,
    "conversation_count": 89,
    "created_at": "2025-01-01T10:00:00Z",
    "updated_at": "2025-01-01T10:00:00Z"
  }
]
```

#### Créer un forum (Admin uniquement)
```
POST /api/forum/forums/
Content-Type: multipart/form-data

{
  "name": "Nom du forum",
  "description": "Description du forum",
  "image": <fichier image>,
  "is_active": true
}
```

#### Détails d'un forum
```
GET /api/forum/forums/{id}/
```

#### Mettre à jour un forum (Admin uniquement)
```
PUT /api/forum/forums/{id}/
PATCH /api/forum/forums/{id}/
```

#### Supprimer un forum (Admin uniquement - soft delete)
```
DELETE /api/forum/forums/{id}/
```

---

### Conversations

#### Liste des conversations
```
GET /api/forum/conversations/
```

**Paramètres de requête :**
- `forum` : Filtrer par ID de forum
- `author` : Filtrer par ID d'auteur
- `is_resolved` : Filtrer par statut résolu (true/false)
- `search` : Recherche dans le titre et la description

**Exemple :**
```
GET /api/forum/conversations/?forum=1&search=télétravail
```

**Réponse :**
```json
[
  {
    "id": 1,
    "forum": {
      "id": 1,
      "name": "Annonces Générales",
      ...
    },
    "author": {
      "id": 1,
      "username": "marie.dubois",
      "full_name": "Marie Dubois",
      "avatar_url": "http://localhost:8000/media/avatars/user1.jpg"
    },
    "title": "Nouvelle politique de télétravail 2025",
    "description": "Discussion sur les nouvelles directives...",
    "image": "/media/conversations/conv1.jpg",
    "image_url": "http://localhost:8000/media/conversations/conv1.jpg",
    "is_resolved": false,
    "views": 456,
    "replies_count": 23,
    "last_activity": "Il y a 2 heures",
    "created_at": "2025-01-01T10:00:00Z",
    "updated_at": "2025-01-01T10:00:00Z"
  }
]
```

#### Créer une conversation
```
POST /api/forum/conversations/
Content-Type: multipart/form-data
Authorization: Bearer <token>

{
  "forum": 1,
  "title": "Titre de la conversation",
  "description": "Description détaillée de la conversation",
  "image": <fichier image optionnel>
}
```

**Note :** L'auteur est automatiquement défini comme l'utilisateur connecté.

#### Détails d'une conversation
```
GET /api/forum/conversations/{id}/
```
**Note :** Cette requête incrémente automatiquement le compteur de vues.

#### Mettre à jour une conversation
```
PUT /api/forum/conversations/{id}/
PATCH /api/forum/conversations/{id}/
```
**Permission :** Seul l'auteur ou un admin peut modifier.

#### Supprimer une conversation
```
DELETE /api/forum/conversations/{id}/
```
**Permission :** Seul l'auteur ou un admin peut supprimer.

---

### Commentaires

#### Liste des commentaires d'une conversation
```
GET /api/forum/comments/?conversation={conversation_id}
```

**Réponse :**
```json
[
  {
    "id": 1,
    "conversation": 1,
    "author": {
      "id": 2,
      "username": "pierre.durand",
      "full_name": "Pierre Durand",
      "avatar_url": "http://localhost:8000/media/avatars/user2.jpg"
    },
    "author_avatar": "http://localhost:8000/media/avatars/user2.jpg",
    "content": "Excellente initiative ! Le télétravail...",
    "likes_count": 12,
    "is_liked": false,
    "timestamp": "Il y a 2 heures",
    "created_at": "2025-01-01T10:00:00Z",
    "updated_at": "2025-01-01T10:00:00Z"
  }
]
```

#### Créer un commentaire
```
POST /api/forum/comments/
Content-Type: application/json
Authorization: Bearer <token>

{
  "conversation": 1,
  "content": "Mon commentaire sur cette conversation"
}
```

**Note :** L'auteur est automatiquement défini comme l'utilisateur connecté.

#### Détails d'un commentaire
```
GET /api/forum/comments/{id}/
```

#### Mettre à jour un commentaire
```
PUT /api/forum/comments/{id}/
PATCH /api/forum/comments/{id}/
```
**Permission :** Seul l'auteur ou un admin peut modifier.

#### Supprimer un commentaire
```
DELETE /api/forum/comments/{id}/
```
**Permission :** Seul l'auteur ou un admin peut supprimer.

---

### Likes de commentaires

#### Liker un commentaire
```
POST /api/forum/comments/{comment_id}/like/
Authorization: Bearer <token>
```

**Réponse :**
```json
{
  "message": "Commentaire liké avec succès",
  "liked": true,
  "likes_count": 13
}
```

#### Unliker un commentaire
```
DELETE /api/forum/comments/{comment_id}/like/
Authorization: Bearer <token>
```

**Réponse :**
```json
{
  "message": "Like retiré avec succès",
  "liked": false,
  "likes_count": 12
}
```

---

## Permissions

- **Forums** : Création/modification/suppression réservées aux administrateurs (`is_staff=True`)
- **Conversations** : Tous les utilisateurs authentifiés peuvent créer. Seul l'auteur ou un admin peut modifier/supprimer.
- **Commentaires** : Tous les utilisateurs authentifiés peuvent créer. Seul l'auteur ou un admin peut modifier/supprimer.
- **Likes** : Tous les utilisateurs authentifiés peuvent liker/unliker.

## Authentification

Tous les endpoints nécessitent une authentification (sauf la lecture publique des forums et conversations).

Utilisez le token JWT obtenu via `/api/auth/login/` dans le header :
```
Authorization: Bearer <token>
```

## Upload d'images

Les images sont acceptées pour :
- **Forums** : `image` (jpg, jpeg, png, gif, webp)
- **Conversations** : `image` (jpg, jpeg, png, gif, webp)

Les fichiers sont stockés dans :
- `media/forums/` pour les forums
- `media/conversations/` pour les conversations

## Format des timestamps

Les timestamps sont retournés dans deux formats :
- **ISO 8601** : `created_at`, `updated_at` (pour le traitement technique)
- **Format lisible** : `timestamp`, `last_activity` (pour l'affichage frontend)
  - "À l'instant"
  - "Il y a X minutes"
  - "Il y a X heures"
  - "Il y a X jours"
  - "DD/MM/YYYY" (si > 7 jours)

## Exemples d'utilisation

### Créer une conversation avec image
```javascript
const formData = new FormData();
formData.append('forum', 1);
formData.append('title', 'Nouvelle politique de télétravail');
formData.append('description', 'Discussion sur les nouvelles directives...');
formData.append('image', imageFile);

fetch('http://localhost:8000/api/forum/conversations/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

### Créer un commentaire
```javascript
fetch('http://localhost:8000/api/forum/comments/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    conversation: 1,
    content: 'Mon commentaire sur cette conversation'
  })
});
```

### Liker un commentaire
```javascript
fetch('http://localhost:8000/api/forum/comments/1/like/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

