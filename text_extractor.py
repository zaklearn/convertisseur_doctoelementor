#!/usr/bin/env python3
"""
text_extractor.py
Extraction texte direct DOCX/PDF sans IA - fiabilité 99%
"""

from typing import List, Dict, Any
from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.text.paragraph import Paragraph


def extract_text_from_docx(docx_path: str) -> List[Dict[str, Any]]:
    """
    Extraction directe texte DOCX sans IA
    Détecte hiérarchie H1-H6 par styles Word
    """
    doc = Document(docx_path)
    structure = []
    image_counter = 1
    
    for element in doc.element.body:
        if isinstance(element, CT_P):
            para = Paragraph(element, doc)

            # --- CORRECTION ---
            # 1. Vérifier les images D'ABORD
            is_image = False
            if para._element.xpath('.//pic:pic'):
                structure.append({
                    'type': 'image',
                    'ref_id': f"__IMAGE_{image_counter}__"
                })
                image_counter += 1
                is_image = True
            # --- FIN CORRECTION ---

            # 2. Vérifier le texte
            text = para.text.strip()
            
            if not text:
                # Si c'est juste une image (is_image=True), on a fini.
                # Si c'est un paragraphe vide (is_image=False), on ignore.
                continue
            
            # Si un paragraphe contient A LA FOIS une image ET du texte,
            # on ignore le texte (comportement identique à parse_document).
            if is_image:
                 continue

            # 3. Traiter le texte (seulement si ce n'est pas une image)
            style = para.style.name if para.style else 'Normal'
            
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
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF requis: pip install pymupdf")
    
    doc = fitz.open(pdf_path)
    structure = []
    image_counter = 1
    
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if block["type"] == 0:  # Texte
                for line in block["lines"]:
                    text_parts = []
                    font_sizes = []
                    
                    for span in line["spans"]:
                        text_parts.append(span["text"])
                        font_sizes.append(span["size"])
                    
                    text = "".join(text_parts).strip()
                    if not text:
                        continue
                    
                    # Détection niveau par taille police
                    avg_size = sum(font_sizes) / len(font_sizes)
                    
                    if avg_size >= 20:
                        elem_type = 'h1'
                    elif avg_size >= 16:
                        elem_type = 'h2'
                    elif avg_size >= 14:
                        elem_type = 'h3'
                    elif avg_size >= 12:
                        elem_type = 'h4'
                    else:
                        elem_type = 'p'
                    
                    structure.append({
                        'type': elem_type,
                        'content': text  # CONTENU COMPLET
                    })
            
            elif block["type"] == 1:  # Image
                structure.append({
                    'type': 'image',
                    'ref_id': f"__IMAGE_{image_counter}__"
                })
                image_counter += 1
    
    doc.close()
    return structure