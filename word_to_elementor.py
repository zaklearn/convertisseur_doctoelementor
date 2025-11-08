#!/usr/bin/env python3
"""
word_to_elementor.py

Convertit un document .docx structuré en JSON importable par Elementor.
Utilise l'API Google Gemini pour l'analyse sémantique du contenu.

Version: 3.0.2 - FIXED
"""

import argparse
import json
import os
import sys
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from io import BytesIO
import base64

from dotenv import load_dotenv
import google.generativeai as genai
from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from PIL import Image


# ============================================================================
# LAYOUTS FALLBACK - Configuration embarquée
# ============================================================================

FALLBACK_LAYOUTS = {
    "single_column": {
        "name": "Une seule colonne",
        "columns": [{"size": 100, "content_type": "main"}]
    },
    "two_columns_equal": {
        "name": "Deux colonnes égales",
        "columns": [
            {"size": 50, "content_type": "main"},
            {"size": 50, "content_type": "main"}
        ]
    },
    "two_columns_sidebar_left": {
        "name": "Sidebar à gauche",
        "columns": [
            {"size": 33.33, "content_type": "sidebar"},
            {"size": 66.66, "content_type": "main"}
        ]
    },
    "two_columns_sidebar_right": {
        "name": "Sidebar à droite",
        "columns": [
            {"size": 66.66, "content_type": "main"},
            {"size": 33.33, "content_type": "sidebar"}
        ]
    },
    "three_columns": {
        "name": "Trois colonnes",
        "columns": [
            {"size": 33.33, "content_type": "main"},
            {"size": 33.33, "content_type": "main"},
            {"size": 33.33, "content_type": "main"}
        ]
    },
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
    """Distribution automatique intelligente"""
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
    """Distribution avec stratégies"""
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
# CONFIGURATION ET INITIALISATION
# ============================================================================

def load_api_key() -> str:
    """Charge la clé API Google Gemini depuis le fichier .env"""
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        raise ValueError(
            "Clé API Google non trouvée. "
            "Veuillez créer un fichier .env avec GOOGLE_API_KEY=votre_clé"
        )
    
    return api_key


def configure_gemini(api_key: str) -> genai.GenerativeModel:
    """Configure l'API Google Gemini"""
    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-pro',
        generation_config=generation_config
    )
    
    return model


# ============================================================================
# PARSING DU DOCUMENT - CORRIGÉ
# ============================================================================

def extract_image_data(image_part) -> Dict[str, Any]:
    """Extrait les données d'une image"""
    try:
        image_bytes = image_part.blob
        image = Image.open(BytesIO(image_bytes))
        
        buffered = BytesIO()
        image.save(buffered, format=image.format or "PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            'data': image_bytes,
            'base64': img_base64,
            'format': image.format or "PNG",
            'width': image.width,
            'height': image.height
        }
    except Exception as e:
        print(f"Erreur lors de l'extraction de l'image: {e}", file=sys.stderr)
        return None


