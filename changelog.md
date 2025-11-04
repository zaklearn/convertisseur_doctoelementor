# 📝 Changelog - Word to Elementor Converter

Toutes les modifications importantes du projet sont documentées ici.

---

## [3.4.0] - 2025-11-04

### 🚀 OPTIMISATION & EXPORT ZIP

#### 🎉 Ce qui est nouveau

**Package de téléchargement complet**
-   ✅ **Export ZIP :** L'application génère désormais un fichier `.zip` contenant le `_elementor.json` ainsi qu'un sous-dossier `images/` avec toutes les images extraites.
-   ✅ **Bouton de téléchargement ZIP :** Ajout d'un bouton de téléchargement "Package (JSON + Images)" (style primaire) à côté du bouton "JSON Seulement".

**Optimisations du workflow**
-   ✅ **Noms d'images uniques :** L'extraction d'images (`parse_document` et `parse_pdf`) utilise maintenant un préfixe temporel (ex: `20251104_213005_001.png`) pour éviter les conflits de noms et les problèmes de cache dans la médiathèque WordPress.
-   ✅ **Vidage du cache :** Ajout d'un bouton "Vider le cache des images" dans la sidebar pour supprimer le dossier `outputs` local et libérer de l'espace.

#### 🔄 Modifications des fichiers existants

**`app.py`** :
-   Import de `zipfile`, `io`, et `shutil`.
-   Ajout de la logique de création de ZIP en mémoire pour le téléchargement du package.
-   Ajout de la fonction `clear_output_cache` et du bouton associé dans la sidebar.
-   **Réorganisation de l'interface :** "Étape 1 : Charger" et "Étape 2 : Lancer" sont maintenant sur deux colonnes.
-   Ajout du logo `assets/img/logo.png` (width=90) en haut de la sidebar.
-   Ajout de CSS pour cacher le bouton d'agrandissement sur les images.

**`word_to_elementor.py`** :
-   `parse_document()` et `parse_pdf()` renvoient maintenant le `output_folder_path` pour la création du ZIP.
-   Modification de la logique de nommage des fichiers images pour inclure un `timestamp_prefix`.

---

## [3.3.0] - 2025-11-04

### 🔧 REFACTOR "NO-AI" & INTÉGRATION CRÉDITS

#### 🎉 Ce qui est nouveau

-   ✅ **Module de Crédits :** Ajout d'un fichier `credits.py` dédié pour gérer l'attribution, la licence (MIT + Attribution) et les informations sur l'auteur (Zakaria Benhoumad) et l'organisation (ONG Meridie).
-   ✅ **Crédits Dynamiques :** Remplacement des sections statiques "À propos" et "Footer" dans `app.py` par des appels dynamiques aux fonctions `show_credits_sidebar(language="fr")` et `show_credits_footer(language="fr")`.

#### 🧹 Refactorisation

-   ✅ **Suppression totale de l'IA :** L'application est désormais 100% "No-AI" (extraction directe).
-   ✅ **Nettoyage :** Suppression de toutes les dépendances, imports (`google.generativeai`, `dotenv`), fonctions (`get_semantic_structure`, `configure_gemini`) et logique conditionnelle liés à l'API Gemini.
-   ✅ **Simplification :** Le script `word_to_elementor.py` ne contient plus l'argument CLI `--use-ai`.

#### 📁 Nouveaux fichiers

1.  **`credits.py`** - Module de gestion des attributions et de la licence.

#### 🔄 Modifications des fichiers existants

**`app.py`** :
-   Suppression de toute la logique de clé API et de la checkbox "Utiliser IA Gemini".
-   Le flux de conversion utilise désormais *uniquement* l'extraction directe.
-   Import et intégration du nouveau module `credits.py`.

**`word_to_elementor.py`** :
-   Suppression de toutes les fonctions et imports liés à Gemini AI.
-   Nettoyage de la fonction `main()` pour supprimer la logique `--use-ai`.

---

## [3.2.0] - 2025-11-04

### 🔗 NOUVELLE FONCTIONNALITÉ - Liaison des URL d'images

#### ❌ Problème identifié
Le JSON généré contenait des widgets d'image avec des champs `"url"` vides (ex: `"url": ""`). Cela forçait l'utilisateur à relier manuellement chaque image après l'importation dans Elementor.

#### ✅ Solution appliquée
Implémentation d'un système de liaison "semi-automatique" des URL :

1.  **Interface (Sidebar) :** Ajout d'un champ de texte "URL de base des médias" dans `app.py`.
2.  **Logique :** L'utilisateur uploade ses images sur WordPress, copie l'URL du dossier (ex: `.../wp-content/uploads/2025/11/`) et la colle dans ce champ.
3.  **Injection :** L'URL de base est passée à `build_elementor_json` et `create_image_widget`.
4.  **Résultat :** Le JSON final contient maintenant l'URL complète pour chaque image (ex: `"url": ".../2025/11/image_001.png"`), permettant un import 100% fonctionnel.

