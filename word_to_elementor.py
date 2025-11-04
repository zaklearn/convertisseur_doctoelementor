#!/usr/bin/env python3
"""
word_to_elementor.py

Convertit un document .docx structuré en JSON importable par Elementor.
Utilise l'extraction directe basée sur les styles.

Version: 3.2 (No-AI, ZIP Package)
"""

import argparse
import json
import os
import sys
import re
from typing import List, Dict, Any, Optional, Tuple # <- Tuple
from pathlib import Path
from io import BytesIO
import base64
from datetime import datetime

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from PIL import Image

# Module extraction images
from image_extractor import extract_all_images, get_image_positions

# Module extraction texte direct
from text_extractor import extract_text_from_docx, extract_text_from_pdf


# ============================================================================
# LAYOUTS FALLBACK - Configuration embarquée
# ============================================================================

FALLBACK_LAYOUTS = {
    "single_column": {
        "name": "Une seule colonne",
        "columns": [{"size": 100, "content_type": "main"}]
    },
    # ... (autres layouts inchangés) ...
    "blog_layout": {
        "name": "Layout Blog",
        "columns": [
            {"size": 60, "content_type": "main"},
            {"size": 40, "content_type": "sidebar"}
        ],
        "spacing": {"column_gap": "30", "padding": "20px"}
    }
}


def fallback_distribute_auto(elements, columns_config):
    # ... (fonction inchangée) ...
    num_columns = len(columns_config)
    distributed = [[] for _ in range(num_columns)]
    
    main_col_idx = 0
    max_size = 0
    for col_idx, col_config in enumerate(columns_config):
        if col_config.get("size", 0) > max_size:
            max_size = col_config["size"]
            main_col_idx = col_idx
    
    if num_columns == 2:
        h1_found = False
        intro_added = False
        
        for element in elements:
            element_type = element.get("type", "")
            
            if element_type == "h1" and not h1_found:
                distributed[main_col_idx].append(element)
                h1_found = True
            elif element_type == "p" and h1_found and not intro_added:
                distributed[main_col_idx].append(element)
                intro_added = True
            else:
                if len(distributed[0]) <= len(distributed[1]):
                    distributed[0].append(element)
                else:
                    distributed[1].append(element)
    
    elif num_columns == 3:
        for idx, element in enumerate(elements):
            col_idx = idx % 3
            distributed[col_idx].append(element)
    
    else:
        distributed[0] = elements
    
    return distributed


def fallback_distribute(elements, columns_config, strategy="auto"):
    # ... (fonction inchangée) ...
    num_columns = len(columns_config)
    distributed = [[] for _ in range(num_columns)]
    
    if strategy == "auto":
        return fallback_distribute_auto(elements, columns_config)
    
    elif strategy == "alternating":
        for idx, element in enumerate(elements):
            col_idx = idx % num_columns
            distributed[col_idx].append(element)
    
    elif strategy == "balanced":
        elements_per_column = len(elements) // num_columns
        remainder = len(elements) % num_columns
        
        current_idx = 0
        for col_idx in range(num_columns):
            num_elements = elements_per_column + (1 if col_idx < remainder else 0)
            distributed[col_idx] = elements[current_idx:current_idx + num_elements]
            current_idx += num_elements
    
    elif strategy == "sequential":
        elements_per_column = len(elements) // num_columns
        remainder = len(elements) % num_columns
        
        current_idx = 0
        for col_idx in range(num_columns):
            num_elements = elements_per_column
            if col_idx < remainder:
                num_elements += 1
            
            distributed[col_idx] = elements[current_idx:current_idx + num_elements]
            current_idx += num_elements
    
    else:
        for idx, element in enumerate(elements):
            col_idx = idx % num_columns
            distributed[col_idx].append(element)
    
    return distributed


# ============================================================================
# PARSING DU DOCUMENT
# ============================================================================

