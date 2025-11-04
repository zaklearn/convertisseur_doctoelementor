# Word to Elementor Converter (V3.4)

🚀 **Script Python professionnel avec interface web Streamlit** pour convertir automatiquement des documents Word (.docx) et PDF (.pdf) en JSON importable par Elementor, en utilisant l'extraction directe, avec layouts multi-colonnes et export ZIP.

## ✨ NOUVEAU dans la V3.4 : Extraction Locale et Export ZIP

Cette version supprime toute dépendance à l'IA externe et se concentre sur un workflow local, rapide et robuste.

-   ✅ **Export en Package .ZIP :** Téléchargez un fichier `.zip` contenant votre `.json` et un dossier `images/` avec tous les médias extraits, prêt à être uploadé sur WordPress.
-   ✅ **Liaison d'URL d'images :** Une nouvelle "URL de base des médias" dans la sidebar vous permet de lier automatiquement les images au JSON, pour un import 100% fonctionnel dans Elementor.
-   ✅ **Extraction 100% Locale (No-AI) :** Plus besoin de clé API ! La conversion est plus rapide, gratuite et respecte la confidentialité en ne quittant jamais votre machine.
-   ✅ **Noms d'images uniques :** Les images sont renommées avec un timestamp (ex: `20251104_213005_001.png`) pour éviter les conflits dans la médiathèque WordPress.
-   ✅ **Support des PDF :** Conversion directe des fichiers `.pdf` (textes et images) en plus des `.docx`.
-   ✅ **Gestion des Crédits :** L'application inclut désormais un module de licence (`credits.py`) pour l'attribution (Zakaria Benhoumad & ONG Meridie).
-   ✅ **Nettoyage de Cache :** Un bouton dans la sidebar permet de vider le dossier `outputs/` local.

## 🎨 Layouts Multi-Colonnes (de la V3.0)

Créez des mises en page professionnelles avec **6 types de layouts** et **4 stratégies de distribution** :

### 📐 Layouts disponibles
-   **📄 Une colonne** - Contenu pleine largeur
-   **⚖️ Deux colonnes égales** - Répartition 50/50
-   **◀️ Sidebar gauche** - Navigation + Contenu (33/67)
-   **▶️ Sidebar droite** - **Idéal pour les blogs !** (67/33) ⭐
-   **▦ Trois colonnes** - Grilles et portfolios (33/33/33)
-   **📰 Layout blog optimisé** - Article professionnel (60/40) ⭐⭐

### 📦 Templates prédéfinis
-   📰 **Article de Blog** - Pour vos articles ⭐
-   🚀 Landing Page - Pages de vente
-   🎨 Portfolio - Galeries de projets
-   📰 Magazine - Style éditorial
-   📚 Documentation - Guides et tutoriels

## 📋 Fonctionnalités

-   ✅ **Interface web conviviale** avec Streamlit
-   ✅ **Extraction 100% Locale (No-AI)** basée sur les styles
-   ✅ **Support des .docx et .pdf**
-   ✅ **Layouts multi-colonnes** - 6 types + templates prédéfinis
-   ✅ **Distribution intelligente** du contenu entre colonnes
-   ✅ **Export en package .ZIP (JSON + Images)**
-   ✅ **Liaison d'URL d'images** pour WordPress
-   ✅ **Extraction complète** du contenu (textes, styles, images)
-   ✅ **Mapping strict** vers le format JSON Elementor (v0.4)
-   ✅ **Responsive automatique** (colonnes empilées sur mobile)
-   ✅ **Nettoyage de cache** intégré

## 🔧 Prérequis

-   Python 3.9 ou supérieur
-   Pip pour l'installation des dépendances

## 📦 Installation

### 1. Cloner ou télécharger le projet

```bash
# Si vous utilisez git
git clone [url-du-repo]
cd word-to-elementor

# Sinon, téléchargez et décompressez les fichiers