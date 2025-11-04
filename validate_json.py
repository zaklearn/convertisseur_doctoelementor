#!/usr/bin/env python3
"""
valider_json.py

Script de validation pour vérifier que le JSON généré est compatible avec Elementor.
Permet de tester un fichier JSON avant de l'importer dans Elementor.

Usage:
    python valider_json.py fichier.json
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List


def validate_json_structure(data: Any) -> tuple[bool, List[str]]:
    """
    Valide la structure du JSON Elementor
    
    Returns:
        tuple: (est_valide, liste_erreurs)
    """
    errors = []
    
    # Vérification 1: Le JSON doit être un dictionnaire
    if not isinstance(data, dict):
        errors.append("❌ Le JSON doit être un objet (dictionnaire), pas un array")
        return False, errors
    
    # Vérification 2: Présence des champs obligatoires
    required_fields = ['version', 'type', 'content']
    for field in required_fields:
        if field not in data:
            errors.append(f"❌ Champ obligatoire manquant : '{field}'")
    
    # Vérification 3: Version
    if 'version' in data:
        if not isinstance(data['version'], str):
            errors.append("❌ Le champ 'version' doit être une chaîne de caractères")
        elif data['version'] != "0.4":
            errors.append(f"⚠️  Version '{data['version']}' - Version recommandée: '0.4'")
    
    # Vérification 4: Type
    if 'type' in data:
        valid_types = ['page', 'section', 'widget', 'post', 'container']
        if data['type'] not in valid_types:
            errors.append(f"⚠️  Type '{data['type']}' non standard - Types valides: {', '.join(valid_types)}")
    
    # Vérification 5: Content doit être un array
    if 'content' in data:
        if not isinstance(data['content'], list):
            errors.append("❌ Le champ 'content' doit être un array")
        elif len(data['content']) == 0:
            errors.append("⚠️  Le champ 'content' est vide")
        else:
            # Vérifier la structure du premier élément
            first_element = data['content'][0]
            if not isinstance(first_element, dict):
                errors.append("❌ Les éléments dans 'content' doivent être des objets")
            else:
                # Vérifier les champs obligatoires d'un élément
                element_required = ['id', 'elType', 'settings', 'elements']
                for field in element_required:
                    if field not in first_element:
                        errors.append(f"❌ Élément manquant dans content[0] : '{field}'")
    
    # Vérification 6: Présence de title (optionnel mais recommandé)
    if 'title' not in data:
        errors.append("ℹ️  Champ 'title' absent (optionnel mais recommandé)")
    
    is_valid = len([e for e in errors if e.startswith("❌")]) == 0
    return is_valid, errors


def validate_elementor_elements(content: List[Dict[str, Any]]) -> List[str]:
    """
    Valide les éléments Elementor dans le content
    
    Returns:
        list: Liste des erreurs/avertissements
    """
    warnings = []
    
    for idx, element in enumerate(content):
        if element.get('elType') == 'section':
            # Vérifier qu'une section contient des colonnes
            if 'elements' not in element or not element['elements']:
                warnings.append(f"⚠️  Section #{idx} : Pas de colonnes définies")
            else:
                for col_idx, column in enumerate(element['elements']):
                    if column.get('elType') != 'column':
                        warnings.append(f"⚠️  Section #{idx} : L'élément #{col_idx} n'est pas une colonne")
                    
                    # Vérifier les widgets dans la colonne
                    if 'elements' in column:
                        for widget_idx, widget in enumerate(column['elements']):
                            if widget.get('elType') != 'widget':
                                warnings.append(f"⚠️  Section #{idx}, Colonne #{col_idx} : L'élément #{widget_idx} n'est pas un widget")
                            
                            # Vérifier le widgetType
                            if 'widgetType' not in widget:
                                warnings.append(f"❌ Section #{idx}, Colonne #{col_idx}, Widget #{widget_idx} : 'widgetType' manquant")
    
    return warnings


def validate_json_file(filepath: str, verbose: bool = False) -> bool:
    """
    Valide un fichier JSON pour Elementor
    
    Args:
        filepath: Chemin vers le fichier JSON
        verbose: Afficher les détails complets
        
    Returns:
        bool: True si valide, False sinon
    """
    print(f"🔍 Validation du fichier : {filepath}")
    print("=" * 60)
    
    # Vérifier que le fichier existe
    if not Path(filepath).exists():
        print(f"❌ Erreur : Le fichier '{filepath}' n'existe pas")
        return False
    
    # Lire et parser le JSON
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de parsing JSON : {e}")
        print(f"   Ligne {e.lineno}, Colonne {e.colno}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier : {e}")
        return False
    
    print("✅ JSON valide (syntaxe correcte)")
    print()
    
    # Valider la structure Elementor
    is_valid, errors = validate_json_structure(data)
    
    # Afficher les erreurs/avertissements
    if errors:
        print("📋 Résultats de la validation :")
        print()
        for error in errors:
            print(f"  {error}")
        print()
    
    # Validation des éléments
    if 'content' in data and isinstance(data['content'], list):
        element_warnings = validate_elementor_elements(data['content'])
        if element_warnings:
            print("📋 Analyse des éléments :")
            print()
            for warning in element_warnings:
                print(f"  {warning}")
            print()
    
    # Statistiques
    if verbose and isinstance(data, dict) and 'content' in data:
        print("📊 Statistiques :")
        print()
        
        content = data['content']
        section_count = sum(1 for el in content if el.get('elType') == 'section')
        
        widget_count = 0
        widget_types = {}
        
        for section in content:
            if section.get('elType') == 'section':
                for column in section.get('elements', []):
                    if column.get('elType') == 'column':
                        for widget in column.get('elements', []):
                            if widget.get('elType') == 'widget':
                                widget_count += 1
                                wtype = widget.get('widgetType', 'unknown')
                                widget_types[wtype] = widget_types.get(wtype, 0) + 1
        
        print(f"  Sections : {section_count}")
        print(f"  Widgets : {widget_count}")
        
        if widget_types:
            print(f"  Types de widgets :")
            for wtype, count in widget_types.items():
                print(f"    - {wtype} : {count}")
        
        print()
    
    # Résultat final
    print("=" * 60)
    if is_valid:
        print("✅ VALIDATION RÉUSSIE")
        print("   Le fichier JSON est prêt pour l'import dans Elementor !")
        return True
    else:
        print("❌ VALIDATION ÉCHOUÉE")
        print("   Corrigez les erreurs avant d'importer dans Elementor")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Valide un fichier JSON pour l'import dans Elementor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python valider_json.py output.json
  python valider_json.py output.json -v
  python valider_json.py output.json --verbose
        """
    )
    
    parser.add_argument(
        'json_file',
        type=str,
        help='Chemin vers le fichier JSON à valider'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Afficher les statistiques détaillées'
    )
    
    args = parser.parse_args()
    
    # Valider le fichier
    is_valid = validate_json_file(args.json_file, args.verbose)
    
    # Code de sortie
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()