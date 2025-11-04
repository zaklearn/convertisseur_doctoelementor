#!/usr/bin/env python3
"""
app.py - Interface Streamlit pour Word to Elementor Converter

Application web conviviale pour convertir des documents Word/PDF en JSON Elementor
par extraction directe.

Version: 2.3 (Réorganisée)
"""

import streamlit as st
import json
import os
import sys
from io import BytesIO
from pathlib import Path
import tempfile
import shutil 
import zipfile 
import io      

# Import des fonctions du script principal
from word_to_elementor import (
    parse_document,
    parse_pdf,
    build_elementor_json
)
from text_extractor import extract_text_from_docx, extract_text_from_pdf

# Importation des crédits
try:
    from credits import show_credits_sidebar, show_credits_footer
    CREDITS_LOADED = True
except ImportError:
    CREDITS_LOADED = False

# Définition du dossier de cache
OUTPUT_CACHE_DIR = "outputs"

def clear_output_cache():
    """Supprime et recrée le dossier 'outputs'."""
    if os.path.exists(OUTPUT_CACHE_DIR):
        try:
            shutil.rmtree(OUTPUT_CACHE_DIR)
            os.makedirs(OUTPUT_CACHE_DIR)
            st.toast("Cache du dossier 'outputs' vidé !", icon="🗑️")
        except Exception as e:
            st.error(f"Erreur lors du vidage du cache : {e}")
    else:
        st.toast("Le dossier 'outputs' n'existe pas encore.", icon="ℹ️")


# ============================================================================
# CONFIGURATION DE LA PAGE STREAMLIT
# ============================================================================

st.set_page_config(
    page_title="Word to Elementor Converter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour améliorer l'apparence
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #92400E;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stDownloadButton button {
        background-color: #92400E;
        color: white;
        font-weight: bold;
        padding: 0.5rem 2rem;
        border-radius: 0.5rem;
    }
    /* Style pour le bouton ZIP (primaire) */
    .stDownloadButton button[kind="primary"] {
        background-color: #059669; /* Vert */
    }
    .stDownloadButton button[kind="primary"]:hover {
        background-color: #047857;
    }
    /* Cache le bouton d'agrandissement sur les images */
    
    </style>
""", unsafe_allow_html=True)


# ============================================================================
# INITIALISATION DE LA SESSION STATE
# ============================================================================

if 'conversion_done' not in st.session_state:
    st.session_state.conversion_done = False
if 'json_output' not in st.session_state:
    st.session_state.json_output = None
if 'semantic_structure' not in st.session_state:
    st.session_state.semantic_structure = None
if 'stats' not in st.session_state:
    st.session_state.stats = {}
if 'image_data' not in st.session_state:
    st.session_state.image_data = None
if 'output_folder_path' not in st.session_state:
    st.session_state.output_folder_path = None


# ============================================================================
# SIDEBAR - CONFIGURATION
# ============================================================================

with st.sidebar:
    
    #st.sidebar.image("assets/img/logo.png", width=90)
    #st.markdown("---")
    st.title("⚙️ Configuration")
    
    st.markdown("---")
    
    # Configuration du Layout (V3.0)
    st.subheader("🎨 Layout et Colonnes")
    
    try:
        from layouts import LayoutConfig, PREDEFINED_TEMPLATES
        
        st.markdown("**Templates prédéfinis**")
        template_options = {
            "Personnalisé": None,
            "📰 Article de Blog": "blog_article",
            "🚀 Landing Page": "landing_page",
            "🎨 Portfolio": "portfolio",
            "📰 Magazine": "magazine",
            "📚 Documentation": "documentation"
        }
        selected_template = st.selectbox(
            "Choisir un template",
            options=list(template_options.keys()),
            help="Templates optimisés pour différents types de contenu"
        )
        if selected_template != "Personnalisé":
            template_config = PREDEFINED_TEMPLATES[template_options[selected_template]]
            st.info(f"💡 {template_config['description']}")
            layout_type = template_config["layout"]
            distribution_strategy = template_config["distribution"]
            with st.expander("ℹ️ Détails du template"):
                st.write(f"**Layout:** {layout_type}")
                st.write(f"**Distribution:** {distribution_strategy}")
                st.write(f"**Recommandé pour:** {', '.join(template_config['recommended_for'])}")
        else:
            st.markdown("**Configuration manuelle**")
            layouts = LayoutConfig.get_all_layouts()
            layout_options = {
                f"{config['icon']} {config['name']}": key 
                for key, config in layouts.items()
            }
            selected_layout = st.selectbox(
                "Type de layout",
                options=list(layout_options.keys()),
                index=0,
                help="Choisissez comment organiser votre contenu en colonnes"
            )
            layout_type = layout_options[selected_layout]
            layout_config = layouts[layout_type]
            st.info(f"💡 {layout_config['description']}")
            distribution_options = {
                "🤖 Automatique (recommandé)": "auto",
                "📋 Séquentielle": "sequential",
                "🔄 Alternée": "alternating",
                "⚖️ Équilibrée": "balanced"
            }
            selected_distribution = st.selectbox(
                "Distribution du contenu",
                options=list(distribution_options.keys()),
                help="Comment répartir le contenu entre les colonnes"
            )
            distribution_strategy = distribution_options[selected_distribution]
    except ImportError:
        st.warning("⚠️ Module layouts.py non trouvé, layout par défaut utilisé")
        layout_type = "single_column"
        distribution_strategy = "auto"
    
    st.session_state.layout_type = layout_type
    st.session_state.distribution_strategy = distribution_strategy

    st.markdown("---")

    # URL Média pour les images
    st.subheader("🖼️ URL Média")
    base_image_url = st.text_input(
        "URL de base des médias (optionnel)",
        help="Ex: https://votre-site.com/wp-content/uploads/2025/11",
        placeholder="https://..."
    )
    
    st.markdown("---")
    
    # Options avancées
    with st.expander("🔧 Options avancées"):
        show_raw_structure = st.checkbox(
            "Afficher la structure brute extraite",
            value=False
        )
        show_semantic_structure = st.checkbox(
            "Afficher la structure extraite",
            value=True
        )
        json_indent = st.slider(
            "Indentation du JSON",
            min_value=0,
            max_value=4,
            value=2,
            help="Nombre d'espaces pour l'indentation"
        )
    
    # Maintenance (Cache)
    st.markdown("---")
    st.subheader("🧹 Maintenance")
    if st.button("Vider le cache des images", help=f"Supprime le contenu du dossier '{OUTPUT_CACHE_DIR}' local."):
        clear_output_cache()

    # Section Crédits
    if CREDITS_LOADED:
        show_credits_sidebar(language="fr")
    else:
        st.sidebar.markdown("---")
        st.sidebar.error("Erreur: Fichier credits.py manquant.")
    
    st.markdown("---")
    
    # Lien vers la documentation
    #st.markdown("""
    #📚 [Documentation complète](https://github.com/votre-repo)
    
    #🐛 [Signaler un bug](https://github.com/votre-repo/issues)
    #""")


