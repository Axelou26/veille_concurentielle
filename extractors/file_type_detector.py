"""
🔍 Détecteur de Type de Fichier Unifié
=====================================

Détection unifiée et cohérente du type de fichier pour tous les extracteurs.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FileTypeDetector:
    """
    Détecteur unifié de type de fichier
    
    Centralise la logique de détection pour éviter les incohérences
    entre différents modules.
    """
    
    # Mapping des extensions vers les types
    EXTENSION_TO_TYPE = {
        '.pdf': 'pdf',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.txt': 'text',
        '.md': 'text',
        '.doc': 'text',
        '.docx': 'text',
        '.csv': 'excel',  # Traité comme Excel
    }
    
    # Types reconnus dans les analyses de fichiers
    ANALYSIS_TYPE_MAPPING = {
        'pdf_avance': 'pdf',
        'pdf': 'pdf',
        'excel': 'excel',
        'texte': 'text',
        'text': 'text',
        'word': 'text',
        'csv': 'excel',
    }
    
    @classmethod
    def detect(cls, file_path: str = None, file_name: str = None, 
               file_analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Détecte le type de fichier de manière unifiée
        
        Args:
            file_path: Chemin complet du fichier (optionnel)
            file_name: Nom du fichier avec extension (optionnel)
            file_analysis: Analyse préliminaire du fichier (optionnel)
            
        Returns:
            Type de fichier détecté ('pdf', 'excel', 'text', 'other')
        """
        try:
            # 1. Vérifier dans l'analyse du fichier en premier (plus fiable)
            if file_analysis:
                detected_type = cls._detect_from_analysis(file_analysis)
                if detected_type != 'other':
                    return detected_type
            
            # 2. Utiliser le nom du fichier ou le chemin
            file_to_check = file_name
            if file_to_check is None and file_path:
                file_to_check = os.path.basename(file_path)
            
            if file_to_check:
                extension = os.path.splitext(file_to_check)[1].lower()
                detected_type = cls.EXTENSION_TO_TYPE.get(extension, 'other')
                
                if detected_type != 'other':
                    logger.debug(f"Type détecté depuis extension '{extension}': {detected_type}")
                    return detected_type
            
            # 3. Type inconnu
            logger.warning(f"Type de fichier non détecté pour: {file_name or file_path}")
            return 'other'
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection du type de fichier: {e}")
            return 'other'
    
    @classmethod
    def _detect_from_analysis(cls, file_analysis: Dict[str, Any]) -> str:
        """
        Détecte le type depuis l'analyse du fichier
        
        Args:
            file_analysis: Analyse préliminaire du fichier
            
        Returns:
            Type de fichier ou 'other'
        """
        try:
            contenu_extraite = file_analysis.get('contenu_extraite', {})
            file_type = contenu_extraite.get('type', '')
            
            if file_type:
                mapped_type = cls.ANALYSIS_TYPE_MAPPING.get(file_type.lower(), 'other')
                if mapped_type != 'other':
                    logger.debug(f"Type détecté depuis analyse: {file_type} -> {mapped_type}")
                    return mapped_type
            
            return 'other'
            
        except Exception as e:
            logger.error(f"Erreur détection depuis analyse: {e}")
            return 'other'
    
    @classmethod
    def is_supported(cls, file_type: str) -> bool:
        """
        Vérifie si un type de fichier est supporté
        
        Args:
            file_type: Type à vérifier
            
        Returns:
            True si supporté, False sinon
        """
        supported_types = ['pdf', 'excel', 'text']
        return file_type in supported_types
    
    @classmethod
    def get_supported_extensions(cls) -> list:
        """
        Retourne la liste de toutes les extensions supportées
        
        Returns:
            Liste des extensions supportées
        """
        return list(cls.EXTENSION_TO_TYPE.keys())


