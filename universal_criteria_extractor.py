#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extracteur de critères universel pour tous les types de documents
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from criteria_extractor import CriteriaExtractor, TableauCriteres, CritereAttribution

logger = logging.getLogger(__name__)

@dataclass
class UniversalCriteriaResult:
    """Résultat de l'extraction universelle des critères"""
    has_criteria: bool
    criteria_type: str  # 'structured_table', 'text_patterns', 'none'
    global_criteria: List[CritereAttribution]
    lot_specific_criteria: Dict[int, List[CritereAttribution]]
    confidence_score: float  # 0.0 à 1.0
    extraction_method: str

class UniversalCriteriaExtractor:
    """Extracteur de critères universel pour tous les types de documents"""
    
    def __init__(self):
        self.criteria_extractor = CriteriaExtractor()
        self.extraction_methods = [
            self._extract_structured_table,
            self._extract_text_patterns,
            self._extract_percentage_patterns,
            self._extract_keyword_patterns
        ]
    
    def extract_criteria(self, text: str, document_type: str = "unknown") -> UniversalCriteriaResult:
        """
        Extrait les critères d'un texte avec toutes les méthodes disponibles
        
        Args:
            text: Texte à analyser
            document_type: Type de document (pdf, excel, word, txt)
        
        Returns:
            UniversalCriteriaResult: Résultat de l'extraction
        """
        try:
            logger.info(f"🔍 Extraction universelle des critères pour {document_type}")
            
            # Essayer d'abord sur le texte original (pour les tableaux structurés)
            best_result = None
            best_confidence = 0.0
            
            # Tester d'abord la méthode des tableaux structurés sur le texte original
            try:
                result = self._extract_structured_table(text, document_type)
                if result and result.confidence_score > best_confidence:
                    best_result = result
                    best_confidence = result.confidence_score
            except Exception as e:
                logger.warning(f"Erreur méthode _extract_structured_table: {e}")
            
            # Si pas de résultat, nettoyer le texte et essayer les autres méthodes
            if not best_result:
                cleaned_text = self._clean_text(text)
                
                for method in self.extraction_methods[1:]:  # Skip _extract_structured_table
                    try:
                        result = method(cleaned_text, document_type)
                        if result and result.confidence_score > best_confidence:
                            best_result = result
                            best_confidence = result.confidence_score
                    except Exception as e:
                        logger.warning(f"Erreur méthode {method.__name__}: {e}")
                        continue
            
            # Si aucune méthode n'a trouvé de critères, retourner un résultat vide
            if not best_result:
                return UniversalCriteriaResult(
                    has_criteria=False,
                    criteria_type='none',
                    global_criteria=[],
                    lot_specific_criteria={},
                    confidence_score=0.0,
                    extraction_method='none'
                )
            
            logger.info(f"✅ Critères extraits avec {best_result.extraction_method} (confiance: {best_result.confidence_score:.2f})")
            return best_result
            
        except Exception as e:
            logger.error(f"Erreur extraction universelle: {e}")
            return UniversalCriteriaResult(
                has_criteria=False,
                criteria_type='none',
                global_criteria=[],
                lot_specific_criteria={},
                confidence_score=0.0,
                extraction_method='error'
            )
    
    def _extract_structured_table(self, text: str, document_type: str) -> Optional[UniversalCriteriaResult]:
        """Extraction des critères depuis des tableaux structurés"""
        try:
            # Utiliser l'extracteur spécialisé
            tableau = self.criteria_extractor.extract_from_text(text)
            
            if tableau.criteres_globaux or tableau.criteres_par_lot:
                # Calculer le score de confiance
                confidence = self._calculate_confidence(tableau.criteres_globaux, tableau.criteres_par_lot)
                
                return UniversalCriteriaResult(
                    has_criteria=True,
                    criteria_type='structured_table',
                    global_criteria=tableau.criteres_globaux,
                    lot_specific_criteria=tableau.criteres_par_lot,
                    confidence_score=confidence,
                    extraction_method='structured_table'
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur extraction tableaux structurés: {e}")
            return None
    
    def _extract_text_patterns(self, text: str, document_type: str) -> Optional[UniversalCriteriaResult]:
        """Extraction des critères depuis des patterns de texte"""
        try:
            criteres = []
            
            # Patterns pour différents types de critères
            patterns = {
                'economique': [
                    r'critère\s+(?:économique|prix|coût|cout|financier)[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*%',
                    r'prix[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*%',
                    r'coût[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*%'
                ],
                'technique': [
                    r'critère\s+(?:technique|qualité|qualite|performance)[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*%',
                    r'valeur\s+technique[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*%',
                    r'qualité[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*%'
                ],
                'autre': [
                    r'critère\s+(?:autre|autres|général|general)[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*%',
                    r'qualité\s+des\s+services[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*%'
                ],
                'rse': [
                    r'critère\s+(?:rse|développement\s+durable|durable|environnemental)[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*%',
                    r'développement\s+durable[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*%'
                ]
            }
            
            for type_critere, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        try:
                            pourcentage = float(match.group(1).replace(',', '.'))
                            if 0 <= pourcentage <= 100:
                                critere = CritereAttribution(
                                    nom=f"Critère {type_critere}",
                                    pourcentage=pourcentage,
                                    description=f"Critère {type_critere} détecté",
                                    type_critere=f"critère {type_critere}"
                                )
                                criteres.append(critere)
                        except ValueError:
                            continue
            
            if criteres:
                confidence = min(0.7, len(criteres) * 0.2)  # Confiance basée sur le nombre de critères
                return UniversalCriteriaResult(
                    has_criteria=True,
                    criteria_type='text_patterns',
                    global_criteria=criteres,
                    lot_specific_criteria={},
                    confidence_score=confidence,
                    extraction_method='text_patterns'
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur extraction patterns texte: {e}")
            return None
    
    def _extract_percentage_patterns(self, text: str, document_type: str) -> Optional[UniversalCriteriaResult]:
        """Extraction des critères depuis des patterns de pourcentages"""
        try:
            criteres = []
            
            # Chercher tous les pourcentages dans le texte
            percentage_pattern = r'(\d+(?:[.,]\d+)?)\s*%'
            matches = re.finditer(percentage_pattern, text, re.IGNORECASE)
            
            for i, match in enumerate(matches):
                try:
                    pourcentage = float(match.group(1).replace(',', '.'))
                    if 5 <= pourcentage <= 100:  # Pourcentages raisonnables pour des critères
                        # Chercher le contexte autour du pourcentage
                        start = max(0, match.start() - 100)
                        end = min(len(text), match.end() + 100)
                        context = text[start:end]
                        
                        # Déterminer le type de critère basé sur le contexte
                        type_critere = self._classify_criteria_from_context(context)
                        
                        critere = CritereAttribution(
                            nom=f"Critère {i+1}",
                            pourcentage=pourcentage,
                            description=f"Critère détecté: {type_critere}",
                            type_critere=type_critere
                        )
                        criteres.append(critere)
                        
                        if len(criteres) >= 5:  # Limiter à 5 critères
                            break
                            
                except ValueError:
                    continue
            
            if criteres:
                confidence = min(0.5, len(criteres) * 0.1)  # Confiance plus faible
                return UniversalCriteriaResult(
                    has_criteria=True,
                    criteria_type='percentage_patterns',
                    global_criteria=criteres,
                    lot_specific_criteria={},
                    confidence_score=confidence,
                    extraction_method='percentage_patterns'
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur extraction patterns pourcentages: {e}")
            return None
    
    def _extract_keyword_patterns(self, text: str, document_type: str) -> Optional[UniversalCriteriaResult]:
        """Extraction des critères depuis des mots-clés"""
        try:
            criteres = []
            
            # Mots-clés pour différents types de critères
            keywords = {
                'economique': ['prix', 'coût', 'cout', 'financier', 'économique', 'budget'],
                'technique': ['technique', 'qualité', 'qualite', 'performance', 'valeur technique'],
                'autre': ['autre', 'général', 'general', 'services', 'qualité des services'],
                'rse': ['rse', 'développement durable', 'durable', 'environnemental', 'social']
            }
            
            # Chercher les mots-clés dans le texte
            for type_critere, kw_list in keywords.items():
                for keyword in kw_list:
                    if keyword.lower() in text.lower():
                        # Chercher un pourcentage près du mot-clé
                        pattern = rf'{re.escape(keyword)}[^%]*?(\d+(?:[.,]\d+)?)\s*%'
                        match = re.search(pattern, text, re.IGNORECASE)
                        
                        if match:
                            try:
                                pourcentage = float(match.group(1).replace(',', '.'))
                                if 0 <= pourcentage <= 100:
                                    critere = CritereAttribution(
                                        nom=f"Critère {type_critere}",
                                        pourcentage=pourcentage,
                                        description=f"Critère {type_critere} basé sur '{keyword}'",
                                        type_critere=f"critère {type_critere}"
                                    )
                                    criteres.append(critere)
                            except ValueError:
                                continue
            
            if criteres:
                confidence = min(0.4, len(criteres) * 0.15)  # Confiance faible
                return UniversalCriteriaResult(
                    has_criteria=True,
                    criteria_type='keyword_patterns',
                    global_criteria=criteres,
                    lot_specific_criteria={},
                    confidence_score=confidence,
                    extraction_method='keyword_patterns'
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur extraction patterns mots-clés: {e}")
            return None
    
    def _classify_criteria_from_context(self, context: str) -> str:
        """Classifie un critère basé sur son contexte"""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['prix', 'coût', 'cout', 'financier', 'économique']):
            return "critère économique"
        elif any(word in context_lower for word in ['technique', 'qualité', 'qualite', 'performance']):
            return "critère technique"
        elif any(word in context_lower for word in ['rse', 'développement durable', 'durable', 'environnemental']):
            return "critère RSE"
        else:
            return "autre critère"
    
    def _calculate_confidence(self, global_criteria: List[CritereAttribution], 
                            lot_criteria: Dict[int, List[CritereAttribution]]) -> float:
        """Calcule le score de confiance basé sur les critères trouvés"""
        total_criteria = len(global_criteria) + sum(len(crits) for crits in lot_criteria.values())
        
        if total_criteria == 0:
            return 0.0
        elif total_criteria >= 4:
            return 1.0
        elif total_criteria >= 2:
            return 0.8
        else:
            return 0.6
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte pour améliorer l'extraction"""
        # Remplacer les caractères problématiques
        text = text.replace('\x00', ' ')
        # Normaliser les espaces multiples mais préserver les sauts de ligne
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # Garder les caractères utiles incluant les accents et symboles spéciaux
        text = re.sub(r'[^\w\s%.,()°éèêëàâäôöùûüçÉÈÊËÀÂÄÔÖÙÛÜÇ\n-]', ' ', text)
        return text
    
    def format_criteria_summary(self, result: UniversalCriteriaResult) -> str:
        """Formate un résumé des critères extraits"""
        if not result.has_criteria:
            return "Aucun critère d'attribution détecté."
        
        summary = f"## Critères d'attribution détectés ({result.extraction_method})\n"
        summary += f"**Confiance**: {result.confidence_score:.1%}\n\n"
        
        if result.global_criteria:
            summary += "### Critères globaux\n"
            for critere in result.global_criteria:
                summary += f"- **{critere.nom}**: {critere.pourcentage}% ({critere.type_critere})\n"
            summary += "\n"
        
        if result.lot_specific_criteria:
            summary += "### Critères par lot\n"
            for lot_num, criteres in result.lot_specific_criteria.items():
                summary += f"**Lot {lot_num}**:\n"
                for critere in criteres:
                    summary += f"- **{critere.nom}**: {critere.pourcentage}% ({critere.type_critere})\n"
                summary += "\n"
        
        return summary
