"""
🚀 AOExtractor V2 - Architecture Modulaire
==========================================

Version refactorisée du AOExtractor utilisant l'architecture modulaire.
Remplace l'ancien ao_extractor.py avec une approche plus maintenable.
"""

import pandas as pd
import logging
import time
import traceback
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import os

# Import des modules modulaires
from extractors import (
    PatternManager, ValidationEngine, PDFExtractor, 
    ExcelExtractor, TextExtractor, LotDetector
)
from extractors.file_type_detector import FileTypeDetector
from extractors.intelligent_post_processor import IntelligentPostProcessor
from extractors.database_context_learner import DatabaseContextLearner

logger = logging.getLogger(__name__)

class AOExtractorV2:
    """
    Extracteur d'Appels d'Offres V2 - Architecture Modulaire
    
    Version refactorisée utilisant une architecture modulaire pour une meilleure
    maintenabilité, performance et extensibilité.
    """
    
    def __init__(self, reference_data: pd.DataFrame = None, database_manager=None):
        """
        Initialise l'extracteur V2
        
        Args:
            reference_data: DataFrame de référence pour l'apprentissage (optionnel)
            database_manager: Instance de DatabaseManager pour apprendre depuis la BDD (optionnel)
        """
        self.reference_data = reference_data
        self.database_manager = database_manager
        
        # Initialiser les composants modulaires
        self.pattern_manager = PatternManager()
        self.validation_engine = ValidationEngine()
        self.lot_detector = LotDetector()
        
        # Initialiser l'apprenant contextuel depuis la BDD
        self.database_learner = DatabaseContextLearner(database_manager)
        if database_manager:
            # Apprendre depuis la BDD de manière asynchrone pour ne pas bloquer
            try:
                self.database_learner.learn_from_database(limit=500)
                logger.info("✅ Apprentissage depuis la base de données terminé")
            except Exception as e:
                logger.warning(f"⚠️ Erreur apprentissage BDD: {e}")
        
        # Initialiser les extracteurs spécialisés
        self.pdf_extractor = PDFExtractor(self.pattern_manager, self.validation_engine)
        self.excel_extractor = ExcelExtractor(self.pattern_manager, self.validation_engine)
        self.text_extractor = TextExtractor(self.pattern_manager, self.validation_engine)
        
        # Passer le database_learner aux extracteurs pour la génération intelligente
        if self.database_learner:
            self.pdf_extractor.database_learner = self.database_learner
            self.excel_extractor.database_learner = self.database_learner
            self.text_extractor.database_learner = self.database_learner
        
        # Initialiser le détecteur de type de fichier unifié
        self.file_type_detector = FileTypeDetector
        
        # Initialiser le post-processeur intelligent
        self.intelligent_processor = IntelligentPostProcessor(enable_improver=True)
        
        # Métriques de performance améliorées
        self.performance_metrics = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'extraction_errors': 0,
            'average_extraction_time': 0.0,
            'extraction_by_type': {
                'pdf': 0,
                'excel': 0,
                'text': 0,
                'other': 0
            },
            'errors_by_type': {},
            'extraction_time_by_type': {
                'pdf': [],
                'excel': [],
                'text': [],
                'other': []
            },
            'field_extraction_stats': {},
            'validation_failure_reasons': {}
        }
        
        # Apprentissage depuis les données de référence
        if self.reference_data is not None and not self.reference_data.empty:
            self._learn_from_reference_data()
        # Note: L'apprentissage depuis la BDD est déjà fait au-dessus si database_manager est fourni
        
        logger.info("🚀 AOExtractor V2 initialisé avec architecture modulaire")
    
    def extract_from_file(self, uploaded_file, file_analysis: Dict[str, Any], target_columns: List[str] = None) -> List[Dict[str, Any]]:
        """
        Extrait les informations d'un appel d'offres depuis un fichier uploadé
        
        Args:
            uploaded_file: Fichier uploadé par l'utilisateur
            file_analysis: Analyse préliminaire du fichier
            target_columns: Liste des colonnes cibles de la base de données
            
        Returns:
            Liste des données extraites
        """
        start_time = time.time()
        
        try:
            self.performance_metrics['total_extractions'] += 1
            logger.info(f"📁 Extraction depuis le fichier: {uploaded_file.name}")
            
            # Déterminer le type de fichier avec le détecteur unifié
            file_type = self.file_type_detector.detect(
                file_name=uploaded_file.name,
                file_analysis=file_analysis
            )
            logger.info(f"📋 Type de fichier détecté: {file_type}")
            
            extractor = self._get_extractor_for_type(file_type)
            
            if not extractor:
                logger.error(f"❌ Type de fichier non supporté: {file_type}")
                return [{'erreur': f"Type de fichier non supporté: {file_type}"}]
            
            # Logger l'extracteur utilisé
            extractor_name = extractor.__class__.__name__
            logger.info(f"🔧 Utilisation de l'extracteur: {extractor_name}")
            
            # Effectuer l'extraction
            extracted_entries = extractor.extract(uploaded_file, file_analysis=file_analysis)
            logger.info(f"✅ Extraction terminée avec {extractor_name}: {len(extracted_entries) if extracted_entries else 0} entrée(s)")
            
            if not extracted_entries:
                logger.warning("⚠️ Aucune donnée extraite")
                return []
            
            # Filtrer les colonnes cibles si spécifiées
            if target_columns:
                extracted_entries = self._filter_target_columns(extracted_entries, target_columns)
            
            # Mettre à jour les métriques
            self.performance_metrics['successful_extractions'] += 1
            self.performance_metrics['extraction_by_type'][file_type] += 1
            
            # Calculer le temps d'extraction
            extraction_time = time.time() - start_time
            
            # Mettre à jour le temps moyen
            if self.performance_metrics['total_extractions'] > 0:
                self.performance_metrics['average_extraction_time'] = (
                    (self.performance_metrics['average_extraction_time'] * 
                     (self.performance_metrics['total_extractions'] - 1) + extraction_time) /
                    self.performance_metrics['total_extractions']
                )
            else:
                self.performance_metrics['average_extraction_time'] = extraction_time
            
            # Enregistrer le temps par type
            if file_type in self.performance_metrics['extraction_time_by_type']:
                self.performance_metrics['extraction_time_by_type'][file_type].append(extraction_time)
            
            # Enrichir avec le post-processeur intelligent (si activé)
            if self.intelligent_processor.is_available() and extracted_entries:
                for entry in extracted_entries:
                    if 'valeurs_extraites' in entry:
                        # Récupérer le texte source si disponible
                        text_source = entry.get('text_source', '')
                        if text_source:
                            enhanced_data = self.intelligent_processor.enhance_extraction(
                                entry['valeurs_extraites'],
                                text_source,
                                context=file_analysis
                            )
                            entry['valeurs_extraites'] = enhanced_data
            
            # Enrichir avec les suggestions depuis la base de données
            if self.database_learner and self.database_learner.is_trained:
                for entry in extracted_entries:
                    if 'valeurs_extraites' in entry:
                        self._enrich_with_database_suggestions(entry['valeurs_extraites'])
            
            # Les valeurs générées (segment, famille) sont déjà créées dans generate_missing_values()
            # via les méthodes _classify_segment() et _classify_famille() qui utilisent database_learner
            
            logger.info(f"✅ Extraction terminée: {len(extracted_entries)} entrées en {extraction_time:.2f}s")
            return extracted_entries
            
        except Exception as e:
            self.performance_metrics['extraction_errors'] += 1
            error_type = type(e).__name__
            
            # Logger avec traceback pour debug
            logger.error(
                f"❌ Erreur lors de l'extraction ({error_type}): {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            # Mettre à jour les métriques d'erreur par type
            if 'errors_by_type' not in self.performance_metrics:
                self.performance_metrics['errors_by_type'] = {}
            self.performance_metrics['errors_by_type'][error_type] = \
                self.performance_metrics['errors_by_type'].get(error_type, 0) + 1
            
            return [{
                'erreur': f"Erreur lors de l'extraction: {error_type} - {str(e)}",
                'error_type': error_type,
                'error_details': str(e)
            }]
    
    
    def _get_extractor_for_type(self, file_type: str):
        """
        Retourne l'extracteur approprié pour le type de fichier
        
        Args:
            file_type: Type de fichier
            
        Returns:
            Extracteur approprié ou None
        """
        extractors = {
            'pdf': self.pdf_extractor,
            'excel': self.excel_extractor,
            'text': self.text_extractor
        }
        
        return extractors.get(file_type)
    
    def _filter_target_columns(self, extracted_entries: List[Dict[str, Any]], target_columns: List[str]) -> List[Dict[str, Any]]:
        """
        Filtre les entrées pour ne garder que les colonnes cibles
        
        Args:
            extracted_entries: Entrées extraites
            target_columns: Colonnes cibles
            
        Returns:
            Entrées filtrées
        """
        try:
            filtered_entries = []
            
            for entry in extracted_entries:
                if 'valeurs_extraites' in entry:
                    # Filtrer les valeurs extraites
                    filtered_values = {}
                    for col in target_columns:
                        if col in entry['valeurs_extraites']:
                            filtered_values[col] = entry['valeurs_extraites'][col]
                    
                    # Créer une nouvelle entrée avec les valeurs filtrées
                    filtered_entry = entry.copy()
                    filtered_entry['valeurs_extraites'] = filtered_values
                    filtered_entries.append(filtered_entry)
                else:
                    # Garder l'entrée telle quelle si pas de valeurs_extraites
                    filtered_entries.append(entry)
            
            logger.info(f"📊 Filtrage terminé: {len(filtered_entries)} entrées filtrées")
            return filtered_entries
            
        except Exception as e:
            logger.error(f"Erreur filtrage colonnes cibles: {e}")
            return extracted_entries
    
    def validate_extraction(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Valide une extraction
        
        Args:
            data: Données à valider
            
        Returns:
            Résultat de validation ou None
        """
        try:
            return self.validation_engine.validate_extraction(data)
        except Exception as e:
            logger.error(f"Erreur validation extraction: {e}")
            return None
    
    def get_patterns_for_field(self, field_name: str) -> List[str]:
        """
        Récupère les patterns pour un champ
        
        Args:
            field_name: Nom du champ
            
        Returns:
            Liste des patterns
        """
        try:
            return self.pattern_manager.get_field_patterns(field_name)
        except Exception as e:
            logger.error(f"Erreur récupération patterns pour {field_name}: {e}")
            return []
    
    def add_custom_pattern(self, category: str, subcategory: str, pattern: str):
        """
        Ajoute un pattern personnalisé
        
        Args:
            category: Catégorie du pattern
            subcategory: Sous-catégorie du pattern
            pattern: Pattern regex
        """
        try:
            self.pattern_manager.add_pattern(category, subcategory, pattern)
            logger.info(f"Pattern personnalisé ajouté: {category}.{subcategory}")
        except Exception as e:
            logger.error(f"Erreur ajout pattern personnalisé: {e}")
    
    def detect_lots(self, text: str) -> List[Dict[str, Any]]:
        """
        Détecte les lots dans un texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Liste des lots détectés
        """
        try:
            lots = self.lot_detector.detect_lots(text)
            return [lot.__dict__ for lot in lots]
        except Exception as e:
            logger.error(f"Erreur détection lots: {e}")
            return []
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Retourne les métriques de performance
        
        Returns:
            Dictionnaire des métriques
        """
        metrics = self.performance_metrics.copy()
        
        # Ajouter les métriques des composants
        metrics['pattern_manager'] = self.pattern_manager.get_performance_stats()
        metrics['validation_engine'] = self.validation_engine.get_performance_metrics()
        metrics['lot_detector'] = self.lot_detector.get_performance_metrics()
        
        return metrics
    
    def reset_metrics(self):
        """Remet à zéro toutes les métriques"""
        self.performance_metrics = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'extraction_errors': 0,
            'average_extraction_time': 0.0,
            'extraction_by_type': {
                'pdf': 0,
                'excel': 0,
                'text': 0,
                'other': 0
            },
            'errors_by_type': {},
            'extraction_time_by_type': {
                'pdf': [],
                'excel': [],
                'text': [],
                'other': []
            },
            'field_extraction_stats': {},
            'validation_failure_reasons': {}
        }
        
        self.pattern_manager.reset_stats()
        self.validation_engine.reset_metrics()
        self.lot_detector.reset_metrics()
        
        logger.info("📊 Métriques remises à zéro")
    
    def _learn_from_reference_data(self):
        """
        Apprend des patterns depuis les données de référence
        
        Analyse les données existantes pour extraire des patterns communs
        et améliorer la détection future.
        Si une DatabaseManager est disponible, utilise aussi les données de la BDD.
        """
        try:
            if self.reference_data is None or self.reference_data.empty:
                # Si pas de reference_data mais qu'on a un database_manager, l'utiliser
                if self.database_manager and not self.database_learner.is_trained:
                    logger.info("📊 Pas de reference_data, utilisation directe de la BDD...")
                    self.database_learner.learn_from_database(limit=500)
                return
            
            logger.info(f"🧠 Apprentissage depuis {len(self.reference_data)} enregistrements de référence...")
            
            # Analyser les intitulés de lots pour extraire des patterns
            if 'intitule_lot' in self.reference_data.columns:
                lots = self.reference_data['intitule_lot'].dropna()
                if not lots.empty:
                    common_words = self._extract_common_words(lots)
                    logger.info(f"📊 {len(common_words)} mots communs extraits depuis les intitulés de lots")
            
            # Analyser les montants pour détecter des patterns
            if 'montant_global_estime' in self.reference_data.columns:
                montants = self.reference_data['montant_global_estime'].dropna()
                if not montants.empty:
                    montant_stats = {
                        'min': float(montants.min()),
                        'max': float(montants.max()),
                        'mean': float(montants.mean()),
                        'median': float(montants.median())
                    }
                    logger.info(f"💰 Statistiques montants: {montant_stats}")
            
            # Si on a aussi un database_manager, fusionner les apprentissages
            if self.database_manager and not self.database_learner.is_trained:
                logger.info("📊 Enrichissement avec les données de la BDD...")
                self.database_learner.learn_from_database(limit=500)
            
            logger.info("✅ Apprentissage terminé")
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de l'apprentissage: {e}")
    
    def _enrich_with_database_suggestions(self, extracted_data: Dict[str, Any]):
        """
        Enrichit les données extraites avec des suggestions depuis la BDD
        NE REMPLACE QUE LES CHAMPS VRAIMENT VIDES - ne modifie pas les valeurs extraites
        
        Args:
            extracted_data: Données extraites à enrichir (modifié sur place)
        """
        try:
            if not self.database_learner or not self.database_learner.is_trained:
                return
            
            # Champs à enrichir UNIQUEMENT si complètement manquants ou vides
            # Note: segment et famille sont maintenant générés intelligemment dans generate_missing_values()
            fields_to_enrich = ['type_procedure', 'mono_multi', 'univers', 'groupement']
            
            for field in fields_to_enrich:
                # Vérifier si le champ est vraiment vide (pas présent, None, ou chaîne vide)
                current_value = extracted_data.get(field)
                
                if not current_value or (isinstance(current_value, str) and current_value.strip() == ''):
                    # Suggérer une valeur depuis la BDD
                    suggestion = self.database_learner.suggest_value(field, extracted_data)
                    if suggestion:
                        extracted_data[field] = suggestion
                        logger.debug(f"💡 Valeur suggérée depuis BDD pour {field}: {suggestion}")
                else:
                    # Le champ a déjà une valeur - NE PAS la remplacer
                    logger.debug(f"✓ Champ '{field}' déjà rempli ({current_value}), pas de suggestion")
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur enrichissement avec suggestions BDD: {e}")
    
    def _extract_common_words(self, series: pd.Series, min_occurrences: int = 3) -> List[str]:
        """
        Extrait les mots communs d'une série de textes
        
        Args:
            series: Série de textes à analyser
            min_occurrences: Nombre minimum d'occurrences pour être considéré comme commun
            
        Returns:
            Liste des mots communs
        """
        try:
            from collections import Counter
            import re
            
            # Joindre tous les textes
            all_text = ' '.join(series.astype(str)).lower()
            
            # Extraire les mots (au moins 3 caractères)
            words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', all_text)
            
            # Compter les occurrences
            word_counts = Counter(words)
            
            # Filtrer par nombre minimum d'occurrences
            common_words = [
                word for word, count in word_counts.items() 
                if count >= min_occurrences
            ]
            
            return sorted(common_words, key=lambda x: word_counts[x], reverse=True)[:50]
            
        except Exception as e:
            logger.error(f"Erreur extraction mots communs: {e}")
            return []
    
    def save_patterns_config(self, config_file: str):
        """
        Sauvegarde la configuration des patterns
        
        Args:
            config_file: Chemin du fichier de configuration
        """
        try:
            self.pattern_manager.save_to_file(config_file)
            logger.info(f"Configuration patterns sauvegardée: {config_file}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration: {e}")
    
    def load_patterns_config(self, config_file: str):
        """
        Charge la configuration des patterns
        
        Args:
            config_file: Chemin du fichier de configuration
        """
        try:
            self.pattern_manager.load_from_file(config_file)
            logger.info(f"Configuration patterns chargée: {config_file}")
        except Exception as e:
            logger.error(f"Erreur chargement configuration: {e}")
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """
        Retourne un résumé de l'extraction
        
        Returns:
            Résumé de l'extraction
        """
        metrics = self.get_performance_metrics()
        
        return {
            'total_extractions': metrics['total_extractions'],
            'success_rate': (
                metrics['successful_extractions'] / metrics['total_extractions'] * 100
                if metrics['total_extractions'] > 0 else 0
            ),
            'average_time': metrics['average_extraction_time'],
            'extraction_by_type': metrics['extraction_by_type'],
            'pattern_compilations': metrics['pattern_manager']['total_compilations'],
            'validation_success_rate': (
                metrics['validation_engine']['successful_validations'] / 
                metrics['validation_engine']['total_validations'] * 100
                if metrics['validation_engine']['total_validations'] > 0 else 0
            ),
            'lot_detection_success_rate': (
                metrics['lot_detector']['successful_detections'] / 
                metrics['lot_detector']['total_detections'] * 100
                if metrics['lot_detector']['total_detections'] > 0 else 0
            )
        }
    
    def __str__(self) -> str:
        """Représentation string de l'extracteur"""
        metrics = self.get_performance_metrics()
        return f"AOExtractorV2(extractions={metrics['total_extractions']}, success_rate={self.get_extraction_summary()['success_rate']:.1f}%)"
    
    def __repr__(self) -> str:
        """Représentation détaillée de l'extracteur"""
        return f"AOExtractorV2(pattern_manager={self.pattern_manager}, validation_engine={self.validation_engine})"