#### 🔄 Modifications des fichiers existants

**`word_to_elementor.py`** :
-   `create_image_widget()` accepte `base_image_url` pour construire l'URL complète.
-   `build_elementor_json()` accepte et transmet `base_image_url`.
-   Argument CLI `--base-url` ajouté pour la ligne de commande.

**`app.py`** :
-   Ajout du champ `st.text_input("URL de base des médias...")` dans la sidebar.
-   L'URL est passée à `build_elementor_json` lors de la conversion.
-   Mise à jour de la FAQ pour expliquer ce nouveau workflow.

---

## [3.1.0] - 2025-11-04

### 🔧 CORRECTIF CRITIQUE - Mode "Sans IA" (Extraction Directe)

#### ❌ Problème identifié
L'extraction directe (sans IA) souffrait de deux bugs critiques :
1.  **Crash :** L'application (`word_to_elementor.py`) tentait d'appeler la variable `model` (liée à l'IA) même si elle n'était pas initialisée, provoquant un `NameError`.
2.  **Images manquantes :** L'extracteur (`text_extractor.py`) ignorait les images si elles étaient seules sur un paragraphe (sans texte).

#### ✅ Solution appliquée

1.  **`word_to_elementor.py`** : Suppression de l'appel erroné à `get_semantic_structure` qui se trouvait en dehors de la condition de vérification de l'IA.
2.  **`text_extractor.py`** : Inversion de la logique dans `extract_text_from_docx`. Le script vérifie désormais la présence d'une image (`.xpath('.//pic:pic')`) *avant* de vérifier si le paragraphe contient du texte (`if not text: continue`).

#### 🎯 Impact utilisateur

-   ✅ Le mode "Extraction Directe" (Sans IA) est désormais stable et fonctionnel.
-   ✅ Toutes les images sont correctement détectées et incluses dans la structure.

---

## [3.0.0] - 2025-10-13

### 🎨 NOUVELLE FONCTIONNALITÉ MAJEURE - Layouts Multi-Colonnes

#### 🎉 Ce qui est nouveau

**Système de layouts paramétrable** pour créer des mises en page professionnelles :

- ✅ **6 types de layouts** disponibles
- ✅ **4 stratégies de distribution** du contenu
- ✅ **5 templates prédéfinis** optimisés
- ✅ **Interface Streamlit** enrichie pour la configuration
- ✅ **Support responsive** automatique

#### 📐 Types de layouts

1. **📄 Single Column** (100%) - Pages simples
2. **⚖️ Two Columns Equal** (50/50) - Comparaisons
3. **◀️ Sidebar Left** (33/67) - Documentation
4. **▶️ Sidebar Right** (67/33) - **Blog classique** ⭐
5. **▦ Three Columns** (33/33/33) - Portfolio
6. **📰 Blog Layout** (60/40) - **Articles optimisés** ⭐⭐

#### 🤖 Stratégies de distribution

- **Auto** : Distribution intelligente (recommandé)
- **Sequential** : Remplissage progressif
- **Alternating** : Zig-zag entre colonnes
- **Balanced** : Équilibrage automatique

#### 📦 Templates prédéfinis

- 📰 **Article de Blog** - Layout blog avec sidebar
- 🚀 **Landing Page** - Pleine largeur
- 🎨 **Portfolio** - Grille 3 colonnes
- 📰 **Magazine** - Style éditorial
- 📚 **Documentation** - Navigation latérale

#### 📁 Nouveaux fichiers

1. **`layouts.py`** - Module de configuration des layouts
   - Classes `LayoutConfig` et `ContentDistributor`
   - Définitions des layouts et stratégies
   - Templates prédéfinis

2. **`GUIDE_LAYOUTS.md`** - Documentation complète des layouts
   - Exemples visuels de chaque layout
   - Guide d'utilisation détaillé
   - Bonnes pratiques et conseils

#### 🔄 Modifications des fichiers existants

**`word_to_elementor.py`** :
- Fonction `build_elementor_json()` mise à jour
  - Nouveaux paramètres : `layout_type`, `distribution_strategy`
  - Support multi-colonnes
  - Distribution intelligente du contenu
- Arguments CLI enrichis :
  - `-l, --layout` : Choisir le type de layout
  - `-d, --distribution` : Choisir la stratégie

**`app.py`** :
- Nouvelle section "🎨 Layout et Colonnes" dans la sidebar
- Sélection de templates prédéfinis
- Configuration manuelle du layout
- Affichage du layout dans les statistiques
- Paramètres stockés dans session_state

---

## [2.1.0] - 2025-10-13

### 🔧 CORRECTIF CRITIQUE - Format JSON Elementor

#### ❌ Problème identifié
Lors de l'import du JSON dans Elementor, une erreur critique se produisait :