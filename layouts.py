#!/usr/bin/env python3
"""
layouts.py

Configuration des layouts multi-colonnes pour Elementor.
Définit différents templates pour différents types de contenu.

Version: 3.0
"""

from typing import Dict, List, Any
from enum import Enum


class LayoutType(Enum):
    """Types de layouts disponibles"""
    SINGLE_COLUMN = "single_column"
    TWO_COLUMNS_EQUAL = "two_columns_equal"
    TWO_COLUMNS_SIDEBAR_LEFT = "two_columns_sidebar_left"
    TWO_COLUMNS_SIDEBAR_RIGHT = "two_columns_sidebar_right"
    THREE_COLUMNS = "three_columns"
    BLOG_LAYOUT = "blog_layout"


class LayoutConfig:
    """Configuration des layouts Elementor"""
    
    # Définitions des layouts
    LAYOUTS = {
        # 1 colonne (100%)
        "single_column": {
            "name": "Une seule colonne",
            "description": "Contenu pleine largeur (idéal pour pages simples)",
            "icon": "📄",
            "columns": [
                {"size": 100, "content_type": "main"}
            ]
        },
        
        # 2 colonnes égales (50% / 50%)
        "two_columns_equal": {
            "name": "Deux colonnes égales",
            "description": "Contenu réparti équitablement (50/50)",
            "icon": "⚖️",
            "columns": [
                {"size": 50, "content_type": "main"},
                {"size": 50, "content_type": "main"}
            ]
        },
        
        # Sidebar gauche (33% / 67%)
        "two_columns_sidebar_left": {
            "name": "Sidebar à gauche",
            "description": "Sidebar 33% + Contenu principal 67%",
            "icon": "◀️",
            "columns": [
                {"size": 33.33, "content_type": "sidebar"},
                {"size": 66.66, "content_type": "main"}
            ]
        },
        
        # Sidebar droite (67% / 33%) - Layout BLOG classique
        "two_columns_sidebar_right": {
            "name": "Sidebar à droite",
            "description": "Contenu principal 67% + Sidebar 33% (classique blog)",
            "icon": "▶️",
            "columns": [
                {"size": 66.66, "content_type": "main"},
                {"size": 33.33, "content_type": "sidebar"}
            ]
        },
        
        # 3 colonnes égales (33% / 33% / 33%)
        "three_columns": {
            "name": "Trois colonnes égales",
            "description": "Contenu en 3 colonnes (idéal pour grilles)",
            "icon": "▦",
            "columns": [
                {"size": 33.33, "content_type": "main"},
                {"size": 33.33, "content_type": "main"},
                {"size": 33.33, "content_type": "main"}
            ]
        },
        
        # Layout Blog optimisé
        "blog_layout": {
            "name": "Layout Blog optimisé",
            "description": "Article 60% + Sidebar 40% avec espacement optimisé",
            "icon": "📰",
            "columns": [
                {"size": 60, "content_type": "main"},
                {"size": 40, "content_type": "sidebar"}
            ],
            "spacing": {
                "column_gap": "30",
                "padding": "20px"
            }
        }
    }
    
    # Stratégies de distribution du contenu
    DISTRIBUTION_STRATEGIES = {
        "auto": {
            "name": "Automatique",
            "description": "Distribution intelligente selon le type de contenu"
        },
        "sequential": {
            "name": "Séquentielle",
            "description": "Remplir colonne 1, puis colonne 2, etc."
        },
        "alternating": {
            "name": "Alternée",
            "description": "Alterner entre les colonnes (1-2-1-2...)"
        },
        "balanced": {
            "name": "Équilibrée",
            "description": "Répartir pour avoir un nombre égal d'éléments"
        }
    }
    
    # Configuration responsive par défaut
    RESPONSIVE_CONFIG = {
        "desktop": {
            "breakpoint": ">= 1025px",
            "apply_layout": True
        },
        "tablet": {
            "breakpoint": "768px - 1024px",
            "apply_layout": True,
            "stack_columns": False
        },
        "mobile": {
            "breakpoint": "< 768px",
            "apply_layout": False,
            "stack_columns": True  # Force une colonne sur mobile
        }
    }
    
    @classmethod
    def get_layout(cls, layout_type: str) -> Dict[str, Any]:
        """
        Récupère la configuration d'un layout
        
        Args:
            layout_type: Type de layout (clé du dictionnaire LAYOUTS)
            
        Returns:
            dict: Configuration du layout
        """
        return cls.LAYOUTS.get(layout_type, cls.LAYOUTS["single_column"])
    
    @classmethod
    def get_all_layouts(cls) -> Dict[str, Dict[str, Any]]:
        """Retourne tous les layouts disponibles"""
        return cls.LAYOUTS
    
    @classmethod
    def get_blog_layout(cls) -> Dict[str, Any]:
        """Retourne le layout optimisé pour les blogs"""
        return cls.LAYOUTS["blog_layout"]


