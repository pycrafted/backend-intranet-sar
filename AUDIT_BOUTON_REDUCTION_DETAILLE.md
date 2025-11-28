# 🔍 Audit Détaillé : Problème du Bouton de Réduction

## 📋 Description du Problème

**Symptômes observés** :
1. ✅ Si le nœud est **fermé par défaut** → Le bouton fonctionne (ouvrir/fermer)
2. ❌ Si le nœud est **ouvert par défaut** → Le bouton ne fonctionne pas pour fermer
3. ✅ Si le nœud est **fermé au chargement** → On peut l'ouvrir et le fermer normalement

## 🔎 Analyse du Code

### **Point Critique 1 : Logique de Fallback Incohérente**

**Fichier** : `react-flow-organigramme.tsx`

**Ligne 215 et 277** :
```typescript
const isExpanded = expandedNodes.get(emp.id) || level < 2
```

**Ligne 84** (dans `toggleNodeExpansion`) :
```typescript
const isCurrentlyExpanded = newMap.get(nodeId) || false
```

**PROBLÈME IDENTIFIÉ** :

Il y a une **incohérence fondamentale** entre :
- Comment `buildHierarchy` détermine si un nœud est expansé
- Comment `toggleNodeExpansion` détermine si un nœud est expansé

**Scénario problématique** :

1. **Nœud de niveau < 2 (niveau 0, 1, ou 2)** :
   - Dans `buildHierarchy` : `isExpanded = expandedNodes.get(emp.id) || level < 2`
   - Si le nœud n'est **pas dans le Map**, `expandedNodes.get(emp.id)` retourne `undefined`
   - Mais `level < 2` est `true`, donc `isExpanded = true` (fallback)
   - **Résultat** : Le nœud est affiché comme expansé

2. **Dans `toggleNodeExpansion`** :
   - `isCurrentlyExpanded = newMap.get(nodeId) || false`
   - Si le nœud n'est **pas dans le Map**, `newMap.get(nodeId)` retourne `undefined`
   - Donc `isCurrentlyExpanded = false`
   - **Résultat** : Le système pense que le nœud est fermé

3. **Quand l'utilisateur clique sur "Réduire"** :
   - Le nœud est visuellement expansé (grâce au fallback `level < 2`)
   - Mais `isCurrentlyExpanded = false` (car pas dans le Map)
   - Donc le code exécute le bloc `else` : `newMap.set(nodeId, true)`
   - **Résultat** : Au lieu de fermer, on essaie d'ouvrir ! Le nœud reste ouvert.

### **Point Critique 2 : Initialisation Incomplète**

**Lignes 60-78** : L'initialisation ajoute seulement les niveaux 0, 1 et 2 au Map :
```typescript
initialExpanded.set(ceo.id, true)  // Niveau 0
level1.forEach(emp => initialExpanded.set(emp.id, true))  // Niveau 1
level2.forEach(e => initialExpanded.set(e.id, true))  // Niveau 2
```

**PROBLÈME** :
- Les nœuds de niveau 0, 1, 2 sont explicitement dans le Map → Ils fonctionnent
- Mais si un nœud de niveau >= 3 est ouvert par défaut (dans le Map), il fonctionne aussi
- **MAIS** : Si un nœud de niveau < 2 n'est pas explicitement dans le Map (ce qui ne devrait pas arriver normalement), il y a le problème décrit ci-dessus

### **Point Critique 3 : Condition de Fallback Problématique**

**Le fallback `|| level < 2` crée deux "sources de vérité"** :

1. **Source 1** : Le Map `expandedNodes` (état explicite)
2. **Source 2** : Le fallback `level < 2` (règle implicite)

**Quand les deux sont en conflit** :
- Le Map dit : "Pas dans le Map" (donc fermé selon la logique normale)
- Le fallback dit : "Niveau < 2" (donc ouvert)
- `buildHierarchy` utilise le fallback → Affiche comme ouvert
- `toggleNodeExpansion` utilise seulement le Map → Pense que c'est fermé
- **Résultat** : Incohérence

### **Point Critique 4 : Synchronisation Map vs Affichage**

**Ligne 293** : `isExpanded: isExpanded` est passé au composant `EmployeeNode`

**Ligne 168** (dans `EmployeeNode`) : Le bouton utilise `isExpanded` pour déterminer son état visuel