def parse_document(docx_path: str) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Parse le document .docx - VERSION CORRIGÉE"""
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Le fichier '{docx_path}' n'existe pas")
    
    try:
        doc = Document(docx_path)
    except Exception as e:
        raise Exception(f"Impossible de lire le fichier .docx: {e}")
    
    raw_structure = []
    image_data = {}
    image_counter = 1
    
    for element in doc.element.body:
        if isinstance(element, CT_P):
            paragraph = Paragraph(element, doc)
            
            # CORRECTION : Vérifier d'abord s'il y a une image dans ce paragraphe
            has_image = False
            if paragraph._element.xpath('.//pic:pic'):
                # Parcourir les runs pour trouver l'image
                for run in paragraph.runs:
                    if 'graphic' in run._element.xml:
                        # Extraire le rId de l'image depuis le XML
                        import xml.etree.ElementTree as ET
                        try:
                            # Parser le XML du run pour trouver le rId
                            root = ET.fromstring(run._element.xml)
                            # Chercher l'attribut r:embed ou r:link
                            for elem in root.iter():
                                for attr_name, attr_value in elem.attrib.items():
                                    if 'embed' in attr_name or 'link' in attr_name:
                                        # Trouver la relation correspondante
                                        if attr_value in doc.part.rels:
                                            rel = doc.part.rels[attr_value]
                                            if "image" in rel.target_ref:
                                                image_ref_id = f"__IMAGE_{image_counter}__"
                                                img_data = extract_image_data(rel.target_part)
                                                
                                                if img_data:
                                                    image_data[image_ref_id] = img_data
                                                    raw_structure.append({
                                                        'type': 'image',
                                                        'ref_id': image_ref_id
                                                    })
                                                    image_counter += 1
                                                    has_image = True
                                                    break
                                if has_image:
                                    break
                        except:
                            # Fallback : méthode alternative si le parsing XML échoue
                            # Extraire toutes les images de ce paragraphe
                            for rel_id, rel in doc.part.rels.items():
                                if "image" in rel.target_ref:
                                    # Vérifier si cette image est référencée dans ce paragraphe
                                    if rel_id in run._element.xml:
                                        image_ref_id = f"__IMAGE_{image_counter}__"
                                        img_data = extract_image_data(rel.target_part)
                                        
                                        if img_data:
                                            image_data[image_ref_id] = img_data
                                            raw_structure.append({
                                                'type': 'image',
                                                'ref_id': image_ref_id
                                            })
                                            image_counter += 1
                                            has_image = True
                                            break
                        
                        if has_image:
                            break
            
            # Traiter le texte seulement s'il n'y a pas d'image ou s'il y a du texte en plus
            text = paragraph.text.strip()
            if text and not has_image:  # Ne pas ajouter le texte si c'est un paragraphe avec image
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
    
    return raw_structure, image_data


# ============================================================================
# ANALYSE SÉMANTIQUE AVEC GEMINI
# ============================================================================

def build_gemini_prompt(raw_structure: List[Dict[str, Any]]) -> str:
    """Construit le prompt pour l'API Gemini"""
    text_representation = []
    for item in raw_structure:
        if item['type'] == 'image':
            text_representation.append(f"[IMAGE: {item['ref_id']}]")
        else:
            content = item['content']
            if len(content) > 150:
                content = content[:150] + "..."
            text_representation.append(f"[{item['type'].upper()}] {content}")
    
    structure_text = "\n".join(text_representation)
    
    prompt = f"""Analyse ce document et retourne UNIQUEMENT un tableau JSON.

RÈGLES STRICTES:
1. Types: h1, h2, h3, h4, p, image
2. Premier titre = h1
3. Images: utilise les IDs fournis
4. Format: SEULEMENT le JSON, rien d'autre

DOCUMENT:
{structure_text}

RETOURNE UNIQUEMENT CE FORMAT (exemple):
[{{"type":"h1","content":"Titre"}},{{"type":"p","content":"Texte"}},{{"type":"image","ref_id":"__IMAGE_1__"}}]"""

    return prompt


def get_semantic_structure(
    raw_structure: List[Dict[str, Any]], 
    model: genai.GenerativeModel,
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    """Analyse avec l'API Gemini"""
    prompt = build_gemini_prompt(raw_structure)
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"🔄 Tentative {attempt + 1}/{max_retries}...", file=sys.stderr)
            else:
                print("📡 Envoi de la requête à l'API Gemini...", file=sys.stderr)
            
            response = model.generate_content(prompt)
            
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = response.candidates[0].finish_reason
                if finish_reason == 2:
                    print("⚠️  Réponse bloquée par les filtres de sécurité, retry...", file=sys.stderr)
                    continue
                elif finish_reason == 3:
                    print("⚠️  Réponse tronquée, retry...", file=sys.stderr)
                    if len(raw_structure) > 20:
                        print("📊 Document trop long, traitement par sections...", file=sys.stderr)
                        return process_long_document(raw_structure, model)
                    continue
            
            if not response or not response.text:
                print("⚠️  Pas de réponse texte, retry...", file=sys.stderr)
                continue
            
            response_text = response.text.strip()
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'^```\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = response_text.strip()
            
            print("✅ Réponse reçue de Gemini", file=sys.stderr)
            
            try:
                semantic_structure = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"❌ Erreur de parsing JSON: {e}", file=sys.stderr)
                if attempt < max_retries - 1:
                    print(f"🔄 Nouvelle tentative...", file=sys.stderr)
                    continue
                else:
                    print(f"Réponse brute de l'IA:\n{response_text[:500]}...", file=sys.stderr)
                    raise Exception(f"JSON invalide après {max_retries} tentatives: {e}")
            
            if not isinstance(semantic_structure, list):
                raise Exception("La structure sémantique doit être une liste")
            
            for item in semantic_structure:
                if not isinstance(item, dict):
                    raise Exception("Chaque élément doit être un dictionnaire")
                if 'type' not in item:
                    raise Exception("Chaque élément doit avoir un 'type'")
                if item['type'] != 'image' and 'content' not in item:
                    raise Exception(f"Les éléments de type '{item['type']}' doivent avoir un 'content'")
            
            print(f"✅ Structure sémantique validée: {len(semantic_structure)} éléments", file=sys.stderr)
            return semantic_structure
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Erreur: {e}", file=sys.stderr)
                print(f"🔄 Nouvelle tentative...", file=sys.stderr)
                continue
            else:
                raise Exception(f"Erreur après {max_retries} tentatives: {e}")
    
    raise Exception("Impossible d'obtenir une réponse valide de l'API Gemini")


