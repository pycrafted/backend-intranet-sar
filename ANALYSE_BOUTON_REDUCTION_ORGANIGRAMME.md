# 📋 Compte-Rendu d'Analyse : Problème du Bouton de Réduction dans l'Organigramme

## 🔍 Problème Identifié

Le bouton de réduction (collapse/expand) dans la page organigramme ne fonctionne pas toujours de manière fiable.

## 🏗️ Architecture du Système

### 1. **Composant Principal**
- **Fichier** : `frontend-intranet-sar/components/react-flow-organigramme.tsx`
- **Composant** : `ReactFlowOrganigramme`

### 2. **Composant du Nœud**
- **Fichier** : `frontend-intranet-sar/components/nodes/employee-node.tsx`
- **Composant** : `EmployeeNode`
- **Bouton de réduction** : Lignes 161-183

### 3. **Flux de Données**

```
EmployeeNode (bouton cliqué)
  ↓ onClick → onToggleExpand()
  ↓
toggleNodeExpansion(employee.id)
  ↓ Modifie expandedNodes (Map)
  ↓ Incrémente expansionVersion
  ↓
useMemo (recalcule nodes/edges)
  ↓ Dépend de expansionVersion
  ↓
buildHierarchy() utilise expandedNodes.get(employee.id)
  ↓
setNodes() / setEdges() via useEffect
  ↓
React Flow re-render
```

## 🔎 Analyse Détaillée

### **Point 1 : Gestion de l'État avec Map**

**Code concerné** : Lignes 56-57, 81-103
```typescript
const [expandedNodes, setExpandedNodes] = useState<Map<number, boolean>>(new Map())
const [expansionVersion, setExpansionVersion] = useState(0)
```

**Problème potentiel** :
- React ne détecte pas automatiquement les changements dans un `Map` car il compare par référence
- Le code utilise `expansionVersion` comme mécanisme de contournement pour forcer le re-render
- Cependant, si `expandedNodes` n'est pas correctement synchronisé, le `useMemo` pourrait utiliser une version obsolète

### **Point 2 : Fonction toggleNodeExpansion**

**Code concerné** : Lignes 81-103
```typescript
const toggleNodeExpansion = useCallback((nodeId: number) => {
  setExpandedNodes(prev => {
    const newMap = new Map(prev)
    const isCurrentlyExpanded = newMap.get(nodeId) || false
    
    if (isCurrentlyExpanded) {
      // Fermeture : supprime le nœud et tous ses descendants
      const removeDescendants = (id: number) => {
        const children = employees?.filter(e => e.manager === id) || []
        children.forEach(child => {
          newMap.delete(child.id)
          removeDescendants(child.id)
        })
      }
      newMap.delete(nodeId)
      removeDescendants(nodeId)
    } else {
      newMap.set(nodeId, true)
    }
    return newMap
  })
  setExpansionVersion(prev => prev + 1)
}, [employees])
```

**Problèmes identifiés** :

1. **Dépendance `employees`** : 
   - La fonction dépend de `employees` dans le callback
   - Si `employees` change, la fonction est recréée
   - Cela peut causer des problèmes de synchronisation si `employees` change pendant l'expansion

2. **Suppression récursive des descendants** :
   - La fonction `removeDescendants` est récursive
   - Si la hiérarchie est profonde, cela peut prendre du temps
   - Pas de vérification si les enfants existent réellement dans le Map

3. **Race condition potentielle** :
   - `setExpandedNodes` et `setExpansionVersion` sont deux appels séparés
   - Entre les deux, React pourrait re-render avec un état incohérent

### **Point 3 : Utilisation dans buildHierarchy**

**Code concerné** : Lignes 215, 277
```typescript
const isExpanded = expandedNodes.get(emp.id) || level < 2
```

**Problème identifié** :
- Si `expandedNodes` n'est pas à jour au moment du calcul, `isExpanded` sera incorrect
- Le fallback `|| level < 2` peut masquer des problèmes d'état

### **Point 4 : useMemo et Dépendances**

**Code concerné** : Ligne 612
```typescript
}, [employees, config.horizontalSpacing, config.verticalSpacing, config.gridCols, expansionVersion, handleMouseEnter, handleMouseLeave])
```

**Problèmes identifiés** :

1. **`expandedNodes` n'est pas dans les dépendances** :
   - Seul `expansionVersion` est utilisé comme dépendance
   - Le `useMemo` se recalcule quand `expansionVersion` change
   - Mais `buildHierarchy` lit directement `expandedNodes` qui n'est pas dans les dépendances
   - Cela peut créer une incohérence si `expandedNodes` change mais que `expansionVersion` n'est pas encore mis à jour

2. **`toggleNodeExpansion` n'est pas dans les dépendances** :
   - `buildHierarchy` utilise `toggleNodeExpansion` via `onToggleExpand`
   - Mais `toggleNodeExpansion` n'est pas dans les dépendances du `useMemo`
   - Si `toggleNodeExpansion` change (à cause de la dépendance `employees`), le `useMemo` ne se recalcule pas

### **Point 5 : Synchronisation avec React Flow**

