# Guide d'Optimisation des Performances

## 📊 Logs de Performance

Un middleware de performance a été ajouté pour mesurer le temps de chargement de chaque page. Les logs apparaissent dans la console avec les informations suivantes :

- **🟢 Vert** : < 500ms (excellent)
- **🟠 Orange** : 500ms - 1s (acceptable)
- **🟡 Jaune** : 1s - 2s (lent, optimisation recommandée)
- **🔴 Rouge** : > 2s (très lent, optimisation urgente)

Format des logs :
```
[PERF] METHOD /path | Temps total: XXXms | SQL: N requêtes (XXXms) | Traitement: XXXms | Status: XXX
```

## 🎯 Pistes d'Optimisation

### 1. Optimisation des Requêtes SQL (N+1 Problem)

**Problème** : Requêtes SQL multiples pour charger des données liées

**Solutions** :
- Utiliser `select_related()` pour les relations ForeignKey
- Utiliser `prefetch_related()` pour les relations ManyToMany et Reverse ForeignKey
- Utiliser `only()` et `defer()` pour limiter les champs chargés

**Exemple** :
```python
# ❌ Mauvais (N+1 queries)
articles = Article.objects.all()
for article in articles:
    print(article.author.name)  # 1 requête par article

# ✅ Bon (1 query)
articles = Article.objects.select_related('author').all()
for article in articles:
    print(article.author.name)  # Pas de requête supplémentaire
```

### 2. Mise en Cache

**Problème** : Données recalculées à chaque requête

**Solutions** :
- Utiliser le cache Redis pour les données fréquemment accédées
- Mettre en cache les résultats de requêtes complexes
- Utiliser `@cache_page` pour les vues statiques

**Exemple** :
```python
from django.views.decorators.cache import cache_page
from django.core.cache import cache

@cache_page(60 * 15)  # Cache 15 minutes
def my_view(request):
    ...

# Ou dans la vue
def my_view(request):
    cache_key = f'articles_{page}'
    articles = cache.get(cache_key)
    if articles is None:
        articles = Article.objects.all()
        cache.set(cache_key, articles, 60 * 15)
    return articles
```

### 3. Pagination

**Problème** : Chargement de toutes les données en une fois

**Solutions** :
- Implémenter la pagination pour les listes
- Utiliser `Paginator` de Django
- Limiter le nombre d'éléments par page (10-50)

**Exemple** :
```python
from django.core.paginator import Paginator

def my_view(request):
    articles = Article.objects.all()
    paginator = Paginator(articles, 20)  # 20 par page
    page = request.GET.get('page', 1)
    articles_page = paginator.get_page(page)
    return render(request, 'template.html', {'articles': articles_page})
```

### 4. Optimisation des Images

**Problème** : Images trop lourdes chargées en entier

**Solutions** :
- Compresser les images avant upload
- Utiliser des formats modernes (WebP)
- Implémenter le lazy loading
- Générer des thumbnails pour les listes

**Exemple Frontend** :
```tsx
<img 
  src={imageUrl} 
  loading="lazy" 
  alt="Description"
  style={{ width: '100%', height: 'auto' }}
/>
```

### 5. Optimisation des Requêtes API

**Problème** : Appels API multiples et séquentiels

**Solutions** :
- Utiliser `Promise.all()` pour les appels parallèles
- Implémenter le debouncing pour les recherches
- Mettre en cache les réponses API
- Utiliser la pagination côté API

**Exemple** :
```typescript
// ❌ Mauvais (séquentiel)
const user = await fetchUser();
const posts = await fetchPosts(user.id);
const comments = await fetchComments(posts[0].id);

// ✅ Bon (parallèle)
const [user, posts, comments] = await Promise.all([
  fetchUser(),
  fetchPosts(userId),
  fetchComments(postId)
]);
```

### 6. Optimisation de la Base de Données

**Problème** : Index manquants, requêtes non optimisées

**Solutions** :
- Ajouter des index sur les colonnes fréquemment filtrées
- Analyser les requêtes lentes avec `EXPLAIN`
- Utiliser `db_index=True` dans les modèles
- Éviter les `LIKE '%pattern%'` (utiliser des index full-text)

**Exemple** :
```python
class Article(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    created_at = models.DateTimeField(db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
```

### 7. Optimisation Frontend (Next.js)

**Problème** : Bundle JavaScript trop lourd, rendu bloquant

**Solutions** :
- Utiliser le code splitting avec `dynamic()`
- Implémenter le Server-Side Rendering (SSR) pour les pages statiques
- Utiliser `getStaticProps` pour les données statiques
- Optimiser les imports (éviter les imports globaux)

**Exemple** :
```typescript
// Lazy loading des composants
const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <p>Chargement...</p>,
  ssr: false
});
```

### 8. Compression et Minification

**Problème** : Fichiers CSS/JS non compressés

**Solutions** :
- Activer la compression Gzip/Brotli
- Minifier les fichiers CSS/JS en production
- Utiliser CDN pour les assets statiques

### 9. Optimisation des Sessions

**Problème** : Sessions lourdes ou trop fréquentes

**Solutions** :
- Utiliser Redis pour les sessions (déjà configuré)
- Réduire `SESSION_SAVE_EVERY_REQUEST` si nécessaire
- Nettoyer les sessions expirées régulièrement

### 10. Monitoring et Analyse

**Actions** :
- Surveiller les logs de performance régulièrement
- Identifier les pages les plus lentes
- Analyser les requêtes SQL avec `django-debug-toolbar`
- Utiliser des outils comme New Relic ou Sentry

## 🔧 Outils Recommandés

1. **django-debug-toolbar** : Pour analyser les requêtes SQL en développement
2. **django-silk** : Profiling des requêtes
3. **Redis** : Cache (déjà configuré)
4. **PostgreSQL EXPLAIN** : Pour analyser les requêtes SQL
5. **Lighthouse** : Pour analyser les performances frontend

## 📈 Objectifs de Performance

- **Temps de chargement initial** : < 1s
- **Temps de réponse API** : < 500ms
- **Requêtes SQL par page** : < 10
- **Temps total SQL** : < 200ms
- **Score Lighthouse** : > 90

## 🚀 Actions Immédiates

1. ✅ Middleware de performance ajouté
2. ⏳ Analyser les logs pour identifier les pages lentes
3. ⏳ Optimiser les requêtes SQL avec select_related/prefetch_related
4. ⏳ Mettre en cache les données fréquemment accédées
5. ⏳ Implémenter la pagination partout où nécessaire
6. ⏳ Optimiser les images (compression, lazy loading)

