#!/usr/bin/env python3
"""
json_builder.py - Construction JSON Elementor avec widgets corrects
"""

import random
import string
from typing import List, Dict, Any, Optional


def generate_id() -> str:
    """Génère un ID unique pour Elementor"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))


def create_heading_widget(content: str, level: str) -> Dict[str, Any]:
    """Crée un widget heading avec la structure correcte"""
    return {
        "id": generate_id(),
        "elType": "widget",
        "settings": {
            "title": content,
            "header_size": level
        },
        "elements": [],
        "widgetType": "heading"
    }


def create_text_widget(content: str) -> Dict[str, Any]:
    """Crée un widget text-editor"""
    return {
        "id": generate_id(),
        "elType": "widget",
        "settings": {
            "editor": content
        },
        "elements": [],
        "widgetType": "text-editor"
    }


def create_image_widget(ref_id: str, image_urls: Dict[str, str], image_data: Dict[str, Any]) -> Dict[str, Any]:
    """Crée un widget image avec URL et métadonnées"""
    image_url = image_urls.get(ref_id, "")
    img_info = image_data.get(ref_id, {})
    
    settings = {
        "image": {
            "url": image_url,
            "id": ""
        },
        "image_size": "full"
    }
    
    # Ajouter dimensions si disponibles
    if 'width' in img_info and 'height' in img_info:
        settings["image"]["width"] = img_info['width']
        settings["image"]["height"] = img_info['height']
    
    return {
        "id": generate_id(),
        "elType": "widget",
        "settings": settings,
        "elements": [],
        "widgetType": "image"
    }


def build_elementor_json(
    structure: List[Dict[str, Any]], 
    image_data: Dict[str, Any],
    image_urls: Dict[str, str]
) -> Dict[str, Any]:
    """
    Construit le JSON Elementor final avec widgets corrects
    """
    widgets = []
    
    for item in structure:
        item_type = item.get('type')
        
        # Headings (h1-h6)
        if item_type in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            widget = create_heading_widget(item['content'], item_type)
            widgets.append(widget)
        
        # Paragraphes
        elif item_type == 'p':
            widget = create_text_widget(item['content'])
            widgets.append(widget)
        
        # Images
        elif item_type == 'image':
            ref_id = item.get('ref_id')
            widget = create_image_widget(ref_id, image_urls, image_data)
            widgets.append(widget)
    
    # Structure Elementor complète
    column = {
        "id": generate_id(),
        "elType": "column",
        "settings": {
            "_column_size": 100,
            "_inline_size": None
        },
        "elements": widgets
    }
    
    section = {
        "id": generate_id(),
        "elType": "section",
        "settings": {},
        "elements": [column]
    }
    
    return {
        "version": "0.4",
        "title": "Document importé",
        "type": "page",
        "content": [section]
    }
