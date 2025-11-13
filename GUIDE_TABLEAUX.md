# 📊 Guide Détection des Tableaux

## Vue d'ensemble

L'application détecte automatiquement les tableaux dans les documents Word et les convertit en tableaux HTML stylés pour Elementor.

---

## 🎯 Fonctionnalités

### Détection automatique
- ✅ Tableaux Word natifs
- ✅ Préservation de l'ordre dans le document
- ✅ Détection des headers (première ligne)
- ✅ Support multi-colonnes (les tableaux sont distribués)

### Conversion HTML
- Tableaux convertis en HTML complet
- Style intégré (bordures, padding, couleurs)
- Headers avec fond gris et texte en gras
- Largeur 100% responsive

---

## 📝 Exemple de tableau Word

```
┌──────────────┬──────────────┬──────────┐
│ Type d'IA    │ Carac.       │ Exemple  │  ← Header
├──────────────┼──────────────┼──────────┤
│ Symbolique   │ Règles SI-   │ Expert   │
│              │ ALORS        │ System   │
├──────────────┼──────────────┼──────────┤
│ Connexion.   │ ML, Réseaux  │ Deep     │
│              │ neuronaux    │ Learning │
└──────────────┴──────────────┴──────────┘
```

---

## 🔄 Conversion en HTML

Le tableau ci-dessus devient :

```html
<table style="width:100%; border-collapse: collapse;">
  <thead>
    <tr>
      <th style="border:1px solid #ddd; padding:8px; 
                 background-color:#f2f2f2; font-weight:bold;">
        Type d'IA
      </th>
      <th>Caractéristiques</th>
      <th>Exemple</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border:1px solid #ddd; padding:8px;">
        Symbolique
      </td>
      <td>Règles SI-ALORS</td>
      <td>Expert System</td>
    </tr>
    <!-- ... autres lignes -->
  </tbody>
</table>
```

---

## 📊 Statistiques d'extraction

### Document test : `demo_tables_complete.docx`

**Structure extraite :**
- 1 H1
- 3 H2
- 6 Paragraphes
- **3 Tableaux** ✅

**Tableaux détectés :**
1. **Tableau 1** : 4x3 (Types d'IA)
   - Header détecté : ✅
   
2. **Tableau 2** : 5x4 (Performances)
   - Header détecté : ❌ (heuristique)
   
3. **Tableau 3** : 3x2 (Applications)
   - Header détecté : ✅

---

## 🎨 Styles appliqués

### Headers (première ligne si détectée)
```css
background-color: #f2f2f2;
font-weight: bold;
border: 1px solid #ddd;
padding: 8px;
```

### Cellules normales
```css
border: 1px solid #ddd;
padding: 8px;
```

### Tableau complet
```css
width: 100%;
border-collapse: collapse;
```

---

## 🔍 Détection des headers

L'application utilise une heuristique pour détecter si la première ligne est un header :

```python
# Comparaison longueur moyenne des cellules
first_row_avg = moyenne_longueur(ligne_1)
second_row_avg = moyenne_longueur(ligne_2)

if first_row_avg < second_row_avg * 1.5:
    has_header = True
```

**Résultat :**
- Headers courts (titres) → Détectés ✅
- Headers longs → Traités comme lignes normales

---

## 📐 Comportement avec layouts multi-colonnes

Les tableaux sont distribués entre les colonnes selon la stratégie choisie :

### 1 Colonne
```
┌─────────────────────┐
│ Texte               │
│ Tableau 1           │
│ Texte               │
│ Tableau 2           │
└─────────────────────┘
```

### 2 Colonnes (auto)
```
┌──────────────┬──────────────┐
│ Texte        │ Tableau 2    │
│ Tableau 1    │ Texte        │
└──────────────┴──────────────┘
```

### 3 Colonnes (balanced)
```
┌────────┬────────┬────────┐
│ Texte  │ Tabl 2 │ Texte  │
│ Tabl 1 │ Texte  │ Tabl 3 │
└────────┴────────┴────────┘
```

---

## 📦 Résultats de conversion

### Widgets générés par document

| Document | Éléments | Tableaux | Widgets HTML |
|----------|----------|----------|--------------|
| test_with_table.docx | 4 | 1 | 1 table |
| demo_tables_complete.docx | 13 | 3 | 3 tables |

---

## 💡 Bonnes pratiques

### Dans Word
1. **Utiliser des tableaux natifs** (Insertion → Tableau)
2. **Première ligne = Header** (courts et descriptifs)
3. **Éviter les fusions** complexes de cellules
4. **Texte simple** dans les cellules

### Après import dans Elementor
1. Les tableaux sont modifiables via l'éditeur HTML
2. Possibilité d'ajouter des classes CSS personnalisées
3. Le style peut être surchargé par votre thème

---

## 🧪 Fichiers de test fournis

### Documents Word
- `test_with_table.docx` - Test simple (1 tableau)
- `demo_tables_complete.docx` - Test complet (3 tableaux)

### JSON générés
- `demo_1col_auto.json` - Version 1 colonne
- `demo_2col_auto.json` - Version 2 colonnes
- `demo_3col_balanced.json` - Version 3 colonnes

**Tous contiennent les mêmes 3 tableaux**, distribués différemment.

---

## ✅ Compatibilité

- **Elementor** : Version 0.4+
- **WordPress** : Toutes versions avec Elementor
- **Browsers** : Tous (HTML standard)
- **Responsive** : Oui (overflow-x: auto)

---

## 🚀 Utilisation

1. Créer tableau dans Word
2. Upload document dans l'application
3. Choisir layout (1/2/3 colonnes)
4. Convertir
5. Télécharger JSON
6. Importer dans Elementor

**Les tableaux apparaissent automatiquement** dans la page avec le style par défaut.

---

## 🎯 Core intact

L'ajout de la détection des tableaux **n'affecte pas** :
- ✅ L'ordre des éléments
- ✅ La position des images
- ✅ La détection des titres
- ✅ Les layouts multi-colonnes

**Extension sans modification du core existant.**
