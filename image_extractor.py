#!/usr/bin/env python3
"""
image_extractor.py
Module extraction images DOCX - évite duplication
"""

import os
from typing import Dict, Tuple
from pathlib import Path
from docx import Document
from PIL import Image
from io import BytesIO


def extract_all_images(docx_path: str, output_folder: str, base_name: str = "image") -> Tuple[Dict[int, str], Dict[int, dict]]:
    """
    Extrait TOUTES les images du DOCX
    
    Returns:
        tuple: (filenames_map, metadata_map)
        - filenames_map: {1: "image_001.png", 2: "image_002.jpg", ...}
        - metadata_map: {1: {"width": 800, "height": 600, "format": "PNG"}, ...}
    """
    os.makedirs(output_folder, exist_ok=True)
    
    doc = Document(docx_path)
    filenames_map = {}
    metadata_map = {}
    
    # Extraire toutes les relations image
    image_counter = 1
    processed_rids = set()
    
    for rel_id, rel in doc.part.rels.items():
        if "image" in rel.target_ref and rel_id not in processed_rids:
            try:
                # Extraire image
                image_part = rel.target_part
                image_bytes = image_part.blob
                img = Image.open(BytesIO(image_bytes))
                
                # Extension
                ext = img.format.lower() if img.format else 'png'
                if ext == 'jpeg':
                    ext = 'jpg'
                
                # Nom fichier
                filename = f"{base_name}_{image_counter:03d}.{ext}"
                filepath = os.path.join(output_folder, filename)
                
                # Sauvegarder
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                
                # Stocker mapping
                filenames_map[image_counter] = filename
                metadata_map[image_counter] = {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format or "PNG"
                }
                
                processed_rids.add(rel_id)
                image_counter += 1
                
            except Exception as e:
                print(f"Erreur image {rel_id}: {e}")
                continue
    
    return filenames_map, metadata_map


def get_image_positions(docx_path: str) -> Dict[int, int]:
    """
    Détermine position de chaque image dans le document
    
    Returns:
        dict: {image_index: paragraph_position}
    """
    doc = Document(docx_path)
    positions = {}
    image_counter = 1
    para_position = 0
    
    for para in doc.paragraphs:
        if para._element.xpath('.//pic:pic'):
            positions[image_counter] = para_position
            image_counter += 1
        para_position += 1
    
    return positions
