"""
🔍 Moteur de Validation - Validation Intelligente
================================================

Moteur de validation avancé pour les données extraites des appels d'offres.
Fournit une validation contextuelle, des scores de confiance et des suggestions.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Niveaux de validation"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"

@dataclass
class ValidationIssue:
    """Problème de validation"""
    field: str
    level: ValidationLevel
    message: str
    suggestion: Optional[str] = None
    confidence: float = 0.0

@dataclass
class ValidationResult:
    """Résultat de validation complet"""
    is_valid: bool
    confidence: float
    field_validations: Dict[str, Dict[str, Any]]
    issues: List[ValidationIssue]
    suggestions: List[str]
    warnings: List[str]
    errors: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le résultat en dictionnaire"""
        return {
            'is_valid': self.is_valid,
            'confidence': self.confidence,
            'field_validations': self.field_validations,
            'issues': [{'field': issue.field, 'level': issue.level.value, 'message': issue.message} for issue in self.issues],
            'suggestions': self.suggestions,
            'warnings': self.warnings,
            'errors': self.errors,
            'metadata': self.metadata
        }

class ValidationEngine:
    """Moteur de validation intelligent pour les données d'appels d'offres"""
    
    def __init__(self):
        """Initialise le moteur de validation"""
        self.validators = {
            'montant': self._validate_montant,
            'date': self._validate_date,
            'reference': self._validate_reference,
            'email': self._validate_email,
            'telephone': self._validate_telephone,
            'url': self._validate_url,
            'coherence': self._validate_coherence,
            'completeness': self._validate_completeness
        }
        
        self.field_weights = {
            'reference_procedure': 0.15,
            'intitule_procedure': 0.15,
            'montant_global_estime': 0.12,
            'date_limite': 0.10,
            'groupement': 0.08,
            'type_procedure': 0.08,
            'nbr_lots': 0.07,
            'intitule_lot': 0.06,
            'date_attribution': 0.05,
            'duree_marche': 0.05,
            'criteres_economique': 0.04,
            'criteres_techniques': 0.03,
            'autres_criteres': 0.02
        }
        
        self.performance_metrics = {
            'total_validations': 0,
            'successful_validations': 0,
            'validation_errors': 0,
            'average_validation_time': 0.0
        }
    
    def validate_extraction(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Valide une extraction complète
        
        Args:
            data: Données à valider
            
        Returns:
            Résultat de validation détaillé
        """
        start_time = datetime.now()
        
        try:
            self.performance_metrics['total_validations'] += 1
            
            # Initialiser le résultat
            result = ValidationResult(
                is_valid=True,
                confidence=0.0,
                field_validations={},
                issues=[],
                suggestions=[],
                warnings=[],
                errors=[],
                metadata={
                    'validation_timestamp': datetime.now().isoformat(),
                    'total_fields': len(data),
                    'filled_fields': sum(1 for v in data.values() if v and str(v).strip())
                }
            )
            
            # Validation des champs essentiels
            essential_score = self._validate_essential_fields(data, result)
            
            # Validation des champs par type
            type_scores = self._validate_by_type(data, result)
            
            # Validation de cohérence
            coherence_score = self._validate_coherence(data, result)
            
            # Calcul du score global pondéré
            total_weight = sum(self.field_weights.values())
            weighted_score = (
                essential_score * 0.4 +  # 40% pour les champs essentiels
                sum(type_scores.values()) / len(type_scores) * 0.4 +  # 40% pour la validation par type
                coherence_score * 0.2  # 20% pour la cohérence
            )
            
            result.confidence = min(weighted_score, 1.0)
            result.is_valid = result.confidence >= 0.6 and len(result.errors) == 0
            
            # Génération des suggestions
            result.suggestions = self._generate_suggestions(data, result)
            
            # Mise à jour des métriques
            if result.is_valid:
                self.performance_metrics['successful_validations'] += 1
            else:
                self.performance_metrics['validation_errors'] += 1
            
            # Calcul du temps de validation
            validation_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics['average_validation_time'] = (
                (self.performance_metrics['average_validation_time'] * 
                 (self.performance_metrics['total_validations'] - 1) + validation_time) /
                self.performance_metrics['total_validations']
            )
            
            result.metadata['validation_time'] = validation_time
            result.metadata['confidence_breakdown'] = {
                'essential_score': essential_score,
                'type_scores': type_scores,
                'coherence_score': coherence_score
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation: {e}")
            self.performance_metrics['validation_errors'] += 1
            
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                field_validations={},
                issues=[ValidationIssue(
                    field='system',
                    level=ValidationLevel.ERROR,
                    message=f"Erreur de validation: {str(e)}"
                )],
                suggestions=[],
                warnings=[],
                errors=[f"Erreur de validation: {str(e)}"],
                metadata={'error': str(e)}
            )
    
    def _validate_essential_fields(self, data: Dict[str, Any], result: ValidationResult) -> float:
        """Valide les champs essentiels"""
        essential_fields = ['reference_procedure', 'intitule_procedure']
        essential_score = 0
        
        for field in essential_fields:
            if field in data and data[field] and str(data[field]).strip():
                # Validation spécifique du champ
                field_score = self._validate_field(field, data[field], data)
                result.field_validations[field] = {
                    'valid': field_score > 0.5,
                    'confidence': field_score,
                    'message': 'Champ présent et valide' if field_score > 0.5 else 'Champ présent mais format douteux'
                }
                essential_score += field_score
                
                if field_score < 0.5:
                    result.issues.append(ValidationIssue(
                        field=field,
                        level=ValidationLevel.WARNING,
                        message=f"Format du champ '{field}' douteux",
                        suggestion=f"Vérifier le format du champ '{field}'"
                    ))
            else:
                result.field_validations[field] = {
                    'valid': False,
                    'confidence': 0.0,
                    'message': 'Champ manquant ou vide'
                }
                result.issues.append(ValidationIssue(
                    field=field,
                    level=ValidationLevel.ERROR,
                    message=f"Champ essentiel '{field}' manquant",
                    suggestion=f"Compléter le champ '{field}'"
                ))
                result.errors.append(f"Champ essentiel '{field}' manquant")
        
        return essential_score / len(essential_fields) if essential_fields else 0
    
    def _validate_by_type(self, data: Dict[str, Any], result: ValidationResult) -> Dict[str, float]:
        """Valide les champs par type"""
        type_scores = {}
        
        # Validation des montants
        montant_fields = ['montant_global_estime', 'montant_global_maxi']
        montant_score = 0
        for field in montant_fields:
            if field in data and data[field]:
                score = self._validate_montant(data[field], data)
                type_scores[field] = score
                montant_score += score
                
                if score < 0.5:
                    result.issues.append(ValidationIssue(
                        field=field,
                        level=ValidationLevel.WARNING,
                        message=f"Format de montant invalide pour '{field}'",
                        suggestion="Vérifier le format du montant (ex: 100000 ou 100 000€)"
                    ))
        type_scores['montants'] = montant_score / len(montant_fields) if montant_fields else 0
        
        # Validation des dates
        date_fields = ['date_limite', 'date_attribution']
        date_score = 0
        for field in date_fields:
            if field in data and data[field]:
                score = self._validate_date(data[field], data)
                type_scores[field] = score
                date_score += score
                
                if score < 0.5:
                    result.issues.append(ValidationIssue(
                        field=field,
                        level=ValidationLevel.WARNING,
                        message=f"Format de date invalide pour '{field}'",
                        suggestion="Vérifier le format de la date (ex: DD/MM/YYYY)"
                    ))
        type_scores['dates'] = date_score / len(date_fields) if date_fields else 0
        
        # Validation des références
        ref_fields = ['reference_procedure']
        ref_score = 0
        for field in ref_fields:
            if field in data and data[field]:
                score = self._validate_reference(data[field], data)
                type_scores[field] = score
                ref_score += score
        type_scores['references'] = ref_score / len(ref_fields) if ref_fields else 0
        
        return type_scores
    
    def _validate_field(self, field_name: str, value: Any, context: Dict[str, Any]) -> float:
        """Valide un champ spécifique"""
        if not value or not str(value).strip():
            return 0.0
        
        # Déterminer le type de validation
        if 'montant' in field_name.lower():
            return self._validate_montant(value, context)
        elif 'date' in field_name.lower():
            return self._validate_date(value, context)
        elif 'reference' in field_name.lower():
            return self._validate_reference(value, context)
        elif 'email' in field_name.lower():
            return self._validate_email(value, context)
        elif 'telephone' in field_name.lower():
            return self._validate_telephone(value, context)
        else:
            # Validation générique
            return 0.8 if len(str(value).strip()) > 3 else 0.3
    
    def _validate_montant(self, value: Any, context: Dict[str, Any] = None) -> float:
        """Valide un montant"""
        try:
            if isinstance(value, (int, float)):
                return 1.0 if value > 0 else 0.5
            
            value_str = str(value).strip()
            if not value_str:
                return 0.0
            
            # Nettoyer le montant
            cleaned = re.sub(r'[^\d,.\s€]', '', value_str)
            cleaned = cleaned.replace('€', '').replace('euros', '').replace('euro', '')
            cleaned = cleaned.replace(' ', '').replace(',', '.')
            
            if not cleaned:
                return 0.0
            
            montant = float(cleaned)
            
            # Validation de la plage
            if montant < 0:
                return 0.2
            elif montant > 1000000000:  # 1 milliard
                return 0.7
            elif montant > 1000000:  # 1 million
                return 0.9
            else:
                return 1.0
                
        except (ValueError, TypeError):
            return 0.0
    
    def _validate_date(self, value: Any, context: Dict[str, Any] = None) -> float:
        """Valide une date"""
        try:
            if not value or not str(value).strip():
                return 0.0
            
            value_str = str(value).strip()
            
            # Formats de date supportés
            date_formats = [
                '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d',
                '%d/%m/%y', '%d-%m-%y', '%y-%m-%d',
                '%d %m %Y', '%d %m %y'
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(value_str, fmt)
                    
                    # Validation de la plage de dates
                    current_year = datetime.now().year
                    if parsed_date.year < 2000 or parsed_date.year > current_year + 10:
                        return 0.5
                    
                    return 1.0
                except ValueError:
                    continue
            
            # Vérifier si c'est une date en toutes lettres (français)
            months_fr = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                        'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
            
            if any(month in value_str.lower() for month in months_fr):
                return 0.8
            
            # Vérifier si c'est une date numérique simple
            if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', value_str):
                return 0.6
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _validate_reference(self, value: Any, context: Dict[str, Any] = None) -> float:
        """Valide une référence"""
        try:
            if not value or not str(value).strip():
                return 0.0
            
            value_str = str(value).strip()
            
            # Patterns de référence connus
            ref_patterns = [
                r'\d{4}-[A-Z]\d{3}',  # 2024-R001
                r'\d{4}-[A-Z]\d{3}-\d{3}-\d{3}',  # 2024-R001-000-000
                r'[A-Z]{2,}\d{4,}',  # AO2024001
                r'[A-Z]{2,}-\d{4,}',  # AO-2024-001
                r'[A-Z]{2,}_\d{4,}',  # AO_2024_001
                r'[A-Z]{2,}\.\d{4,}',  # AO.2024.001
                r'[A-Z]{2,}\s\d{4,}'   # AO 2024 001
            ]
            
            for pattern in ref_patterns:
                if re.match(pattern, value_str):
                    return 1.0
            
            # Validation générique
            if len(value_str) >= 3 and re.match(r'[A-Z0-9\-_\.\s]+', value_str):
                return 0.7
            
            return 0.3
            
        except Exception:
            return 0.0
    
    def _validate_email(self, value: Any, context: Dict[str, Any] = None) -> float:
        """Valide un email"""
        try:
            if not value or not str(value).strip():
                return 0.0
            
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(email_pattern, str(value).strip()):
                return 1.0
            
            return 0.0
        except Exception:
            return 0.0
    
    def _validate_telephone(self, value: Any, context: Dict[str, Any] = None) -> float:
        """Valide un numéro de téléphone"""
        try:
            if not value or not str(value).strip():
                return 0.0
            
            value_str = str(value).strip()
            
            # Patterns de téléphone français
            phone_patterns = [
                r'\+33\s?\d{1,2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}',  # +33 1 23 45 67 89
                r'0\d{1,2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}',  # 01 23 45 67 89
                r'\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}'  # 01 23 45 67 89
            ]
            
            for pattern in phone_patterns:
                if re.match(pattern, value_str):
                    return 1.0
            
            return 0.0
        except Exception:
            return 0.0
    
    def _validate_url(self, value: Any, context: Dict[str, Any] = None) -> float:
        """Valide une URL"""
        try:
            if not value or not str(value).strip():
                return 0.0
            
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if re.match(url_pattern, str(value).strip()):
                return 1.0
            
            return 0.0
        except Exception:
            return 0.0
    
    def _validate_coherence(self, data: Dict[str, Any], result: ValidationResult) -> float:
        """Valide la cohérence des données"""
        coherence_score = 1.0
        
        try:
            # Vérifier la cohérence des montants
            if 'montant_global_estime' in data and 'montant_global_maxi' in data:
                estime = data['montant_global_estime']
                maxi = data['montant_global_maxi']
                
                if estime and maxi:
                    try:
                        estime_val = float(str(estime).replace(' ', '').replace(',', '.').replace('€', ''))
                        maxi_val = float(str(maxi).replace(' ', '').replace(',', '.').replace('€', ''))
                        
                        if maxi_val < estime_val:
                            result.issues.append(ValidationIssue(
                                field='montant_global_maxi',
                                level=ValidationLevel.ERROR,
                                message="Le montant maximum est inférieur au montant estimé",
                                suggestion="Vérifier la cohérence des montants"
                            ))
                            result.errors.append("Incohérence des montants")
                            coherence_score -= 0.3
                    except (ValueError, TypeError):
                        pass
            
            # Vérifier la cohérence des dates
            if 'date_limite' in data and 'date_attribution' in data:
                date_limite = data['date_limite']
                date_attribution = data['date_attribution']
                
                if date_limite and date_attribution:
                    try:
                        # Essayer de parser les dates
                        limite_parsed = self._parse_date(date_limite)
                        attribution_parsed = self._parse_date(date_attribution)
                        
                        if limite_parsed and attribution_parsed and attribution_parsed < limite_parsed:
                            result.issues.append(ValidationIssue(
                                field='date_attribution',
                                level=ValidationLevel.WARNING,
                                message="La date d'attribution est antérieure à la date limite",
                                suggestion="Vérifier les dates"
                            ))
                            result.warnings.append("Incohérence des dates")
                            coherence_score -= 0.2
                    except Exception:
                        pass
            
            # Vérifier la cohérence du nombre de lots
            if 'nbr_lots' in data and 'lot_numero' in data:
                nbr_lots = data['nbr_lots']
                lot_numero = data['lot_numero']
                
                if nbr_lots and lot_numero:
                    try:
                        nbr_lots_val = int(str(nbr_lots))
                        lot_numero_val = int(str(lot_numero))
                        
                        if lot_numero_val > nbr_lots_val:
                            result.issues.append(ValidationIssue(
                                field='lot_numero',
                                level=ValidationLevel.WARNING,
                                message="Le numéro de lot dépasse le nombre de lots",
                                suggestion="Vérifier la cohérence des lots"
                            ))
                            result.warnings.append("Incohérence du nombre de lots")
                            coherence_score -= 0.1
                    except (ValueError, TypeError):
                        pass
            
            return max(coherence_score, 0.0)
            
        except Exception as e:
            logger.error(f"Erreur validation cohérence: {e}")
            return 0.5
    
    def _validate_completeness(self, data: Dict[str, Any], result: ValidationResult) -> float:
        """Valide la complétude des données"""
        try:
            total_fields = len(data)
            filled_fields = sum(1 for v in data.values() if v and str(v).strip())
            
            completeness_rate = filled_fields / total_fields if total_fields > 0 else 0
            
            if completeness_rate < 0.3:
                result.issues.append(ValidationIssue(
                    field='global',
                    level=ValidationLevel.WARNING,
                    message=f"Données incomplètes ({completeness_rate:.1%})",
                    suggestion="Compléter davantage d'informations"
                ))
                result.warnings.append(f"Données incomplètes ({completeness_rate:.1%})")
            
            return completeness_rate
            
        except Exception:
            return 0.0
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse une date depuis une chaîne"""
        try:
            date_formats = [
                '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d',
                '%d/%m/%y', '%d-%m-%y', '%y-%m-%d',
                '%d %m %Y', '%d %m %y'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(str(date_str).strip(), fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def _generate_suggestions(self, data: Dict[str, Any], result: ValidationResult) -> List[str]:
        """Génère des suggestions d'amélioration"""
        suggestions = []
        
        # Suggestions basées sur les champs manquants
        essential_fields = ['reference_procedure', 'intitule_procedure', 'montant_global_estime', 'date_limite']
        missing_essential = [field for field in essential_fields if not data.get(field)]
        
        if missing_essential:
            suggestions.append(f"Compléter les champs essentiels manquants: {', '.join(missing_essential)}")
        
        # Suggestions basées sur la confiance des champs
        low_confidence_fields = [
            field for field, validation in result.field_validations.items()
            if validation.get('confidence', 1.0) < 0.5
        ]
        
        if low_confidence_fields:
            suggestions.append(f"Vérifier le format des champs: {', '.join(low_confidence_fields)}")
        
        # Suggestions basées sur la cohérence
        if result.issues:
            coherence_issues = [issue for issue in result.issues if 'cohérence' in issue.message.lower()]
            if coherence_issues:
                suggestions.append("Vérifier la cohérence des données (montants, dates, lots)")
        
        # Suggestions générales
        if result.confidence < 0.7:
            suggestions.append("Améliorer la qualité générale des données extraites")
        
        if not suggestions:
            suggestions.append("Données de bonne qualité")
        
        return suggestions
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de performance"""
        return self.performance_metrics.copy()
    
    def reset_metrics(self):
        """Remet à zéro les métriques"""
        self.performance_metrics = {
            'total_validations': 0,
            'successful_validations': 0,
            'validation_errors': 0,
            'average_validation_time': 0.0
        }
