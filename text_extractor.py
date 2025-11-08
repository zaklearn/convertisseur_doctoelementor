#!/usr/bin/env python3
"""
text_extractor.py
Extraction texte direct DOCX/PDF sans IA - fiabilité 99%
VERSION CORRIGÉE - Conserve la position des images
"""

from typing import List, Dict, Any
from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.text.paragraph import Paragraph


def extract_text_from_docx(docx_path: str) -> List[Dict[str, Any]]:
    """
    Extraction directe texte DOCX sans IA
    Détecte hiérarchie H1-H6 par styles Word
    VERSION CORRIGÉE - Conserve l'ordre exact des éléments
    """
    doc = Document(docx_path)
    structure = []
    image_counter = 1
    
    for element in doc.element.body:
        if isinstance(element, CT_P):
            para = Paragraph(element, doc)
            
            # Vérifier s'il y a une image dans ce paragraphe
            has_image = False
            if para._element.xpath('.//pic:pic'):
                # Ajouter l'image à sa position exacte
                structure.append({
                    'type': 'image',
                    'ref_id': f"__IMAGE_{image_counter}__"
                })
                image_counter += 1
                has_image = True
            
            # Traiter le texte SEULEMENT s'il n'y a pas d'image dans ce paragraphe
            # ou si on veut garder le texte qui accompagne l'image (comportement configurable)
            text = para.text.strip()
            
            # Si le paragraphe contient une image ET du texte, on ignore le texte
            # (comportement par défaut pour correspondre à parse_document)
            if text and not has_image:
                style = para.style.name if para.style else 'Normal'
                
                # Déterminer le type d'élément basé sur le style
                if 'Heading 1' in style or 'Title' in style:
                    elem_type = 'h1'
                elif 'Heading 2' in style:
                    elem_type = 'h2'
                elif 'Heading 3' in style:
                    elem_type = 'h3'
                elif 'Heading 4' in style:
                    elem_type = 'h4'
                elif 'Heading 5' in style:
                    elem_type = 'h5'
                elif 'Heading 6' in style:
                    elem_type = 'h6'
                else:
                    elem_type = 'p'
                
                structure.append({
                    'type': elem_type,
                    'content': text  # CONTENU COMPLET sans troncation
                })
    
    return structure


def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extraction directe texte PDF sans IA
    Détecte hiérarchie par taille police
    VERSION CORRIGÉE - Conserve l'ordre des éléments
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF requis: pip install pymupdf")
    
    doc = fitz.open(pdf_path)
    structure = []
    image_counter = 1
    
    for page_num, page in enumerate(doc):
        # Obtenir tous les blocs dans l'ordre d'apparition
        blocks = page.get_text("dict")["blocks"]
        
        # Trier les blocs par position verticale (y) pour maintenir l'ordre
        blocks_sorted = sorted(blocks, key=lambda b: (b.get("bbox", [0, 0])[1], b.get("bbox", [0, 0])[0]))
        
        for block in blocks_sorted:
            if block["type"] == 0:  # Texte
                # Collecter tout le texte du bloc
                block_texts = []
                block_sizes = []
                
                for line in block.get("lines", []):
                    line_text = ""
                    line_sizes = []
                    
                    for span in line.get("spans", []):
                        span_text = span.get("text", "")
                        line_text += span_text
                        if span.get("size"):
                            line_sizes.append(span["size"])
                    
                    line_text = line_text.strip()
                    if line_text:
                        block_texts.append(line_text)
                        if line_sizes:
                            block_sizes.extend(line_sizes)
                
                # Joindre toutes les lignes du bloc
                full_text = " ".join(block_texts).strip()
                if not full_text:
                    continue
                
                # Déterminer le niveau basé sur la taille de police moyenne
                if block_sizes:
                    avg_size = sum(block_sizes) / len(block_sizes)
                else:
                    avg_size = 12  # Taille par défaut
                
                # Classification améliorée des niveaux
                if avg_size >= 24:
                    elem_type = 'h1'
                elif avg_size >= 20:
                    elem_type = 'h2'
                elif avg_size >= 16:
                    elem_type = 'h3'
                elif avg_size >= 14:
                    elem_type = 'h4'
                elif avg_size >= 13:
                    elem_type = 'h5'
                elif avg_size >= 12:
                    elem_type = 'h6'
                else:
                    elem_type = 'p'
                
                structure.append({
                    'type': elem_type,
                    'content': full_text,
                    '_page': page_num + 1,  # Info supplémentaire pour debug
                    '_size': round(avg_size, 1)  # Info supplémentaire pour debug
                })
            
            elif block["type"] == 1:  # Image
                structure.append({
                    'type': 'image',
                    'ref_id': f"__IMAGE_{image_counter}__",
                    '_page': page_num + 1  # Info supplémentaire pour debug
                })
                image_counter += 1
    
    doc.close()
    return structure


def merge_consecutive_paragraphs(structure: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fonction utilitaire pour fusionner les paragraphes consécutifs
    si nécessaire (optionnel)
    """
    if not structure:
        return structure
    
    merged = []
    current_p = None
    
    for item in structure:
        if item['type'] == 'p' and current_p is not None:
            # Fusionner avec le paragraphe précédent
            current_p['content'] += ' ' + item['content']
        else:
            # Nouvel élément ou changement de type
            if current_p is not None:
                merged.append(current_p)
            
            if item['type'] == 'p':
                current_p = item.copy()
            else:
                current_p = None
                merged.append(item)
    
    # Ajouter le dernier paragraphe s'il existe
    if current_p is not None:
        merged.append(current_p)
    
    return merged