class ContentDistributor:
    """Gère la distribution du contenu entre les colonnes"""
    
    @staticmethod
    def distribute_auto(
        elements: List[Dict[str, Any]], 
        columns_config: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Distribution automatique intelligente
        
        Règles améliorées :
        - H1 + premier paragraphe dans la colonne principale
        - Reste du contenu distribué équitablement
        - Les H2 marquent souvent le début d'une nouvelle section
        
        Args:
            elements: Liste des éléments à distribuer
            columns_config: Configuration des colonnes
            
        Returns:
            list: Liste de listes (une par colonne) contenant les éléments
        """
        num_columns = len(columns_config)
        distributed = [[] for _ in range(num_columns)]
        
        # Identifier la colonne principale (la plus large)
        main_col_idx = 0
        max_size = 0
        for col_idx, col_config in enumerate(columns_config):
            if col_config.get("size", 0) > max_size:
                max_size = col_config["size"]
                main_col_idx = col_idx
        
        # Pour 2 colonnes : distribution intelligente
        if num_columns == 2:
            h1_found = False
            intro_added = False
            
            for element in elements:
                element_type = element.get("type", "")
                
                # Premier H1 va toujours dans la colonne principale
                if element_type == "h1" and not h1_found:
                    distributed[main_col_idx].append(element)
                    h1_found = True
                # Premier paragraphe après H1 (intro) va dans colonne principale  
                elif element_type == "p" and h1_found and not intro_added:
                    distributed[main_col_idx].append(element)
                    intro_added = True
                # Le reste est distribué pour équilibrer les colonnes
                else:
                    # Ajouter à la colonne qui a le moins d'éléments
                    if len(distributed[0]) <= len(distributed[1]):
                        distributed[0].append(element)
                    else:
                        distributed[1].append(element)
        
        elif num_columns == 3:
            # Pour 3 colonnes : distribution par rotation
            for idx, element in enumerate(elements):
                col_idx = idx % 3
                distributed[col_idx].append(element)
        
        else:
            # 1 colonne ou fallback
            distributed[0] = elements
        
        return distributed
    
    @staticmethod
    def distribute_sequential(
        elements: List[Dict[str, Any]], 
        columns_config: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Distribution séquentielle : remplir colonne par colonne
        """
        num_columns = len(columns_config)
        distributed = [[] for _ in range(num_columns)]
        
        elements_per_column = len(elements) // num_columns
        remainder = len(elements) % num_columns
        
        current_idx = 0
        for col_idx in range(num_columns):
            # Ajouter les éléments de base
            num_elements = elements_per_column
            # Distribuer le reste
            if col_idx < remainder:
                num_elements += 1
            
            distributed[col_idx] = elements[current_idx:current_idx + num_elements]
            current_idx += num_elements
        
        return distributed
    
    @staticmethod
    def distribute_alternating(
        elements: List[Dict[str, Any]], 
        columns_config: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Distribution alternée : 1-2-3-1-2-3...
        """
        num_columns = len(columns_config)
        distributed = [[] for _ in range(num_columns)]
        
        for idx, element in enumerate(elements):
            col_idx = idx % num_columns
            distributed[col_idx].append(element)
        
        return distributed
    
    @staticmethod
    def distribute_balanced(
        elements: List[Dict[str, Any]], 
        columns_config: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Distribution équilibrée : même nombre d'éléments par colonne
        """
        num_columns = len(columns_config)
        distributed = [[] for _ in range(num_columns)]
        
        elements_per_column = len(elements) // num_columns
        remainder = len(elements) % num_columns
        
        current_idx = 0
        for col_idx in range(num_columns):
            num_elements = elements_per_column + (1 if col_idx < remainder else 0)
            distributed[col_idx] = elements[current_idx:current_idx + num_elements]
            current_idx += num_elements
        
        return distributed
    
    @classmethod
    def distribute(
        cls, 
        elements: List[Dict[str, Any]], 
        columns_config: List[Dict[str, Any]],
        strategy: str = "auto"
    ) -> List[List[Dict[str, Any]]]:
        """
        Distribue les éléments selon la stratégie choisie
        
        Args:
            elements: Liste des éléments à distribuer
            columns_config: Configuration des colonnes
            strategy: Stratégie de distribution
            
        Returns:
            list: Éléments distribués par colonne
        """
        if strategy == "auto":
            return cls.distribute_auto(elements, columns_config)
        elif strategy == "sequential":
            return cls.distribute_sequential(elements, columns_config)
        elif strategy == "alternating":
            return cls.distribute_alternating(elements, columns_config)
        elif strategy == "balanced":
            return cls.distribute_balanced(elements, columns_config)
        else:
            # Par défaut, stratégie auto
            return cls.distribute_auto(elements, columns_config)


# Templates prédéfinis pour différents cas d'usage
PREDEFINED_TEMPLATES = {
    "blog_article": {
        "name": "Article de Blog",
        "layout": "blog_layout",
        "distribution": "auto",
        "description": "Layout classique avec contenu principal et sidebar",
        "recommended_for": ["articles", "posts", "actualités"]
    },
    
    "landing_page": {
        "name": "Page de Destination",
        "layout": "single_column",
        "distribution": "sequential",
        "description": "Contenu pleine largeur pour un impact maximal",
        "recommended_for": ["landing pages", "pages de vente", "pages promotionnelles"]
    },
    
    "portfolio": {
        "name": "Portfolio",
        "layout": "three_columns",
        "distribution": "balanced",
        "description": "Grille à 3 colonnes pour présenter des projets",
        "recommended_for": ["portfolios", "galeries", "catalogues"]
    },
    
    "magazine": {
        "name": "Style Magazine",
        "layout": "two_columns_sidebar_right",
        "distribution": "auto",
        "description": "Layout magazine avec sidebar pour widgets",
        "recommended_for": ["magazines", "news", "médias"]
    },
    
    "documentation": {
        "name": "Documentation",
        "layout": "two_columns_sidebar_left",
        "distribution": "sequential",
        "description": "Sidebar gauche pour navigation, contenu à droite",
        "recommended_for": ["documentation", "guides", "tutoriels"]
    }
}