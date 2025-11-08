#!/usr/bin/env python3
"""
app.py - Interface Streamlit pour Word to Elementor Converter
VERSION CORRIGÉE - Conserve la position exacte des images

Application web conviviale pour convertir des documents Word en JSON Elementor
avec extraction directe et préservation de l'ordre des éléments.

Version: 3.4 FIXED
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
import base64
from PIL import Image
from datetime import datetime

# Module d'extraction corrigé intégré
from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.text.paragraph import Paragraph


# ============================================================================
# FONCTION D'EXTRACTION CORRIGÉE - Conserve la position des images
# ============================================================================

def parse_document_fixed(docx_path: str) -> tuple:
    """
    Parse le document .docx en conservant l'ordre exact des éléments
    VERSION CORRIGÉE
    """
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Le fichier '{docx_path}' n'existe pas")
    
    try:
        doc = Document(docx_path)
    except Exception as e:
        raise Exception(f"Impossible de lire le fichier .docx: {e}")
    
    raw_structure = []
    image_data = {}
    image_counter = 1
    
    # Créer un mapping des relations d'images
    image_rels = {}
    for rel_id, rel in doc.part.rels.items():
        if "image" in rel.target_ref:
            image_rels[rel_id] = rel
    
    # Parcourir le document dans l'ordre
    for element in doc.element.body:
        if isinstance(element, CT_P):
            paragraph = Paragraph(element, doc)
            
            # Vérifier s'il y a une image
            has_image = False
            if paragraph._element.xpath('.//pic:pic'):
                # Extraire le rId de l'image depuis le XML du paragraphe
                para_xml = paragraph._element.xml
                
                # Chercher les références d'images
                for match_pattern in ['r:embed="', 'r:link="']:
                    if match_pattern in para_xml:
                        start = para_xml.find(match_pattern) + len(match_pattern)
                        end = para_xml.find('"', start)
                        if start > len(match_pattern) - 1 and end > start:
                            rel_id = para_xml[start:end]
                            
                            # Vérifier si c'est une vraie relation d'image
                            if rel_id in image_rels:
                                rel = image_rels[rel_id]
                                image_ref_id = f"__IMAGE_{image_counter}__"
                                
                                try:
                                    # Extraire les données de l'image
                                    image_bytes = rel.target_part.blob
                                    img = Image.open(BytesIO(image_bytes))
                                    
                                    image_data[image_ref_id] = {
                                        'data': image_bytes,
                                        'format': img.format or "PNG",
                                        'width': img.width,
                                        'height': img.height,
                                        'position': len(raw_structure)  # Position dans la structure
                                    }
                                    
                                    raw_structure.append({
                                        'type': 'image',
                                        'ref_id': image_ref_id
                                    })
                                    
                                    image_counter += 1
                                    has_image = True
                                    break
                                except Exception as e:
                                    print(f"Erreur extraction image: {e}")
                        
                        if has_image:
                            break
            
            # Traiter le texte s'il n'y a pas d'image ou après l'image
            text = paragraph.text.strip()
            if text and not has_image:
                style_name = paragraph.style.name if paragraph.style else 'Normal'
                
                if 'Heading 1' in style_name or 'Title' in style_name:
                    elem_type = 'h1'
                elif 'Heading 2' in style_name:
                    elem_type = 'h2'
                elif 'Heading 3' in style_name:
                    elem_type = 'h3'
                elif 'Heading 4' in style_name:
                    elem_type = 'h4'
                elif 'Heading 5' in style_name:
                    elem_type = 'h5'
                elif 'Heading 6' in style_name:
                    elem_type = 'h6'
                else:
                    elem_type = 'p'
                
                raw_structure.append({
                    'type': elem_type,
                    'content': text,
                    'original_style': style_name
                })
    
    if not raw_structure:
        raise ValueError("Le document ne contient aucun contenu exploitable")
    
    return raw_structure, image_data


def extract_images_to_folder(image_data: dict, output_folder: str, base_url: str = "") -> dict:
    """
    Extrait les images vers un dossier avec noms uniques
    """
    os.makedirs(output_folder, exist_ok=True)
    image_urls = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for idx, (ref_id, img_info) in enumerate(image_data.items(), 1):
        if 'data' in img_info:
            ext = img_info.get('format', 'PNG').lower()
            if ext == 'jpeg':
                ext = 'jpg'
            
            filename = f"{timestamp}_{idx:03d}.{ext}"
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, 'wb') as f:
                f.write(img_info['data'])
            
            # Créer l'URL complète si une URL de base est fournie
            if base_url:
                image_urls[ref_id] = f"{base_url.rstrip('/')}/{filename}"
            else:
                image_urls[ref_id] = f"{filename}"
    
    return image_urls


def build_elementor_json_fixed(semantic_structure: list, image_data: dict, image_urls: dict = None) -> dict:
    """
    Construit le JSON Elementor en conservant l'ordre des éléments
    """
    def generate_unique_id():
        import random
        import string
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
    
    elements_widgets = []
    
    for item in semantic_structure:
        item_type = item.get('type')
        
        if item_type in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            widget = {
                "id": generate_unique_id(),
                "elType": "widget",
                "settings": {
                    "title": item['content'],
                    "header_size": item_type
                },
                "elements": [],
                "widgetType": "heading"
            }
            elements_widgets.append(widget)
            
        elif item_type == 'p':
            widget = {
                "id": generate_unique_id(),
                "elType": "widget",
                "settings": {
                    "editor": item['content']
                },
                "elements": [],
                "widgetType": "text-editor"
            }
            elements_widgets.append(widget)
            
        elif item_type == 'image':
            ref_id = item.get('ref_id')
            image_url = "https://example.com/placeholder.jpg"
            
            if image_urls and ref_id in image_urls:
                image_url = image_urls[ref_id]
            
            widget = {
                "id": generate_unique_id(),
                "elType": "widget",
                "settings": {
                    "image": {
                        "url": image_url,
                        "id": ""
                    },
                    "image_size": "full"
                },
                "elements": [],
                "widgetType": "image"
            }
            
            # Ajouter dimensions si disponibles
            if image_data and ref_id in image_data:
                img_info = image_data[ref_id]
                if 'width' in img_info and 'height' in img_info:
                    widget["settings"]["image"]["width"] = img_info['width']
                    widget["settings"]["image"]["height"] = img_info['height']
            
            elements_widgets.append(widget)
    
    # Créer la structure Elementor
    elementor_content = [
        {
            "id": generate_unique_id(),
            "elType": "section",
            "settings": {},
            "elements": [
                {
                    "id": generate_unique_id(),
                    "elType": "column",
                    "settings": {
                        "_column_size": 100,
                        "_inline_size": None
                    },
                    "elements": elements_widgets
                }
            ]
        }
    ]
    
    return {
        "version": "0.4",
        "title": "Imported from Word - Fixed",
        "type": "page",
        "content": elementor_content
    }


# ============================================================================
# CONFIGURATION STREAMLIT
# ============================================================================

st.set_page_config(
    page_title="Word to Elementor Converter - FIXED",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
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
    }
    </style>
""", unsafe_allow_html=True)

