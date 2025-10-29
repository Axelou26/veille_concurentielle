"""
🧩 Extracteurs d'Appels d'Offres - Module Principal
==================================================

Architecture modulaire pour l'extraction intelligente d'informations
depuis différents types de documents d'appels d'offres.

Modules disponibles:
- base_extractor: Classe de base abstraite
- pattern_manager: Gestion des patterns regex
- pdf_extractor: Extraction PDF spécialisée
- excel_extractor: Extraction Excel spécialisée
- text_extractor: Extraction texte spécialisée
- lot_detector: Détection des lots avec stratégies
- validation_engine: Moteur de validation amélioré
- file_type_detector: Détection unifiée du type de fichier
- intelligent_post_processor: Post-traitement intelligent avec ExtractionImprover
"""

from .base_extractor import BaseExtractor
from .pattern_manager import PatternManager
from .pdf_extractor import PDFExtractor
from .excel_extractor import ExcelExtractor
from .text_extractor import TextExtractor
from .lot_detector import LotDetector
from .validation_engine import ValidationEngine, ValidationResult
from .file_type_detector import FileTypeDetector
from .intelligent_post_processor import IntelligentPostProcessor

__all__ = [
    'BaseExtractor',
    'PatternManager', 
    'PDFExtractor',
    'ExcelExtractor',
    'TextExtractor',
    'LotDetector',
    'ValidationEngine',
    'ValidationResult',
    'FileTypeDetector',
    'IntelligentPostProcessor'
]

__version__ = "2.0.0"
__author__ = "IA Veille Concurrentielle Team"

