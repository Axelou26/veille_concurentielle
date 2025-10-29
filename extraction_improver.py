"""
🔧 Améliorateur d'Extraction de Données
=====================================

Système d'extraction simplifié et plus robuste pour les appels d'offres
- Patterns regex simplifiés et plus précis
- Validation des données extraites
- Nettoyage automatique des résultats
- Détection des erreurs d'extraction
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtractionImprover:
    """Améliorateur d'extraction de données pour les appels d'offres"""
    
    def __init__(self):
        """Initialise l'améliorateur avec des patterns simplifiés"""
        self.simple_patterns = self._init_simple_patterns()
        self.validation_rules = self._init_validation_rules()
        self.context_analyzer = self._init_context_analyzer()
        self.intelligent_extractors = self._init_intelligent_extractors()
        
    def _init_simple_patterns(self) -> Dict[str, List[str]]:
        """Patterns d'extraction simplifiés et plus précis"""
        return {
            # Intitulé de procédure - patterns simples
            'intitule_procedure': [
                r'(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
                r'(?:procédure|procedure)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
                r'(?:appel|offre|consultation)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
                r'(?:objet|sujet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
                r'(?:marché|marche)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)'
            ],
            
            # Type de procédure - patterns simples
            'type_procedure': [
                r'(?:type|nature)[\s\w]*[:]\s*([^.\n]{5,50})(?:\n|$)',
                r'(?:procédure|procedure)[\s\w]*[:]\s*([^.\n]{5,50})(?:\n|$)',
                r'(?:appel|offre|consultation)[\s\w]*[:]\s*([^.\n]{5,50})(?:\n|$)',
                r'(?:marché|marche)[\s\w]*[:]\s*([^.\n]{5,50})(?:\n|$)'
            ],
            
            # Intitulé de lot - patterns simples
            'intitule_lot': [
                r'(?:lot|prestation)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
                r'(?:intitulé|intitule|titre)[\s\w]*(?:lot|prestation)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
                r'(?:objet|sujet)[\s\w]*(?:lot|prestation)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)'
            ],
            
            # Groupement - patterns simples
            'groupement': [
                r'(?:groupement|organisme|entité|entite)[\s\w]*[:]\s*([^.\n]{3,50})(?:\n|$)',
                r'(?:acheteur|donneur|ordre)[\s\w]*[:]\s*([^.\n]{3,50})(?:\n|$)',
                r'(?:établissement|etablissement|institution)[\s\w]*[:]\s*([^.\n]{3,50})(?:\n|$)'
            ],
            
            # Montant global estimé - patterns simples
            'montant_global_estime': [
                r'(?:montant|budget|prix)[\s\w]*[:]\s*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                r'(?:budget|montant)[\s\w]*[:]\s*(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?)',
                r'(?:enveloppe|allocation)[\s\w]*[:]\s*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)'
            ],
            
            # Date limite - patterns simples
            'date_limite': [
                r'(?:date|échéance|clôture)[\s\w]*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:date|échéance|clôture)[\s\w]*[:]\s*(\d{4}-\d{2}-\d{2})',
                r'(?:date|échéance|clôture)[\s\w]*[:]\s*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})'
            ],
            
            # Statut - patterns simples
            'statut': [
                r'(?:statut|état|etat|phase)[\s\w]*[:]\s*([^.\n]{3,30})',
                r'(?:procédure|procedure)[\s\w]*(?:statut|état|etat)[\s\w]*[:]\s*([^.\n]{3,30})'
            ],
            
            # Nombre de lots - patterns simples
            'nbr_lots': [
                r'(?:nombre|nb|nbr)[\s\w]*(?:lots|prestations)[\s\w]*[:]\s*(\d+)',
                r'(?:lots|prestations)[\s\w]*(?:nombre|nb|nbr)[\s\w]*[:]\s*(\d+)',
                r'(?:total)[\s\w]*(?:lots|prestations)[\s\w]*[:]\s*(\d+)'
            ],
            
            # Quantités - patterns simples
            'quantite_minimum': [
                r'(?:quantité|quantite|qty)[\s\w]*(?:minimum|min)[\s\w]*[:]\s*(\d+)',
                r'(?:minimum|min)[\s\w]*(?:quantité|quantite)[\s\w]*[:]\s*(\d+)'
            ],
            
            'quantites_estimees': [
                r'(?:quantité|quantite|qty)[\s\w]*(?:estimée|estimee|prévue|prevue)[\s\w]*[:]\s*(\d+)',
                r'(?:estimée|estimee|prévue|prevue)[\s\w]*(?:quantité|quantite)[\s\w]*[:]\s*(\d+)'
            ],
            
            'quantite_maximum': [
                r'(?:quantité|quantite|qty)[\s\w]*(?:maximum|max)[\s\w]*[:]\s*(\d+)',
                r'(?:maximum|max)[\s\w]*(?:quantité|quantite)[\s\w]*[:]\s*(\d+)'
            ],
            
            # Critères - patterns simples
            'criteres_economique': [
                r'(?:critère|critere)[\s\w]*(?:économique|economique|prix)[\s\w]*[:]\s*([^.\n]{10,100})',
                r'(?:économique|economique|prix)[\s\w]*(?:critère|critere)[\s\w]*[:]\s*([^.\n]{10,100})'
            ],
            
            'criteres_techniques': [
                r'(?:critère|critere)[\s\w]*(?:technique|technique)[\s\w]*[:]\s*([^.\n]{10,100})',
                r'(?:technique|technique)[\s\w]*(?:critère|critere)[\s\w]*[:]\s*([^.\n]{10,100})'
            ],
            
            # Informations complémentaires - patterns simples
            'infos_complementaires': [
                r'(?:information|info|renseignement)[\s\w]*(?:complémentaire|complementaire|supplémentaire|supplementaire)[\s\w]*[:]\s*([^.\n]{10,200})',
                r'(?:complémentaire|complementaire|supplémentaire|supplementaire)[\s\w]*(?:information|info)[\s\w]*[:]\s*([^.\n]{10,200})'
            ]
        }
    
    def _init_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Règles de validation pour les données extraites"""
        return {
            'intitule_procedure': {
                'min_length': 10,
                'max_length': 100,
                'forbidden_patterns': [r'^[.,\s]+$', r'^[\[\]()]+$', r'^\.+$', r'^[^a-zA-Z]', r'[\[\]]'],
                'required_words': ['procédure', 'appel', 'offre', 'consultation', 'marché', 'prestation', 'fourniture', 'service']
            },
            'intitule_lot': {
                'min_length': 10,
                'max_length': 200,
                'forbidden_patterns': [r'^[.,\s]+$', r'^[\[\]()]+$', r'^\.+$', r'^[^a-zA-Z]', r'[\[\]]'],
                'required_words': ['lot', 'prestation', 'service', 'fourniture', 'équipement', 'matériel', 'formation', 'formations']
            },
            'groupement': {
                'min_length': 3,
                'max_length': 50,
                'forbidden_patterns': [r'^[.,\s]+$', r'^[\[\]()]+$', r'^\.+$', r'^[^a-zA-Z]', r'[\[\]]'],
                'required_words': ['RESAH', 'UNIHA', 'UGAP', 'CAIH', 'groupement', 'organisme']
            },
            'montant_global_estime': {
                'min_value': 0,
                'max_value': 1000000000,  # 1 milliard
                'pattern': r'^\d+(?:[.,]\d+)?$'
            },
            'date_limite': {
                'pattern': r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$|^\d{4}-\d{2}-\d{2}$'
            },
            'nbr_lots': {
                'min_value': 1,
                'max_value': 100,
                'pattern': r'^\d+$'
            }
        }
    
    def extract_improved_data(self, text: str) -> Dict[str, Any]:
        """Extraction améliorée des données avec validation et intelligence contextuelle"""
        try:
            logger.info("Début de l'extraction améliorée intelligente")
            
            # Nettoyer le texte
            cleaned_text = self._clean_text(text)
            
            # Analyser le contexte du document
            context = self._analyze_document_context(cleaned_text)
            logger.info(f"Contexte détecté: {context['document_type']}")
            
            # Extraction intelligente multi-étapes
            extracted_data = {}
            
            # Étape 0: Extraction de l'intitulé sur le texte brut (avant nettoyage)
            intitule_procedure = self._extract_intitule_procedure_intelligent(text, context, {})
            if intitule_procedure:
                extracted_data['intitule_procedure'] = intitule_procedure
            
            # Étape 1: Extraction directe avec patterns
            for field, patterns in self.simple_patterns.items():
                if field == 'intitule_procedure' and 'intitule_procedure' in extracted_data:
                    continue  # Skip intitule_procedure car déjà extrait
                value = self._extract_field(cleaned_text, patterns, field)
                if value:
                    extracted_data[field] = value
            
            # Étape 1.5: Extraction spécifique des lots (avant l'extraction intelligente)
            if 'intitule_lot' not in extracted_data:
                intitule_lot = self._extract_intitule_lot_intelligent(text, context, extracted_data)
                if intitule_lot:
                    extracted_data['intitule_lot'] = intitule_lot
            
            if 'montant_global_estime' not in extracted_data:
                montant_estime = self._extract_montant_global_estime_intelligent(text, context, extracted_data)
                if montant_estime:
                    extracted_data['montant_global_estime'] = montant_estime
            
            # Étape 2: Extraction intelligente contextuelle
            intelligent_data = self._extract_intelligent_data(cleaned_text, context, extracted_data)
            extracted_data.update(intelligent_data)
            
            # Étape 2.5: Extraction des dates en priorité
            date_data = self._extract_dates_priority(cleaned_text, context, extracted_data)
            extracted_data.update(date_data)
            
            # Étape 3: Déduction des valeurs manquantes
            deduced_data = self._deduce_missing_values(extracted_data, context)
            extracted_data.update(deduced_data)
            
            # Étape 4: Validation contextuelle
            validated_data = self._validate_extracted_data(extracted_data)
            
            # Étape 5: Nettoyage et finalisation
            cleaned_data = self._clean_extracted_data(validated_data)
            
            # Étape 6: Enrichissement avec données générées
            enriched_data = self._enrich_with_generated_data(cleaned_data, context)
            
            # Étape 7: Validation et correction avec la base de données
            validated_data = self._validate_with_database(enriched_data)
            
            logger.info(f"Extraction intelligente terminée: {len(validated_data)} champs extraits")
            return validated_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction: {e}")
            return {}
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte pour améliorer l'extraction"""
        # Remplacer les caractères problématiques MAIS garder les slashes pour les dates
        text = re.sub(r'[^\w\s.,:;()€/-]', ' ', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Normaliser les deux-points
        text = re.sub(r'[:]\s*', ': ', text)
        
        return text.strip()
    
    def _extract_field(self, text: str, patterns: List[str], field: str) -> Optional[str]:
        """Extrait un champ spécifique avec les patterns donnés"""
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Prendre le premier match valide
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    
                    # Nettoyer le match
                    cleaned_match = self._clean_match(match)
                    
                    # Valider le match
                    if self._is_valid_match(cleaned_match, field):
                        return cleaned_match
        
        return None
    
    def _clean_match(self, match: str) -> str:
        """Nettoie un match extrait"""
        # Supprimer les caractères indésirables
        cleaned = re.sub(r'^[.,\s]+|[.,\s]+$', '', match)
        
        # Supprimer les crochets et parenthèses vides
        cleaned = re.sub(r'^[\[\]()]+$', '', cleaned)
        
        # Supprimer les points multiples
        cleaned = re.sub(r'^\.+$', '', cleaned)
        
        return cleaned.strip()
    
    def _is_valid_match(self, match: str, field: str) -> bool:
        """Valide si un match est valide pour un champ donné"""
        if not match or len(match.strip()) == 0:
            return False
        
        # Vérifier les règles de validation
        if field in self.validation_rules:
            rules = self.validation_rules[field]
            
            # Vérifier la longueur
            if 'min_length' in rules and len(match) < rules['min_length']:
                return False
            if 'max_length' in rules and len(match) > rules['max_length']:
                return False
            
            # Vérifier les patterns interdits
            if 'forbidden_patterns' in rules:
                for pattern in rules['forbidden_patterns']:
                    if re.match(pattern, match):
                        return False
            
            # Vérifier les mots requis
            if 'required_words' in rules:
                match_lower = match.lower()
                if not any(word.lower() in match_lower for word in rules['required_words']):
                    return False
            
            # Vérifier les patterns spécifiques
            if 'pattern' in rules:
                if not re.match(rules['pattern'], match):
                    return False
        
        return True
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valide les données extraites"""
        validated_data = {}
        
        for field, value in data.items():
            if self._is_valid_match(str(value), field):
                validated_data[field] = value
            else:
                logger.warning(f"Valeur invalide pour {field}: {value}")
        
        return validated_data
    
    def _clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Nettoie les données extraites"""
        cleaned_data = {}
        
        for field, value in data.items():
            if isinstance(value, str):
                # Nettoyer les chaînes
                cleaned_value = re.sub(r'\s+', ' ', str(value)).strip()
                cleaned_value = re.sub(r'^[.,\s]+|[.,\s]+$', '', cleaned_value)
                
                if cleaned_value:
                    cleaned_data[field] = cleaned_value
            else:
                cleaned_data[field] = value
        
        return cleaned_data
    
    def _init_context_analyzer(self) -> Dict[str, Any]:
        """Initialise l'analyseur de contexte"""
        return {
            'document_types': {
                'appel_offres': ['appel d\'offres', 'ao', 'consultation', 'marché public'],
                'consultation': ['consultation', 'marché de services', 'prestation'],
                'achat_direct': ['achat direct', 'commande', 'bon de commande'],
                'convention': ['convention', 'accord', 'partenariat']
            },
            'sections': {
                'identite': ['objet', 'intitulé', 'titre', 'procédure'],
                'financier': ['montant', 'budget', 'prix', 'coût', 'enveloppe'],
                'temporel': ['date', 'échéance', 'durée', 'période'],
                'technique': ['critères', 'spécifications', 'cahier des charges'],
                'administratif': ['groupement', 'organisme', 'attributaire']
            }
        }
    
    def _init_intelligent_extractors(self) -> Dict[str, callable]:
        """Initialise les extracteurs intelligents pour chaque type de données"""
        return {
            'mots_cles': self._extract_mots_cles_intelligent,
            'univers': self._extract_univers_intelligent,
            'segment': self._extract_segment_intelligent,
            'famille': self._extract_famille_intelligent,
            'statut': self._extract_statut_intelligent,
            'groupement': self._extract_groupement_intelligent,
            'reference_procedure': self._extract_reference_procedure_intelligent,
            'type_procedure': self._extract_type_procedure_intelligent,
            'mono_multi': self._extract_mono_multi_intelligent,
            'execution_marche': self._extract_execution_marche_intelligent,
            'date_limite': self._extract_date_limite_intelligent,
            'date_attribution': self._extract_date_attribution_intelligent,
            'duree_marche': self._extract_duree_marche_intelligent,
            'reconduction': self._extract_reconduction_intelligent,
            'fin_sans_reconduction': self._extract_fin_sans_reconduction_intelligent,
            'fin_avec_reconduction': self._extract_fin_avec_reconduction_intelligent,
            'nbr_lots': self._extract_nbr_lots_intelligent,
            'intitule_procedure': self._extract_intitule_procedure_intelligent,
            'lot_numero': self._extract_lot_numero_intelligent,
            'intitule_lot': self._extract_intitule_lot_intelligent,
            'montant_global_estime': self._extract_montant_global_estime_intelligent,
            'montant_global_maxi': self._extract_montant_global_maxi_intelligent,
            'achat': self._extract_achat_intelligent,
            'credit_bail': self._extract_credit_bail_intelligent,
            'credit_bail_duree': self._extract_credit_bail_duree_intelligent,
            'location': self._extract_location_intelligent,
            'location_duree': self._extract_location_duree_intelligent,
            'mad': self._extract_mad_intelligent,
            'quantite_minimum': self._extract_quantite_minimum_intelligent,
            'quantites_estimees': self._extract_quantites_estimees_intelligent,
            'quantite_maximum': self._extract_quantite_maximum_intelligent,
            'criteres_economique': self._extract_criteres_economique_intelligent,
            'criteres_techniques': self._extract_criteres_techniques_intelligent,
            'autres_criteres': self._extract_autres_criteres_intelligent,
            'rse': self._extract_rse_intelligent,
            'contribution_fournisseur': self._extract_contribution_fournisseur_intelligent,
            'attributaire': self._extract_attributaire_intelligent,
            'produit_retenu': self._extract_produit_retenu_intelligent,
            'infos_complementaires': self._extract_infos_complementaires_intelligent,
            'remarques': self._extract_remarques_intelligent,
            'notes_acheteur_procedure': self._extract_notes_acheteur_procedure_intelligent,
            'notes_acheteur_fournisseur': self._extract_notes_acheteur_fournisseur_intelligent,
            'notes_acheteur_positionnement': self._extract_notes_acheteur_positionnement_intelligent,
            'note_veille': self._extract_note_veille_intelligent
        }
    
    def _analyze_document_context(self, text: str) -> Dict[str, Any]:
        """Analyse le contexte du document pour une extraction intelligente"""
        context = {
            'document_type': 'appel_offres',
            'sections_found': [],
            'language': 'fr',
            'has_financial_info': False,
            'has_temporal_info': False,
            'has_technical_info': False,
            'complexity_level': 'medium'
        }
        
        text_lower = text.lower()
        
        # Détecter le type de document
        for doc_type, keywords in self.context_analyzer['document_types'].items():
            if any(keyword in text_lower for keyword in keywords):
                context['document_type'] = doc_type
                break
        
        # Détecter les sections présentes
        for section, keywords in self.context_analyzer['sections'].items():
            if any(keyword in text_lower for keyword in keywords):
                context['sections_found'].append(section)
        
        # Analyser la complexité
        if 'financier' in context['sections_found']:
            context['has_financial_info'] = True
        if 'temporel' in context['sections_found']:
            context['has_temporal_info'] = True
        if 'technique' in context['sections_found']:
            context['has_technical_info'] = True
        
        # Déterminer le niveau de complexité
        if len(context['sections_found']) >= 4:
            context['complexity_level'] = 'high'
        elif len(context['sections_found']) <= 2:
            context['complexity_level'] = 'low'
        
        return context
    
    def _extract_intelligent_data(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraction intelligente basée sur le contexte"""
        intelligent_data = {}
        
        # Utiliser les extracteurs intelligents pour chaque champ
        for field, extractor_func in self.intelligent_extractors.items():
            if field not in existing_data:  # Ne pas écraser les données existantes
                try:
                    value = extractor_func(text, context, existing_data)
                    if value:
                        intelligent_data[field] = value
                except Exception as e:
                    logger.warning(f"Erreur extraction intelligente {field}: {e}")
        
        return intelligent_data
    
    def _extract_dates_priority(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraction prioritaire des dates"""
        date_data = {}
        
        # Extraire les dates en priorité
        date_limite = self._extract_date_limite_intelligent(text, context, existing_data)
        if date_limite:
            date_data['date_limite'] = date_limite
        
        date_attribution = self._extract_date_attribution_intelligent(text, context, existing_data)
        if date_attribution:
            date_data['date_attribution'] = date_attribution
        
        return date_data
    
    def _deduce_missing_values(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Déduit les valeurs manquantes basées sur le contexte et les données existantes"""
        deduced_data = {}
        
        # Déduction de l'univers basé sur l'intitulé
        if 'univers' not in extracted_data and 'intitule_procedure' in extracted_data:
            univers = self._deduce_univers_from_title(extracted_data['intitule_procedure'])
            if univers:
                deduced_data['univers'] = univers
        
        # Déduction du segment basé sur l'univers
        if 'segment' not in extracted_data and 'univers' in extracted_data:
            segment = self._deduce_segment_from_univers(extracted_data['univers'])
            if segment:
                deduced_data['segment'] = segment
        
        # Déduction de la famille basée sur l'intitulé du lot
        if 'famille' not in extracted_data and 'intitule_lot' in extracted_data:
            famille = self._deduce_famille_from_lot_title(extracted_data['intitule_lot'])
            if famille:
                deduced_data['famille'] = famille
        
        # Déduction du statut basé sur les dates
        if 'statut' not in extracted_data:
            statut = self._deduce_statut_from_dates(extracted_data, context)
            if statut:
                deduced_data['statut'] = statut
        
        # Déduction du type de procédure
        if 'type_procedure' not in extracted_data and context['document_type']:
            type_proc = self._deduce_type_procedure_from_context(context)
            if type_proc:
                deduced_data['type_procedure'] = type_proc
        
        return deduced_data
    
    def _enrich_with_generated_data(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichit les données avec des valeurs générées intelligemment"""
        enriched_data = extracted_data.copy()
        
        # Générer des mots-clés basés sur l'intitulé
        if 'mots_cles' not in enriched_data and 'intitule_procedure' in enriched_data:
            mots_cles = self._generate_mots_cles(enriched_data['intitule_procedure'])
            if mots_cles:
                enriched_data['mots_cles'] = mots_cles
        
        # Générer des informations complémentaires
        if 'infos_complementaires' not in enriched_data:
            infos = self._generate_infos_complementaires(extracted_data, context)
            if infos:
                enriched_data['infos_complementaires'] = infos
        
        return enriched_data
    
    def get_extraction_report(self, original_data: Dict[str, Any], improved_data: Dict[str, Any]) -> str:
        """Génère un rapport d'amélioration de l'extraction"""
        report = "🔧 **Rapport d'amélioration de l'extraction**\n\n"
        
        # Comparer les données
        for field in improved_data:
            original_value = original_data.get(field, "Non trouvé")
            improved_value = improved_data[field]
            
            report += f"**{field}**:\n"
            report += f"- Avant: {original_value}\n"
            report += f"- Après: {improved_value}\n"
            report += f"- Amélioration: {'✅' if improved_value != original_value else '➖'}\n\n"
        
        # Statistiques
        total_fields = len(improved_data)
        improved_fields = sum(1 for field in improved_data if field in original_data and improved_data[field] != original_data[field])
        
        report += f"**Statistiques**:\n"
        report += f"- Total de champs: {total_fields}\n"
        report += f"- Champs améliorés: {improved_fields}\n"
        report += f"- Taux d'amélioration: {(improved_fields/total_fields*100):.1f}%\n"
        
        return report
    
    # ===== EXTRACTEURS INTELLIGENTS POUR CHAQUE COLONNE =====
    
    def _extract_mots_cles_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente des mots-clés"""
        # Essayer d'abord avec l'intitulé de procédure
        if 'intitule_procedure' in existing_data and existing_data['intitule_procedure']:
            return self._generate_mots_cles_improved(existing_data['intitule_procedure'])
        
        # Essayer avec l'intitulé du lot
        if 'intitule_lot' in existing_data and existing_data['intitule_lot']:
            return self._generate_mots_cles_improved(existing_data['intitule_lot'])
        
        # Essayer avec le texte complet
        if text:
            return self._generate_mots_cles_improved(text[:500])  # Prendre les 500 premiers caractères
        
        return None
    
    def _extract_univers_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente de l'univers"""
        # Patterns pour détecter l'univers
        univers_patterns = {
            'Médical': ['médical', 'medical', 'santé', 'sante', 'hôpital', 'hopital', 'clinique', 'pharmacie', 'laboratoire', 'soins', 'diagnostic', 'thérapie', 'therapie'],
            'Informatique': ['informatique', 'informatique', 'système', 'systeme', 'logiciel', 'logiciel', 'données', 'donnees', 'numérique', 'numerique', 'digital', 'cyber', 'réseau', 'reseau'],
            'Mobilier': ['mobilier', 'mobilier', 'bureau', 'bureau', 'siège', 'siege', 'table', 'chaise', 'armoire', 'armoire', 'étagère', 'etagere'],
            'Équipement': ['équipement', 'equipement', 'matériel', 'materiel', 'machine', 'outil', 'véhicule', 'vehicule', 'engin', 'appareil']
        }
        
        text_lower = text.lower()
        for univers, keywords in univers_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return univers
        
        return None
    
    def _extract_segment_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente du segment"""
        if 'univers' in existing_data:
            return self._deduce_segment_from_univers(existing_data['univers'])
        return None
    
    def _extract_famille_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente de la famille"""
        # Essayer d'abord avec l'intitulé du lot
        if 'intitule_lot' in existing_data and existing_data['intitule_lot']:
            return self._deduce_famille_improved(existing_data['intitule_lot'])
        
        # Essayer avec l'intitulé de procédure
        if 'intitule_procedure' in existing_data and existing_data['intitule_procedure']:
            return self._deduce_famille_improved(existing_data['intitule_procedure'])
        
        # Essayer avec le texte complet
        if text:
            return self._deduce_famille_improved(text[:500])  # Prendre les 500 premiers caractères
        
        return None
    
    def _extract_statut_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente du statut"""
        statut_patterns = {
            'En cours': ['en cours', 'en_cours', 'en_cours', 'ouvert', 'ouvert', 'actif', 'actif'],
            'Attribué': ['attribué', 'attribue', 'attribué', 'gagné', 'gagne', 'retenu', 'retenu'],
            'Clos': ['clos', 'clos', 'fermé', 'ferme', 'terminé', 'termine', 'fini', 'fini'],
            'Annulé': ['annulé', 'annule', 'annulé', 'abandonné', 'abandonne', 'supprimé', 'supprime']
        }
        
        text_lower = text.lower()
        for statut, keywords in statut_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return statut
        
        # Ne PAS retourner de valeur par défaut - laisser None si pas trouvé
        return None
    
    def _extract_groupement_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente du groupement"""
        groupement_patterns = {
            'RESAH': ['resah', 'RESAH', 'Réseau', 'Reseau'],
            'UNIHA': ['uniha', 'UNIHA', 'Union', 'Union'],
            'UGAP': ['ugap', 'UGAP', 'Union', 'Union'],
            'CAIH': ['caih', 'CAIH', 'Centre', 'Centre']
        }
        
        text_lower = text.lower()
        for groupement, keywords in groupement_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return groupement
        
        return None
    
    def _extract_reference_procedure_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente de la référence de procédure"""
        # Patterns universels pour les références (du plus spécifique au plus générique)
        ref_patterns = [
            # Format RESAH standard
            r'N°(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',
            r'(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',
            r'Référence[:\s]*(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',
            r'Code[:\s]*(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',
            r'N°\s*(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',
            # Formats alternatifs
            r'N°\s*(\d{4}[A-Z]\d{3}\d{3}\d{3})',
            r'(\d{4}[A-Z]\d{3}\d{3}\d{3})',
            # Format M_XXXX et similaires
            r'N°\s*([A-Z]\d{1,4})',
            r'([A-Z]\d{1,4})',
            r'([A-Z]_\d{1,4})',
            r'N°\s*([A-Z]_\d{1,4})',
            # Formats avec préfixes
            r'N°\s*([A-Z]{2,4}[-_]?\d{1,4})',
            r'([A-Z]{2,4}[-_]?\d{1,4})',
            r'([A-Z]{2,4}[-_]\d{1,4})',
            # Formats génériques
            r'(\d{4}-[A-Z]\d{2,3}-\d{2,3}-\d{2,3})',
            r'(\d{4}[A-Z]\d{2,3}\d{2,3}\d{2,3})',
            r'([A-Z]{2,4}[\-\/]?\d{4}[\-\/]?\d{2,4})',
            r'(\d{4}[\-\/][A-Z]\d{2,3})',
            # Formats génériques universels
            r'N°\s*([A-Z0-9]{3,15})',
            r'([A-Z0-9]{3,15})',
            # Patterns avec contexte
            r'(?:référence|reference|ref|n°|no)[\s\w]*[:]\s*([A-Z0-9_\-]{2,15})',
            r'(?:procédure|procedure)[\s\w]*[:]\s*([A-Z0-9_\-]{2,15})',
            r'(?:marché|marche)[\s\w]*[:]\s*([A-Z0-9_\-]{2,15})',
            r'(?:consultation)[\s\w]*[:]\s*([A-Z0-9_\-]{2,15})'
        ]
        
        for pattern in ref_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                ref = matches[0].strip()
                # Valider que c'est une référence valide
                if (len(ref) >= 2 and 
                    not ref.lower() in ['cha', 'the', 'and', 'for', 'des', 'les', 'du', 'de', 'la', 'sur', 'par', 'avec', 'dans', 'pour', 'sur', 'page'] and
                    not ref.isdigit() and  # Éviter les numéros de page
                    not re.match(r'^\d{1,2}$', ref) and  # Éviter les petits nombres
                    not re.match(r'^[a-z]+$', ref) and  # Éviter les mots en minuscules
                    not ref.startswith('http') and  # Éviter les URLs
                    not ref.startswith('www') and  # Éviter les URLs
                    not ref.startswith('mailto')):  # Éviter les emails
                    return ref
        
        return None
    
    def _extract_type_procedure_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente du type de procédure"""
        type_patterns = {
            'Appel d\'offres ouvert': ['appel d\'offres ouvert', 'ao ouvert', 'ouvert'],
            'Appel d\'offres restreint': ['appel d\'offres restreint', 'ao restreint', 'restreint'],
            'Consultation': ['consultation', 'marché de services', 'prestation'],
            'Achat direct': ['achat direct', 'commande', 'bon de commande'],
            'Convention': ['convention', 'accord', 'partenariat']
        }
        
        text_lower = text.lower()
        for type_proc, keywords in type_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return type_proc
        
        # Ne PAS retourner de valeur par défaut - laisser None si pas trouvé
        return None
    
    def _extract_mono_multi_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente mono/multi-attributif"""
        # D'abord, vérifier nbr_lots pour inférer (c'est une inférence valide, pas une valeur par défaut)
        if 'nbr_lots' in existing_data and existing_data['nbr_lots']:
            try:
                nbr_lots = int(existing_data['nbr_lots']) if str(existing_data['nbr_lots']).isdigit() else 1
                if nbr_lots > 1:
                    return 'Multi-attributif'
                elif nbr_lots == 1:
                    return 'Mono-attributif'
            except:
                pass
        
        # Chercher dans le texte
        text_lower = text.lower()
        if 'multi' in text_lower or 'plusieurs' in text_lower or 'alloti' in text_lower or 'lotissement' in text_lower:
            return 'Multi-attributif'
        elif 'mono' in text_lower or 'unique' in text_lower or 'unitaire' in text_lower:
            return 'Mono-attributif'
        
        # Ne PAS retourner de valeur par défaut - laisser None si pas trouvé
        return None
    
    def _extract_execution_marche_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente de l'exécution du marché"""
        execution_patterns = {
            'Travaux': ['travaux', 'construction', 'bâtiment', 'batiment', 'infrastructure'],
            'Services': ['services', 'prestation', 'maintenance', 'formation', 'conseil'],
            'Fournitures': ['fourniture', 'fourniture', 'matériel', 'materiel', 'équipement', 'equipement']
        }
        
        text_lower = text.lower()
        for execution, keywords in execution_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return execution
        
        # Ne PAS retourner de valeur par défaut - laisser None si pas trouvé
        return None
    
    def _extract_date_limite_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente de la date limite"""
        # Patterns améliorés pour les dates
        date_patterns = [
            # Patterns avec contexte spécifique pour date limite
            r'(?:date|échéance|clôture)[\s\w]*(?:limite|remise|offres)[\s\w]*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:date|échéance|clôture)[\s\w]*(?:limite|remise|offres)[\s\w]*[:]\s*(\d{4}-\d{2}-\d{2})',
            r'(?:date|échéance|clôture)[\s\w]*(?:limite|remise|offres)[\s\w]*[:]\s*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
            # Patterns plus permissifs
            r'(?:date|échéance|clôture)[\s\w]*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:date|échéance|clôture)[\s\w]*[:]\s*(\d{4}-\d{2}-\d{2})',
            # Patterns génériques (plus permissifs)
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})',
            # Patterns avec format français
            r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                date_str = matches[0]
                # Valider que c'est une date valide
                if self._is_valid_date_format(date_str):
                    return date_str
        
        # Si aucun pattern spécifique ne fonctionne, essayer les patterns génériques
        generic_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in generic_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                date_str = matches[0]
                if self._is_valid_date_format(date_str):
                    return date_str
        
        return None
    
    def _extract_date_attribution_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente de la date d'attribution"""
        attribution_patterns = [
            # Patterns avec contexte spécifique
            r'(?:attribution|attribué)[\s\w]*(?:marché|marche|contrat)[\s\w]*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:attribution|attribué)[\s\w]*(?:marché|marche|contrat)[\s\w]*[:]\s*(\d{4}-\d{2}-\d{2})',
            r'(?:attribution|attribué)[\s\w]*(?:marché|marche|contrat)[\s\w]*[:]\s*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
            # Patterns avec contexte général
            r'(?:attribution|attribué)[\s\w]*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:attribution|attribué)[\s\w]*[:]\s*(\d{4}-\d{2}-\d{2})',
            # Patterns génériques
            r'(?:attribution|attribué)[\s\w]*[:]\s*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})'
        ]
        
        for pattern in attribution_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                date_str = matches[0]
                # Valider que c'est une date valide
                if self._is_valid_date_format(date_str):
                    return date_str
        
        return None
    
    def _extract_duree_marche_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[int]:
        """Extraction intelligente de la durée du marché"""
        duree_patterns = [
            r'(?:durée|duree|période)[\s\w]*[:]\s*(\d+)\s*(?:mois|mois)',
            r'(\d+)\s*(?:mois|mois)[\s\w]*(?:durée|duree|marché|marche)'
        ]
        
        for pattern in duree_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except:
                    continue
        
        return None
    
    def _extract_reconduction_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente de la reconduction"""
        reconduction_patterns = {
            'Oui': ['reconduction', 'renouvelable', 'renouvelable', 'tacite', 'tacite'],
            'Non': ['sans reconduction', 'non reconduction', 'non renouvelable']
        }
        
        text_lower = text.lower()
        for reconduction, keywords in reconduction_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return reconduction
        
        # Ne PAS retourner de valeur par défaut
        return None
    
    def _extract_fin_sans_reconduction_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente de la fin sans reconduction"""
        if 'date_limite' in existing_data and 'duree_marche' in existing_data:
            try:
                from datetime import datetime, timedelta
                
                # Parser la date limite
                date_limite_str = existing_data['date_limite']
                date_limite = None
                
                # Essayer différents formats de date
                formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d %B %Y', '%d %b %Y']
                for fmt in formats:
                    try:
                        date_limite = datetime.strptime(date_limite_str, fmt)
                        break
                    except:
                        continue
                
                if date_limite and existing_data['duree_marche']:
                    duree_mois = int(existing_data['duree_marche'])
                    # Calcul plus précis : 30.44 jours par mois en moyenne
                    fin_date = date_limite + timedelta(days=int(duree_mois * 30.44))
                    return fin_date.strftime('%d/%m/%Y')
            except Exception as e:
                logger.warning(f"Erreur calcul fin sans reconduction: {e}")
        
        return None
    
    def _extract_fin_avec_reconduction_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente de la fin avec reconduction"""
        if 'fin_sans_reconduction' in existing_data and 'reconduction' in existing_data:
            if existing_data['reconduction'] == 'Oui':
                try:
                    from datetime import datetime, timedelta
                    
                    # Parser la fin sans reconduction
                    fin_sans_str = existing_data['fin_sans_reconduction']
                    fin_sans = None
                    
                    # Essayer différents formats de date
                    formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d %B %Y', '%d %b %Y']
                    for fmt in formats:
                        try:
                            fin_sans = datetime.strptime(fin_sans_str, fmt)
                            break
                        except:
                            continue
                    
                    if fin_sans:
                        # Calcul plus précis : +1 an exact
                        fin_avec = fin_sans + timedelta(days=365)
                        return fin_avec.strftime('%d/%m/%Y')
                except Exception as e:
                    logger.warning(f"Erreur calcul fin avec reconduction: {e}")
        
        return None
    
    def _extract_nbr_lots_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[int]:
        """Extraction intelligente du nombre de lots"""
        nbr_patterns = [
            r'(?:nombre|nb|nbr)[\s\w]*(?:lots|prestations)[\s\w]*[:]\s*(\d+)',
            r'(?:lots|prestations)[\s\w]*(?:nombre|nb|nbr)[\s\w]*[:]\s*(\d+)',
            r'(?:total)[\s\w]*(?:lots|prestations)[\s\w]*[:]\s*(\d+)'
        ]
        
        for pattern in nbr_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except:
                    continue
        
        # Ne PAS retourner de valeur par défaut
        return None
    
    def _extract_intitule_procedure_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente de l'intitulé de procédure"""
        # Patterns universels pour les intitulés de RC (du plus spécifique au plus générique)
        rc_patterns = [
            # Patterns spécifiques pour formation
            r'REALISATION DE PRESTATIONS DE FORMATION[^\n]*',
            r'PRESTATIONS DE FORMATION[^\n]*',
            r'FORMATION PROFESSIONNELLE[^\n]*',
            r'PRESTATIONS ASSOCIEES[^\n]*',
            # Patterns génériques pour prestations
            r'REALISATION[^\n]*',
            r'PRESTATIONS[^\n]*',
            r'FORMATION[^\n]*',
            r'SERVICES[^\n]*',
            r'TRAVAUX[^\n]*',
            r'FOURNITURES[^\n]*',
            r'ÉQUIPEMENTS[^\n]*',
            r'MATÉRIELS[^\n]*',
            # Patterns avec contexte
            r'OBJET[^\n]*',
            r'OBJET DE LA CONSULTATION[^\n]*',
            r'OBJET DU MARCHÉ[^\n]*',
            r'OBJET DE LA PROCÉDURE[^\n]*',
            # Patterns génériques pour titres
            r'[A-Z]{3,}[^\n]*',
            r'[A-Z][A-Z\s]{10,50}[^\n]*'
        ]
        
        for pattern in rc_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                intitule = matches[0].strip()
                # Post-traitement : couper au premier saut de ligne ou point
                intitule = intitule.split('\n')[0].split('.')[0].strip()
                # Validation améliorée
                if (len(intitule) >= 10 and len(intitule) <= 200 and
                    not intitule.startswith('sur ') and  # Éviter "sur 16"
                    not intitule.startswith('REGLEMENT') and  # Éviter les en-têtes
                    not intitule.startswith('RÈGLEMENT') and
                    not intitule.startswith('(RC)') and
                    not intitule.startswith('N°') and
                    not intitule.startswith('Article') and
                    not intitule.startswith('Page') and
                    not re.match(r'^\d+$', intitule) and  # Éviter les numéros
                    not re.match(r'^\d+\s+sur\s+\d+$', intitule)):  # Éviter "1 sur 16"
                    return intitule
        
        # Fallback vers la méthode améliorée
        return self._extract_intitule_procedure_improved(text, context, existing_data)
    
    def _extract_lot_numero_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[int]:
        """Extraction intelligente du numéro de lot"""
        # Chercher d'abord dans la section des lots
        lots_section = self._extract_lots_section(text)
        if lots_section:
            # Patterns universels pour extraire les numéros de lots
            lot_patterns = [
                # Format standard avec espaces
                r'(\d+)\s+[A-Z][A-Z\s/]+?\s+\d{1,3}(?:\s\d{3})*\s+\d{1,3}(?:\s\d{3})*',
                # Format avec unités monétaires
                r'(\d+)\s+[A-Z][A-Z\s/]+?\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
                # Format flexible
                r'(\d+)\s+[A-Z][A-Z\s/]+?\s+\d+(?:[.,]\d+)?\s*[kKmM]?€?\s+\d+(?:[.,]\d+)?\s*[kKmM]?€?',
                # Format simple
                r'(\d+)\s+[A-Z][A-Z\s/]+?\s+\d+(?:[.,]\d+)?\s+\d+(?:[.,]\d+)?',
                # Format très flexible
                r'(\d+)\s+[A-Z][A-Z\s/]+?\s+\d+(?:[.,]\d+)?\s*[kKmM]?\s+\d+(?:[.,]\d+)?\s*[kKmM]?',
                # Format avec séparateurs
                r'(\d+)\s*\|\s*[A-Z][A-Z\s/]+?\s*\|\s*\d+(?:[.,]\d+)?\s*\|\s*\d+(?:[.,]\d+)?',
                # Format avec tirets
                r'(\d+)\s+[A-Z][A-Z\s/]+?\s+-\s+\d+(?:[.,]\d+)?\s+-\s+\d+(?:[.,]\d+)?',
                # Format générique
                r'(\d+)\s+[A-Z][A-Z\s/]+?\s+[0-9,.\s€kKmM]+'
            ]
            
            for pattern in lot_patterns:
                matches = re.findall(pattern, lots_section, re.IGNORECASE | re.MULTILINE)
                if matches:
                    try:
                        return int(matches[0])
                    except:
                        continue
        
        # Fallback vers les patterns génériques
        lot_patterns = [
            r'(?:lot|prestation)[\s\w]*[:]\s*(\d+)',
            r'(?:n°|no)[\s\w]*[:]\s*(\d+)'
        ]
        
        for pattern in lot_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except:
                    continue
        
        # Ne PAS retourner de valeur par défaut
        return None
    
    def _extract_lots_section(self, text: str) -> Optional[str]:
        """Extraction de la section des lots"""
        # Chercher la section des lots avec des patterns universels
        lots_section_patterns = [
            # Patterns RESAH standard
            r'Allotissement[^\n]*montant estimatif[^\n]*montant maximum[^\n]*(.*?)(?=1\.3|Article|$)',
            r'Allotissement[^\n]*montant[^\n]*(.*?)(?=1\.3|Article|$)',
            r'Intitulé du lot[^\n]*(.*?)(?=1\.3|Article|$)',
            r'Allotissement[^\n]*(.*?)(?=1\.3|Article|$)',
            r'montant estimatif[^\n]*(.*?)(?=1\.3|Article|$)',
            # Patterns génériques
            r'LOTISSEMENT[^\n]*(.*?)(?=Article|$)',
            r'LOTS[^\n]*(.*?)(?=Article|$)',
            r'REPARTITION[^\n]*LOTS[^\n]*(.*?)(?=Article|$)',
            r'ALLOTISSEMENT[^\n]*(.*?)(?=Article|$)',
            r'Lot[^\n]*Intitulé[^\n]*(.*?)(?=Article|$)',
            r'Lot\s*N°[^\n]*(.*?)(?=Article|$)',
            r'Lot\s*N[^\n]*(.*?)(?=Article|$)',
            r'N°[^\n]*Intitulé[^\n]*(.*?)(?=Article|$)',
            r'Intitulé[^\n]*Montant[^\n]*(.*?)(?=Article|$)',
            r'Montant[^\n]*estimatif[^\n]*(.*?)(?=Article|$)',
            # Patterns avec séparateurs
            r'[^\n]*\|[^\n]*Intitulé[^\n]*\|[^\n]*Montant[^\n]*(.*?)(?=Article|$)',
            r'[^\n]*\|[^\n]*lot[^\n]*\|[^\n]*Montant[^\n]*(.*?)(?=Article|$)',
            # Patterns génériques pour tableaux
            r'(?:\d+\s+[A-Z][A-Z\s/]+?\s+\d{1,3}(?:\s\d{3})*\s+\d{1,3}(?:\s\d{3})*.*?)(?=Article|$)',
            r'(?:\d+\s+[A-Z][A-Z\s/]+?\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?).*?)(?=Article|$)'
        ]
        
        for pattern in lots_section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section = match.group(1)
                # Vérifier que la section contient des lots avec des patterns plus flexibles
                lot_patterns = [
                    r'\d+\s+[A-Z][A-Z\s/]+?\s+\d{1,3}(?:\s\d{3})*\s+\d{1,3}(?:\s\d{3})*',  # Format standard
                    r'\d+\s+[A-Z][A-Z\s/]+?\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)',  # Format avec unités
                    r'\d+\s+[A-Z][A-Z\s/]+?\s+\d+(?:[.,]\d+)?\s*[kKmM]?€?\s+\d+(?:[.,]\d+)?\s*[kKmM]?€?',  # Format flexible
                    r'\d+\s+[A-Z][A-Z\s/]+?\s+\d+(?:[.,]\d+)?\s+\d+(?:[.,]\d+)?',  # Format simple
                    r'\d+\s+[A-Z][A-Z\s/]+?\s+\d+(?:[.,]\d+)?\s*[kKmM]?\s+\d+(?:[.,]\d+)?\s*[kKmM]?'  # Format très flexible
                ]
                
                for lot_pattern in lot_patterns:
                    if re.search(lot_pattern, section, re.IGNORECASE | re.MULTILINE):
                        return section
        
        return None
    
    def _extract_intitule_lot_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction intelligente de l'intitulé du lot"""
        # Chercher d'abord dans la section des lots
        lots_section = self._extract_lots_section(text)
        if lots_section:
            # Patterns universels pour extraire les intitulés de lots
            intitule_patterns = [
                # Format standard avec espaces
                r'\d+\s+([A-Z][A-Z\s/]+?)\s+\d{1,3}(?:\s\d{3})*\s+\d{1,3}(?:\s\d{3})*',
                # Format avec unités monétaires
                r'\d+\s+([A-Z][A-Z\s/]+?)\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
                # Format flexible
                r'\d+\s+([A-Z][A-Z\s/]+?)\s+\d+(?:[.,]\d+)?\s*[kKmM]?€?\s+\d+(?:[.,]\d+)?\s*[kKmM]?€?',
                # Format simple
                r'\d+\s+([A-Z][A-Z\s/]+?)\s+\d+(?:[.,]\d+)?\s+\d+(?:[.,]\d+)?',
                # Format très flexible
                r'\d+\s+([A-Z][A-Z\s/]+?)\s+\d+(?:[.,]\d+)?\s*[kKmM]?\s+\d+(?:[.,]\d+)?\s*[kKmM]?',
                # Format avec séparateurs
                r'\d+\s*\|\s*([A-Z][A-Z\s/]+?)\s*\|\s*\d+(?:[.,]\d+)?\s*\|\s*\d+(?:[.,]\d+)?',
                # Format avec tirets
                r'\d+\s+([A-Z][A-Z\s/]+?)\s+-\s+\d+(?:[.,]\d+)?\s+-\s+\d+(?:[.,]\d+)?',
                # Format générique
                r'\d+\s+([A-Z][A-Z\s/]+?)\s+[0-9,.\s€kKmM]+'
            ]
            
            for pattern in intitule_patterns:
                matches = re.findall(pattern, lots_section, re.IGNORECASE | re.MULTILINE)
                if matches:
                    intitule = matches[0].strip()
                    # Nettoyer l'intitulé
                    intitule = re.sub(r'\s+', ' ', intitule)
                    # Enlever les caractères parasites
                    intitule = re.sub(r'[|]', '', intitule)
                    intitule = re.sub(r'[€$]', '', intitule)
                    intitule = re.sub(r'\s+', ' ', intitule).strip()
                    
                    if len(intitule) >= 5:  # Réduire la longueur minimale
                        return intitule
        
        # Fallback vers la méthode améliorée
        return self._extract_intitule_lot_improved(text, context, existing_data)
    
    def _extract_montant_global_estime_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[float]:
        """Extraction intelligente du montant global estimé"""
        # Chercher d'abord dans la section des lots
        lots_section = self._extract_lots_section(text)
        if lots_section:
            # Patterns universels pour extraire les montants estimatifs
            montant_patterns = [
                # Format standard avec espaces (corrigé)
                r'\d+\s+[A-Z][A-Z\s/]+?\s+(\d{1,3}(?:\s\d{3})*)\s+\d{1,3}(?:\s\d{3})*',
                # Format avec unités monétaires
                r'\d+\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
                # Format flexible
                r'\d+\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?)\s*[kKmM]?€?\s+\d+(?:[.,]\d+)?\s*[kKmM]?€?',
                # Format simple (corrigé)
                r'\d+\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?)\s+\d+(?:[.,]\d+)?',
                # Format très flexible
                r'\d+\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?)\s*[kKmM]?\s+\d+(?:[.,]\d+)?\s*[kKmM]?',
                # Format avec séparateurs
                r'\d+\s*\|\s*[A-Z][A-Z\s/]+?\s*\|\s*(\d+(?:[.,]\d+)?)\s*\|\s*\d+(?:[.,]\d+)?',
                # Format avec tirets
                r'\d+\s+[A-Z][A-Z\s/]+?\s+-\s+(\d+(?:[.,]\d+)?)\s+-\s+\d+(?:[.,]\d+)?',
                # Format générique
                r'\d+\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?)\s*[0-9,.\s€kKmM]+',
                # Format avec espaces dans les montants (nouveau)
                r'\d+\s+[A-Z][A-Z\s/]+?\s+(\d{1,3}(?:\s\d{3})*)\s+\d{1,3}(?:\s\d{3})*'
            ]
            
            for pattern in montant_patterns:
                matches = re.findall(pattern, lots_section, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # Calculer le total des montants estimatifs
                    total = 0
                    for montant_str in matches:
                        try:
                            # Nettoyer le montant
                            montant_clean = montant_str.replace(' ', '').replace(',', '.')
                            
                            # Gérer les unités
                            if 'k' in montant_clean.lower():
                                montant = float(montant_clean.lower().replace('k', '')) * 1000
                            elif 'm' in montant_clean.lower():
                                montant = float(montant_clean.lower().replace('m', '')) * 1000000
                            else:
                                montant = float(montant_clean)
                            
                            total += montant
                        except:
                            continue
                    
                    if total > 0:
                        return total
        
        # Fallback vers les patterns génériques
        montant_patterns = [
            r'(?:montant|budget|prix)[\s\w]*[:]\s*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
            r'(?:budget|montant)[\s\w]*[:]\s*(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?)'
        ]
        
        for pattern in montant_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    montant_str = matches[0].replace('€', '').replace(',', '.').replace(' ', '').strip()
                    if 'k' in montant_str.lower():
                        return float(montant_str.lower().replace('k', '')) * 1000
                    elif 'm' in montant_str.lower():
                        return float(montant_str.lower().replace('m', '')) * 1000000
                    else:
                        return float(montant_str)
                except:
                    continue
        
        return None
    
    def _extract_montant_global_maxi_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[float]:
        """Extraction intelligente du montant global maximum"""
        max_patterns = [
            r'(?:maximum|maxi|plafond)[\s\w]*[:]\s*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
            r'(?:budget|montant)[\s\w]*(?:maximum|maxi|plafond)[\s\w]*[:]\s*(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?)'
        ]
        
        for pattern in max_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    montant_str = matches[0].replace('€', '').replace(',', '.').replace(' ', '').strip()
                    if 'k' in montant_str.lower():
                        return float(montant_str.lower().replace('k', '')) * 1000
                    elif 'm' in montant_str.lower():
                        return float(montant_str.lower().replace('m', '')) * 1000000
                    else:
                        return float(montant_str)
                except:
                    continue
        
        return None
    
    # ===== MÉTHODES DE DÉDUCTION INTELLIGENTE =====
    
    def _deduce_univers_from_title(self, title: str) -> Optional[str]:
        """Déduit l'univers basé sur le titre"""
        if not title:
            return None
            
        title_lower = title.lower()
        
        univers_keywords = {
            'MÉDICAL': ['médical', 'medical', 'santé', 'sante', 'hôpital', 'hopital', 'clinique', 'pharmacie', 'laboratoire', 'soins', 'diagnostic', 'thérapie', 'therapie', 'congélateur', 'congelateur', 'réfrigérateur', 'refrigerateur', 'biomédical', 'biomedical'],
            'INFORMATIQUE': ['informatique', 'informatique', 'système', 'systeme', 'logiciel', 'logiciel', 'données', 'donnees', 'numérique', 'numerique', 'digital', 'cyber', 'réseau', 'reseau', 'serveur', 'serveur', 'application', 'plateforme'],
            'SERVICE': ['service', 'prestation', 'formation', 'conseil', 'assistance', 'support', 'accompagnement', 'intervention', 'accompagnement', 'développement', 'developpement'],
            'ÉQUIPEMENT': ['équipement', 'equipement', 'matériel', 'materiel', 'machine', 'outil', 'véhicule', 'vehicule', 'engin', 'appareil', 'fourniture', 'produit'],
            'MOBILIER': ['mobilier', 'mobilier', 'bureau', 'bureau', 'siège', 'siege', 'table', 'chaise', 'armoire', 'armoire', 'étagère', 'etagere', 'ameublement'],
            'VÉHICULES': ['véhicule', 'vehicule', 'transport', 'logistique', 'ambulance', 'camion', 'voiture', 'engin'],
            'CONSOMMABLES': ['consommable', 'papier', 'encre', 'cartouche', 'fourniture', 'bureau', 'hygiène', 'hygiene', 'désinfectant', 'desinfectant']
        }
        
        # Compter les occurrences pour chaque univers
        univers_scores = {}
        for univers, keywords in univers_keywords.items():
            score = sum(1 for keyword in keywords if keyword in title_lower)
            if score > 0:
                univers_scores[univers] = score
        
        # Retourner l'univers avec le score le plus élevé
        if univers_scores:
            return max(univers_scores, key=univers_scores.get)
        
        # Déduction basée sur le contexte
        if 'formation' in title_lower or 'prestation' in title_lower:
            return 'SERVICE'
        elif 'informatique' in title_lower or 'numérique' in title_lower:
            return 'INFORMATIQUE'
        elif 'médical' in title_lower or 'santé' in title_lower:
            return 'MÉDICAL'
        elif 'fourniture' in title_lower or 'matériel' in title_lower:
            return 'ÉQUIPEMENT'
        
        # Ne PAS retourner de valeur par défaut
        return None
    
    def _deduce_segment_from_univers(self, univers: str) -> Optional[str]:
        """Déduit le segment basé sur l'univers"""
        if not univers:
            return None
            
        segment_mapping = {
            'MÉDICAL': 'E-SANTÉ',
            'INFORMATIQUE': 'PRESTATION INFORMATIQUE',
            'SERVICE': 'PRESTATION INTELLECTUELLE',
            'ÉQUIPEMENT': 'EQUIPEMENT GÉNÉRAL',
            'MOBILIER': 'MOBILIER DE BUREAU',
            'VÉHICULES': 'VÉHICULES',
            'CONSOMMABLES': 'CONSOMMABLES DE BUREAU'
        }
        
        return segment_mapping.get(univers.upper())
    
    def _deduce_famille_from_lot_title(self, lot_title: str) -> Optional[str]:
        """Déduit la famille basée sur l'intitulé du lot"""
        title_lower = lot_title.lower()
        
        famille_keywords = {
            'Fourniture': ['fourniture', 'fourniture', 'achat', 'achat', 'matériel', 'materiel', 'équipement', 'equipement'],
            'Services': ['service', 'service', 'maintenance', 'maintenance', 'formation', 'formation', 'conseil', 'conseil'],
            'Travaux': ['travaux', 'travaux', 'construction', 'construction', 'bâtiment', 'batiment', 'infrastructure', 'infrastructure']
        }
        
        for famille, keywords in famille_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return famille
        
        # Ne PAS retourner de valeur par défaut
        return None
    
    def _deduce_statut_from_dates(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Déduit le statut basé sur les dates"""
        from datetime import datetime
        
        if 'date_limite' in extracted_data:
            try:
                date_limite = datetime.strptime(extracted_data['date_limite'], '%d/%m/%Y')
                today = datetime.now()
                
                if date_limite < today:
                    return 'Clos'
                else:
                    return 'En cours'
            except:
                pass
        
        # Ne PAS retourner de valeur par défaut - laisser None si pas trouvé
        return None
    
    def _deduce_type_procedure_from_context(self, context: Dict[str, Any]) -> Optional[str]:
        """Déduit le type de procédure basé sur le contexte"""
        doc_type = context.get('document_type', 'appel_offres')
        
        type_mapping = {
            'appel_offres': 'Appel d\'offres ouvert',
            'consultation': 'Consultation',
            'achat_direct': 'Achat direct',
            'convention': 'Convention'
        }
        
        return type_mapping.get(doc_type)
    
    def _generate_mots_cles(self, title: str) -> Optional[str]:
        """Génère des mots-clés basés sur le titre"""
        if not title:
            return None
        
        # Extraire les mots significatifs
        words = re.findall(r'\b\w{4,}\b', title.lower())
        
        # Filtrer les mots vides
        stop_words = {'procédure', 'procedure', 'appel', 'offres', 'consultation', 'marché', 'marche', 'fourniture', 'service', 'travaux'}
        keywords = [word for word in words if word not in stop_words]
        
        # Limiter à 5 mots-clés maximum
        return ', '.join(keywords[:5]) if keywords else None
    
    def _generate_infos_complementaires(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Génère des informations complémentaires"""
        infos = []
        
        if context.get('has_financial_info'):
            infos.append('Informations financières disponibles')
        
        if context.get('has_temporal_info'):
            infos.append('Dates et durées spécifiées')
        
        if context.get('has_technical_info'):
            infos.append('Critères techniques détaillés')
        
        if context.get('complexity_level') == 'high':
            infos.append('Marché complexe multi-lots')
        
        return '; '.join(infos) if infos else None
    
    # ===== EXTRACTEURS POUR LES AUTRES COLONNES =====
    
    def _extract_achat_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        return 'Oui' if 'achat' in text.lower() else 'Non'
    
    def _extract_credit_bail_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        return 'Oui' if 'crédit bail' in text.lower() or 'credit bail' in text.lower() else 'Non'
    
    def _extract_credit_bail_duree_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[int]:
        if 'crédit bail' in text.lower() or 'credit bail' in text.lower():
            matches = re.findall(r'(\d+)\s*(?:ans?|années?)', text, re.IGNORECASE)
            if matches:
                return int(matches[0])
        return None
    
    def _extract_location_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        return 'Oui' if 'location' in text.lower() else 'Non'
    
    def _extract_location_duree_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[int]:
        if 'location' in text.lower():
            matches = re.findall(r'(\d+)\s*(?:ans?|années?)', text, re.IGNORECASE)
            if matches:
                return int(matches[0])
        return None
    
    def _extract_mad_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        return 'Oui' if 'mad' in text.lower() or 'mise à disposition' in text.lower() else 'Non'
    
    def _extract_quantite_minimum_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[int]:
        patterns = [
            r'(?:quantité|quantite)[\s\w]*(?:minimum|min)[\s\w]*[:]\s*(\d+)',
            r'(?:minimum|min)[\s\w]*(?:quantité|quantite)[\s\w]*[:]\s*(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except:
                    continue
        
        return None
    
    def _extract_quantites_estimees_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[int]:
        patterns = [
            r'(?:quantité|quantite)[\s\w]*(?:estimée|estimee|prévue|prevue)[\s\w]*[:]\s*(\d+)',
            r'(?:estimée|estimee|prévue|prevue)[\s\w]*(?:quantité|quantite)[\s\w]*[:]\s*(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except:
                    continue
        
        return None
    
    def _extract_quantite_maximum_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[int]:
        patterns = [
            r'(?:quantité|quantite)[\s\w]*(?:maximum|max)[\s\w]*[:]\s*(\d+)',
            r'(?:maximum|max)[\s\w]*(?:quantité|quantite)[\s\w]*[:]\s*(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except:
                    continue
        
        return None
    
    def _extract_criteres_economique_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        patterns = [
            r'(?:critère|critere)[\s\w]*(?:économique|economique|prix)[\s\w]*[:]\s*([^.\n]{10,100})',
            r'(?:économique|economique|prix)[\s\w]*(?:critère|critere)[\s\w]*[:]\s*([^.\n]{10,100})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_criteres_techniques_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        patterns = [
            r'(?:critère|critere)[\s\w]*(?:technique|technique)[\s\w]*[:]\s*([^.\n]{10,100})',
            r'(?:technique|technique)[\s\w]*(?:critère|critere)[\s\w]*[:]\s*([^.\n]{10,100})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_autres_criteres_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        patterns = [
            r'(?:autre|autres)[\s\w]*(?:critère|critere)[\s\w]*[:]\s*([^.\n]{10,100})',
            r'(?:critère|critere)[\s\w]*(?:autre|autres)[\s\w]*[:]\s*([^.\n]{10,100})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_rse_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        return 'Oui' if 'rse' in text.lower() or 'responsabilité sociale' in text.lower() else 'Non'
    
    def _extract_contribution_fournisseur_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        return 'Oui' if 'contribution' in text.lower() or 'participation' in text.lower() else 'Non'
    
    def _extract_attributaire_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        patterns = [
            r'(?:attributaire|gagnant|retenu)[\s\w]*[:]\s*([^.\n]{3,50})',
            r'(?:gagnant|retenu)[\s\w]*(?:attributaire)[\s\w]*[:]\s*([^.\n]{3,50})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_produit_retenu_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        patterns = [
            r'(?:produit|solution)[\s\w]*(?:retenu|retenu)[\s\w]*[:]\s*([^.\n]{5,100})',
            r'(?:retenu|retenu)[\s\w]*(?:produit|solution)[\s\w]*[:]\s*([^.\n]{5,100})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_infos_complementaires_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        patterns = [
            r'(?:information|info)[\s\w]*(?:complémentaire|complementaire)[\s\w]*[:]\s*([^.\n]{10,200})',
            r'(?:complémentaire|complementaire)[\s\w]*(?:information|info)[\s\w]*[:]\s*([^.\n]{10,200})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_remarques_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        patterns = [
            r'(?:remarque|note|observation)[\s\w]*[:]\s*([^.\n]{10,200})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_notes_acheteur_procedure_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        patterns = [
            r'(?:note|avis)[\s\w]*(?:acheteur|acheteur)[\s\w]*(?:procédure|procedure)[\s\w]*[:]\s*([^.\n]{10,200})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_notes_acheteur_fournisseur_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        patterns = [
            r'(?:note|avis)[\s\w]*(?:acheteur|acheteur)[\s\w]*(?:fournisseur|fournisseur)[\s\w]*[:]\s*([^.\n]{10,200})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_notes_acheteur_positionnement_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        patterns = [
            r'(?:note|avis)[\s\w]*(?:acheteur|acheteur)[\s\w]*(?:positionnement|positionnement)[\s\w]*[:]\s*([^.\n]{10,200})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_note_veille_intelligent(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        patterns = [
            r'(?:note|avis)[\s\w]*(?:veille|veille)[\s\w]*[:]\s*([^.\n]{10,200})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """Valide le format d'une date"""
        try:
            from datetime import datetime
            
            # Essayer différents formats de date
            formats = [
                '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', 
                '%d %B %Y', '%d %b %Y', '%d/%m/%y', '%d-%m-%y'
            ]
            
            for fmt in formats:
                try:
                    datetime.strptime(date_str, fmt)
                    return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def _extract_intitule_procedure_improved(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction améliorée de l'intitulé de procédure"""
        # Patterns spécifiques pour les règlements de consultation (priorité absolue)
        rc_patterns = [
            r'REALISATION DE PRESTATIONS DE FORMATION[^\n]*',
            r'PRESTATIONS DE FORMATION[^\n]*',
            r'FORMATION PROFESSIONNELLE[^\n]*',
            r'PRESTATIONS ASSOCIEES[^\n]*'
        ]
        
        for pattern in rc_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                intitule = matches[0].strip()
                if self._is_valid_intitule(intitule):
                    return intitule
        
        # Patterns spécifiques pour l'intitulé de procédure (priorité aux patterns avec "procédure")
        patterns = [
            # Patterns avec contexte spécifique et fin de ligne stricte
            r'(?:intitulé|intitule|titre|objet)[\s\w]*(?:procédure|procedure)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            r'(?:procédure|procedure)[\s\w]*(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            # Patterns avec contexte général et fin de ligne stricte
            r'(?:procédure|procedure)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            # Patterns avec contexte d'appel d'offres et fin de ligne stricte
            r'(?:appel|offre|consultation)[\s\w]*(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            r'(?:appel|offre|consultation)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            # Patterns avec contexte de marché et fin de ligne stricte
            r'(?:marché|marche)[\s\w]*(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            r'(?:marché|marche)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                intitule = matches[0].strip()
                # Valider que c'est un intitulé valide
                if self._is_valid_intitule(intitule):
                    return intitule
        
        # Si aucun pattern spécifique ne fonctionne, essayer les patterns génériques
        # mais exclure ceux qui contiennent "lot" ou "prestation"
        generic_patterns = [
            r'(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            r'(?:procédure|procedure)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)'
        ]
        
        for pattern in generic_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches:
                    intitule = match.strip()
                    # Exclure les intitulés qui contiennent "lot" ou "prestation"
                    if 'lot' not in intitule.lower() and 'prestation' not in intitule.lower():
                        if self._is_valid_intitule(intitule):
                            return intitule
        
        return None
    
    def _extract_intitule_lot_improved(self, text: str, context: Dict[str, Any], existing_data: Dict[str, Any]) -> Optional[str]:
        """Extraction améliorée de l'intitulé du lot"""
        # Patterns spécifiques pour l'intitulé du lot (priorité aux patterns avec "lot")
        patterns = [
            # Patterns avec contexte spécifique et fin de ligne stricte
            r'(?:intitulé|intitule|titre|objet)[\s\w]*(?:lot|prestation)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            r'(?:lot|prestation)[\s\w]*(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            # Patterns avec contexte général et fin de ligne stricte
            r'(?:lot|prestation)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            # Patterns avec numéro de lot et fin de ligne stricte
            r'(?:lot|prestation)[\s\w]*(?:n°|no|numéro|numero)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            r'(?:n°|no|numéro|numero)[\s\w]*(?:lot|prestation)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                intitule = matches[0].strip()
                # Valider que c'est un intitulé valide
                if self._is_valid_intitule(intitule):
                    return intitule
        
        # Si aucun pattern spécifique ne fonctionne, essayer les patterns génériques
        # mais privilégier ceux qui contiennent "lot" ou "prestation"
        generic_patterns = [
            r'(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
            r'(?:lot|prestation)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)'
        ]
        
        for pattern in generic_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches:
                    intitule = match.strip()
                    # Privilégier les intitulés qui contiennent "lot" ou "prestation"
                    if 'lot' in intitule.lower() or 'prestation' in intitule.lower():
                        if self._is_valid_intitule(intitule):
                            return intitule
        
        return None
    
    def _is_valid_intitule(self, intitule: str) -> bool:
        """Valide qu'un intitulé est valide"""
        if not intitule or len(intitule.strip()) < 5:
            return False
        
        intitule = intitule.strip()
        
        # Vérifier qu'il ne contient pas de patterns interdits
        forbidden_patterns = [
            r'^[.,\s]+$',  # Que des points, virgules ou espaces
            r'^[\[\]()]+$',  # Que des crochets ou parenthèses
            r'^\.+$',  # Que des points
            r'^[^a-zA-Z]',  # Ne commence pas par une lettre
            r'[\[\]]'  # Contient des crochets
        ]
        
        for pattern in forbidden_patterns:
            if re.match(pattern, intitule):
                return False
        
        # Vérifier qu'il contient des mots significatifs (au moins 1 mot de 3+ caractères)
        words = re.findall(r'\b\w{3,}\b', intitule.lower())
        if len(words) < 1:
            return False
        
        # Vérifier qu'il ne contient pas trop de texte (limiter à 200 caractères)
        if len(intitule) > 200:
            return False
        
        # Accepter les intitulés de règlements de consultation
        if any(keyword in intitule.upper() for keyword in ['REALISATION', 'PRESTATIONS', 'FORMATION', 'PROFESSIONNELLE']):
            return True
        
        return True
    
    def _generate_mots_cles_improved(self, title: str) -> Optional[str]:
        """Génération améliorée des mots-clés"""
        if not title:
            return None
        
        mots_cles = []
        
        # Extraire les mots significatifs du titre
        words = re.findall(r'\b\w{4,}\b', title.lower())
        
        # Mots-clés basés sur le contenu du titre
        title_lower = title.lower()
        
        # Mots-clés spécifiques par domaine
        if 'formation' in title_lower:
            mots_cles.extend(['Formation', 'Apprentissage', 'Développement'])
        if 'prestation' in title_lower:
            mots_cles.extend(['Prestations', 'Services'])
        if 'service' in title_lower:
            mots_cles.extend(['Services', 'Support', 'Assistance'])
        if 'fourniture' in title_lower:
            mots_cles.extend(['Fournitures', 'Matériel', 'Équipement'])
        if 'travaux' in title_lower:
            mots_cles.extend(['Travaux', 'Construction', 'Réalisation'])
        if 'médical' in title_lower or 'santé' in title_lower:
            mots_cles.extend(['Médical', 'Santé', 'Soins'])
        if 'informatique' in title_lower or 'numérique' in title_lower:
            mots_cles.extend(['Informatique', 'IT', 'Numérique'])
        if 'maintenance' in title_lower:
            mots_cles.extend(['Maintenance', 'Entretien', 'Réparation'])
        if 'consultation' in title_lower:
            mots_cles.extend(['Consultation', 'Conseil', 'Expertise'])
        if 'accord' in title_lower:
            mots_cles.extend(['Accord-cadre', 'Framework'])
        if 'règlement' in title_lower:
            mots_cles.extend(['Règlement', 'RC'])
        
        # Filtrer les mots vides
        stop_words = {
            'procédure', 'procedure', 'appel', 'offres', 'consultation', 
            'marché', 'marche', 'fourniture', 'service', 'travaux',
            'pour', 'les', 'des', 'dans', 'avec', 'sans', 'sous', 'sur',
            'par', 'de', 'du', 'de la', 'du', 'des', 'et', 'ou', 'mais',
            'ainsi', 'donc', 'alors', 'cependant', 'néanmoins', 'toutefois',
            'réalisation', 'realisation', 'professionnelle', 'associées', 'associees'
        }
        
        # Ajouter les mots significatifs du titre
        keywords = [word for word in words if word not in stop_words]
        mots_cles.extend(keywords)
        
        # Supprimer les doublons et limiter à 8 mots-clés maximum
        mots_cles_uniques = list(dict.fromkeys(mots_cles))
        return ', '.join(mots_cles_uniques[:8])
    
    def _deduce_famille_improved(self, lot_title: str) -> Optional[str]:
        """Déduction améliorée de la famille basée sur l'intitulé du lot"""
        if not lot_title:
            return None
        
        title_lower = lot_title.lower()
        
        # Mots-clés plus spécifiques pour chaque famille
        famille_keywords = {
            'PRESTATIONS INTELLECTUELLES': [
                'formation', 'formation', 'conseil', 'conseil', 'expertise', 'expertise',
                'accompagnement', 'accompagnement', 'coaching', 'coaching', 'développement',
                'developpement', 'apprentissage', 'apprentissage', 'enseignement', 'enseignement',
                'prestation', 'prestation', 'service', 'service', 'support', 'support',
                'assistance', 'assistance', 'intervention', 'intervention', 'accompagnement'
            ],
            'SOLUTIONS INFORMATIQUES': [
                'informatique', 'informatique', 'numérique', 'numerique', 'digital', 'digital',
                'logiciel', 'logiciel', 'système', 'systeme', 'application', 'application',
                'plateforme', 'plateforme', 'outil', 'outil', 'solution', 'solution',
                'développement', 'developpement', 'programmation', 'programmation', 'IT'
            ],
            'FOURNITURES': [
                'fourniture', 'fourniture', 'achat', 'achat', 'matériel', 'materiel', 
                'équipement', 'equipement', 'produit', 'produit', 'article', 'article',
                'congélateur', 'congelateur', 'réfrigérateur', 'refrigerateur', 'machine',
                'appareil', 'outil', 'instrument', 'dispositif', 'système', 'systeme',
                'médical', 'medical', 'biomédical', 'biomedical', 'laboratoire'
            ],
            'SERVICES': [
                'service', 'service', 'maintenance', 'maintenance', 'entretien', 'entretien',
                'prestation', 'prestation', 'intervention', 'intervention', 'réparation',
                'reparation', 'installation', 'installation', 'mise en service', 'support',
                'assistance', 'assistance', 'conseil', 'conseil', 'accompagnement'
            ],
            'TRAVAUX': [
                'travaux', 'travaux', 'construction', 'construction', 'bâtiment', 'batiment', 
                'infrastructure', 'infrastructure', 'aménagement', 'amenagement', 'réhabilitation',
                'rehabilitation', 'rénovation', 'renovation', 'restauration', 'restauration'
            ]
        }
        
        # Compter les occurrences de chaque famille
        famille_scores = {}
        for famille, keywords in famille_keywords.items():
            score = sum(1 for keyword in keywords if keyword in title_lower)
            if score > 0:
                famille_scores[famille] = score
        
        # Retourner la famille avec le score le plus élevé
        if famille_scores:
            return max(famille_scores, key=famille_scores.get)
        
        # Déduction basée sur le contexte général
        if 'formation' in title_lower or 'prestation' in title_lower:
            return 'PRESTATIONS INTELLECTUELLES'
        elif 'informatique' in title_lower or 'numérique' in title_lower:
            return 'SOLUTIONS INFORMATIQUES'
        elif 'fourniture' in title_lower or 'matériel' in title_lower:
            return 'FOURNITURES'
        elif 'service' in title_lower or 'maintenance' in title_lower:
            return 'SERVICES'
        elif 'travaux' in title_lower or 'construction' in title_lower:
            return 'TRAVAUX'
        
        # Ne PAS retourner de valeur par défaut
        return None
    
    def _validate_with_database(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et corrige les données avec la base de données existante"""
        try:
            logger.info("Validation des données extraites...")
            
            # Validation simplifiée sans dépendance externe
            validated_data = self._simple_validation(extracted_data)
            
            logger.info("Validation terminée avec succès")
            return validated_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation: {e}")
            return extracted_data
    
    def _simple_validation(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validation simplifiée des données extraites"""
        validated_data = extracted_data.copy()
        
        # Nettoyer les chaînes de caractères
        for key, value in validated_data.items():
            if isinstance(value, str):
                # Supprimer les espaces en début/fin
                validated_data[key] = value.strip()
                # Limiter la longueur
                if len(validated_data[key]) > 500:
                    validated_data[key] = validated_data[key][:500] + "..."
        
        return validated_data
    
    def validate_extraction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validation intelligente des données extraites avec validation croisée avancée"""
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'confidence_score': 0.0,
            'validation_details': {}
        }
        
        try:
            logger.info("🔍 Début de la validation croisée des données...")
            
            # Validation des champs obligatoires
            required_fields = ['intitule_procedure', 'montant_global_estime', 'montant_global_maxi']
            for field in required_fields:
                if not data.get(field) or data[field].strip() == '':
                    validation_results['errors'].append(f"Champ obligatoire manquant: {field}")
                    validation_results['is_valid'] = False
                else:
                    validation_results['validation_details'][field] = 'present'
            
            # Validation des montants avec patterns avancés
            if data.get('montant_global_estime'):
                montant_est = self._parse_montant(data['montant_global_estime'])
                if montant_est is None:
                    validation_results['warnings'].append("Montant global estimé non valide")
                    validation_results['validation_details']['montant_global_estime'] = 'invalid'
                elif montant_est <= 0:
                    validation_results['warnings'].append("Montant global estimé doit être positif")
                    validation_results['validation_details']['montant_global_estime'] = 'negative'
                else:
                    validation_results['validation_details']['montant_global_estime'] = 'valid'
            
            if data.get('montant_global_maxi'):
                montant_max = self._parse_montant(data['montant_global_maxi'])
                if montant_max is None:
                    validation_results['warnings'].append("Montant global maximum non valide")
                    validation_results['validation_details']['montant_global_maxi'] = 'invalid'
                elif montant_max <= 0:
                    validation_results['warnings'].append("Montant global maximum doit être positif")
                    validation_results['validation_details']['montant_global_maxi'] = 'negative'
                else:
                    validation_results['validation_details']['montant_global_maxi'] = 'valid'
            
            # Validation de cohérence des montants
            if data.get('montant_global_estime') and data.get('montant_global_maxi'):
                montant_est = self._parse_montant(data['montant_global_estime'])
                montant_max = self._parse_montant(data['montant_global_maxi'])
                if montant_est and montant_max and montant_est > montant_max:
                    validation_results['warnings'].append("Montant global estimé supérieur au montant maximum")
                    validation_results['validation_details']['montant_coherence'] = 'inconsistent'
                else:
                    validation_results['validation_details']['montant_coherence'] = 'consistent'
            
            # Validation des dates avec patterns avancés
            if data.get('date_limite'):
                if not self._is_valid_date(data['date_limite']):
                    validation_results['warnings'].append("Date limite non valide")
                    validation_results['validation_details']['date_limite'] = 'invalid'
                else:
                    validation_results['validation_details']['date_limite'] = 'valid'
            
            # Validation des lots avec validation croisée
            if data.get('nbr_lots'):
                lots_validation = self._validate_lots_count(data['nbr_lots'])
                validation_results['validation_details']['lots'] = lots_validation
                
                if not lots_validation['is_valid']:
                    validation_results['warnings'].extend(lots_validation['warnings'])
            
            # Validation des critères d'attribution
            if data.get('criteres_economique') or data.get('criteres_techniques'):
                criteres_validation = self._validate_criteres_attribution(data)
                validation_results['validation_details']['criteres'] = criteres_validation
                
                if not criteres_validation['is_valid']:
                    validation_results['warnings'].extend(criteres_validation['warnings'])
            
            # Validation de la cohérence globale
            coherence_score = self._calculate_coherence_score(data)
            validation_results['confidence_score'] = coherence_score
            
            # Suggestions d'amélioration intelligentes
            suggestions = self._generate_suggestions(data, validation_results)
            validation_results['suggestions'].extend(suggestions)
            
            # Validation croisée avec patterns de RC
            pattern_validation = self._validate_rc_patterns(data)
            validation_results['validation_details']['patterns'] = pattern_validation
            
            if not pattern_validation['is_valid']:
                validation_results['warnings'].extend(pattern_validation['warnings'])
            
            logger.info(f"✅ Validation terminée - Score de confiance: {coherence_score:.2f}")
            
        except Exception as e:
            logger.error(f"Erreur validation: {e}")
            validation_results['errors'].append(f"Erreur de validation: {str(e)}")
            validation_results['is_valid'] = False
        
        return validation_results
    
    def _parse_montant(self, montant_str: str) -> Optional[float]:
        """Parse un montant depuis une chaîne de caractères"""
        try:
            if not montant_str:
                return None
            
            # Nettoyer la chaîne
            montant_clean = str(montant_str).replace('€', '').replace(',', '.').replace(' ', '').strip()
            
            # Gérer les unités
            if 'k' in montant_clean.lower():
                return float(montant_clean.lower().replace('k', '')) * 1000
            elif 'm' in montant_clean.lower():
                return float(montant_clean.lower().replace('m', '')) * 1000000
            else:
                return float(montant_clean)
        except:
            return None
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Valide si une date est valide"""
        try:
            from datetime import datetime
            
            # Essayer différents formats de date
            formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d %B %Y', '%d %b %Y']
            for fmt in formats:
                try:
                    datetime.strptime(date_str, fmt)
                    return True
                except:
                    continue
            return False
        except:
            return False
    
    def _validate_lots_count(self, nbr_lots: Any) -> Dict[str, Any]:
        """Validation du nombre de lots"""
        lots_validation = {
            'is_valid': True,
            'warnings': []
        }
        
        try:
            nbr = int(nbr_lots) if str(nbr_lots).isdigit() else 0
            
            if nbr <= 0:
                lots_validation['warnings'].append("Nombre de lots doit être positif")
                lots_validation['is_valid'] = False
            elif nbr > 100:
                lots_validation['warnings'].append("Nombre de lots très élevé")
                lots_validation['is_valid'] = False
            
        except Exception as e:
            lots_validation['warnings'].append(f"Erreur validation nombre de lots: {str(e)}")
            lots_validation['is_valid'] = False
        
        return lots_validation
    
    def _validate_criteres_attribution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validation des critères d'attribution"""
        criteres_validation = {
            'is_valid': True,
            'warnings': [],
            'total_percentage': 0.0
        }
        
        try:
            # Vérifier la présence des critères essentiels
            essential_criteres = ['criteres_economique', 'criteres_techniques']
            for critere in essential_criteres:
                if not data.get(critere) or data[critere].strip() == '':
                    criteres_validation['warnings'].append(f"Critère {critere} manquant")
                    criteres_validation['is_valid'] = False
            
            # Calculer le pourcentage total des critères
            total_percentage = 0.0
            for critere, valeur in data.items():
                if critere.startswith('criteres_') and valeur and str(valeur).strip():
                    # Extraire le pourcentage de la valeur
                    percentage_match = re.search(r'(\d+(?:[.,]\d+)?)\s*%', str(valeur))
                    if percentage_match:
                        percentage = float(percentage_match.group(1).replace(',', '.'))
                        total_percentage += percentage
            
            criteres_validation['total_percentage'] = total_percentage
            
            # Vérifier que le total est proche de 100%
            if total_percentage > 0:
                if abs(total_percentage - 100.0) > 5.0:  # Tolérance de 5%
                    criteres_validation['warnings'].append(f"Total des critères ({total_percentage:.1f}%) n'est pas proche de 100%")
                    criteres_validation['is_valid'] = False
            else:
                criteres_validation['warnings'].append("Aucun pourcentage de critère trouvé")
                criteres_validation['is_valid'] = False
            
        except Exception as e:
            logger.error(f"Erreur validation critères: {e}")
            criteres_validation['warnings'].append(f"Erreur validation critères: {str(e)}")
            criteres_validation['is_valid'] = False
        
        return criteres_validation
    
    def _calculate_coherence_score(self, data: Dict[str, Any]) -> float:
        """Calcule un score de cohérence global des données extraites"""
        score = 0.0
        max_score = 100.0
        
        try:
            # Score pour les champs obligatoires (30 points)
            required_fields = ['intitule_procedure', 'montant_global_estime', 'montant_global_maxi']
            present_fields = sum(1 for field in required_fields if data.get(field) and str(data[field]).strip())
            score += (present_fields / len(required_fields)) * 30
            
            # Score pour la cohérence des montants (20 points)
            if data.get('montant_global_estime') and data.get('montant_global_maxi'):
                montant_est = self._parse_montant(data['montant_global_estime'])
                montant_max = self._parse_montant(data['montant_global_maxi'])
                if montant_est and montant_max and montant_est <= montant_max:
                    score += 20
                elif montant_est and montant_max:
                    score += 10  # Partiel si incohérent
            
            # Score pour les lots (15 points)
            if data.get('nbr_lots'):
                nbr_lots = int(data['nbr_lots']) if str(data['nbr_lots']).isdigit() else 0
                if nbr_lots > 0 and nbr_lots <= 100:
                    score += 15
                elif nbr_lots > 0:
                    score += 10  # Partiel si nombre élevé
            
            # Score pour les critères d'attribution (15 points)
            if data.get('criteres_economique') or data.get('criteres_techniques'):
                criteres_score = 0
                if data.get('criteres_economique') and str(data['criteres_economique']).strip():
                    criteres_score += 1
                if data.get('criteres_techniques') and str(data['criteres_techniques']).strip():
                    criteres_score += 1
                if data.get('autres_criteres') and str(data['autres_criteres']).strip():
                    criteres_score += 1
                score += (criteres_score / 3) * 15
            
            # Score pour les dates (10 points)
            if data.get('date_limite'):
                if self._is_valid_date(data['date_limite']):
                    score += 10
            
            # Score pour les informations complémentaires (10 points)
            if data.get('infos_complementaires') or data.get('mots_cles'):
                score += 10
            
        except Exception as e:
            logger.error(f"Erreur calcul score cohérence: {e}")
        
        return min(score, max_score)
    
    def _generate_suggestions(self, data: Dict[str, Any], validation_results: Dict[str, Any]) -> List[str]:
        """Génère des suggestions intelligentes d'amélioration"""
        suggestions = []
        
        try:
            # Suggestions basées sur les champs manquants
            if not data.get('criteres_economique') and not data.get('criteres_techniques'):
                suggestions.append("Ajouter les critères d'attribution pour améliorer la qualité de l'extraction")
            
            if not data.get('duree_marche'):
                suggestions.append("Ajouter la durée du marché pour une information complète")
            
            if not data.get('type_procedure'):
                suggestions.append("Ajouter le type de procédure pour une classification précise")
            
            # Suggestions basées sur la qualité des données
            if data.get('nbr_lots'):
                nbr_lots = int(data['nbr_lots']) if str(data['nbr_lots']).isdigit() else 0
                if nbr_lots > 10:
                    suggestions.append(f"Marché complexe avec {nbr_lots} lots - vérifier la cohérence des données")
            
            # Suggestions basées sur le score de confiance
            confidence_score = validation_results.get('confidence_score', 0)
            if confidence_score < 70:
                suggestions.append("Score de confiance faible - vérifier la qualité de l'extraction")
            elif confidence_score < 85:
                suggestions.append("Score de confiance moyen - quelques améliorations possibles")
            
            # Suggestions basées sur les patterns de RC
            if not data.get('groupement'):
                suggestions.append("Ajouter le groupement (RESAH, UNIHA, UGAP, CAIH)")
            
            if not data.get('univers'):
                suggestions.append("Ajouter l'univers (MÉDICAL, INFORMATIQUE, ÉQUIPEMENT, etc.)")
            
        except Exception as e:
            logger.error(f"Erreur génération suggestions: {e}")
        
        return suggestions
    
    def _validate_rc_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validation basée sur les patterns typiques des RC"""
        pattern_validation = {
            'is_valid': True,
            'warnings': [],
            'patterns_found': []
        }
        
        try:
            # Vérifier la présence de patterns typiques des RC
            if data.get('intitule_procedure'):
                intitule = str(data['intitule_procedure']).upper()
                rc_patterns = [
                    'ACCORD-CADRE',
                    'MARCHE',
                    'CONSULTATION',
                    'APPEL D\'OFFRES',
                    'PROCEDURE',
                    'LOT',
                    'ALLOTISSEMENT',
                    'FORMATION',
                    'PRESTATION'
                ]
                
                found_patterns = [pattern for pattern in rc_patterns if pattern in intitule]
                pattern_validation['patterns_found'] = found_patterns
                
                if not found_patterns:
                    pattern_validation['warnings'].append("Intitulé ne contient pas de patterns typiques des RC")
                    pattern_validation['is_valid'] = False
            
            # Vérifier la cohérence des montants avec les patterns de RC
            if data.get('montant_global_estime') and data.get('montant_global_maxi'):
                montant_est = self._parse_montant(data['montant_global_estime'])
                montant_max = self._parse_montant(data['montant_global_maxi'])
                
                if montant_est and montant_max:
                    # Vérifier que les montants sont dans une plage raisonnable pour un RC
                    if montant_est < 1000:  # Moins de 1000€
                        pattern_validation['warnings'].append("Montant global estimé très faible pour un RC")
                    elif montant_est > 10000000:  # Plus de 10M€
                        pattern_validation['warnings'].append("Montant global estimé très élevé pour un RC")
                    
                    # Vérifier la cohérence entre estimatif et maximum
                    if montant_max > montant_est * 2:
                        pattern_validation['warnings'].append("Écart important entre montant estimatif et maximum")
            
        except Exception as e:
            logger.error(f"Erreur validation patterns RC: {e}")
            pattern_validation['warnings'].append(f"Erreur validation patterns: {str(e)}")
            pattern_validation['is_valid'] = False
        
        return pattern_validation

# Instance globale
extraction_improver = ExtractionImprover()
