"""
🧠 Apprenant Contextuel depuis la Base de Données
================================================

Module permettant à l'extracteur d'apprendre depuis les données existantes
de la base de données pour améliorer l'extraction future.

Utilise les patterns, formats et structures des données historiques
pour améliorer la précision de l'extraction.
"""

import pandas as pd
import re
import logging
from typing import Dict, Any, List, Optional, Set
from collections import Counter
from datetime import datetime
import unicodedata

logger = logging.getLogger(__name__)


class DatabaseContextLearner:
    """Apprend des patterns depuis la base de données pour améliorer l'extraction"""
    
    def __init__(self, database_manager=None):
        """
        Initialise l'apprenant contextuel
        
        Args:
            database_manager: Instance de DatabaseManager pour accéder à la BDD
        """
        self.db_manager = database_manager
        self.learned_patterns = {}
        self.learned_values = {}
        self.field_statistics = {}
        self.correlation_rules = {}
        self.is_trained = False
        
    def learn_from_database(self, limit: int = 1000) -> bool:
        """
        Apprend depuis les données de la base de données
        
        Args:
            limit: Nombre maximum d'enregistrements à analyser
            
        Returns:
            True si l'apprentissage a réussi
        """
        try:
            if not self.db_manager:
                logger.warning("⚠️ Pas de DatabaseManager fourni, apprentissage impossible")
                return False
            
            logger.info(f"🧠 Apprentissage depuis la base de données (limite: {limit})...")
            
            # Récupérer les données de la BDD
            df = self.db_manager.get_all_data()
            
            if df.empty:
                logger.warning("⚠️ Aucune donnée dans la base de données pour l'apprentissage")
                return False
            
            # Limiter le nombre d'enregistrements pour les performances
            if len(df) > limit:
                df = df.head(limit)
                logger.info(f"📊 Analyse de {limit} enregistrements (sur {len(self.db_manager.get_all_data())} total)")
            
            # Analyser chaque champ
            self._analyze_field_patterns(df)
            self._analyze_value_distributions(df)
            self._analyze_correlations(df)
            self._extract_format_patterns(df)
            self._learn_contextual_rules(df)
            
            self.is_trained = True
            logger.info(f"✅ Apprentissage terminé: {len(self.learned_patterns)} patterns appris")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'apprentissage depuis la BDD: {e}")
            return False
    
    def _analyze_field_patterns(self, df: pd.DataFrame):
        """Analyse les patterns des champs textuels"""
        text_fields = [
            'reference_procedure', 'intitule_procedure', 'intitule_lot',
            'type_procedure', 'mono_multi', 'groupement', 'univers',
            'execution_marche', 'criteres_economique', 'criteres_techniques',
            'segment', 'famille'  # Ajouter segment et famille pour apprendre les valeurs fréquentes
        ]
        
        for field in text_fields:
            if field not in df.columns:
                continue
            
            # Prendre les valeurs non nulles
            values = df[field].dropna().astype(str)
            
            if values.empty:
                continue
            
            # Analyser les patterns de format
            patterns = self._extract_format_patterns_for_field(values, field)
            if patterns:
                self.learned_patterns[field] = patterns
                
            # Extraire les valeurs fréquentes
            value_counts = values.value_counts()
            if not value_counts.empty:
                frequent_values = value_counts.head(10).to_dict()
                self.learned_values[field] = frequent_values
                
                logger.debug(f"📊 {field}: {len(frequent_values)} valeurs fréquentes détectées")
    
    def _analyze_value_distributions(self, df: pd.DataFrame):
        """Analyse les distributions de valeurs pour les statistiques"""
        numeric_fields = ['montant_global_estime', 'montant_global_maxi', 'duree_marche', 'nbr_lots']
        
        for field in numeric_fields:
            if field not in df.columns:
                continue
            
            values = pd.to_numeric(df[field], errors='coerce').dropna()
            
            if values.empty:
                continue
            
            self.field_statistics[field] = {
                'min': float(values.min()),
                'max': float(values.max()),
                'mean': float(values.mean()),
                'median': float(values.median()),
                'std': float(values.std()) if len(values) > 1 else 0,
                'percentiles': {
                    25: float(values.quantile(0.25)),
                    75: float(values.quantile(0.75))
                }
            }
            
            logger.debug(f"📊 Statistiques {field}: min={self.field_statistics[field]['min']:.2f}, max={self.field_statistics[field]['max']:.2f}")
    
    def _analyze_correlations(self, df: pd.DataFrame):
        """Analyse les corrélations entre champs pour améliorer l'extraction"""
        try:
            # Corrélations entre groupement et autres champs
            if 'groupement' in df.columns:
                groupement_values = df['groupement'].dropna().unique()
                
                for groupement in groupement_values:
                    group_data = df[df['groupement'] == groupement]
                    
                    correlations = {}
                    
                    # Types de procédures courants pour ce groupement
                    if 'type_procedure' in group_data.columns:
                        type_counts = group_data['type_procedure'].dropna().value_counts()
                        if not type_counts.empty:
                            correlations['type_procedure'] = type_counts.head(3).to_dict()
                    
                    # Univers courants pour ce groupement
                    if 'univers' in group_data.columns:
                        univers_counts = group_data['univers'].dropna().value_counts()
                        if not univers_counts.empty:
                            correlations['univers'] = univers_counts.head(3).to_dict()
                    
                    if correlations:
                        self.correlation_rules[groupement] = correlations
                        logger.debug(f"📊 Corrélations pour {groupement}: {list(correlations.keys())}")
            
            # Corrélations entre nombre de lots et mono_multi
            if 'nbr_lots' in df.columns and 'mono_multi' in df.columns:
                lots_data = df[['nbr_lots', 'mono_multi']].dropna()
                if not lots_data.empty:
                    mono_multi_by_lots = {}
                    for nbr_lots in lots_data['nbr_lots'].unique():
                        subset = lots_data[lots_data['nbr_lots'] == nbr_lots]
                        mono_multi_counts = subset['mono_multi'].value_counts()
                        if not mono_multi_counts.empty:
                            mono_multi_by_lots[int(nbr_lots)] = mono_multi_counts.index[0]
                    
                    if mono_multi_by_lots:
                        self.correlation_rules['nbr_lots_to_mono_multi'] = mono_multi_by_lots
                        logger.debug(f"📊 Corrélation nbr_lots->mono_multi: {len(mono_multi_by_lots)} règles")
            
            # Corrélations univers -> segment
            if 'univers' in df.columns and 'segment' in df.columns:
                univers_segment_data = df[['univers', 'segment']].dropna()
                if not univers_segment_data.empty:
                    for univers in univers_segment_data['univers'].dropna().unique():
                        subset = univers_segment_data[univers_segment_data['univers'] == univers]
                        segment_counts = subset['segment'].value_counts()
                        if not segment_counts.empty:
                            rule_key = f"{univers}_suggests_segment"
                            self.correlation_rules[rule_key] = segment_counts.index[0]  # Segment le plus fréquent
                            logger.debug(f"📊 Corrélation {univers} → segment = {segment_counts.index[0]}")
            
            # Corrélations univers + segment -> famille
            if 'univers' in df.columns and 'segment' in df.columns and 'famille' in df.columns:
                family_data = df[['univers', 'segment', 'famille']].dropna()
                if not family_data.empty:
                    # Corrélation univers -> famille
                    for univers in family_data['univers'].dropna().unique():
                        subset = family_data[family_data['univers'] == univers]
                        famille_counts = subset['famille'].value_counts()
                        if not famille_counts.empty:
                            rule_key = f"{univers}_suggests_famille"
                            self.correlation_rules[rule_key] = famille_counts.index[0]
                            logger.debug(f"📊 Corrélation {univers} → famille = {famille_counts.index[0]}")
                    
                    # Corrélation univers+segment -> famille (plus précis)
                    for univers in family_data['univers'].dropna().unique():
                        for segment in family_data[family_data['univers'] == univers]['segment'].dropna().unique():
                            subset = family_data[(family_data['univers'] == univers) & 
                                                 (family_data['segment'] == segment)]
                            famille_counts = subset['famille'].value_counts()
                            if not famille_counts.empty and len(subset) >= 3:  # Au moins 3 occurrences
                                rule_key = f"{univers}_{segment}_suggests_famille"
                                self.correlation_rules[rule_key] = famille_counts.index[0]
                                logger.debug(f"📊 Corrélation {univers}+{segment} → famille = {famille_counts.index[0]}")
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur analyse corrélations: {e}")
    
    def _extract_format_patterns(self, df: pd.DataFrame):
        """Extrait les patterns de format pour les références, montants, etc."""
        try:
            # Patterns pour les références de procédure
            if 'reference_procedure' in df.columns:
                refs = df['reference_procedure'].dropna().astype(str)
                
                # Analyser les formats communs
                format_patterns = []
                for ref in refs.head(100):  # Analyser les 100 premières
                    # Extraire les patterns structurels
                    pattern = self._normalize_to_pattern(ref)
                    if pattern and pattern not in format_patterns:
                        format_patterns.append(pattern)
                
                if format_patterns:
                    self.learned_patterns['reference_format'] = format_patterns
                    logger.debug(f"📊 Patterns référence détectés: {len(format_patterns)} formats")
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur extraction patterns format: {e}")
    
    def _learn_contextual_rules(self, df: pd.DataFrame):
        """Apprend des règles contextuelles depuis les données"""
        try:
            # Règle: Si groupement = RESAH, alors souvent type_procedure = Consultation
            if 'groupement' in df.columns and 'type_procedure' in df.columns:
                for groupement in df['groupement'].dropna().unique():
                    group_data = df[df['groupement'] == groupement]
                    
                    if 'type_procedure' in group_data.columns:
                        most_common_type = group_data['type_procedure'].dropna().mode()
                        if not most_common_type.empty:
                            rule_key = f"{groupement}_suggests_type_procedure"
                            self.correlation_rules[rule_key] = most_common_type.iloc[0]
                            logger.debug(f"📊 Règle: {groupement} → type_procedure = {most_common_type.iloc[0]}")
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur apprentissage règles contextuelles: {e}")
    
    def suggest_value(self, field: str, context: Dict[str, Any] = None) -> Optional[Any]:
        """
        Suggère une valeur pour un champ basé sur les données apprises
        
        Args:
            field: Nom du champ
            context: Contexte (autres champs déjà extraits)
            
        Returns:
            Valeur suggérée ou None
        """
        if not self.is_trained:
            return None
        
        suggestions = []
        
        # 1. Suggestion basée sur les corrélations
        if context:
            suggestion = self._suggest_from_correlations(field, context)
            if suggestion:
                suggestions.append(('correlation', suggestion))
        
        # 2. Suggestion basée sur les valeurs fréquentes
        if field in self.learned_values:
            most_frequent = list(self.learned_values[field].keys())[0]
            suggestions.append(('frequency', most_frequent))
        
        # 3. Retourner la meilleure suggestion
        if suggestions:
            # Préférer les corrélations aux fréquences
            for source, value in suggestions:
                if source == 'correlation':
                    return value
            return suggestions[0][1]
        
        return None
    
    def _suggest_from_correlations(self, field: str, context: Dict[str, Any]) -> Optional[Any]:
        """Suggère une valeur basée sur les corrélations apprises"""
        try:
            # Si on a un groupement, suggérer type_procedure
            if field == 'type_procedure' and 'groupement' in context:
                groupement = context.get('groupement')
                rule_key = f"{groupement}_suggests_type_procedure"
                if rule_key in self.correlation_rules:
                    return self.correlation_rules[rule_key]
            
            # Si on a un univers, suggérer segment
            if field == 'segment' and 'univers' in context:
                univers = context.get('univers')
                rule_key = f"{univers}_suggests_segment"
                if rule_key in self.correlation_rules:
                    return self.correlation_rules[rule_key]
            
            # Si on a un univers et un segment, suggérer famille (plus précis)
            if field == 'famille':
                univers = context.get('univers')
                segment = context.get('segment')
                if univers and segment:
                    rule_key = f"{univers}_{segment}_suggests_famille"
                    if rule_key in self.correlation_rules:
                        return self.correlation_rules[rule_key]
                # Sinon, juste avec l'univers
                if univers:
                    rule_key = f"{univers}_suggests_famille"
                    if rule_key in self.correlation_rules:
                        return self.correlation_rules[rule_key]
            
            # Si on a nbr_lots, suggérer mono_multi
            if field == 'mono_multi' and 'nbr_lots' in context:
                nbr_lots = context.get('nbr_lots')
                if 'nbr_lots_to_mono_multi' in self.correlation_rules:
                    mapping = self.correlation_rules['nbr_lots_to_mono_multi']
                    if nbr_lots in mapping:
                        return mapping[nbr_lots]
            
            # Suggestion depuis les corrélations de groupement
            if 'groupement' in context:
                groupement = context.get('groupement')
                if groupement in self.correlation_rules:
                    correlations = self.correlation_rules[groupement]
                    if field in correlations:
                        # Retourner la valeur la plus fréquente
                        field_values = correlations[field]
                        if field_values:
                            return list(field_values.keys())[0]
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur suggestion depuis corrélations: {e}")
        
        return None
    
    def validate_extracted_value(self, field: str, value: Any) -> Dict[str, Any]:
        """
        Valide une valeur extraite en la comparant aux patterns appris
        
        Args:
            field: Nom du champ
            value: Valeur extraite
            
        Returns:
            Dictionnaire avec validation et suggestions
        """
        validation = {
            'is_valid': True,
            'confidence': 1.0,
            'suggestions': [],
            'warnings': []
        }
        
        if not self.is_trained:
            return validation
        
        try:
            # Validation des valeurs textuelles
            if isinstance(value, str) and field in self.learned_values:
                # Vérifier si la valeur est dans les valeurs fréquentes
                if value in self.learned_values[field]:
                    validation['confidence'] = 0.9
                else:
                    # Proposer des valeurs similaires
                    similar_values = self._find_similar_values(field, value)
                    if similar_values:
                        validation['suggestions'] = similar_values
                        validation['confidence'] = 0.6
                        validation['warnings'].append(f"Valeur '{value}' non trouvée dans les données historiques")
            
            # Validation des valeurs numériques
            if isinstance(value, (int, float)) and field in self.field_statistics:
                stats = self.field_statistics[field]
                
                # Vérifier si la valeur est dans une plage raisonnable
                if value < stats['min'] * 0.5 or value > stats['max'] * 1.5:
                    validation['warnings'].append(
                        f"Valeur {value} en dehors de la plage observée "
                        f"({stats['min']:.2f} - {stats['max']:.2f})"
                    )
                    validation['confidence'] = 0.7
                elif stats['min'] <= value <= stats['max']:
                    validation['confidence'] = 0.95
            
            # Validation des formats
            if field == 'reference_procedure' and 'reference_format' in self.learned_patterns:
                if not any(self._matches_pattern(value, pattern) for pattern in self.learned_patterns['reference_format']):
                    validation['warnings'].append("Format de référence non standard")
                    validation['confidence'] = 0.8
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur validation valeur: {e}")
        
        return validation
    
    def _extract_format_patterns_for_field(self, values: pd.Series, field: str) -> List[str]:
        """Extrait les patterns de format pour un champ"""
        patterns = []
        
        try:
            # Pour les références, analyser le format
            if field == 'reference_procedure':
                for value in values.head(50):
                    pattern = self._normalize_to_pattern(str(value))
                    if pattern and pattern not in patterns:
                        patterns.append(pattern)
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur extraction patterns pour {field}: {e}")
        
        return patterns
    
    def _normalize_to_pattern(self, value: str) -> str:
        """Convertit une valeur en pattern (remplace chiffres par #, lettres par X)"""
        pattern = value
        
        # Remplacer les chiffres par #
        pattern = re.sub(r'\d', '#', pattern)
        
        # Remplacer les lettres par X
        pattern = re.sub(r'[A-Za-z]', 'X', pattern)
        
        return pattern
    
    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """Vérifie si une valeur correspond à un pattern"""
        normalized = self._normalize_to_pattern(value)
        return normalized == pattern
    
    def _find_similar_values(self, field: str, value: str, threshold: float = 0.8) -> List[str]:
        """Trouve des valeurs similaires dans les données apprises"""
        if field not in self.learned_values:
            return []
        
        value_lower = value.lower()
        similar = []
        
        for learned_value in self.learned_values[field].keys():
            learned_lower = str(learned_value).lower()
            
            # Calcul de similarité simple (Levenshtein simplifié)
            similarity = self._calculate_similarity(value_lower, learned_lower)
            
            if similarity >= threshold:
                similar.append(learned_value)
        
        return similar[:5]  # Retourner les 5 plus similaires
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calcule la similarité entre deux chaînes (0.0 à 1.0)"""
        if s1 == s2:
            return 1.0
        
        if not s1 or not s2:
            return 0.0
        
        # Similarité basée sur les sous-chaînes communes
        longer = s1 if len(s1) > len(s2) else s2
        shorter = s2 if len(s1) > len(s2) else s1
        
        if longer.startswith(shorter) or shorter in longer:
            return len(shorter) / len(longer)
        
        # Compter les caractères communs
        common = sum(1 for c in shorter if c in longer)
        return common / len(longer) if longer else 0.0
    
    def get_learned_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'apprentissage"""
        return {
            'is_trained': self.is_trained,
            'patterns_learned': len(self.learned_patterns),
            'value_distributions': len(self.learned_values),
            'correlation_rules': len(self.correlation_rules),
            'field_statistics': len(self.field_statistics)
        }
    
    def reset(self):
        """Remet à zéro l'apprentissage"""
        self.learned_patterns = {}
        self.learned_values = {}
        self.field_statistics = {}
        self.correlation_rules = {}
        self.is_trained = False
        logger.info("🔄 Apprentissage réinitialisé")


