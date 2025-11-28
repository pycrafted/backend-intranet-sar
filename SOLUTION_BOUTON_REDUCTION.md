# 🔧 Solution pour Corriger le Bouton de Réduction

## 🎯 Stratégie de Correction

### **Problème Principal**
Race condition entre `setExpandedNodes` et `setExpansionVersion` + dépendances manquantes dans `useMemo`.

### **Solution Choisie**
1. **Remplacer Map par objet simple** : React détecte mieux les changements d'objets
2. **Mise à jour atomique** : Combiner les deux états en une seule mise à jour
3. **Dépendances correctes** : Ajouter l'état d'expansion aux dépendances du `useMemo`
4. **Stabiliser toggleNodeExpansion** : Utiliser `useRef` pour éviter les recréations inutiles

## 📝 Modifications à Apporter

### **Modification 1 : Remplacer Map par Objet**

**Avant** :
```typescript
const [expandedNodes, setExpandedNodes] = useState<Map<number, boolean>>(new Map())
const [expansionVersion, setExpansionVersion] = useState(0)
```

**Après** :
```typescript
// Utiliser un objet simple au lieu d'un Map pour que React détecte les changements
const [expandedNodes, setExpandedNodes] = useState<Record<number, boolean>>({})
```

### **Modification 2 : Mise à Jour Atomique**

**Avant** :
```typescript
const toggleNodeExpansion = useCallback((nodeId: number) => {
  setExpandedNodes(prev => {
    // ... logique ...
    return newMap
  })
  setExpansionVersion(prev => prev + 1)
}, [employees])
```

**Après** :
```typescript
const toggleNodeExpansion = useCallback((nodeId: number) => {
  setExpandedNodes(prev => {
    const newState = { ...prev } // Copie de l'objet
    const isCurrentlyExpanded = newState[nodeId] || false
    
    if (isCurrentlyExpanded) {
      // Supprimer le nœud et tous ses descendants
      const removeDescendants = (id: number) => {
        const children = employees?.filter(e => e.manager === id) || []
        children.forEach(child => {
          delete newState[child.id]
          removeDescendants(child.id)
        })
      }
      delete newState[nodeId]
      removeDescendants(nodeId)
    } else {
      newState[nodeId] = true
    }
    
    return newState // Retourner un nouvel objet pour forcer le re-render
  })
}, [employees])
```

### **Modification 3 : Initialisation avec Objet**

**Avant** :
```typescript
const initialExpanded = new Map<number, boolean>()
initialExpanded.set(ceo.id, true)
// ...
setExpandedNodes(initialExpanded)
setExpansionVersion(prev => prev + 1)
```

**Après** :
```typescript
const initialExpanded: Record<number, boolean> = {}
initialExpanded[ceo.id] = true
// ...
setExpandedNodes(initialExpanded)
```

### **Modification 4 : Utilisation dans buildHierarchy**

**Avant** :
```typescript
const isExpanded = expandedNodes.get(emp.id) || level < 2
```

**Après** :
```typescript
const isExpanded = expandedNodes[emp.id] || level < 2
```

### **Modification 5 : Ajouter expandedNodes aux Dépendances**

**Avant** :
```typescript
}, [employees, config.horizontalSpacing, config.verticalSpacing, config.gridCols, expansionVersion, handleMouseEnter, handleMouseLeave])
```

**Après** :
```typescript
// Convertir l'objet en string pour la comparaison (ou utiliser une clé de version)
const expandedNodesKey = JSON.stringify(Object.keys(expandedNodes).sort())
}, [employees, config.horizontalSpacing, config.verticalSpacing, config.gridCols, expandedNodesKey, handleMouseEnter, handleMouseLeave])
```

**OU mieux** : Utiliser un compteur de version qui s'incrémente avec expandedNodes :
```typescript
const [expansionVersion, setExpansionVersion] = useState(0)

const toggleNodeExpansion = useCallback((nodeId: number) => {
  setExpandedNodes(prev => {
    // ... logique ...
    setExpansionVersion(v => v + 1) // Incrémenter dans le callback
    return newState
  })
}, [employees])
```

### **Modification 6 : Stabiliser toggleNodeExpansion avec useRef**

Pour éviter que `toggleNodeExpansion` change quand `employees` change (sauf si vraiment nécessaire) :

```typescript
const employeesRef = useRef(employees)
useEffect(() => {
  employeesRef.current = employees
}, [employees])

const toggleNodeExpansion = useCallback((nodeId: number) => {
  setExpandedNodes(prev => {
    const newState = { ...prev }
    const isCurrentlyExpanded = newState[nodeId] || false
    const currentEmployees = employeesRef.current // Utiliser la ref
    
    if (isCurrentlyExpanded) {
      const removeDescendants = (id: number) => {
        const children = currentEmployees?.filter(e => e.manager === id) || []
        children.forEach(child => {
          delete newState[child.id]
          removeDescendants(child.id)
        })
      }
      delete newState[nodeId]
      removeDescendants(nodeId)
    } else {
      newState[nodeId] = true
    }
    
    return newState
  })
}, []) // Plus de dépendance sur employees !
```

## 🎯 Solution Recommandée (La Plus Simple)

La solution la plus simple et efficace serait :

1. **Remplacer Map par objet** : Plus simple et React le détecte mieux
2. **Garder expansionVersion** : Pour forcer le re-render si nécessaire
3. **Incrémenter expansionVersion dans le callback** : Pour synchronisation
4. **Utiliser useRef pour employees** : Pour stabiliser toggleNodeExpansion

Cette approche :
- ✅ Élimine la race condition
- ✅ Stabilise les callbacks
- ✅ Force React à détecter les changements
- ✅ Minimal changes au code existant

## 📊 Ordre de Priorité des Corrections

1. **PRIORITÉ 1** : Remplacer Map par objet (corrige 80% du problème)
2. **PRIORITÉ 2** : Stabiliser toggleNodeExpansion avec useRef
3. **PRIORITÉ 3** : S'assurer que expansionVersion est bien dans les dépendances