**Code concerné** : Lignes 614-626
```typescript
const [nodesState, setNodes, onNodesChange] = useNodesState(nodes)
const [edgesState, setEdges, onEdgesChange] = useEdgesState(edges)

useEffect(() => {
  setNodes(nodes)
  setEdges(edges)
}, [nodes, edges, setNodes, setEdges])
```

**Problème potentiel** :
- Si `nodes` ou `edges` changent de référence mais ont le même contenu, React Flow pourrait ne pas détecter le changement
- Les nœuds React Flow sont identifiés par leur `id`, donc si un nœud est supprimé puis recréé avec le même `id`, cela peut causer des problèmes

## 🐛 Scénarios de Défaillance

### **Scénario 1 : Clics Rapides**
1. Utilisateur clique rapidement sur plusieurs boutons de réduction
2. Plusieurs appels à `toggleNodeExpansion` sont en cours
3. Les états `expandedNodes` et `expansionVersion` peuvent être désynchronisés
4. Le `useMemo` se recalcule avec un état intermédiaire incorrect

### **Scénario 2 : Changement de Département**
1. L'utilisateur change de département (filtre)
2. `employees` change
3. `toggleNodeExpansion` est recréé (nouvelle référence)
4. Les anciens callbacks `onToggleExpand` dans les nœuds pointent vers l'ancienne fonction
5. Le bouton ne fonctionne plus jusqu'à ce que les nœuds soient recréés

### **Scénario 3 : Nœuds Profonds**
1. L'utilisateur réduit un nœud avec beaucoup de descendants
2. La fonction récursive `removeDescendants` prend du temps
3. Pendant ce temps, l'utilisateur clique à nouveau
4. L'état peut être incohérent

### **Scénario 4 : Re-render Partiel**
1. `expansionVersion` change
2. `useMemo` se recalcule
3. Mais `expandedNodes` n'est pas encore mis à jour dans la closure
4. `buildHierarchy` utilise une version obsolète de `expandedNodes`

## 💡 Causes Probables

### **Cause Principale : Race Condition**

Le problème principal semble être une **race condition** entre :
1. La mise à jour de `expandedNodes` (asynchrone via `setExpandedNodes`)
2. L'incrémentation de `expansionVersion` (asynchrone via `setExpansionVersion`)
3. Le recalcul du `useMemo` qui lit `expandedNodes` directement

### **Cause Secondaire : Dépendances Manquantes**

Le `useMemo` ne dépend pas directement de `expandedNodes`, ce qui peut créer des incohérences.

### **Cause Tertiaire : Callbacks Obsolètes**

Les callbacks `onToggleExpand` dans les nœuds peuvent pointer vers une ancienne version de `toggleNodeExpansion` si `employees` change.

## 📊 Recommandations (Sans Modification du Code)

### **1. Vérification Immédiate**
- Ajouter des logs dans `toggleNodeExpansion` pour voir si la fonction est appelée
- Vérifier si `expansionVersion` est bien incrémenté
- Vérifier si `expandedNodes` est bien mis à jour

### **2. Tests à Effectuer**
- Tester avec des clics rapides multiples
- Tester après un changement de département
- Tester avec des nœuds ayant beaucoup de descendants
- Tester avec des nœuds profonds dans la hiérarchie

### **3. Points d'Attention**
- Surveiller les logs de console pour voir l'ordre des mises à jour
- Vérifier si le problème survient uniquement lors de la réduction ou aussi lors de l'expansion
- Vérifier si le problème est lié à certains nœuds spécifiques

## 🔧 Solutions Proposées (Pour Information)

### **Solution 1 : Utiliser un État Unifié**
Au lieu d'utiliser `Map` + `expansionVersion`, utiliser un objet simple qui force React à détecter les changements.

### **Solution 2 : Ajouter expandedNodes aux Dépendances**
Ajouter `expandedNodes` aux dépendances du `useMemo` (mais cela nécessiterait de convertir le Map en structure sérialisable).

### **Solution 3 : Utiliser useReducer**
Remplacer `useState` par `useReducer` pour gérer l'état de manière plus prévisible.

### **Solution 4 : Debounce les Clics**
Ajouter un debounce sur `toggleNodeExpansion` pour éviter les clics rapides multiples.

### **Solution 5 : Mémoriser toggleNodeExpansion**
S'assurer que `toggleNodeExpansion` ne change pas de référence sauf quand nécessaire.

## 📝 Conclusion

Le problème du bouton de réduction semble être causé par une **race condition** et des **dépendances manquantes** dans le `useMemo`. Le système utilise un mécanisme de contournement (`expansionVersion`) pour forcer le re-render, mais cela ne garantit pas que `expandedNodes` soit à jour au moment du recalcul.

Le problème est **intermittent** car il dépend de :
- La vitesse des clics de l'utilisateur
- Le timing des mises à jour d'état React
- Les changements de `employees` (filtrage par département)

Pour résoudre définitivement le problème, il faudrait :
1. Réorganiser la gestion de l'état pour éviter les race conditions
2. S'assurer que toutes les dépendances sont correctement déclarées
3. Peut-être utiliser un système de state management plus robuste (useReducer ou Zustand)