def process_long_document(
    raw_structure: List[Dict[str, Any]], 
    model: genai.GenerativeModel
) -> List[Dict[str, Any]]:
    """Traite un document long en sections"""
    print("🔄 Traitement du document en sections...", file=sys.stderr)
    
    chunk_size = 15
    chunks = [raw_structure[i:i + chunk_size] for i in range(0, len(raw_structure), chunk_size)]
    
    all_results = []
    
    for idx, chunk in enumerate(chunks):
        print(f"📊 Traitement section {idx + 1}/{len(chunks)}...", file=sys.stderr)
        prompt = build_gemini_prompt(chunk)
        
        try:
            response = model.generate_content(prompt)
            if response and response.text:
                response_text = response.text.strip()
                response_text = re.sub(r'^```json\s*', '', response_text)
                response_text = re.sub(r'^```\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
                response_text = response_text.strip()
                
                chunk_result = json.loads(response_text)
                all_results.extend(chunk_result)
        except Exception as e:
            print(f"⚠️  Erreur section {idx + 1}: {e}", file=sys.stderr)
            continue
    
    print(f"✅ Document complet traité: {len(all_results)} éléments", file=sys.stderr)
    return all_results


# ============================================================================
# GÉNÉRATION DES WIDGETS ELEMENTOR
# ============================================================================

def generate_unique_id() -> str:
    """Génère un ID unique pour les éléments Elementor"""
    import random
    import string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))


def create_heading_widget(content: str, tag: str) -> Dict[str, Any]:
    """Crée un widget heading Elementor"""
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
    """Crée un widget text-editor Elementor"""
    return {
        "id": generate_unique_id(),
        "elType": "widget",
        "settings": {
            "editor": content
        },
        "elements": [],
        "widgetType": "text-editor"
    }


def create_image_widget(ref_id: str, image_info: Optional[Dict] = None) -> Dict[str, Any]:
    """Crée un widget image Elementor"""
    image_url = "https://example.com/placeholder.jpg"
    
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
    
    if image_info and 'width' in image_info and 'height' in image_info:
        widget["settings"]["image"]["width"] = image_info['width']
        widget["settings"]["image"]["height"] = image_info['height']
    
    return widget


# ============================================================================
# CONSTRUCTION DU JSON ELEMENTOR
# ============================================================================

def build_elementor_json(
    semantic_structure: List[Dict[str, Any]], 
    image_data: Dict[str, Any],
    layout_type: str = "single_column",
    distribution_strategy: str = "auto"
) -> Dict[str, Any]:
    """Construit le JSON Elementor final"""
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
                widget = create_image_widget(ref_id, img_info)
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
    
    parser.add_argument(
        'docx_file',
        type=str,
        help='Chemin vers le fichier .docx à convertir'
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
    
    args = parser.parse_args()
    
    try:
        if args.verbose:
            print("🔧 Initialisation...", file=sys.stderr)
        
        api_key = load_api_key()
        model = configure_gemini(api_key)
        
        if args.verbose:
            print(f"📄 Parsing du document '{args.docx_file}'...", file=sys.stderr)
        
        raw_structure, image_data = parse_document(args.docx_file)
        
        if args.verbose:
            print(f"   → {len(raw_structure)} éléments extraits", file=sys.stderr)
            print(f"   → {len(image_data)} images trouvées", file=sys.stderr)
        
        if args.verbose:
            print("🤖 Analyse sémantique avec Gemini...", file=sys.stderr)
        
        semantic_structure = get_semantic_structure(raw_structure, model)
        
        if args.verbose:
            print("🗏 Construction du JSON Elementor...", file=sys.stderr)
            print(f"   Layout: {args.layout}", file=sys.stderr)
            print(f"   Distribution: {args.distribution}", file=sys.stderr)
        
        elementor_json = build_elementor_json(
            semantic_structure, 
            image_data,
            layout_type=args.layout,
            distribution_strategy=args.distribution
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