# Initialisation session state
if 'conversion_done' not in st.session_state:
    st.session_state.conversion_done = False
if 'json_output' not in st.session_state:
    st.session_state.json_output = None

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("⚙️ Configuration")
    st.markdown("---")
    
    st.subheader("🔗 URL de base WordPress")
    base_media_url = st.text_input(
        "URL de votre site WordPress",
        placeholder="https://votre-site.com/wp-content/uploads/2024/11",
        help="URL où les images seront uploadées sur WordPress"
    )
    
    st.markdown("---")
    
    # Options de conversion
    st.subheader("🎯 Options de conversion")
    preserve_order = st.checkbox(
        "Préserver l'ordre exact des éléments",
        value=True,
        help="Conserve la position exacte des images et du texte"
    )
    
    export_zip = st.checkbox(
        "Exporter en package ZIP",
        value=True,
        help="Créer un ZIP avec JSON + dossier images"
    )
    
    st.markdown("---")
    
    # Nettoyage du cache
    if st.button("🗑️ Nettoyer le cache", type="secondary"):
        outputs_dir = Path("outputs")
        if outputs_dir.exists():
            shutil.rmtree(outputs_dir)
            outputs_dir.mkdir()
        st.success("✅ Cache nettoyé")

# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

st.markdown('<div class="main-header">📄 Word to Elementor Converter</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Version CORRIGÉE - Conserve la position exacte des images</div>', unsafe_allow_html=True)

