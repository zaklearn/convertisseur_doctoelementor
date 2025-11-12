# Word to Elementor - Version Optimisée

Application corrigée avec détection heuristique des titres.

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app_optimized.py
```

## Corrections appliquées

1. **Détection heuristique des titres** : Pattern numérique (2.1, 2.2), longueur, majuscules
2. **Widgets corrects** : heading vs text-editor typés correctement
3. **Position exacte des images** : Ordre préservé du document source
4. **URLs images** : Liaison automatique avec URL base WordPress

## Utilisation

1. Uploader fichier .docx
2. Entrer URL base WordPress (optionnel)
3. Convertir
4. Télécharger JSON ou ZIP (JSON + images)
5. Uploader images dans WordPress
6. Importer JSON dans Elementor

## Modules

- `word_processor.py` : Extraction document + détection heuristique
- `json_builder.py` : Construction JSON Elementor
- `app_optimized.py` : Interface Streamlit

## Test

Résultat avec CHAPITRE_II.docx :
- 10 headings (7 h2 + 3 h3)
- 20 paragraphes
- 7 images
- JSON : CHAPITRE_II_optimized.json
