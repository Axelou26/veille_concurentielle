"""
🧠 Post-Processeur Intelligent
=============================

Intègre ExtractionImprover dans l'architecture modulaire V2
pour enrichir les extractions avec une intelligence contextuelle.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Ajouter le répertoire parent au path pour importer extraction_improver
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from extraction_improver import extraction_improver
    EXTRACTION_IMPROVER_AVAILABLE = True
except ImportError:
    EXTRACTION_IMPROVER_AVAILABLE = False
    logging.warning("⚠️ ExtractionImprover non disponible - fonctionnalités d'enrichissement désactivées")

logger = logging.getLogger(__name__)


class IntelligentPostProcessor:
    """
    Post-processeur intelligent utilisant ExtractionImprover
    
    Enrichit les données extraites avec une analyse contextuelle avancée
    et une validation améliorée.
    """
    
    def __init__(self, enable_improver: bool = True):
        """
        Initialise le post-processeur
        
        Args:
            enable_improver: Activer l'améliorateur (désactivable si non disponible)
        """
        self.enable_improver = enable_improver and EXTRACTION_IMPROVER_AVAILABLE
        
        if self.enable_improver:
            try:
                self.extraction_improver = extraction_improver
                logger.info("✅ IntelligentPostProcessor initialisé avec ExtractionImprover")
            except Exception as e:
                logger.warning(f"⚠️ Impossible d'initialiser ExtractionImprover: {e}")
                self.enable_improver = False
        else:
            self.extraction_improver = None
            logger.info("ℹ️ IntelligentPostProcessor initialisé sans ExtractionImprover")
    
    def enhance_extraction(self, raw_data: Dict[str, Any], text: str, 
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enrichit les données extraites avec une analyse intelligente
        
        Args:
            raw_data: Données extraites brutes
            text: Texte source complet
            context: Contexte supplémentaire (optionnel)
            
        Returns:
            Données enrichies
        """
        if not self.enable_improver or not self.extraction_improver:
            logger.debug("Post-processeur désactivé, retour des données brutes")
            return raw_data
        
        try:
            # Utiliser ExtractionImprover pour enrichir
            improved_data = self.extraction_improver.extract_improved_data(text)
            
            # Fusionner intelligemment avec les données brutes
            enhanced_data = self._merge_data(raw_data, improved_data)
            
            logger.debug(f"✅ Données enrichies: {len(enhanced_data)} champs")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement: {e}")
            # Retourner les données brutes en cas d'erreur
            return raw_data
    
    def _merge_data(self, raw_data: Dict[str, Any], 
                   improved_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fusionne intelligemment les données brutes et améliorées
        
        Priorité: données améliorées si disponibles et valides, sinon données brutes
        
        Args:
            raw_data: Données extraites brutes
            improved_data: Données améliorées par ExtractionImprover
            
        Returns:
            Données fusionnées
        """
        merged = raw_data.copy()
        
        # Parcourir les données améliorées
        for key, improved_value in improved_data.items():
            # Ignorer les valeurs None, vides
            if improved_value is None or improved_value == '':
                continue
            
            # Si la clé n'existe pas dans raw_data OU si raw_data est vide, utiliser improved_value
            if key not in merged or not merged.get(key):
                merged[key] = improved_value
                logger.debug(f"✓ Champ '{key}' enrichi depuis ExtractionImprover")
            # Si les deux existent, comparer pour voir lequel est meilleur
            elif self._is_better_value(improved_value, merged.get(key)):
                merged[key] = improved_value
                logger.debug(f"✓ Champ '{key}' remplacé par ExtractionImprover (valeur meilleure)")
        
        return merged
    
    def _is_better_value(self, improved_value: Any, raw_value: Any) -> bool:
        """
        Détermine si la valeur améliorée est meilleure que la valeur brute
        
        Args:
            improved_value: Valeur améliorée
            raw_value: Valeur brute
            
        Returns:
            True si la valeur améliorée est meilleure
        """
        # Si raw_value est vide ou None, improved_value est meilleur
        if not raw_value or raw_value == '':
            return True
        
        # Pour les chaînes, comparer la longueur (plus longue = souvent mieux)
        if isinstance(improved_value, str) and isinstance(raw_value, str):
            # Améliorée si plus longue (contient plus d'info)
            if len(improved_value) > len(raw_value) * 1.2:
                return True
            # Améliorée si raw_value contient des patterns invalides
            invalid_patterns = ['[...', '...', '[', ']', '(', ')']
            if any(pattern in raw_value for pattern in invalid_patterns):
                if not any(pattern in improved_value for pattern in invalid_patterns):
                    return True
        
        # Par défaut, garder la valeur brute
        return False
    
    def validate_enhanced_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide les données enrichies
        
        Args:
            data: Données à valider
            
        Returns:
            Données validées avec indicateurs de qualité
        """
        validation_result = {
            'data': data,
            'quality_score': 0.0,
            'completeness': 0.0,
            'issues': []
        }
        
        # Calculer le score de complétude
        total_fields = len(data)
        filled_fields = sum(1 for v in data.values() if v is not None and v != '')
        validation_result['completeness'] = (
            filled_fields / total_fields * 100 if total_fields > 0 else 0
        )
        
        # Calculer le score de qualité global
        validation_result['quality_score'] = validation_result['completeness']
        
        # Détecter les problèmes
        if validation_result['completeness'] < 50:
            validation_result['issues'].append("Complétude faible (< 50%)")
        
        # Vérifier les patterns invalides dans les chaînes
        for key, value in data.items():
            if isinstance(value, str):
                invalid_patterns = ['[...', '...]', '[', ']']
                if any(pattern in value for pattern in invalid_patterns):
                    validation_result['issues'].append(f"Patterns invalides dans '{key}'")
        
        return validation_result
    
    def is_available(self) -> bool:
        """
        Vérifie si le post-processeur est disponible
        
        Returns:
            True si disponible, False sinon
        """
        return self.enable_improver

