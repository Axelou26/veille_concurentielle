"""
📊 Extracteur Excel - Spécialisé
================================

Extracteur spécialisé pour les fichiers Excel d'appels d'offres.
Gère la détection des lots et l'extraction des données structurées.
"""

import pandas as pd
import logging
import traceback
from typing import Dict, Any, List, Optional
from .base_extractor import BaseExtractor
from .pattern_manager import PatternManager
from .lot_detector import LotDetector, LotInfo
from .validation_engine import ValidationEngine

logger = logging.getLogger(__name__)

class ExcelExtractor(BaseExtractor):
    """Extracteur spécialisé pour les fichiers Excel"""
    
    def __init__(self, pattern_manager: PatternManager = None, validation_engine: ValidationEngine = None):
        """
        Initialise l'extracteur Excel
        
        Args:
            pattern_manager: Gestionnaire de patterns (optionnel)
            validation_engine: Moteur de validation (optionnel)
        """
        super().__init__(pattern_manager, validation_engine)
        self.lot_detector = LotDetector()
        self.pattern_manager = pattern_manager or PatternManager()
        self.validation_engine = validation_engine or ValidationEngine()
    
    def extract(self, source: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Extrait les données d'un fichier Excel
        
        Args:
            source: Source de données (fichier Excel, DataFrame, etc.)
            **kwargs: Arguments supplémentaires
            
        Returns:
            Liste des données extraites
        """
        try:
            logger.info("📊 Début de l'extraction Excel...")
            
            # Charger le DataFrame Excel
            df = self._load_excel_data(source)
            if df is None or df.empty:
                logger.warning("⚠️ Aucune donnée Excel chargée")
                return []
            
            logger.info(f"📊 Fichier Excel chargé: {len(df)} lignes, {len(df.columns)} colonnes")
            
            # Détecter les lots dans le fichier Excel
            lots_detected = self._detect_lots_in_excel(df)
            
            if lots_detected:
                logger.info(f"✅ {len(lots_detected)} lots détectés dans le fichier Excel")
                return self._create_entries_for_lots(df, lots_detected)
            else:
                logger.info("⚠️ Aucun lot détecté, traitement standard")
                return self._extract_single_excel_entry(df)
                
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"❌ Erreur extraction Excel ({error_type}): {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            return [{
                'erreur': f"Erreur extraction Excel: {error_type} - {str(e)}",
                'error_type': error_type,
                'error_details': str(e)
            }]
    
    def _load_excel_data(self, source: Any) -> Optional[pd.DataFrame]:
        """
        Charge les données Excel depuis la source
        
        Args:
            source: Source Excel (fichier, DataFrame, etc.)
            
        Returns:
            DataFrame ou None
        """
        try:
            # Si c'est déjà un DataFrame
            if isinstance(source, pd.DataFrame):
                return source
            
            # Si c'est un fichier uploadé (Streamlit)
            if hasattr(source, 'read'):
                return pd.read_excel(source)
            
            # Si c'est un chemin de fichier
            if isinstance(source, str):
                return pd.read_excel(source)
            
            # Si c'est un dictionnaire avec des données
            if isinstance(source, dict) and 'data' in source:
                return pd.DataFrame(source['data'])
            
            logger.warning(f"Type de source non supporté: {type(source)}")
            return None
            
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"❌ Erreur chargement données Excel ({error_type}): {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            return None
    
    def _detect_lots_in_excel(self, df: pd.DataFrame) -> List[LotInfo]:
        """
        Détecte les lots dans un fichier Excel
        
        Args:
            df: DataFrame Excel
            
        Returns:
            Liste des lots détectés
        """
        lots = []
        
        try:
            logger.info("🔍 Détection des lots dans le fichier Excel...")
            
            # Rechercher des colonnes qui pourraient contenir des informations sur les lots
            lot_columns = []
            for col in df.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['lot', 'numero', 'numéro', 'intitule', 'titre', 'objet']):
                    lot_columns.append(col)
            
            if lot_columns:
                logger.info(f"📋 Colonnes de lots détectées: {lot_columns}")
                
                # Si on trouve une colonne "lot" ou similaire, traiter chaque ligne comme un lot
                for idx, row in df.iterrows():
                    lot_info = self._extract_lot_from_row(row, lot_columns, idx)
                    if lot_info:
                        lots.append(lot_info)
                        logger.info(f"📦 Lot Excel détecté: {lot_info.numero} - {lot_info.intitule[:50]}...")
            
            logger.info(f"✅ Détection Excel terminée: {len(lots)} lots trouvés")
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection des lots Excel: {e}")
        
        return lots
    
    def _extract_lot_from_row(self, row: pd.Series, lot_columns: List[str], row_index: int) -> Optional[LotInfo]:
        """
        Extrait les informations d'un lot depuis une ligne Excel
        
        Args:
            row: Ligne du DataFrame
            lot_columns: Colonnes de lots identifiées
            row_index: Index de la ligne
            
        Returns:
            Informations du lot ou None
        """
        try:
            lot_info = LotInfo(
                numero=row_index + 1,
                intitule="",
                source='excel_extraction'
            )
            
            # Extraire le numéro de lot
            for col in lot_columns:
                if 'numero' in col.lower() or 'numéro' in col.lower() or 'no' in col.lower():
                    try:
                        if pd.notna(row[col]):
                            lot_info.numero = int(row[col])
                    except (ValueError, TypeError):
                        pass
            
            # Extraire l'intitulé du lot
            for col in lot_columns:
                if 'intitule' in col.lower() or 'titre' in col.lower() or 'objet' in col.lower():
                    if pd.notna(row[col]):
                        lot_info.intitule = str(row[col]).strip()
                        break
            
            # Si pas d'intitulé trouvé, utiliser un intitulé par défaut
            if not lot_info.intitule:
                lot_info.intitule = f"Lot {lot_info.numero}"
            
            # Extraire les montants
            for col in row.index:
                col_lower = col.lower()
                if 'montant' in col_lower or 'budget' in col_lower or 'prix' in col_lower:
                    try:
                        if pd.notna(row[col]):
                            value = float(row[col]) if isinstance(row[col], (int, float)) else float(str(row[col]).replace(',', '.'))
                            if 'estime' in col_lower or 'estimation' in col_lower:
                                lot_info.montant_estime = value
                            elif 'max' in col_lower or 'maximum' in col_lower:
                                lot_info.montant_maximum = value
                            else:
                                lot_info.montant_estime = value
                                lot_info.montant_maximum = value
                    except (ValueError, TypeError):
                        pass
            
            # Extraire les quantités
            for col in row.index:
                col_lower = col.lower()
                if 'quantite' in col_lower or 'quantité' in col_lower or 'qte' in col_lower:
                    try:
                        if pd.notna(row[col]):
                            if 'minimum' in col_lower or 'min' in col_lower:
                                lot_info.quantite_minimum = int(row[col])
                            elif 'maximum' in col_lower or 'max' in col_lower:
                                lot_info.quantite_maximum = int(row[col])
                            elif 'estime' in col_lower or 'estimation' in col_lower:
                                lot_info.quantites_estimees = str(row[col])
                            else:
                                lot_info.quantites_estimees = str(row[col])
                    except (ValueError, TypeError):
                        pass
            
            # Extraire les critères d'attribution
            for col in row.index:
                col_lower = col.lower()
                if 'critere' in col_lower or 'critère' in col_lower or 'attribution' in col_lower:
                    try:
                        if pd.notna(row[col]):
                            if 'economique' in col_lower or 'économique' in col_lower or 'prix' in col_lower or 'cout' in col_lower:
                                lot_info.criteres_economique = str(row[col])
                            elif 'technique' in col_lower:
                                lot_info.criteres_techniques = str(row[col])
                            elif 'autre' in col_lower:
                                lot_info.autres_criteres = str(row[col])
                            else:
                                if not lot_info.criteres_economique:
                                    lot_info.criteres_economique = str(row[col])
                    except (ValueError, TypeError):
                        pass
            
            # Extraire RSE et contribution fournisseur
            for col in row.index:
                col_lower = col.lower()
                if 'rse' in col_lower or 'responsabilite' in col_lower or 'responsabilité' in col_lower or 'social' in col_lower or 'environnement' in col_lower:
                    try:
                        if pd.notna(row[col]):
                            lot_info.rse = str(row[col])
                    except (ValueError, TypeError):
                        pass
                elif 'contribution' in col_lower or 'fournisseur' in col_lower:
                    try:
                        if pd.notna(row[col]):
                            lot_info.contribution_fournisseur = str(row[col])
                    except (ValueError, TypeError):
                        pass
            
            # Nettoyer l'intitulé
            lot_info.intitule = self._clean_title(lot_info.intitule)
            
            return lot_info
            
        except Exception as e:
            logger.error(f"Erreur extraction lot depuis ligne Excel: {e}")
            return None
    
    def _clean_title(self, title: str) -> str:
        """Nettoie un intitulé de lot"""
        if not title or not isinstance(title, str):
            return ""
        
        # Remplacer les sauts de ligne par des espaces
        cleaned = title.replace('\n', ' ').replace('\r', ' ')
        
        # Supprimer les espaces multiples
        cleaned = ' '.join(cleaned.split())
        
        # Supprimer les caractères de formatage
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _create_entries_for_lots(self, df: pd.DataFrame, lots: List[LotInfo]) -> List[Dict[str, Any]]:
        """
        Crée des entrées pour chaque lot détecté
        
        Args:
            df: DataFrame Excel
            lots: Liste des lots détectés
            
        Returns:
            Liste des entrées créées
        """
        entries = []
        
        try:
            logger.info(f"📝 Création des entrées pour {len(lots)} lots...")
            
            # Extraire les informations générales du fichier
            general_info = self._extract_general_excel_info(df)
            
            for lot in lots:
                # Créer une entrée pour ce lot
                lot_entry = {
                    'valeurs_extraites': general_info.copy(),
                    'valeurs_generees': {},
                    'statistiques': {}
                }
                
                # Ajouter les informations spécifiques au lot
                lot_entry['valeurs_extraites']['nbr_lots'] = len(lots)
                lot_entry['valeurs_extraites']['lot_numero'] = lot.numero
                lot_entry['valeurs_extraites']['intitule_lot'] = lot.intitule
                lot_entry['valeurs_extraites']['montant_global_estime'] = lot.montant_estime
                lot_entry['valeurs_extraites']['montant_global_maxi'] = lot.montant_maximum
                lot_entry['valeurs_extraites']['quantite_minimum'] = lot.quantite_minimum
                lot_entry['valeurs_extraites']['quantites_estimees'] = lot.quantites_estimees
                lot_entry['valeurs_extraites']['quantite_maximum'] = lot.quantite_maximum
                lot_entry['valeurs_extraites']['criteres_economique'] = lot.criteres_economique
                lot_entry['valeurs_extraites']['criteres_techniques'] = lot.criteres_techniques
                lot_entry['valeurs_extraites']['autres_criteres'] = lot.autres_criteres
                lot_entry['valeurs_extraites']['rse'] = lot.rse
                lot_entry['valeurs_extraites']['contribution_fournisseur'] = lot.contribution_fournisseur
                
                # Générer les valeurs manquantes
                lot_entry['valeurs_extraites'] = self.generate_missing_values(lot_entry['valeurs_extraites'])
                
                # Calculer les statistiques
                lot_entry['statistiques'] = self.calculate_extraction_stats(lot_entry['valeurs_extraites'])
                
                # Validation si disponible
                if self.validation_engine:
                    validation_result = self.validate_extraction(lot_entry['valeurs_extraites'])
                    if validation_result:
                        lot_entry['validation'] = {
                            'is_valid': validation_result.is_valid,
                            'confidence': validation_result.confidence,
                            'issues': [issue.message for issue in validation_result.issues],
                            'suggestions': validation_result.suggestions
                        }
                
                # Ajouter un identifiant unique pour le lot
                lot_entry['lot_id'] = f"LOT_{lot.numero}"
                lot_entry['extraction_source'] = lot.source
                lot_entry['extraction_timestamp'] = self._get_current_timestamp()
                
                entries.append(lot_entry)
                logger.info(f"📦 Entrée Excel créée pour le lot {lot.numero}: {lot.intitule[:50]}...")
            
            logger.info(f"✅ Création des entrées Excel terminée: {len(entries)} entrées créées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des entrées Excel: {e}")
        
        return entries
    
    def _extract_single_excel_entry(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extrait une seule entrée d'un fichier Excel (pas de lots détectés)
        
        Args:
            df: DataFrame Excel
            
        Returns:
            Liste avec une seule entrée
        """
        try:
            logger.info("📊 Extraction d'entrée unique Excel...")
            
            # Extraire les informations générales
            general_info = self._extract_general_excel_info(df)
            
            # Créer l'entrée
            entry = {
                'valeurs_extraites': general_info,
                'valeurs_generees': {},
                'statistiques': {}
            }
            
            # Ajouter des valeurs par défaut
            entry['valeurs_extraites']['nbr_lots'] = 1
            entry['valeurs_extraites']['lot_numero'] = 1
            entry['valeurs_extraites']['intitule_lot'] = entry['valeurs_extraites'].get('intitule_procedure', 'Lot unique')
            
            # Générer les valeurs manquantes
            entry['valeurs_extraites'] = self.generate_missing_values(entry['valeurs_extraites'])
            
            # Calculer les statistiques
            entry['statistiques'] = self.calculate_extraction_stats(entry['valeurs_extraites'])
            
            # Validation si disponible
            if self.validation_engine:
                validation_result = self.validate_extraction(entry['valeurs_extraites'])
                if validation_result:
                    entry['validation'] = {
                        'is_valid': validation_result.is_valid,
                        'confidence': validation_result.confidence,
                        'issues': [issue.message for issue in validation_result.issues],
                        'suggestions': validation_result.suggestions
                    }
            
            # Ajouter des métadonnées
            entry['extraction_source'] = 'excel_single_entry'
            entry['extraction_timestamp'] = self._get_current_timestamp()
            
            logger.info("✅ Entrée Excel unique créée")
            return [entry]
            
        except Exception as e:
            logger.error(f"Erreur extraction entrée unique Excel: {e}")
            return [{'erreur': f"Erreur extraction entrée unique Excel: {e}"}]
    
    def _extract_general_excel_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extrait les informations générales d'un fichier Excel
        
        Args:
            df: DataFrame Excel
            
        Returns:
            Dictionnaire des informations générales
        """
        general_info = {}
        
        try:
            # Mapping intelligent des colonnes Excel vers les 44 colonnes
            column_mapping = {
                # Montants
                'montant_global_estime': ['budget', 'montant', 'prix', 'cout', 'estimation', 'valeur', 'global', 'estime'],
                'montant_global_maxi': ['maximum', 'maxi', 'plafond', 'limite', 'budget_max'],
                
                # Dates
                'date_limite': ['date', 'publication', 'limite', 'echeance', 'cloture', 'remise', 'offres'],
                'date_attribution': ['attribution', 'attribue', 'attribution_marche'],
                'duree_marche': ['duree', 'durée', 'marche', 'mois', 'annee', 'année'],
                
                # Références et procédures
                'reference_procedure': ['reference', 'ref', 'code', 'numero', 'identifiant', 'procedure', 'ao'],
                'intitule_procedure': ['titre', 'nom', 'libelle', 'objet', 'intitule', 'procedure', 'marche', 'ao'],
                'type_procedure': ['type', 'procedure', 'mode', 'forme', 'appel', 'offre', 'consultation'],
                'mono_multi': ['mono', 'multi', 'attribution', 'lotissement', 'unique', 'multiple'],
                
                # Groupements et organismes
                'groupement': ['organisme', 'acheteur', 'client', 'maitre', 'donneur', 'groupement', 'consortium'],
                
                # Informations complémentaires
                'infos_complementaires': ['description', 'detail', 'commentaire', 'infos', 'complementaires', 'contact', 'telephone', 'email', 'lieu', 'adresse'],
                
                # Critères
                'criteres_economique': ['criteres', 'critères', 'economique', 'économique', 'prix', 'cout', 'attribution'],
                'criteres_techniques': ['criteres', 'critères', 'techniques', 'technique', 'attribution'],
                'autres_criteres': ['autres', 'criteres', 'critères', 'attribution', 'autres_criteres'],
                
                # Quantités
                'quantite_minimum': ['quantite', 'quantité', 'qte', 'minimum', 'min'],
                'quantites_estimees': ['quantites', 'quantités', 'qte', 'estimees', 'estimées'],
                'quantite_maximum': ['quantite', 'quantité', 'qte', 'maximum', 'max']
            }
            
            # Analyse des colonnes Excel avec mapping intelligent
            for col in df.columns:
                col_lower = col.lower()
                values = df[col].dropna()
                
                # Mapper les colonnes vers les champs standard
                for field, keywords in column_mapping.items():
                    if any(keyword in col_lower for keyword in keywords):
                        if len(values) > 0:
                            # Prendre la première valeur non nulle et la nettoyer
                            raw_value = values.iloc[0]
                            cleaned_value = self._clean_excel_value(raw_value, field)
                            
                            # Normaliser les valeurs spéciales
                            if field == 'type_procedure' and cleaned_value:
                                cleaned_value = self._normalize_type_procedure(cleaned_value)
                            elif field == 'mono_multi' and cleaned_value:
                                cleaned_value = self._normalize_mono_multi(cleaned_value, general_info.get('nbr_lots'))
                            
                            if cleaned_value:
                                general_info[field] = cleaned_value
                        break
            
            # Essayer aussi avec les patterns si des champs manquent encore
            # (pour les cas où les colonnes ne sont pas bien nommées)
            text_content = self._dataframe_to_text(df)
            missing_fields = ['type_procedure', 'mono_multi', 'groupement']
            
            for field in missing_fields:
                if field not in general_info:
                    patterns = self.pattern_manager.get_field_patterns(field)
                    if patterns:
                        values = self.extract_with_patterns(text_content, patterns, field)
                        if values:
                            cleaned_value = self.clean_extracted_value(values[0], self._get_field_type(field))
                            if field == 'type_procedure':
                                cleaned_value = self._normalize_type_procedure(cleaned_value)
                            elif field == 'mono_multi':
                                cleaned_value = self._normalize_mono_multi(cleaned_value, general_info.get('nbr_lots'))
                            
                            if cleaned_value:
                                general_info[field] = cleaned_value
            
            logger.info(f"📊 Informations générales extraites: {len(general_info)} champs")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des informations générales Excel: {e}")
        
        return general_info
    
    def _clean_excel_value(self, value: Any, field_name: str) -> Any:
        """
        Nettoie une valeur extraite d'Excel
        
        Args:
            value: Valeur brute depuis Excel
            field_name: Nom du champ
            
        Returns:
            Valeur nettoyée
        """
        if pd.isna(value):
            return None
        
        # Convertir en string pour le nettoyage
        if isinstance(value, (int, float)):
            if 'montant' in field_name.lower():
                return float(value)
            elif 'duree' in field_name.lower() or 'quantite' in field_name.lower() or 'nbr' in field_name.lower():
                return int(value)
            else:
                return str(value)
        
        value_str = str(value).strip()
        
        if not value_str or value_str.lower() in ['nan', 'none', 'null', '']:
            return None
        
        return value_str
    
    def _dataframe_to_text(self, df: pd.DataFrame) -> str:
        """
        Convertit un DataFrame en texte pour l'extraction avec patterns
        
        Args:
            df: DataFrame Excel
            
        Returns:
            Texte combiné du DataFrame
        """
        try:
            # Combiner les noms de colonnes et les valeurs
            text_parts = []
            
            # Ajouter les noms de colonnes
            text_parts.append(' '.join(df.columns))
            
            # Ajouter les premières lignes (max 50 pour éviter de traiter trop de données)
            for idx, row in df.head(50).iterrows():
                row_text = ' '.join(str(val) for val in row.values if pd.notna(val))
                text_parts.append(row_text)
            
            return ' '.join(text_parts)
            
        except Exception as e:
            logger.warning(f"Erreur conversion DataFrame en texte: {e}")
            return ''
    
    def _get_field_type(self, field_name: str) -> str:
        """Détermine le type d'un champ pour le nettoyage"""
        if 'montant' in field_name.lower():
            return 'montant'
        elif 'date' in field_name.lower():
            return 'date'
        elif 'duree' in field_name.lower() or 'durée' in field_name.lower():
            return 'duree'
        elif 'reconduction' in field_name.lower():
            return 'reconduction'
        elif 'reference' in field_name.lower():
            return 'reference'
        else:
            return 'text'
    
    def _normalize_type_procedure(self, value: str) -> str:
        """
        Normalise la valeur du type de procédure
        
        Args:
            value: Valeur brute extraite
            
        Returns:
            Valeur normalisée ou None
        """
        if not value or not isinstance(value, str):
            return None
        
        value_lower = value.lower().strip()
        
        # Mapping des valeurs vers les types normalisés
        if 'ouvert' in value_lower and ('appel' in value_lower or 'offre' in value_lower or 'ao' in value_lower):
            return 'Appel d\'offres ouvert'
        elif 'restreint' in value_lower and ('appel' in value_lower or 'offre' in value_lower or 'ao' in value_lower):
            return 'Appel d\'offres restreint'
        elif 'consultation' in value_lower:
            return 'Consultation'
        elif 'achat direct' in value_lower or 'commande' in value_lower:
            return 'Achat direct'
        elif 'convention' in value_lower or 'accord cadre' in value_lower:
            return 'Convention'
        elif 'marché de services' in value_lower:
            return 'Consultation'
        elif len(value.strip()) > 5:  # Garder la valeur originale si elle est assez longue et non reconnue
            return value.strip()
        
        return None
    
    def _normalize_mono_multi(self, value: str, nbr_lots: int = None) -> str:
        """
        Normalise la valeur mono_multi
        
        Args:
            value: Valeur brute extraite
            nbr_lots: Nombre de lots détectés (pour inférence si nécessaire)
            
        Returns:
            Valeur normalisée ou None
        """
        if not value or not isinstance(value, str):
            # Inférer depuis le nombre de lots si disponible
            if nbr_lots is not None:
                return 'Multi-attributif' if nbr_lots > 1 else 'Mono-attributif'
            return None
        
        value_lower = value.lower().strip()
        
        # Mapping des valeurs
        if any(word in value_lower for word in ['multi', 'multiple', 'alloti', 'lotissement', 'lotti']):
            return 'Multi-attributif'
        elif any(word in value_lower for word in ['mono', 'unique', 'unitaire']):
            return 'Mono-attributif'
        elif nbr_lots is not None:
            # Inférer depuis le nombre de lots
            return 'Multi-attributif' if nbr_lots > 1 else 'Mono-attributif'
        
        return None
    
    def _get_current_timestamp(self) -> str:
        """Retourne le timestamp actuel"""
        from datetime import datetime
        return datetime.now().isoformat()