st.markdown("---")

# Upload du fichier
uploaded_file = st.file_uploader(
    "📤 Sélectionnez un fichier .docx",
    type=['docx'],
    help="Le document Word à convertir"
)

if uploaded_file:
    st.success(f"✅ Fichier chargé : **{uploaded_file.name}**")
    
    if st.button("🚀 Convertir en JSON Elementor", type="primary"):
        st.session_state.conversion_done = False
        
        try:
            # Créer un fichier temporaire
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Progress bar
            progress = st.progress(0)
            status = st.empty()
            
            # Étape 1: Extraction du contenu
            status.text("📄 Extraction du document...")
            progress.progress(30)
            
            raw_structure, image_data = parse_document_fixed(tmp_path)
            
            status.text(f"✅ {len(raw_structure)} éléments extraits, {len(image_data)} images trouvées")
            progress.progress(60)
            
            # Étape 2: Extraction des images
            status.text("🖼️ Extraction des images...")
            outputs_dir = Path("outputs")
            outputs_dir.mkdir(exist_ok=True)
            images_dir = outputs_dir / "images"
            
            image_urls = extract_images_to_folder(image_data, str(images_dir), base_media_url)
            progress.progress(80)
            
            # Étape 3: Construction du JSON
            status.text("🏗️ Construction du JSON Elementor...")
            elementor_json = build_elementor_json_fixed(raw_structure, image_data, image_urls)
            
            # Sauvegarder le JSON
            json_output = json.dumps(elementor_json, ensure_ascii=False, indent=2)
            st.session_state.json_output = json_output
            
            json_path = outputs_dir / f"{Path(uploaded_file.name).stem}_elementor.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(json_output)
            
            progress.progress(100)
            status.text("✅ Conversion terminée!")
            st.session_state.conversion_done = True
            
            # Nettoyer
            os.unlink(tmp_path)
            
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")
            if 'tmp_path' in locals():
                os.unlink(tmp_path)

# ============================================================================
# RÉSULTATS
# ============================================================================

if st.session_state.conversion_done and st.session_state.json_output:
    st.markdown("---")
    st.markdown("### 🎉 Conversion réussie!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Télécharger le JSON
        st.download_button(
            label="⬇️ Télécharger le JSON",
            data=st.session_state.json_output,
            file_name=f"{Path(uploaded_file.name).stem}_elementor.json",
            mime="application/json"
        )
    
    with col2:
        # Créer et télécharger le ZIP
        if export_zip:
            outputs_dir = Path("outputs")
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Ajouter le JSON
                json_path = outputs_dir / f"{Path(uploaded_file.name).stem}_elementor.json"
                if json_path.exists():
                    zf.write(json_path, json_path.name)
                
                # Ajouter les images
                images_dir = outputs_dir / "images"
                if images_dir.exists():
                    for img_file in images_dir.glob("*"):
                        zf.write(img_file, f"images/{img_file.name}")
            
            st.download_button(
                label="📦 Télécharger le package ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"{Path(uploaded_file.name).stem}_package.zip",
                mime="application/zip"
            )
    
    # Aperçu du JSON
    with st.expander("👀 Aperçu du JSON généré"):
        st.code(st.session_state.json_output[:2000] + "...", language='json')
    
    st.info("💡 **Astuce :** Uploadez les images du dossier 'images' dans votre médiathèque WordPress, puis importez le JSON dans Elementor.")
