"""
📝 Extracteur Texte - Spécialisé
================================

Extracteur spécialisé pour les documents texte d'appels d'offres.
Utilise les patterns modulaires et la validation intelligente.
"""

import logging
import traceback
import re
from typing import Dict, Any, List, Optional
from .base_extractor import BaseExtractor
from .pattern_manager import PatternManager
from .validation_engine import ValidationEngine

logger = logging.getLogger(__name__)

class TextExtractor(BaseExtractor):
    """Extracteur spécialisé pour les documents texte"""
    
    def __init__(self, pattern_manager: PatternManager = None, validation_engine: ValidationEngine = None):
        """
        Initialise l'extracteur texte
        
        Args:
            pattern_manager: Gestionnaire de patterns (optionnel)
            validation_engine: Moteur de validation (optionnel)
        """
        super().__init__(pattern_manager, validation_engine)
        self.pattern_manager = pattern_manager or PatternManager()
        self.validation_engine = validation_engine or ValidationEngine()
    
    def extract(self, source: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Extrait les données d'un document texte
        
        Args:
            source: Source de données (texte, fichier, etc.)
            **kwargs: Arguments supplémentaires
            
        Returns:
            Liste des données extraites
        """
        try:
            logger.info("📝 Début de l'extraction texte...")
            
            # Extraire le texte de la source
            text_content = self._extract_text_from_source(source)
            if not text_content:
                logger.warning("⚠️ Aucun contenu texte extrait")
                return []
            
            logger.info(f"📝 Contenu texte extrait: {len(text_content)} caractères")
            
            # Extraire les informations
            extracted_data = self._extract_data_from_text(text_content)
            
            # Créer l'entrée
            entry = {
                'valeurs_extraites': extracted_data,
                'valeurs_generees': {},
                'statistiques': {}
            }
            
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
            entry['extraction_source'] = 'text_extraction'
            entry['extraction_timestamp'] = self._get_current_timestamp()
            
            logger.info("✅ Extraction texte terminée")
            return [entry]
                
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"❌ Erreur extraction texte ({error_type}): {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            return [{
                'erreur': f"Erreur extraction texte: {error_type} - {str(e)}",
                'error_type': error_type,
                'error_details': str(e)
            }]
    
    def _extract_text_from_source(self, source: Any) -> str:
        """
        Extrait le texte de la source
        
        Args:
            source: Source de données
            
        Returns:
            Texte extrait
        """
        try:
            # Si c'est déjà du texte, le retourner
            if isinstance(source, str):
                return source
            
            # Si c'est un fichier uploadé (Streamlit)
            if hasattr(source, 'read'):
                content = source.read()
                if isinstance(content, bytes):
                    return content.decode('utf-8', errors='ignore')
                else:
                    return str(content)
            
            # Si c'est un dictionnaire avec le contenu
            if isinstance(source, dict) and 'text_content' in source:
                return source['text_content']
            
            # Si c'est une liste de lignes
            if isinstance(source, list):
                return '\n'.join(str(line) for line in source)
            
            return str(source)
            
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"❌ Erreur extraction texte depuis source ({error_type}): {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            return ""
    
    def _extract_data_from_text(self, text_content: str) -> Dict[str, Any]:
        """
        Extrait les données depuis le texte
        
        Args:
            text_content: Contenu texte
            
        Returns:
            Dictionnaire des données extraites
        """
        extracted_data = {}
        
        try:
            # Extraire d'abord le titre du document pour l'intitulé de procédure (priorité)
            document_title = self._extract_document_title(text_content)
            if document_title and len(document_title.strip()) >= 10:
                extracted_data['intitule_procedure'] = document_title.strip()
                logger.info(f"📄 Titre du document détecté comme intitulé: {document_title[:60]}...")
            
            # Champs à extraire
            fields_to_extract = [
                'reference_procedure', 'intitule_procedure', 'groupement',
                'type_procedure', 'mono_multi', 'date_limite', 'date_attribution',
                'duree_marche', 'montant_global_estime', 'montant_global_maxi',
                'nbr_lots', 'intitule_lot', 'quantite_minimum', 'quantites_estimees', 
                'quantite_maximum', 'criteres_economique', 'criteres_techniques', 
                'autres_criteres', 'rse', 'contribution_fournisseur', 'infos_complementaires',
                'remarques', 'notes_acheteur_procedure', 'notes_acheteur_fournisseur', 
                'notes_acheteur_positionnement', 'segment', 'famille'
            ]
            
            # Extraction parallèle des champs
            for field in fields_to_extract:
                # Ne pas chercher intitule_procedure si déjà extrait depuis le titre du document
                if field == 'intitule_procedure' and 'intitule_procedure' in extracted_data:
                    continue
                
                patterns = self.pattern_manager.get_field_patterns(field)
                if patterns:
                    values = self.extract_with_patterns(text_content, patterns, field)
                    if values:
                        # Prendre la première valeur valide
                        cleaned_value = self.clean_extracted_value(values[0], self._get_field_type(field))
                        # Ne pas écraser le titre du document si déjà présent
                        if field == 'intitule_procedure' and 'intitule_procedure' in extracted_data:
                            # Comparer les longueurs et garder le plus long (souvent plus complet)
                            if len(cleaned_value) > len(extracted_data['intitule_procedure']):
                                extracted_data[field] = cleaned_value
                        else:
                            extracted_data[field] = cleaned_value
            
            logger.info(f"📊 Données extraites: {len(extracted_data)} champs")
            
        except Exception as e:
            logger.error(f"Erreur extraction données depuis texte: {e}")
        
        return extracted_data
    
    def _get_field_type(self, field_name: str) -> str:
        """Détermine le type d'un champ pour le nettoyage"""
        if 'montant' in field_name.lower():
            return 'montant'
        elif 'date' in field_name.lower():
            return 'date'
        elif 'reference' in field_name.lower():
            return 'reference'
        else:
            return 'text'
    
    def _extract_document_title(self, text_content: str) -> Optional[str]:
        """
        Extrait le titre du document (généralement un paragraphe en majuscules sur plusieurs lignes)
        
        Le titre du document est souvent l'intitulé de la procédure.
        Peut être sur plusieurs lignes, souvent dans le 2ème paragraphe en majuscules.
        
        Args:
            text_content: Contenu texte du document
            
        Returns:
            Titre du document ou None
        """
        try:
            lines = text_content.split('\n')
            
            # Prendre les 30 premières lignes (pour capturer le 2ème paragraphe aussi)
            first_lines = lines[:30]
            
            # Mots d'en-tête à exclure (ne sont pas le titre)
            header_keywords = [
                'règlement', 'reglement', 'règlement de consultation', 'rc',
                'appel d\'offres', 'appel d\'offre', 'ao', 'marche', 'marché',
                'procedure', 'procédure', 'consultation', 'avis',
                'reference', 'référence', 'ref', 'numero', 'numéro', 'n°',
                'date', 'groupement', 'organisme', 'acheteur',
                'lot', 'lots', 'lotissement', 'allotissement',
                'article', 'chapitre', 'section', 'annexe', 'centrale',
                'pouvoir adjudicateur', 'accord-cadre', 'accords-cadres'
            ]
            
            candidates = []
            multi_line_candidates = []  # Pour les titres sur plusieurs lignes
            
            # 1. Chercher des blocs de lignes en majuscules consécutives (titres multi-lignes)
            i = 0
            while i < len(first_lines) - 1:
                current_block = []
                start_idx = i
                
                # Chercher un bloc de lignes en majuscules consécutives
                while i < len(first_lines):
                    line = first_lines[i].strip()
                    line_lower = line.lower()
                    
                    # Ignorer les lignes vides
                    if not line:
                        i += 1
                        continue
                    
                    # Arrêter si on rencontre un en-tête évident
                    if any(keyword in line_lower for keyword in header_keywords):
                        if current_block:
                            break
                        i += 1
                        continue
                    
                    # Ignorer les dates et références
                    if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line):
                        if current_block:
                            break
                        i += 1
                        continue
                    if re.match(r'^\d{4}-[A-Z]\d{3}', line):
                        if current_block:
                            break
                        i += 1
                        continue
                    
                    # Si ligne en majuscules significative (≥ 20 chars)
                    # Vérifier si c'est principalement en majuscules (≥ 80% des lettres)
                    letters = [c for c in line if c.isalpha()]
                    upper_letters = [c for c in line if c.isupper()]
                    is_mostly_upper = len(letters) > 0 and (len(upper_letters) / len(letters)) >= 0.8
                    is_long_enough = len(line) >= 20
                    
                    is_upper = is_mostly_upper and is_long_enough
                    is_in_block = len(current_block) > 0
                    
                    # Accepter si majuscules OU si déjà dans un bloc (pour continuer le titre multi-lignes)
                    if is_upper or (is_in_block and len(line) >= 15 and is_mostly_upper):
                        current_block.append(line)
                        i += 1
                    else:
                        # Si on a déjà un bloc, l'arrêter
                        if current_block:
                            break
                        i += 1
                
                # Si on a un bloc de plusieurs lignes en majuscules, c'est probablement le titre
                if len(current_block) >= 1:
                    # Joindre les lignes du bloc
                    block_text = ' '.join(current_block)
                    
                    # Filtrer si trop court ou trop long
                    if 30 <= len(block_text) <= 500:
                        # Score basé sur plusieurs critères
                        score = 0
                        
                        # +15 si toutes les lignes sont principalement en majuscules (≥ 80%)
                        def is_mostly_uppercase(s):
                            letters = [c for c in s if c.isalpha()]
                            if not letters:
                                return False
                            upper_letters = [c for c in s if c.isupper()]
                            return (len(upper_letters) / len(letters)) >= 0.8
                        
                        if all(is_mostly_uppercase(l) for l in current_block if l):
                            score += 15
                        
                        # +10 si c'est un bloc de plusieurs lignes (2+)
                        if len(current_block) >= 2:
                            score += 10
                        
                        # +8 si dans les 15 premières lignes (2ème paragraphe souvent)
                        if start_idx < 15:
                            score += 8
                        
                        # +5 si contient des mots significatifs
                        block_lower = block_text.lower()
                        significant_words = [
                            'prestation', 'formation', 'achat', 'fourniture', 'fournitures',
                            'equipement', 'equipements', 'service', 'services', 'maintenance',
                            'logiciel', 'logiciels', 'materiel', 'consommable', 'mobilier',
                            'installation', 'mise en service', 'ventilation', 'transport',
                            'monitorage', 'localisation'
                        ]
                        if any(word in block_lower for word in significant_words):
                            score += 5
                        
                        # +3 si longueur optimale (50-300 caractères)
                        if 50 <= len(block_text) <= 300:
                            score += 3
                        
                        # -5 si contient trop de mots techniques
                        technical_words = ['page', 'total', 'code', 'article', 'dispositions']
                        tech_count = sum(1 for word in technical_words if word in block_lower)
                        score -= tech_count * 2
                        
                        if score > 0:
                            multi_line_candidates.append((score, block_text, start_idx, len(current_block)))
            
            # 2. Chercher aussi des lignes individuelles en majuscules (fallback)
            for i, line in enumerate(first_lines):
                line = line.strip()
                
                # Ignorer les lignes trop courtes ou trop longues
                if len(line) < 30 or len(line) > 500:
                    continue
                
                # Ignorer les lignes vides
                if not line:
                    continue
                
                # Ignorer les lignes qui sont clairement des en-têtes
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in header_keywords):
                    continue
                
                # Ignorer les lignes qui sont des dates ou références
                if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line):
                    continue
                if re.match(r'^\d{4}-[A-Z]\d{3}', line):
                    continue
                
                # Chercher des lignes principalement en majuscules significatives (titres longs)
                # Vérifier si ≥ 80% des lettres sont en majuscules
                letters = [c for c in line if c.isalpha()]
                if letters:
                    upper_ratio = len([c for c in line if c.isupper() and c.isalpha()]) / len(letters)
                    is_mostly_upper_line = upper_ratio >= 0.8 and len(line) >= 30
                else:
                    is_mostly_upper_line = False
                
                if is_mostly_upper_line:
                    score = 0
                    
                    # +10 si la ligne est en majuscules et longue
                    if len(line) >= 50:
                        score += 10
                    else:
                        score += 5
                    
                    # +5 si elle est dans les 15 premières lignes (2ème paragraphe)
                    if i < 15:
                        score += 5
                    
                    # +5 si elle contient des mots significatifs
                    significant_words = [
                        'prestation', 'formation', 'achat', 'fourniture', 'fournitures',
                        'equipement', 'equipements', 'service', 'services', 'maintenance',
                        'logiciel', 'logiciels', 'installation', 'ventilation'
                    ]
                    if any(word in line_lower for word in significant_words):
                        score += 5
                    
                    # +3 si longueur raisonnable (50-300 caractères)
                    if 50 <= len(line) <= 300:
                        score += 3
                    
                    if score > 0:
                        candidates.append((score, line, i))
            
            # Trier les candidats multi-lignes par score (priorité)
            multi_line_candidates.sort(key=lambda x: (-x[0], x[2]))
            
            # Trier les candidats simples
            candidates.sort(key=lambda x: (-x[0], x[2]))
            
            # Préférer les blocs multi-lignes si score élevé
            if multi_line_candidates and multi_line_candidates[0][0] >= 15:
                best_candidate = multi_line_candidates[0][1]
                logger.debug(f"📄 Titre multi-lignes détecté ({multi_line_candidates[0][3]} lignes)")
            elif candidates:
                best_candidate = candidates[0][1]
                logger.debug(f"📄 Titre ligne unique détecté")
            else:
                return None
            
            # Nettoyer le titre
            cleaned_title = best_candidate.strip()
            # Supprimer les caractères de formatage excessifs
            cleaned_title = re.sub(r'\s+', ' ', cleaned_title)
            # Limiter la longueur si vraiment trop long (garder jusqu'à 400 caractères pour phrases longues)
            if len(cleaned_title) > 400:
                cleaned_title = cleaned_title[:400].rsplit(' ', 1)[0] + '...'
            
            logger.info(f"📄 Titre du document extrait: {cleaned_title[:80]}...")
            return cleaned_title
            
        except Exception as e:
            logger.debug(f"Erreur extraction titre document: {e}")
            return None
    
    def _get_current_timestamp(self) -> str:
        """Retourne le timestamp actuel"""
        from datetime import datetime
        return datetime.now().isoformat()