# ============================================================================
# HEADER PRINCIPAL
# ============================================================================

st.markdown('<div class="main-header">📄 Word to Elementor Converter</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Convertissez vos documents Word et PDF en JSON Elementor</div>', unsafe_allow_html=True)


# ============================================================================
# --- MODIFIÉ : ZONES DE CHARGEMENT ET CONVERSION EN COLONNES ---
# ============================================================================

st.markdown("---")
col1, col2 = st.columns(2)

# --- Colonne 1 : Étape 1 ---
with col1:
    st.markdown("### 📤 Étape 1 : Charger votre document")
    
    uploaded_file = st.file_uploader(
        "Sélectionnez un fichier .docx ou .pdf",
        type=['docx', 'pdf'],
        help="Format accepté: Microsoft Word (.docx) ou PDF (.pdf)",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        st.success(f"✅ Fichier chargé : **{uploaded_file.name}**")

# --- Colonne 2 : Étape 2 ---
with col2:
    st.markdown("### 🚀 Étape 2 : Lancer la conversion")

    if uploaded_file:
        convert_button = st.button(
            "🎯 Convertir en JSON Elementor",
            type="primary",
            use_container_width=True
        )
    else:
        # Bouton désactivé si aucun fichier n'est chargé
        st.button(
            "🎯 Convertir en JSON Elementor",
            type="primary",
            use_container_width=True,
            disabled=True,
            help="Veuillez d'abord charger un fichier à l'Étape 1"
        )
        convert_button = False # Assure que la logique ne se déclenche pas

st.markdown("---")

# ============================================================================
# LOGIQUE DE CONVERSION (PLEINE LARGEUR)
# ============================================================================

if convert_button:
    # Réinitialiser l'état
    st.session_state.conversion_done = False
    st.session_state.json_output = None
    st.session_state.image_data = None
    st.session_state.output_folder_path = None
    
    try:
        file_ext = Path(uploaded_file.name).suffix.lower()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Barre de progression (maintenant en pleine largeur)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔧 Initialisation...")
        progress_bar.progress(10)
        
        if file_ext == '.pdf':
            status_text.text("📄 Analyse PDF...")
            progress_bar.progress(25)
            try:
                raw_structure, image_data, output_folder_path = parse_pdf(tmp_path)
                st.session_state.stats['elements'] = len(raw_structure)
                st.session_state.stats['images'] = len(image_data)
            except Exception as e:
                st.error(f"❌ Erreur parsing PDF : {str(e)}")
                os.unlink(tmp_path)
                st.stop()
        else:
            status_text.text("📄 Analyse DOCX...")
            progress_bar.progress(25)
            try:
                raw_structure, image_data, output_folder_path = parse_document(tmp_path)
                st.session_state.raw_structure = raw_structure
                st.session_state.stats['elements'] = len(raw_structure)
                st.session_state.stats['images'] = len(image_data)
            except Exception as e:
                st.error(f"❌ Erreur parsing DOCX : {str(e)}")
                os.unlink(tmp_path)
                st.stop()
        
        st.session_state.image_data = image_data
        st.session_state.output_folder_path = output_folder_path
        
        status_text.text("📝 Extraction directe...")
        progress_bar.progress(50)
        try:
            if file_ext == '.pdf':
                semantic_structure = extract_text_from_pdf(tmp_path)
            else:
                semantic_structure = extract_text_from_docx(tmp_path)
            st.session_state.semantic_structure = semantic_structure
        except Exception as e:
            st.error(f"❌ Erreur extraction : {str(e)}")
            os.unlink(tmp_path)
            st.stop()
        
        status_text.text("🏗️ Construction JSON...")
        progress_bar.progress(75)
        
        layout_type = st.session_state.get('layout_type', 'single_column')
        distribution_strategy = st.session_state.get('distribution_strategy', 'auto')
        
        try:
            elementor_data = build_elementor_json(
                semantic_structure, 
                image_data,
                layout_type=layout_type,
                distribution_strategy=distribution_strategy,
                base_image_url=base_image_url 
            )
            
            st.session_state.elementor_data = elementor_data
            st.session_state.stats['layout'] = layout_type
            st.session_state.stats['distribution'] = distribution_strategy
        except Exception as e:
            st.error(f"❌ Erreur JSON : {str(e)}")
            os.unlink(tmp_path)
            st.stop()
        
        status_text.text("✨ Finalisation...")
        progress_bar.progress(90)
        
        json_output = json.dumps(
            elementor_data,
            ensure_ascii=False,
            indent=json_indent
        )
        
        st.session_state.json_output = json_output
        st.session_state.conversion_done = True
        
        os.unlink(tmp_path)
        
        progress_bar.progress(100)
        status_text.text("✅ Conversion terminée avec succès !")
        
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ Erreur inattendue : {str(e)}")
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ============================================================================
# AFFICHAGE DES RÉSULTATS
# ============================================================================

if st.session_state.conversion_done and st.session_state.json_output:
    
    st.markdown("### 🎉 Conversion réussie !")
    
    # Statistiques
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric( "📝 Éléments extraits", st.session_state.stats.get('elements', 0))
    with col2:
        st.metric( "🖼️ Images trouvées", st.session_state.stats.get('images', 0))
    with col3:
        st.metric( "🎯 Éléments Elementor", len(st.session_state.semantic_structure) if st.session_state.semantic_structure else 0)
    with col4:
        json_size = len(st.session_state.json_output.encode('utf-8')) / 1024
        st.metric( "💾 Taille du JSON", f"{json_size:.1f} KB")
    with col5:
        layout_icons = {
            "single_column": "📄", "two_columns_equal": "⚖️", "two_columns_sidebar_left": "◀️",
            "two_columns_sidebar_right": "▶️", "three_columns": "▦", "blog_layout": "📰"
        }
        layout = st.session_state.stats.get('layout', 'single_column')
        icon = layout_icons.get(layout, "📄")
        st.metric( f"{icon} Layout", layout.replace('_', ' ').title())
    
    st.markdown("---")
    
    # Zone de téléchargement
    st.markdown("### 📥 Étape 3 : Télécharger le résultat")
    
    dl_col1, dl_col2, dl_col3 = st.columns([1, 2, 1])
    
    with dl_col2:
        # Noms de fichiers de sortie
        output_filename_base = Path(uploaded_file.name).stem
        json_filename = f"{output_filename_base}_elementor.json"
        zip_filename = f"{output_filename_base}_package.zip"

        # Bouton 1: JSON Seulement
        st.download_button(
            label="⬇️ Télécharger JSON Seulement",
            data=st.session_state.json_output,
            file_name=json_filename,
            mime="application/json",
            use_container_width=True
        )

        # Création du ZIP en mémoire
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_f:
            # 1. Ajouter le JSON
            zip_f.writestr(json_filename, st.session_state.json_output)
            
            # 2. Ajouter les images
            image_data = st.session_state.image_data
            output_folder_path = st.session_state.output_folder_path
            
            if image_data and output_folder_path:
                for img_info in image_data.values():
                    img_filename = img_info['filename']
                    img_path = os.path.join(output_folder_path, img_filename)
                    
                    if os.path.exists(img_path):
                        # Ajoute l'image dans un sous-dossier "images" du ZIP
                        zip_f.write(img_path, arcname=f"images/{img_filename}")
                    else:
                        st.warning(f"Image {img_filename} non trouvée sur le serveur.")
        
        # Bouton 2: Package ZIP (JSON + Images)
        st.download_button(
            label="📦 Télécharger Package (JSON + Images)",
            data=zip_buffer.getvalue(),
            file_name=zip_filename,
            mime="application/zip",
            use_container_width=True,
            type="primary" # Style différent
        )

        st.info("""
        💡 **Astuce Package :**
        1. Dézippez le package.
        2. Uploadez les images du dossier `images` dans votre Média WordPress.
        3. Importez le fichier `.json` dans Elementor.
        """)
    
    st.markdown("---")
    
    # Aperçu du JSON
    if show_semantic_structure and st.session_state.semantic_structure:
        with st.expander("🔍 Prévisualisation de la structure extraite", expanded=True):
            st.json(st.session_state.semantic_structure)
    
    if show_raw_structure and 'raw_structure' in st.session_state:
        with st.expander("🔍 Structure brute extraite du document"):
            st.json(st.session_state.raw_structure)

    with st.expander("👀 Aperçu du JSON généré", expanded=False):
        st.code(st.session_state.json_output, language='json')


# ============================================================================
# ZONE D'INSTRUCTIONS (si pas de fichier chargé)
# ============================================================================

if not uploaded_file:
    # Affiche les instructions si aucun fichier n'est chargé
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Comment ça marche ?")
        st.markdown("""
        1. **Préparez votre document Word** avec :
           - Des titres structurés (Heading 1, 2, 3...)
           - Des paragraphes de contenu
           - Des images
        
        2. **Chargez votre fichier .docx** ou .pdf à l'Étape 1.
        
        3. **(Optionnel) Entrez l'URL de base** de vos médias WordPress dans la sidebar.
        
        4. **Cliquez sur "Convertir"** à l'Étape 2.
        
        5. **Téléchargez le Package ZIP** et importez-le dans Elementor !
        """)
    
    with col2:
        st.markdown("### ✨ Fonctionnalités")
        st.markdown("""
        - ✅ **Extraction directe** des styles
        - ✅ **Détection automatique** des titres et paragraphes
        - ✅ **Extraction des images** et liaison via URL
        - ✅ **Package ZIP** (JSON + Images)
        - ✅ **JSON valide** et prêt pour Elementor
        - ✅ **Interface intuitive** et rapide
        """)
    
    st.markdown("---")
    
    # Exemple de document
    st.markdown("### 📖 Format du document Word recommandé")
    
    st.markdown("""
    ```
    Titre Principal                    [Style: Heading 1]
    
    Sous-titre Important               [Style: Heading 2]
    
    Paragraphe de contenu texte...     [Style: Normal]
    
    [Image intégrée]
    ```
    """)
    
    st.info("""
    💡 **Conseil :** Plus votre document est structuré avec les styles Word appropriés, 
    meilleure sera la conversion !
    """)


# ============================================================================
# SECTION D'AIDE
# ============================================================================

st.markdown("---")

with st.expander("❓ FAQ - Questions fréquentes"):
    st.markdown("""
    **Q: Comment faire pour que mes images s'affichent ?**
    
    R: Vous avez deux options :
    
    **Option 1 (Recommandée - Package ZIP):**
    1. Téléchargez le **Package ZIP**.
    2. Uploadez les images du dossier `images` (dans le ZIP) dans votre **Bibliothèque de médias** WordPress.
    3. Copiez l'URL de base (ex: `https://.../wp-content/uploads/2025/11/`).
    4. Collez cette URL dans le champ **"URL de base des médias"** dans la sidebar AVANT de re-convertir.
    5. Téléchargez le nouveau JSON (ou Package) et importez-le. Les liens seront automatiques.

    **Option 2 (Manuelle):**
    1. Téléchargez le **Package ZIP**.
    2. Uploadez les images dans WordPress.
    3. Importez le JSON dans Elementor.
    4. Manuellement, reliez chaque widget image à l'image correspondante dans votre bibliothèque.
    
    ---
    
    **Q: Le JSON est-il directement importable dans Elementor ?**
    
    R: Oui ! Le format JSON généré est compatible avec l'outil d'import 
    de template d'Elementor.
    """)


# ============================================================================
# FOOTER
# ============================================================================

if CREDITS_LOADED:
    show_credits_footer(language="fr")
else:
    st.markdown("---")
    st.error("Erreur: Fichier credits.py manquant.")