**PROBLÈME** :
- Si `isExpanded` vient du fallback (`level < 2`), le bouton affiche "Réduire"
- Mais `toggleNodeExpansion` vérifie le Map, qui dit que le nœud n'est pas expansé
- Donc le clic essaie d'ouvrir au lieu de fermer

## 🎯 Cause Racine Identifiée

### **Cause Principale : Incohérence entre Fallback et État Réel**

Le problème survient quand :
1. Un nœud de niveau < 2 n'est **pas explicitement dans le Map** `expandedNodes`
2. Mais il est considéré comme expansé grâce au fallback `|| level < 2`
3. Le bouton affiche "Réduire" (car `isExpanded = true` via fallback)
4. Mais `toggleNodeExpansion` pense qu'il est fermé (car pas dans le Map)
5. Le clic essaie d'ouvrir au lieu de fermer

### **Pourquoi ça marche parfois ?**

1. **Si le nœud est fermé par défaut** :
   - Il n'est pas dans le Map
   - `level >= 2`, donc pas de fallback
   - `isExpanded = false` partout
   - Le clic ouvre → Ajoute au Map → Fonctionne

2. **Si le nœud est ouvert au chargement (dans le Map)** :
   - Il est explicitement dans le Map
   - `isExpanded = true` partout
   - Le clic ferme → Retire du Map → Fonctionne

3. **Si le nœud est de niveau < 2 et pas dans le Map** :
   - `buildHierarchy` dit : ouvert (fallback)
   - `toggleNodeExpansion` dit : fermé (pas dans Map)
   - **INCOHÉRENCE** → Ne fonctionne pas

## 🔧 Solution Technique

### **Solution 1 : Initialiser TOUS les nœuds de niveau < 2 dans le Map**

S'assurer que tous les nœuds de niveau < 2 sont **toujours** dans le Map lors de l'initialisation.

### **Solution 2 : Utiliser le même fallback dans toggleNodeExpansion**

Modifier `toggleNodeExpansion` pour utiliser la même logique :
```typescript
const getNodeLevel = (nodeId: number) => {
  // Calculer le niveau du nœud
  // ...
}

const isCurrentlyExpanded = newMap.get(nodeId) ?? (getNodeLevel(nodeId) < 2)
```

### **Solution 3 : Éliminer le fallback et initialiser explicitement**

Au lieu d'utiliser `|| level < 2`, s'assurer que tous les nœuds de niveau < 2 sont **toujours** dans le Map, même s'ils sont fermés.

### **Solution 4 : Utiliser une fonction utilitaire commune**

Créer une fonction `isNodeExpanded(nodeId, level)` qui est utilisée partout :
```typescript
const isNodeExpanded = useCallback((nodeId: number, level: number) => {
  return expandedNodes.get(nodeId) ?? (level < 2)
}, [expandedNodes])
```

## 📊 Scénarios de Test

### **Scénario A : Nœud niveau 0 (CEO)**
- ✅ Initialisé dans le Map → Fonctionne
- ❌ Si pas dans le Map → Incohérence (ne devrait pas arriver)

### **Scénario B : Nœud niveau 1 (N-1 du CEO)**
- ✅ Initialisé dans le Map → Fonctionne
- ❌ Si pas dans le Map → Incohérence (ne devrait pas arriver)

### **Scénario C : Nœud niveau 2 (N-2 du CEO)**
- ✅ Initialisé dans le Map → Fonctionne
- ❌ Si pas dans le Map → Incohérence (ne devrait pas arriver)

### **Scénario D : Nœud niveau 3+**
- ✅ Si fermé (pas dans Map) → Fonctionne
- ✅ Si ouvert (dans Map) → Fonctionne
- ✅ Pas de fallback, donc pas d'incohérence

## 🎯 Conclusion de l'Audit

**Cause racine** : Incohérence entre la logique de fallback (`|| level < 2`) utilisée dans `buildHierarchy` et la logique purement basée sur le Map utilisée dans `toggleNodeExpansion`.

**Solution recommandée** : 
1. S'assurer que tous les nœuds de niveau < 2 sont **toujours** dans le Map lors de l'initialisation
2. OU utiliser la même fonction utilitaire partout pour déterminer `isExpanded`
3. OU éliminer le fallback et gérer explicitement tous les nœuds dans le Map

**Priorité** : HAUTE - Le problème affecte l'expérience utilisateur de manière significative.