# --- MODIFIÉ ---
# Le type de retour inclut maintenant un 'str' pour le chemin du dossier
def parse_document(docx_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
# --- FIN MODIFIÉ ---
    """Parse le document .docx"""
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Le fichier '{docx_path}' n'existe pas")
    
    try:
        doc = Document(docx_path)
    except Exception as e:
        raise Exception(f"Impossible de lire le fichier .docx: {e}")
    
    doc_name = Path(docx_path).stem
    output_folder = os.path.join("outputs", doc_name, "images")
    
    timestamp_prefix = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    filenames_map, metadata_map = extract_all_images(
        docx_path, 
        output_folder, 
        timestamp_prefix
    )
    
    image_data = {}
    for idx, filename in filenames_map.items():
        image_ref_id = f"__IMAGE_{idx}__"
        image_data[image_ref_id] = {
            'filename': filename,
            'width': metadata_map[idx]['width'],
            'height': metadata_map[idx]['height'],
            'format': metadata_map[idx]['format']
        }
    
    raw_structure = []
    image_counter = 1
    
    for element in doc.element.body:
        if isinstance(element, CT_P):
            paragraph = Paragraph(element, doc)
            
            if paragraph._element.xpath('.//pic:pic'):
                image_ref_id = f"__IMAGE_{image_counter}__"
                raw_structure.append({
                    'type': 'image',
                    'ref_id': image_ref_id
                })
                image_counter += 1
                continue
            
            text = paragraph.text.strip()
            if not text:
                continue
            
            style_name = paragraph.style.name if paragraph.style else 'Normal'
            
            if 'Heading 1' in style_name or 'Title' in style_name:
                elem_type = 'style_h1'
            elif 'Heading 2' in style_name:
                elem_type = 'style_h2'
            elif 'Heading 3' in style_name:
                elem_type = 'style_h3'
            elif 'Heading 4' in style_name:
                elem_type = 'style_h4'
            else:
                elem_type = 'paragraph'
            
            raw_structure.append({
                'type': elem_type,
                'content': text,
                'original_style': style_name
            })
    
    if not raw_structure:
        raise ValueError("Le document ne contient aucun contenu exploitable")
    
    print(f"✓ {len(image_data)} images extraites dans {output_folder}", file=sys.stderr)
    
    # --- MODIFIÉ ---
    # Renvoie le chemin du dossier en plus
    return raw_structure, image_data, output_folder
    # --- FIN MODIFIÉ ---


# --- MODIFIÉ ---
# Le type de retour inclut maintenant un 'str' pour le chemin du dossier
def parse_pdf(pdf_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
# --- FIN MODIFIÉ ---
    """Parse document PDF"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Fichier inexistant: {pdf_path}")
    
    try:
        import fitz
    except ImportError:
        raise ImportError("PyMuPDF requis: pip install pymupdf")
    
    doc_name = Path(pdf_path).stem
    output_folder = os.path.join("outputs", doc_name, "images")
    os.makedirs(output_folder, exist_ok=True)
    
    timestamp_prefix = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    doc = fitz.open(pdf_path)
    image_data = {}
    image_counter = 1
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images()
        
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            
            filename = f"{timestamp_prefix}_{image_counter:03d}.{ext}"
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            image_ref_id = f"__IMAGE_{image_counter}__"
            image_data[image_ref_id] = {
                'filename': filename,
                'width': base_image.get('width', 800),
                'height': base_image.get('height', 600),
                'format': ext.upper()
            }
            image_counter += 1
    
    doc.close()
    
    raw_structure = [{'type': 'paragraph', 'content': 'PDF parsed'}]
    
    print(f"✓ {len(image_data)} images extraites dans {output_folder}", file=sys.stderr)

    # --- MODIFIÉ ---
    # Renvoie le chemin du dossier en plus
    return raw_structure, image_data, output_folder
    # --- FIN MODIFIÉ ---


# ============================================================================
# GÉNÉRATION DES WIDGETS ELEMENTOR
# ============================================================================

def generate_unique_id() -> str:
    # ... (fonction inchangée) ...
    import random
    import string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))


def create_heading_widget(content: str, tag: str) -> Dict[str, Any]:
    # ... (fonction inchangée) ...
    return {
        "id": generate_unique_id(),
        "elType": "widget",
        "settings": {
            "title": content,
            "header_size": tag
        },
        "elements": [],
        "widgetType": "heading"
    }


def create_text_editor_widget(content: str) -> Dict[str, Any]:
    # ... (fonction inchangée) ...
    return {
        "id": generate_unique_id(),
        "elType": "widget",
        "settings": {
            "editor": content
        },
        "elements": [],
        "widgetType": "text-editor"
    }


def create_image_widget(
    ref_id: str, 
    image_info: Optional[Dict] = None, 
    base_image_url: Optional[str] = None
) -> Dict[str, Any]:
    # ... (fonction inchangée) ...
    filename = image_info.get('filename', 'image.jpg') if image_info else 'image.jpg'
    
    image_url = ""
    if base_image_url:
        image_url = base_image_url.rstrip('/') + '/' + filename
    
    widget = {
        "id": generate_unique_id(),
        "elType": "widget",
        "settings": {
            "image": {
                "url": image_url,
                "id": "",
                "filename": filename
            },
            "image_size": "full"
        },
        "elements": [],
        "widgetType": "image"
    }
    
    if image_info:
        widget["settings"]["image"]["width"] = image_info.get('width')
        widget["settings"]["image"]["height"] = image_info.get('height')
    
    return widget


# ============================================================================
# CONSTRUCTION DU JSON ELEMENTOR
# ============================================================================

def build_elementor_json(
    semantic_structure: List[Dict[str, Any]], 
    image_data: Dict[str, Any],
    layout_type: str = "single_column",
    distribution_strategy: str = "auto",
    base_image_url: Optional[str] = None
) -> Dict[str, Any]:
    # ... (fonction inchangée) ...
    try:
        from layouts import LayoutConfig, ContentDistributor
        layout_config = LayoutConfig.get_layout(layout_type)
        columns_config = layout_config["columns"]
        use_fallback = False
    except ImportError:
        print("💡 Utilisation de la configuration de layout embarquée", file=sys.stderr)
        layout_config = FALLBACK_LAYOUTS.get(layout_type, FALLBACK_LAYOUTS["single_column"])
        columns_config = layout_config["columns"]
        use_fallback = True
    
    if len(columns_config) > 1:
        try:
            if use_fallback:
                distributed_elements = fallback_distribute(
                    semantic_structure,
                    columns_config,
                    distribution_strategy
                )
            else:
                distributed_elements = ContentDistributor.distribute(
                    semantic_structure,
                    columns_config,
                    distribution_strategy
                )
        except Exception as e:
            print(f"⚠️  Erreur de distribution: {e}, fallback", file=sys.stderr)
            distributed_elements = [semantic_structure] + [[] for _ in range(len(columns_config) - 1)]
    else:
        distributed_elements = [semantic_structure]
    
    elementor_columns = []
    
    for col_idx, (col_config, col_elements) in enumerate(zip(columns_config, distributed_elements)):
        column = {
            "id": generate_unique_id(),
            "elType": "column",
            "settings": {
                "_column_size": col_config["size"],
                "_inline_size": None
            },
            "elements": []
        }
        
        for item in col_elements:
            item_type = item.get('type')
            
            if item_type in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                widget = create_heading_widget(item['content'], item_type)
                column["elements"].append(widget)
                
            elif item_type == 'p':
                widget = create_text_editor_widget(item['content'])
                column["elements"].append(widget)
                
            elif item_type == 'image':
                ref_id = item.get('ref_id')
                img_info = image_data.get(ref_id) if ref_id else None
                widget = create_image_widget(ref_id, img_info, base_image_url)
                column["elements"].append(widget)
            
            else:
                print(f"⚠️  Type non reconnu ignoré: {item_type}", file=sys.stderr)
        
        elementor_columns.append(column)
    
    elementor_content = [
        {
            "id": generate_unique_id(),
            "elType": "section",
            "settings": layout_config.get("spacing", {}),
            "elements": elementor_columns
        }
    ]
    
    return {
        "version": "0.4",
        "title": f"Imported from Word - {layout_config.get('name', 'Layout')}",
        "type": "page",
        "content": elementor_content
    }


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Convertit un document .docx en JSON Elementor"
    )
    # ... (arguments inchangés) ...
    parser.add_argument(
        'docx_file',
        type=str,
        help='Chemin vers le fichier .docx ou .pdf à convertir'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Fichier de sortie (optionnel, sinon stdout)',
        default=None
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mode verbeux (affiche les étapes)'
    )
    parser.add_argument(
        '-l', '--layout',
        type=str,
        default='single_column',
        choices=[
            'single_column',
            'two_columns_equal',
            'two_columns_sidebar_left',
            'two_columns_sidebar_right',
            'three_columns',
            'blog_layout'
        ],
        help='Type de layout pour Elementor'
    )
    parser.add_argument(
        '-d', '--distribution',
        type=str,
        default='auto',
        choices=['auto', 'sequential', 'alternating', 'balanced'],
        help='Stratégie de distribution du contenu'
    )
    parser.add_argument(
        '--base-url',
        type=str,
        default=None,
        help='URL de base du dossier Média WordPress (ex: https://site.com/wp-content/uploads/2025/11)'
    )
    
    args = parser.parse_args()
    
    file_ext = Path(args.docx_file).suffix.lower()
    
    try:
        if args.verbose:
            print("🔧 Initialisation...", file=sys.stderr)
        
        if file_ext == '.pdf':
            if args.verbose:
                print(f"📄 Parsing PDF '{args.docx_file}'...", file=sys.stderr)
            # --- MODIFIÉ ---
            # Accepte le 3ème argument (chemin) mais ne l'utilise pas (via _)
            raw_structure, image_data, _ = parse_pdf(args.docx_file)
            # --- FIN MODIFIÉ ---
            if args.verbose:
                print(f"📝 Extraction directe PDF...", file=sys.stderr)
            semantic_structure = extract_text_from_pdf(args.docx_file)
        else:
            if args.verbose:
                print(f"📄 Parsing DOCX '{args.docx_file}'...", file=sys.stderr)
            # --- MODIFIÉ ---
            # Accepte le 3ème argument (chemin) mais ne l'utilise pas (via _)
            raw_structure, image_data, _ = parse_document(args.docx_file)
            # --- FIN MODIFIÉ ---
            if args.verbose:
                print(f"📝 Extraction directe DOCX...", file=sys.stderr)
            semantic_structure = extract_text_from_docx(args.docx_file)
        
        if args.verbose:
            print(f"   → {len(semantic_structure)} éléments structurels trouvés", file=sys.stderr)
            print(f"   → {len(image_data)} images trouvées", file=sys.stderr)
        
        if args.verbose:
            print("🏗️  Construction du JSON Elementor...", file=sys.stderr)
            # ... (logique inchangée) ...
        
        elementor_json = build_elementor_json(
            semantic_structure, 
            image_data,
            layout_type=args.layout,
            distribution_strategy=args.distribution,
            base_image_url=args.base_url
        )
        
        if args.verbose:
            print("✨ Finalisation...", file=sys.stderr)
        
        json_output = json.dumps(elementor_json, ensure_ascii=False, indent=2)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            if args.verbose:
                print(f"✅ JSON sauvegardé dans '{args.output}'", file=sys.stderr)
        else:
            print(json_output)
        
        if args.verbose:
            print("✅ Conversion terminée avec succès!", file=sys.stderr)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"❌ Erreur de configuration: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc(file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())