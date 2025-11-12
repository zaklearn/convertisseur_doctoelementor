#!/usr/bin/env python3
"""
app_optimized.py - Application Streamlit optimisée
"""

import streamlit as st
import json
import os
import tempfile
import shutil
import zipfile
from pathlib import Path
from io import BytesIO
from datetime import datetime

from word_processor import extract_document_structure, save_images
from json_builder import build_elementor_json


st.set_page_config(
    page_title="Word to Elementor - Optimized",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e40af;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #10b981;
        color: white;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stDownloadButton button {
        background-color: #1e40af;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'converted' not in st.session_state:
    st.session_state.converted = False
if 'json_data' not in st.session_state:
    st.session_state.json_data = None
if 'stats' not in st.session_state:
    st.session_state.stats = {}
if 'filename' not in st.session_state:
    st.session_state.filename = ""

def reset_conversion():
    """Réinitialise la conversion pour un nouveau fichier"""
    st.session_state.converted = False
    st.session_state.json_data = None
    st.session_state.stats = {}
    st.session_state.filename = ""

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")
    st.markdown("---")
    
    base_url = st.text_input(
        "URL base des médias",
        placeholder="https://votre-site.com/wp-content/uploads/2024/11",
        help="URL où seront uploadées les images sur WordPress"
    )
    
    st.markdown("---")
    
    create_zip = st.checkbox(
        "Créer package ZIP",
        value=True,
        help="Inclut JSON + dossier images"
    )
    
    if st.button("🗑️ Nettoyer cache"):
        if Path("outputs").exists():
            shutil.rmtree("outputs")
            Path("outputs").mkdir()
        st.success("✅ Cache nettoyé")

# Interface principale
st.markdown('<div class="main-title">📄 Word to Elementor - Optimized</div>', unsafe_allow_html=True)

# Bouton reset si une conversion existe
if st.session_state.converted:
    col_reset1, col_reset2, col_reset3 = st.columns([1, 1, 1])
    with col_reset2:
        if st.button("🔄 Nouveau fichier", type="secondary", use_container_width=True):
            reset_conversion()
            st.rerun()

uploaded_file = st.file_uploader(
    "📤 Sélectionnez un fichier .docx",
    type=['docx'],
    help="Document Word à convertir"
)

if uploaded_file:
    # Stocker le nom du fichier
    filename_base = Path(uploaded_file.name).stem
    st.session_state.filename = filename_base
    
    st.success(f"✅ Fichier chargé : **{uploaded_file.name}**")
    
    if st.button("🚀 Convertir", type="primary", use_container_width=True):
        st.session_state.converted = False
        
        progress = st.progress(0)
        status = st.empty()
        
        try:
            # Créer fichier temporaire
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            # Extraction
            status.text("📄 Extraction du document...")
            progress.progress(20)
            
            structure, image_data = extract_document_structure(tmp_path)
            
            status.text(f"✅ {len(structure)} éléments trouvés")
            progress.progress(40)
            
            # Sauvegarde images
            status.text("🖼️ Extraction des images...")
            outputs_dir = Path("outputs")
            outputs_dir.mkdir(exist_ok=True)
            images_dir = outputs_dir / "images"
            
            image_urls = save_images(image_data, str(images_dir), base_url)
            progress.progress(60)
            
            # Construction JSON
            status.text("🏗️ Génération du JSON Elementor...")
            elementor_json = build_elementor_json(structure, image_data, image_urls)
            progress.progress(80)
            
            # Sauvegarder JSON
            json_output = json.dumps(elementor_json, ensure_ascii=False, indent=2)
            st.session_state.json_data = json_output
            
            json_filename = f"{st.session_state.filename}_elementor.json"
            json_path = outputs_dir / json_filename
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(json_output)
            
            # Statistiques
            h_count = sum(1 for item in structure if item['type'] in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            p_count = sum(1 for item in structure if item['type'] == 'p')
            img_count = len(image_data)
            
            st.session_state.stats = {
                'headings': h_count,
                'paragraphs': p_count,
                'images': img_count,
                'total': len(structure)
            }
            
            progress.progress(100)
            status.text("✅ Conversion terminée!")
            st.session_state.converted = True
            
            os.unlink(tmp_path)
            
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

# Résultats
if st.session_state.converted and st.session_state.json_data:
    st.markdown("---")
    
    # Statistiques
    stats = st.session_state.stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Titres", stats['headings'])
    with col2:
        st.metric("📄 Paragraphes", stats['paragraphs'])
    with col3:
        st.metric("🖼️ Images", stats['images'])
    with col4:
        st.metric("📊 Total", stats['total'])
    
    st.markdown("---")
    
    # Téléchargements
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.download_button(
            label="📥 Télécharger JSON",
            data=st.session_state.json_data,
            file_name=f"{st.session_state.filename}_elementor.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col_b:
        if create_zip:
            outputs_dir = Path("outputs")
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                # JSON
                json_path = outputs_dir / f"{st.session_state.filename}_elementor.json"
                if json_path.exists():
                    zf.write(json_path, json_path.name)
                
                # Images
                images_dir = outputs_dir / "images"
                if images_dir.exists():
                    for img_file in images_dir.glob("*"):
                        zf.write(img_file, f"images/{img_file.name}")
            
            st.download_button(
                label="📦 Télécharger ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"{st.session_state.filename}_package.zip",
                mime="application/zip",
                use_container_width=True
            )
    
    # Aperçu
    with st.expander("👀 Aperçu JSON"):
        preview = st.session_state.json_data[:1500]
        st.code(preview + "\n...", language='json')
    
    st.info("💡 Uploadez les images dans WordPress, puis importez le JSON dans Elementor")