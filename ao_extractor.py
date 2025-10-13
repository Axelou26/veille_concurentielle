"""
Module d'extraction spécialisé pour les appels d'offres
Gère l'extraction intelligente d'informations depuis différents types de fichiers
et la génération de données pour les 44 colonnes de la base de données
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json
from io import BytesIO
import os

# Import des modules existants
from pdf_extractor import pdf_extractor
from extraction_improver import extraction_improver
from criteria_extractor import CriteriaExtractor, TableauCriteres

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AOExtractor:
    """Extracteur spécialisé pour les appels d'offres"""
    
    def __init__(self, reference_data: pd.DataFrame = None):
        """
        Initialise l'extracteur avec les données de référence pour la réflexion
        
        Args:
            reference_data: DataFrame contenant les données existantes pour l'apprentissage
        """
        self.reference_data = reference_data
        self.extraction_patterns = self._initialize_extraction_patterns()
        self.value_generators = self._initialize_value_generators()
        
        # NOUVEAU: Système de validation croisée et apprentissage
        self.validation_rules = self._initialize_validation_rules()
        self.extraction_metrics = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'validation_errors': 0,
            'pattern_improvements': 0
        }
        self.learning_data = []
        
        # NOUVEAU: Extracteur de critères d'attribution
        self.criteria_extractor = CriteriaExtractor()
        
    def _initialize_extraction_patterns(self) -> Dict[str, List[str]]:
        """Initialise les patterns d'extraction ultra intelligents pour les 44 colonnes"""
        return {
            # Patterns pour les montants (Montant global estimé, Montant global maxi) - ULTRA COMPLETS
            'montant_global_estime': [
                # NOUVEAUX: Patterns spécifiques aux tableaux de lots structurés
                r'(?:^|\n)\d+\s+[A-Z][A-Z\s/]+?\s+(\d{1,3}(?:\s\d{3})*)\s+\d{1,3}(?:\s\d{3})*\s*(?:\n|$)',  # Tableau structuré
                r'(?:^|\n)\d+\s+[A-Z][A-Z\s/]+?\s+(\d{1,3}(?:\s\d{3})*)\s*€\s+\d{1,3}(?:\s\d{3})*\s*€\s*(?:\n|$)',  # Tableau avec €
                r'(?:^|\n)\d+\s+[A-Z][A-Z\s/]+?\s+(\d{1,3}(?:\s\d{3})*)\s*euros?\s+\d{1,3}(?:\s\d{3})*\s*euros?\s*(?:\n|$)',  # Tableau avec euros
                
                # Patterns avec contexte complet
                r'(?:montant|budget|prix|coût|cout|valeur|estimation|enveloppe|allocation)[\s\w]*(?:global|total|global|estimé|estime|prévisionnel|previsionnel)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?|HT|TTC|HTA|TVA)',
                r'(?:budget|montant|prix|coût|cout|estimation|enveloppe)[\s\w]*(?:global|total|estimé|estime)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?|HT|TTC)',
                r'(?:montant|budget|prix|coût|cout|valeur|estimation)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?|HT|TTC)',
                r'(?:budget|montant|prix|coût|cout|estimation|enveloppe)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|k\s*€|milliers)',
                r'(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|k\s*€|milliers)',
                r'(?:budget|montant|prix|coût|cout|estimation|enveloppe)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)\s*(?:m€|meuros?|millions?|m\s*€)',
                r'(\d+(?:[.,]\d+)?)\s*(?:m€|meuros?|millions?|m\s*€)',
                # Patterns avec variations de format
                r'(?:montant|budget|prix|coût|cout|estimation)[\s\w]*[:\s]*(\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                r'(?:budget|montant|prix|coût|cout|estimation)[\s\w]*[:\s]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                # Patterns avec mots-clés étendus
                r'(?:enveloppe|allocation|dotation|crédit|credit|financement)[\s\w]*(?:budgetaire|budgetaire|global|total)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                r'(?:coût|cout|prix|valeur)[\s\w]*(?:total|global|estimé|estime|prévisionnel|previsionnel)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                # Patterns pour montants en toutes lettres
                r'(?:montant|budget|prix|coût|cout|estimation)[\s\w]*[:\s]*(?:de\s+)?(\d+(?:\s+et\s+\d+)?)\s*(?:euros?|€)',
                # Patterns avec contexte de marché
                r'(?:marché|marche|contrat|prestation)[\s\w]*(?:montant|budget|prix|coût|cout|estimation)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                # Patterns avec contexte d'appel d'offres
                r'(?:appel|offre|ao|consultation)[\s\w]*(?:montant|budget|prix|coût|cout|estimation)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)'
            ],
            'montant_global_maxi': [
                # Patterns avec contexte de maximum/plafond
                r'(?:maximum|maxi|plafond|limite|seuil|seuil)[\s\w]*(?:budgetaire|budgetaire|global|total|montant)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?|HT|TTC)',
                r'(?:budget|montant|prix|coût|cout)[\s\w]*(?:maximum|maxi|plafond|limite|seuil)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                r'(?:enveloppe|allocation|dotation)[\s\w]*(?:maximum|maxi|plafond|limite)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                r'(?:montant|budget|prix|coût|cout)[\s\w]*(?:maximum|maxi|plafond|limite|seuil)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|k\s*€)',
                r'(?:montant|budget|prix|coût|cout)[\s\w]*(?:maximum|maxi|plafond|limite|seuil)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)\s*(?:m€|meuros?|millions?|m\s*€)',
                # Patterns avec contexte de marché
                r'(?:marché|marche|contrat)[\s\w]*(?:maximum|maxi|plafond|limite)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                # Patterns avec contexte d'appel d'offres
                r'(?:appel|offre|ao|consultation)[\s\w]*(?:maximum|maxi|plafond|limite)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)'
            ],
            
            # Patterns pour les dates (Date limite, Date d'attribution, Durée) - ULTRA COMPLETS
            'date_limite': [
                # Patterns avec contexte complet
                r'(?:date|échéance|clôture|cloture|fin|expiration)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:date|échéance|clôture|cloture|fin|expiration)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot)[\s\w]*[:\s]*(\d{4}-\d{2}-\d{2})',
                r'(?:date|échéance|clôture|cloture|fin|expiration)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot)[\s\w]*[:\s]*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
                # Patterns avec variations de format
                r'(?:date|échéance|clôture|cloture|fin|expiration)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot)[\s\w]*[:\s]*(\d{1,2}\s+(?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)\.?\s+\d{4})',
                r'(?:date|échéance|clôture|cloture|fin|expiration)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot)[\s\w]*[:\s]*(\d{1,2}\s+(?:jan|fév|mar|avr|mai|jun|jul|aoû|sep|oct|nov|déc)\.?\s+\d{4})',
                # Patterns avec contexte d'appel d'offres
                r'(?:appel|offre|ao|consultation|marché|marche)[\s\w]*(?:date|échéance|clôture|cloture|fin)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:appel|offre|ao|consultation|marché|marche)[\s\w]*(?:date|échéance|clôture|cloture|fin)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot)[\s\w]*[:\s]*(\d{4}-\d{2}-\d{2})',
                # Patterns avec contexte de procédure
                r'(?:procédure|procedure|consultation|marché|marche)[\s\w]*(?:date|échéance|clôture|cloture|fin)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                # Patterns génériques (plus permissifs)
                r'(?:date|échéance|clôture|cloture|fin|expiration)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:date|échéance|clôture|cloture|fin|expiration)[\s\w]*[:\s]*(\d{4}-\d{2}-\d{2})',
                r'(?:date|échéance|clôture|cloture|fin|expiration)[\s\w]*[:\s]*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
                # Patterns avec mots-clés étendus
                r'(?:délai|delai|termine|termine|expire|expire)[\s\w]*(?:remise|offres|candidature|soumission|dépôt|depot)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:délai|delai|termine|termine|expire|expire)[\s\w]*(?:remise|offres|candidature|soumission|dépôt|depot)[\s\w]*[:\s]*(\d{4}-\d{2}-\d{2})',
                # Patterns avec contexte temporel
                r'(?:avant|jusqu|until|by)[\s\w]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:avant|jusqu|until|by)[\s\w]*(\d{4}-\d{2}-\d{2})',
                # Patterns avec format français
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})'
            ],
            'date_attribution': [
                # Patterns avec contexte complet
                r'(?:date|attribution|attribué|attribue|attribution)[\s\w]*(?:marché|marche|contrat|prestation|lot)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:date|attribution|attribué|attribue|attribution)[\s\w]*(?:marché|marche|contrat|prestation|lot)[\s\w]*[:\s]*(\d{4}-\d{2}-\d{2})',
                r'(?:attribution|attribué|attribue|attribution)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:attribution|attribué|attribue|attribution)[\s\w]*[:\s]*(\d{4}-\d{2}-\d{2})',
                # Patterns avec contexte d'appel d'offres
                r'(?:appel|offre|ao|consultation)[\s\w]*(?:attribution|attribué|attribue|attribution)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:appel|offre|ao|consultation)[\s\w]*(?:attribution|attribué|attribue|attribution)[\s\w]*[:\s]*(\d{4}-\d{2}-\d{2})',
                # Patterns avec contexte de procédure
                r'(?:procédure|procedure|consultation|marché|marche)[\s\w]*(?:attribution|attribué|attribue|attribution)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                # Patterns avec mots-clés étendus
                r'(?:attribution|attribué|attribue|attribution)[\s\w]*(?:prévue|prevue|prévisionnelle|previsionnelle|estimée|estimee)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:attribution|attribué|attribue|attribution)[\s\w]*(?:prévue|prevue|prévisionnelle|previsionnelle|estimée|estimee)[\s\w]*[:\s]*(\d{4}-\d{2}-\d{2})',
                # Patterns avec contexte temporel
                r'(?:prévue|prevue|prévisionnelle|previsionnelle|estimée|estimee)[\s\w]*(?:attribution|attribué|attribue|attribution)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:prévue|prevue|prévisionnelle|previsionnelle|estimée|estimee)[\s\w]*(?:attribution|attribué|attribue|attribution)[\s\w]*[:\s]*(\d{4}-\d{2}-\d{2})'
            ],
            'duree_marche': [
                # Patterns avec contexte complet
                r'(?:durée|duree|période|periode|temps)[\s\w]*(?:marché|marche|contrat|prestation|exécution|execution)[\s\w]*[:\s]*(\d+)\s*(?:mois|mois|années?|ans?|jours?|jours?)',
                r'(?:durée|duree|période|periode|temps)[\s\w]*[:\s]*(\d+)\s*(?:mois|mois|années?|ans?|jours?|jours?)',
                r'(\d+)\s*(?:mois|mois|années?|ans?|jours?|jours?)[\s\w]*(?:durée|duree|marché|marche|contrat|prestation|exécution|execution)',
                # Patterns avec contexte d'appel d'offres
                r'(?:appel|offre|ao|consultation)[\s\w]*(?:durée|duree|période|periode|temps)[\s\w]*[:\s]*(\d+)\s*(?:mois|mois|années?|ans?|jours?|jours?)',
                # Patterns avec contexte de procédure
                r'(?:procédure|procedure|consultation|marché|marche)[\s\w]*(?:durée|duree|période|periode|temps)[\s\w]*[:\s]*(\d+)\s*(?:mois|mois|années?|ans?|jours?|jours?)',
                # Patterns avec mots-clés étendus
                r'(?:durée|duree|période|periode|temps)[\s\w]*(?:prévue|prevue|prévisionnelle|previsionnelle|estimée|estimee|contractuelle)[\s\w]*[:\s]*(\d+)\s*(?:mois|mois|années?|ans?|jours?|jours?)',
                # Patterns avec contexte temporel
                r'(?:prévue|prevue|prévisionnelle|previsionnelle|estimée|estimee|contractuelle)[\s\w]*(?:durée|duree|période|periode|temps)[\s\w]*[:\s]*(\d+)\s*(?:mois|mois|années?|ans?|jours?|jours?)',
                # Patterns avec format étendu
                r'(\d+)\s*(?:mois|mois|années?|ans?|jours?|jours?)[\s\w]*(?:durée|duree|période|periode|temps)',
                # Patterns avec variations de format
                r'(?:durée|duree|période|periode|temps)[\s\w]*[:\s]*(\d+)\s*(?:mois|mois|années?|ans?|jours?|jours?)[\s\w]*(?:marché|marche|contrat|prestation|exécution|execution)',
                # Patterns avec contexte de marché
                r'(?:marché|marche|contrat|prestation)[\s\w]*(?:durée|duree|période|periode|temps)[\s\w]*[:\s]*(\d+)\s*(?:mois|mois|années?|ans?|jours?|jours?)'
            ],
            
            # Patterns pour les références (Référence de la procédure, Intitulé de la procédure) - ULTRA COMPLETS AMÉLIORÉS
            'reference_procedure': [
                # Patterns spécifiques aux formats RESAH/UGAP - NOUVEAUX
                r'(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*(\d{4}-[A-Z]\d{3})',
                r'(?:ao|marché|marche|contrat|prestation)[\s\w]*(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*(\d{4}-[A-Z]\d{3})',
                r'(\d{4}-[A-Z]\d{3})',  # Format direct 2024-R001
                r'(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',  # Format complet 2024-R001-000-000
                r'(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*(\d{4}[A-Z]\d{3})',
                r'(\d{4}[A-Z]\d{3})',  # Format sans tiret 2024R001
                
                # Patterns avec contexte complet - EXISTANTS
                r'(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*(?:procédure|procedure|ao|marché|marche|contrat|prestation)[\s\w]*[:\s]*([A-Z0-9\-_]+)',
                r'(?:ao|marché|marche|contrat|prestation)[\s\w]*(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*([A-Z0-9\-_]+)',
                r'(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*([A-Z0-9\-_]+)',
                # Patterns avec contexte d'appel d'offres
                r'(?:appel|offre|ao|consultation)[\s\w]*(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*([A-Z0-9\-_]+)',
                # Patterns avec contexte de procédure
                r'(?:procédure|procedure|consultation|marché|marche)[\s\w]*(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*([A-Z0-9\-_]+)',
                # Patterns avec variations de format
                r'([A-Z]{2,}\d{4,})',  # Pattern pour codes comme AO2024001
                r'([A-Z]{2,}-\d{4,})',  # Pattern pour codes comme AO-2024-001
                r'([A-Z]{2,}_\d{4,})',  # Pattern pour codes comme AO_2024_001
                r'([A-Z]{2,}\.\d{4,})',  # Pattern pour codes comme AO.2024.001
                r'([A-Z]{2,}\s\d{4,})',  # Pattern pour codes comme AO 2024 001
                # Patterns avec contexte de marché
                r'(?:marché|marche|contrat|prestation)[\s\w]*(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*([A-Z0-9\-_]+)',
                # Patterns avec contexte de lot
                r'(?:lot|lot)[\s\w]*(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*([A-Z0-9\-_]+)',
                # Patterns génériques
                r'([A-Z]{2,}\d{2,})',  # Pattern pour codes comme AO24
                r'([A-Z]{3,}\d{2,})',  # Pattern pour codes comme CON24
                r'([A-Z]{2,}\d{3,})',  # Pattern pour codes comme AO001
                # Patterns avec contexte de consultation
                r'(?:consultation|consultation)[\s\w]*(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*([A-Z0-9\-_]+)',
                # Patterns avec contexte de prestation
                r'(?:prestation|prestation)[\s\w]*(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*([A-Z0-9\-_]+)'
            ],
            'intitule_procedure': [
                # Patterns avec contexte complet
                r'(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*(?:procédure|procedure|marché|marche|ao|contrat|prestation)[\s\w]*[:\s]*([^,\n]{10,200})',
                r'(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})',
                r'(?:appel|offre|marché|marche|contrat|prestation)[\s\w]*[:\s]*([^,\n]{10,200})',
                # Patterns avec contexte d'appel d'offres
                r'(?:appel|offre|ao|consultation)[\s\w]*(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})',
                # Patterns avec contexte de procédure
                r'(?:procédure|procedure|consultation|marché|marche)[\s\w]*(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})',
                # Patterns avec contexte de marché
                r'(?:marché|marche|contrat|prestation)[\s\w]*(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})',
                # Patterns avec contexte de lot
                r'(?:lot|lot)[\s\w]*(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})',
                # Patterns avec contexte de consultation
                r'(?:consultation|consultation)[\s\w]*(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})',
                # Patterns avec contexte de prestation
                r'(?:prestation|prestation)[\s\w]*(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})',
                # Patterns avec variations de format
                r'(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})',
                # Patterns avec contexte de fourniture
                r'(?:fourniture|fourniture|prestation|prestation|service|service)[\s\w]*(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})',
                # Patterns avec contexte de équipement
                r'(?:équipement|equipement|matériel|materiel|outillage|outillage)[\s\w]*(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})'
            ],
            
            # Patterns pour les organismes et groupements - AMÉLIORÉS
            'groupement': [
                # Patterns spécifiques aux groupements connus - NOUVEAUX
                r'(?:groupement|consortium|alliance|partenariat|réseau|reseau|organisme|acheteur|client|maître|donneur)[\s\w]*[:\s]*(RESAH|UGAP|CNRS|UNIHA|CAIH)',
                r'(RESAH|UGAP|CNRS|UNIHA|CAIH)',  # Direct match
                r'(?:groupement|consortium|alliance|partenariat|réseau|reseau|organisme|acheteur|client|maître|donneur)[\s\w]*[:\s]*([A-Z]{2,})',
                r'(?:groupement|consortium|alliance|partenariat|réseau|reseau|organisme|acheteur|client|maître|donneur)[\s\w]*[:\s]*([A-Z]{2,}[A-Z0-9]*)',
                
                # Patterns génériques - EXISTANTS
                r'(?:groupement|consortium|alliance|partenariat|réseau|reseau)[\s\w]*[:\s]*([^,\n]{5,100})',
                r'(?:ministère|mairie|région|département|établissement|collectivité|entreprise|université|hôpital|cnrs|ugap|resah|uniha)',
                r'(?:organisme|acheteur|client|maître|donneur)[\s\w]*[:\s]*([^,\n]{5,100})'
            ],
            
            # Patterns pour les types de procédure
            'type_procedure': [
                r'(?:type|procédure|procedure|mode|forme)[\s\w]*[:\s]*(?:appel|offre|marché|marche|consultation|négociation|négocié|accord-cadre|accord_cadre|dynamique|dynamique)',
                r'(?:appel|offre|marché|marche|consultation|négociation|négocié|accord-cadre|accord_cadre|dynamique|dynamique)[\s\w]*(?:public|ouvert|restreint|négocié|négocié)'
            ],
            
            # Patterns pour mono/multi attribution
            'mono_multi': [
                r'(?:mono|multi|attribution|lotissement)[\s\w]*[:\s]*(?:mono|multi|attribution|lotissement|unique|multiple)',
                r'(?:attribution|lotissement)[\s\w]*[:\s]*(?:unique|multiple|mono|multi)'
            ],
            
            # Patterns pour les lots - AMÉLIORÉS POUR TABLEAUX
            'nbr_lots': [
                # Patterns avec contexte complet - NOUVEAUX
                r'(?:nombre|nbr|nb)[\s\w]*(?:lots|lot)[\s\w]*[:\s]*(\d+)',
                r'(?:lots|lot)[\s\w]*[:\s]*(\d+)',
                r'(\d+)[\s\w]*(?:lots|lot)',
                # Patterns avec contexte de marché - NOUVEAUX
                r'(?:marché|marche|contrat|prestation)[\s\w]*(?:nombre|nbr|nb)[\s\w]*(?:lots|lot)[\s\w]*[:\s]*(\d+)',
                r'(?:marché|marche|contrat|prestation)[\s\w]*(?:lots|lot)[\s\w]*[:\s]*(\d+)',
                # Patterns avec contexte d'appel d'offres - NOUVEAUX
                r'(?:appel|offre|ao|consultation)[\s\w]*(?:nombre|nbr|nb)[\s\w]*(?:lots|lot)[\s\w]*[:\s]*(\d+)',
                r'(?:appel|offre|ao|consultation)[\s\w]*(?:lots|lot)[\s\w]*[:\s]*(\d+)',
                # Patterns génériques - NOUVEAUX
                r'(\d+)[\s\w]*(?:lots|lot)[\s\w]*(?:marché|marche|contrat|prestation)',
                r'(\d+)[\s\w]*(?:lots|lot)[\s\w]*(?:appel|offre|ao|consultation)',
                # NOUVEAUX: Patterns spécifiques aux tableaux de lots
                r'Allotissement[^\n]*(\d+)[\s\w]*(?:lots|lot)',
                r'LOTISSEMENT[^\n]*(\d+)[\s\w]*(?:lots|lot)',
                r'REPARTITION[^\n]*(\d+)[\s\w]*(?:lots|lot)',
                # Pattern pour compter les lots dans un tableau (détection automatique)
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+\d{1,3}(?:\s\d{3})*\s+\d{1,3}(?:\s\d{3})*\s*(?:\n|$)'
            ],
            'lot_numero': [
                # Patterns avec contexte de lot - AMÉLIORÉS
                r'(?:lot|lot)[\s\w]*(?:n°|numero|numéro|no)[\s\w]*[:\s]*(\d+)',
                r'(?:lot|lot)[\s\w]*[:\s]*(\d+)',
                r'lot[\s\w]*(\d+)',
                # Patterns avec contexte de marché - NOUVEAUX
                r'(?:marché|marche|contrat|prestation)[\s\w]*(?:lot|lot)[\s\w]*(?:n°|numero|numéro|no)[\s\w]*[:\s]*(\d+)',
                r'(?:marché|marche|contrat|prestation)[\s\w]*(?:lot|lot)[\s\w]*[:\s]*(\d+)',
                # Patterns génériques - NOUVEAUX
                r'(\d+)[\s\w]*(?:lot|lot)'
            ],
            'intitule_lot': [
                # Patterns avec contexte de lot - AMÉLIORÉS
                r'(?:intitulé|intitule|titre|objet|libellé|libelle)[\s\w]*(?:lot|lot)[\s\w]*[:\s]*([^,\n]{5,200})',
                r'(?:lot|lot)[\s\w]*[:\s]*([^,\n]{5,200})',
                # Patterns spécifiques aux formations - NOUVEAUX
                r'(?:réalisation|realisation)[\s\w]*(?:prestations|prestation)[\s\w]*(?:formations|formation)[\s\w]*(?:transverses|transverse|santé|sante|soins)[\s\w]*[:\s]*([^,\n]{5,200})',
                r'(?:formations|formation)[\s\w]*(?:transverses|transverse|santé|sante|soins)[\s\w]*(?:organisation|organization)[\s\w]*[:\s]*([^,\n]{5,200})',
                # Patterns génériques - NOUVEAUX
                r'(?:intitulé|intitule|titre|objet|libellé|libelle)[\s\w]*[:\s]*([^,\n]{5,200})',
                # NOUVEAUX: Patterns spécifiques aux tableaux de lots
                r'(?:^|\n)\d+\s+([A-Z][A-Z\s/]+?)\s+\d{1,3}(?:\s\d{3})*\s+\d{1,3}(?:\s\d{3})*\s*(?:\n|$)',
                r'(?:^|\n)\d+\s+([A-Z][A-Z\s/\n]+?)\s+\d{1,3}(?:\s\d{3})*\s+\d{1,3}(?:\s\d{3})*\s*(?:\n|$)',
                # Patterns pour les intitulés de lots dans les tableaux
                r'FORMATIONS\s+[A-Z\s/]+',
                r'[A-Z]+\s+[A-Z\s/]+(?:FORMATION|SERVICE|PRESTATION)',
                r'[A-Z]+\s+[A-Z\s/]+(?:SANTE|SECURITE|SOINS|TRAVAIL)'
            ],
            
            # Patterns pour les informations complémentaires
            'infos_complementaires': [
                r'(?:infos|informations|détails|details|complémentaires|complementaires)[\s\w]*[:\s]*([^,\n]{10,500})',
                r'(?:contact|téléphone|telephone|email|mail|adresse)[\s\w]*[:\s]*([^,\n]{5,200})',
                r'(?:lieu|localisation|adresse)[\s\w]*[:\s]*([^,\n]{5,200})'
            ],
            
            # Patterns pour les critères d'évaluation - AMÉLIORÉS POUR TABLEAUX
            'criteres_economique': [
                # NOUVEAUX: Patterns spécifiques aux tableaux de critères
                r'(?:lot\s*\d+[^\n]*)?(?:économique|prix|coût|cout)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',  # Tableau structuré
                r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:économique|prix|coût|cout)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                
                # NOUVEAUX: Patterns pour les points (35 points = 35%)
                r'(?:lot\s*\d+[^\n]*)?(?:économique|prix|coût|cout)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:économique|prix|coût|cout)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*points?)\s+(\d+(?:[.,]\d+)?\s*points?)\s+(\d+(?:[.,]\d+)?\s*points?)',  # Tableau avec points
                
                # Patterns spécifiques aux pourcentages - EXISTANTS
                r'(?:critères|critères|critères)[\s\w]*(?:économique|economique|prix|coût|cout|attribution)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                r'(?:prix|coût|cout|économique|economique)[\s\w]*(?:critères|critères)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                r'(\d+(?:[.,]\d+)?\s*%)',  # Format direct 40%
                
                # Patterns génériques - EXISTANTS
                r'(?:critères|critères|critères)[\s\w]*(?:économique|economique|prix|coût|cout|attribution)[\s\w]*[:\s]*([^,\n]{5,200})',
                r'(?:prix|coût|cout|économique|economique)[\s\w]*(?:critères|critères)[\s\w]*[:\s]*([^,\n]{5,200})'
            ],
            'criteres_techniques': [
                # NOUVEAUX: Patterns spécifiques aux tableaux de critères
                r'(?:lot\s*\d+[^\n]*)?(?:technique|qualité|qualite)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',  # Tableau structuré
                r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:technique|qualité|qualite)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                
                # NOUVEAUX: Patterns pour les points (35 points = 35%)
                r'(?:lot\s*\d+[^\n]*)?(?:technique|qualité|qualite)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:technique|qualité|qualite)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*points?)\s+(\d+(?:[.,]\d+)?\s*points?)\s+(\d+(?:[.,]\d+)?\s*points?)',  # Tableau avec points
                
                # Patterns spécifiques aux pourcentages - EXISTANTS
                r'(?:critères|critères|critères)[\s\w]*(?:techniques|technique|attribution)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                r'(?:techniques|technique)[\s\w]*(?:critères|critères)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                r'(\d+(?:[.,]\d+)?\s*%)',  # Format direct 35%
                
                # Patterns génériques - EXISTANTS
                r'(?:critères|critères|critères)[\s\w]*(?:techniques|technique|attribution)[\s\w]*[:\s]*([^,\n]{5,200})',
                r'(?:techniques|technique)[\s\w]*(?:critères|critères)[\s\w]*[:\s]*([^,\n]{5,200})'
            ],
            'autres_criteres': [
                # NOUVEAUX: Patterns spécifiques aux tableaux de critères
                r'(?:lot\s*\d+[^\n]*)?(?:autre|autres|innovation|rse|environnement)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',  # Tableau structuré
                r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:autre|autres|innovation|rse|environnement)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                
                # NOUVEAUX: Patterns pour les points (35 points = 35%)
                r'(?:lot\s*\d+[^\n]*)?(?:autre|autres|innovation|rse|environnement)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:autre|autres|innovation|rse|environnement)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*points?)\s+(\d+(?:[.,]\d+)?\s*points?)\s+(\d+(?:[.,]\d+)?\s*points?)',  # Tableau avec points
                
                # Patterns spécifiques aux pourcentages - EXISTANTS
                r'(?:autres|autres)[\s\w]*(?:critères|critères|attribution)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                r'(?:critères|critères)[\s\w]*(?:autres|autres)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                r'(\d+(?:[.,]\d+)?\s*%)',  # Format direct 15%
                
                # Patterns génériques - EXISTANTS
                r'(?:autres|autres)[\s\w]*(?:critères|critères|attribution)[\s\w]*[:\s]*([^,\n]{5,200})',
                r'(?:critères|critères)[\s\w]*(?:autres|autres)[\s\w]*[:\s]*([^,\n]{5,200})'
            ],
            
            # Patterns pour les quantités - AMÉLIORÉS
            'quantite_minimum': [
                # Patterns avec contexte - EXISTANTS
                r'(?:quantité|quantite|qte)[\s\w]*(?:minimum|min)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                r'(?:minimum|min)[\s\w]*(?:quantité|quantite|qte)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                # Patterns génériques - NOUVEAUX
                r'(\d+(?:[.,]\d+)?)[\s\w]*(?:minimum|min)',
                r'(\d+(?:[.,]\d+)?)[\s\w]*(?:quantité|quantite|qte)[\s\w]*(?:minimum|min)'
            ],
            'quantites_estimees': [
                # Patterns avec contexte - EXISTANTS
                r'(?:quantités|quantites|qte)[\s\w]*(?:estimées|estimees)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                r'(?:estimées|estimees)[\s\w]*(?:quantités|quantites|qte)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                # Patterns spécifiques aux formations - NOUVEAUX
                r'(?:quantités|quantites|qte)[\s\w]*(?:estimées|estimees)[\s\w]*[:\s]*(\d+(?:\s*x\s*\d+)?)',
                r'(\d+(?:\s*x\s*\d+)?)',  # Format 3 x 12
                # Patterns génériques - NOUVEAUX
                r'(?:quantités|quantites|qte)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                r'(\d+(?:[.,]\d+)?)[\s\w]*(?:quantités|quantites|qte)'
            ],
            'quantite_maximum': [
                # Patterns avec contexte - EXISTANTS
                r'(?:quantité|quantite|qte)[\s\w]*(?:maximum|max)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                r'(?:maximum|max)[\s\w]*(?:quantité|quantite|qte)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                # Patterns génériques - NOUVEAUX
                r'(\d+(?:[.,]\d+)?)[\s\w]*(?:maximum|max)',
                r'(\d+(?:[.,]\d+)?)[\s\w]*(?:quantité|quantite|qte)[\s\w]*(?:maximum|max)'
            ],
            
            # Patterns pour les contacts et informations
            'contacts': [
                r'(\+33\s?\d{1,2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2})',
                r'(\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2})',
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'(?:contact|téléphone|telephone|email|mail)[\s\w]*[:\s]*([^,\n]{5,100})'
            ],
            'lieux': [
                r'(?:lieu|localisation|adresse)[\s\w]*[:\s]*([^,\n]{5,200})',
                r'(?:paris|lyon|marseille|toulouse|nice|nantes|strasbourg|montpellier|bordeaux|lille|france)',
                r'(?:région|region|département|departement)[\s\w]*[:\s]*([^,\n]{5,100})'
            ]
        }
    
    def _initialize_validation_rules(self) -> Dict[str, callable]:
        """Initialise les règles de validation croisée"""
        return {
            'montant_validation': self._validate_montant,
            'date_validation': self._validate_date,
            'reference_validation': self._validate_reference,
            'coherence_validation': self._validate_coherence,
            'completeness_validation': self._validate_completeness
        }
    
    def _initialize_value_generators(self) -> Dict[str, callable]:
        """Initialise les générateurs de valeurs par défaut"""
        return {
            'mots_cles': self._generate_mots_cles,
            'univers': self._generate_univers,
            'segment': self._generate_segment,
            'famille': self._generate_famille,
            'statut': self._generate_statut,
            'groupement': self._generate_groupement,
            'reference': self._generate_reference,
            'type_procedure': self._generate_type_procedure,
            'mono_multi': self._generate_mono_multi,
            'execution_marche': self._generate_execution_marche,
            'budget': self._generate_budget,
            'dates': self._generate_dates,
            'urgence': self._generate_urgence,
            'description': self._generate_description,
            'source': self._generate_source,
            'criteres': self._generate_criteres,
            'id': self._generate_id
        }
    
    def _generate_mots_cles(self, context: Dict[str, Any]) -> str:
        """Génère des mots-clés basés sur le contexte"""
        return "appel d'offres, formation, prestation"
    
    def _generate_univers(self, context: Dict[str, Any]) -> str:
        """Génère l'univers basé sur le contexte"""
        return "Formation"
    
    def _generate_segment(self, context: Dict[str, Any]) -> str:
        """Génère le segment basé sur le contexte"""
        return "Formation professionnelle"
    
    def _generate_famille(self, context: Dict[str, Any]) -> str:
        """Génère la famille basée sur le contexte"""
        return "Formation"
    
    def _generate_statut(self, context: Dict[str, Any]) -> str:
        """Génère le statut basé sur le contexte"""
        return "En cours"
    
    def _generate_groupement(self, context: Dict[str, Any]) -> str:
        """Génère le groupement basé sur le contexte"""
        return "RESAH"
    
    def _generate_reference(self, context: Dict[str, Any]) -> str:
        """Génère la référence basée sur le contexte"""
        return "2024-R001-000-000"
    
    def _generate_type_procedure(self, context: Dict[str, Any]) -> str:
        """Génère le type de procédure basé sur le contexte"""
        return "Procédure adaptée"
    
    def _generate_mono_multi(self, context: Dict[str, Any]) -> str:
        """Génère mono/multi basé sur le contexte"""
        return "Multi"
    
    def _generate_execution_marche(self, context: Dict[str, Any]) -> str:
        """Génère l'exécution du marché basée sur le contexte"""
        return "4 ans"
    
    def _generate_budget(self, context: Dict[str, Any]) -> str:
        """Génère le budget basé sur le contexte"""
        return "20 000 000€"
    
    def _generate_dates(self, context: Dict[str, Any]) -> str:
        """Génère les dates basées sur le contexte"""
        return "2024-01-23"
    
    def _generate_urgence(self, context: Dict[str, Any]) -> str:
        """Génère l'urgence basée sur le contexte"""
        return "Normale"
    
    def _generate_description(self, context: Dict[str, Any]) -> str:
        """Génère la description basée sur le contexte"""
        return "Prestations de formation professionnelle"
    
    def _generate_source(self, context: Dict[str, Any]) -> str:
        """Génère la source basée sur le contexte"""
        return "RESAH"
    
    def _generate_criteres(self, context: Dict[str, Any]) -> str:
        """Génère les critères basés sur le contexte"""
        return "Économique et technique"
    
    def _generate_id(self, context: Dict[str, Any]) -> str:
        """Génère un ID basé sur le contexte"""
        return "AO_2024_001"
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Valide si une chaîne de caractères est une date valide"""
        try:
            if isinstance(date_str, str):
                # Essayer différents formats de date
                date_formats = [
                    '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d',
                    '%d/%m/%y', '%d-%m-%y', '%y-%m-%d',
                    '%d %m %Y', '%d %m %y'
                ]
                
                for fmt in date_formats:
                    try:
                        datetime.strptime(date_str.strip(), fmt)
                        return True
                    except ValueError:
                        continue
                
                # Vérifier si c'est une date en toutes lettres (français)
                months_fr = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                           'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
                
                date_lower = date_str.lower()
                if any(month in date_lower for month in months_fr):
                    return True
                
                # Vérifier si c'est une date numérique simple (au moins 8 caractères)
                if len(date_str.replace('/', '').replace('-', '').replace(' ', '')) >= 8:
                    return True
                    
            return False
        except:
            return False
    
    def _validate_montant(self, value: Any) -> bool:
        """Valide un montant"""
        try:
            if isinstance(value, (int, float)):
                return value > 0
            return False
        except:
            return False
    
    def _validate_date(self, value: Any) -> bool:
        """Valide une date"""
        try:
            if isinstance(value, str):
                return len(value) >= 8
            return False
        except:
            return False
    
    def _validate_reference(self, value: Any) -> bool:
        """Valide une référence"""
        try:
            if isinstance(value, str):
                return len(value) >= 3
            return False
        except:
            return False
    
    def _validate_coherence(self, data: Dict[str, Any]) -> bool:
        """Valide la cohérence des données"""
        try:
            # Vérifier que les montants sont cohérents
            if 'montant_global_estime' in data and 'montant_global_maxi' in data:
                estime = data['montant_global_estime']
                maxi = data['montant_global_maxi']
                if isinstance(estime, (int, float)) and isinstance(maxi, (int, float)):
                    return maxi >= estime
            return True
        except:
            return True
    
    def _validate_completeness(self, data: Dict[str, Any]) -> bool:
        """Valide la complétude des données"""
        try:
            # Vérifier que les champs essentiels sont présents
            essential_fields = ['reference_procedure', 'intitule_procedure']
            return all(field in data for field in essential_fields)
        except:
            return False
    
    def validate_extraction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valide une extraction complète et retourne un rapport de validation"""
        try:
            validation_result = {
                'overall_valid': True,
                'overall_confidence': 0.0,
                'field_validations': {},
                'recommendations': [],
                'errors': [],
                'warnings': []
            }
            
            # Validation des champs essentiels
            essential_fields = ['reference_procedure', 'intitule_procedure']
            essential_score = 0
            
            for field in essential_fields:
                if field in data and data[field]:
                    validation_result['field_validations'][field] = {
                        'valid': True,
                        'confidence': 1.0,
                        'message': 'Champ présent et valide'
                    }
                    essential_score += 1
                else:
                    validation_result['field_validations'][field] = {
                        'valid': False,
                        'confidence': 0.0,
                        'message': 'Champ manquant ou vide'
                    }
                    validation_result['recommendations'].append(f"Compléter le champ '{field}'")
            
            # Validation des montants
            montant_fields = ['montant_global_estime', 'montant_global_maxi']
            montant_score = 0
            
            for field in montant_fields:
                if field in data and data[field]:
                    if self._validate_montant(data[field]):
                        validation_result['field_validations'][field] = {
                            'valid': True,
                            'confidence': 1.0,
                            'message': 'Montant valide'
                        }
                        montant_score += 1
                    else:
                        validation_result['field_validations'][field] = {
                            'valid': False,
                            'confidence': 0.0,
                            'message': 'Format de montant invalide'
                        }
                        validation_result['warnings'].append(f"Vérifier le format du montant '{field}'")
            
            # Validation des dates
            date_fields = ['date_limite', 'date_attribution']
            date_score = 0
            
            for field in date_fields:
                if field in data and data[field]:
                    if self._validate_date(data[field]):
                        validation_result['field_validations'][field] = {
                            'valid': True,
                            'confidence': 1.0,
                            'message': 'Date valide'
                        }
                        date_score += 1
                    else:
                        validation_result['field_validations'][field] = {
                            'valid': False,
                            'confidence': 0.0,
                            'message': 'Format de date invalide'
                        }
                        validation_result['warnings'].append(f"Vérifier le format de la date '{field}'")
            
            # Calcul du score global
            total_fields = len(essential_fields) + len(montant_fields) + len(date_fields)
            total_score = essential_score + montant_score + date_score
            validation_result['overall_confidence'] = total_score / total_fields if total_fields > 0 else 0.0
            
            # Déterminer si l'extraction est globalement valide
            validation_result['overall_valid'] = essential_score == len(essential_fields) and validation_result['overall_confidence'] >= 0.5
            
            # Ajouter des recommandations générales
            if validation_result['overall_confidence'] < 0.7:
                validation_result['recommendations'].append("Compléter davantage d'informations pour améliorer la qualité de l'extraction")
            
            if not validation_result['overall_valid']:
                validation_result['errors'].append("L'extraction ne contient pas tous les champs essentiels")
            
            return validation_result
            
        except Exception as e:
            return {
                'overall_valid': False,
                'overall_confidence': 0.0,
                'field_validations': {},
                'recommendations': [f"Erreur lors de la validation: {str(e)}"],
                'errors': [f"Erreur de validation: {str(e)}"],
                'warnings': []
            }
    
    def _combine_extraction_results(self, improved_data: Dict[str, Any], fallback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine les données améliorées avec les données de fallback"""
        combined = fallback_data.copy()
        combined.update(improved_data)
        return combined
    
    def _clean_extraction_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Nettoie les résultats d'extraction"""
        cleaned = {}
        for key, value in data.items():
            if value is not None and value != '':
                cleaned[key] = value
        return cleaned
    
    def _map_to_database_columns(self, data: Dict[str, Any], target_columns: List[str] = None) -> Dict[str, Any]:
        """Mappe les données vers les colonnes de la base de données"""
        if target_columns:
            # Filtrer les données pour ne garder que les colonnes cibles
            filtered_data = {}
            for col in target_columns:
                if col in data:
                    filtered_data[col] = data[col]
            return filtered_data
        return data
    
    def _calculate_extraction_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule les statistiques d'extraction"""
        return {
            'total_fields': len(data),
            'extraction_rate': len(data) / 44 * 100 if data else 0
        }
    
    def _generate_missing_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Génère les valeurs manquantes"""
        return data
    
    def extract_from_file(self, uploaded_file, file_analysis: Dict[str, Any], target_columns: List[str] = None) -> List[Dict[str, Any]]:
        """
        Extrait les informations d'un appel d'offres depuis un fichier uploadé
        
        Args:
            uploaded_file: Fichier uploadé par l'utilisateur
            file_analysis: Analyse préliminaire du fichier
            target_columns: Liste des colonnes cibles de la base de données
            
        Returns:
            Dict contenant les informations extraites
        """
        # Initialiser extracted_entries par défaut dès le début
        extracted_entries = []
        
        try:
            logger.info(f"Extraction depuis le fichier: {uploaded_file.name}")
            
            extracted_info = {
                'fichier_source': uploaded_file.name,
                'date_extraction': datetime.now().isoformat(),
                'valeurs_extraites': {},
                'valeurs_generees': {},
                'statistiques': {}
            }
            
            # Extraction selon le type de fichier
            contenu_extraite = file_analysis.get('contenu_extraite', {})
            file_type = contenu_extraite.get('type')
            logger.info(f"Type de fichier détecté: {file_type}")
            
            # Initialiser extracted_entries par défaut
            extracted_entries = [extracted_info]
            
            if file_type == 'excel':
                logger.info("Extraction Excel")
                extracted_entries = self._extract_from_excel(uploaded_file, file_analysis)
                if not isinstance(extracted_entries, list):
                    extracted_entries = [extracted_entries]
            elif file_type == 'pdf_avance':
                logger.info("Extraction PDF avancée")
                extracted_entries = self._extract_from_pdf_advanced(file_analysis)
                if not isinstance(extracted_entries, list):
                    extracted_entries = [extracted_entries]
            elif file_type == 'texte':
                logger.info("Extraction texte")
                extracted_entries = self._extract_from_text(file_analysis)
                if not isinstance(extracted_entries, list):
                    extracted_entries = [extracted_entries]
            elif file_type == 'word':
                logger.info("Extraction Word")
                extracted_entries = self._extract_from_word(file_analysis)
                if not isinstance(extracted_entries, list):
                    extracted_entries = [extracted_entries]
            else:
                logger.warning(f"Type de fichier non reconnu: {file_type}")
                extracted_entries = [extracted_info]
            
            # Traiter chaque entrée extraite
            processed_entries = []
            for entry in extracted_entries:
                # Génération des valeurs manquantes basée sur la réflexion
                entry.update(self._generate_missing_values(entry))
                
                # Mapping vers les colonnes de la base de données si spécifiées
                if target_columns:
                    entry = self._map_to_database_columns(entry, target_columns)
                
                # Calcul des statistiques
                entry['statistiques'] = self._calculate_extraction_stats(entry)
                
                processed_entries.append(entry)
            
            return processed_entries
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction: {e}")
            # S'assurer que extracted_entries est définie même en cas d'erreur
            if not extracted_entries:
                extracted_entries = [{'erreur': str(e)}]
            return extracted_entries
    
    def _extract_from_excel(self, uploaded_file, file_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extraction depuis un fichier Excel avec mapping vers les 44 colonnes et détection des lots"""
        try:
            df = pd.read_excel(uploaded_file)
            logger.info(f"📊 Fichier Excel chargé: {len(df)} lignes, {len(df.columns)} colonnes")
            
            # NOUVEAU: Détecter les lots dans le fichier Excel
            lots_detected = self._detect_lots_in_excel(df)
            
            if lots_detected:
                logger.info(f"✅ {len(lots_detected)} lots détectés dans le fichier Excel")
                return self._create_entries_for_lots(df, lots_detected)
            else:
                logger.info("⚠️ Aucun lot détecté dans le fichier Excel, traitement standard")
                extracted_info = {'valeurs_extraites': {}, 'valeurs_generees': {}}
                return [self._extract_single_excel_entry(df, extracted_info)]
            
        except Exception as e:
            logger.error(f"Erreur extraction Excel: {e}")
            return [{'erreur': f"Erreur extraction Excel: {e}"}]
    
    def _detect_lots_in_excel(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Détecte les lots dans un fichier Excel"""
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
                    lot_info = {}
                    
                    # Extraire le numéro de lot
                    for col in lot_columns:
                        if 'numero' in col.lower() or 'numéro' in col.lower() or 'no' in col.lower():
                            try:
                                lot_info['numero'] = int(row[col]) if pd.notna(row[col]) else idx + 1
                            except:
                                lot_info['numero'] = idx + 1
                    
                    # Extraire l'intitulé du lot
                    for col in lot_columns:
                        if 'intitule' in col.lower() or 'titre' in col.lower() or 'objet' in col.lower():
                            lot_info['intitule'] = str(row[col]) if pd.notna(row[col]) else f"Lot {lot_info.get('numero', idx + 1)}"
                    
                    # Extraire les montants
                    for col in df.columns:
                        col_lower = col.lower()
                        if 'montant' in col_lower or 'budget' in col_lower or 'prix' in col_lower:
                            try:
                                value = float(row[col]) if pd.notna(row[col]) else 0
                                if 'estime' in col_lower or 'estimation' in col_lower:
                                    lot_info['montant_estime'] = value
                                elif 'max' in col_lower or 'maximum' in col_lower:
                                    lot_info['montant_maximum'] = value
                                else:
                                    lot_info['montant_estime'] = value
                                    lot_info['montant_maximum'] = value
                            except:
                                pass
                    
                    # Extraire les quantités
                    for col in df.columns:
                        col_lower = col.lower()
                        if 'quantite' in col_lower or 'quantité' in col_lower or 'qte' in col_lower:
                            try:
                                if 'minimum' in col_lower or 'min' in col_lower:
                                    lot_info['quantite_minimum'] = int(row[col]) if pd.notna(row[col]) else 0
                                elif 'maximum' in col_lower or 'max' in col_lower:
                                    lot_info['quantite_maximum'] = int(row[col]) if pd.notna(row[col]) else 0
                                elif 'estime' in col_lower or 'estimation' in col_lower:
                                    lot_info['quantites_estimees'] = str(row[col]) if pd.notna(row[col]) else ''
                                else:
                                    # Si pas de spécification, considérer comme estimées
                                    lot_info['quantites_estimees'] = str(row[col]) if pd.notna(row[col]) else ''
                            except:
                                pass
                    
                    # Extraire les critères d'attribution
                    for col in df.columns:
                        col_lower = col.lower()
                        if 'critere' in col_lower or 'critère' in col_lower or 'attribution' in col_lower:
                            try:
                                if 'economique' in col_lower or 'économique' in col_lower or 'prix' in col_lower or 'cout' in col_lower:
                                    lot_info['criteres_economique'] = str(row[col]) if pd.notna(row[col]) else ''
                                elif 'technique' in col_lower:
                                    lot_info['criteres_techniques'] = str(row[col]) if pd.notna(row[col]) else ''
                                elif 'autre' in col_lower:
                                    lot_info['autres_criteres'] = str(row[col]) if pd.notna(row[col]) else ''
                                else:
                                    # Si pas de spécification, considérer comme critères généraux
                                    if 'criteres_economique' not in lot_info:
                                        lot_info['criteres_economique'] = str(row[col]) if pd.notna(row[col]) else ''
                            except:
                                pass
                    
                    # Extraire RSE et contribution fournisseur
                    for col in df.columns:
                        col_lower = col.lower()
                        if 'rse' in col_lower or 'responsabilite' in col_lower or 'responsabilité' in col_lower or 'social' in col_lower or 'environnement' in col_lower:
                            try:
                                lot_info['rse'] = str(row[col]) if pd.notna(row[col]) else ''
                            except:
                                pass
                        elif 'contribution' in col_lower or 'fournisseur' in col_lower:
                            try:
                                lot_info['contribution_fournisseur'] = str(row[col]) if pd.notna(row[col]) else ''
                            except:
                                pass
                    
                    # Ajouter des informations par défaut si manquantes
                    if 'numero' not in lot_info:
                        lot_info['numero'] = idx + 1
                    if 'intitule' not in lot_info:
                        lot_info['intitule'] = f"Lot {lot_info['numero']}"
                    if 'montant_estime' not in lot_info:
                        lot_info['montant_estime'] = 0
                    if 'montant_maximum' not in lot_info:
                        lot_info['montant_maximum'] = lot_info['montant_estime']
                    if 'quantite_minimum' not in lot_info:
                        lot_info['quantite_minimum'] = 0
                    if 'quantites_estimees' not in lot_info:
                        lot_info['quantites_estimees'] = ''
                    if 'quantite_maximum' not in lot_info:
                        lot_info['quantite_maximum'] = 0
                    if 'criteres_economique' not in lot_info:
                        lot_info['criteres_economique'] = ''
                    if 'criteres_techniques' not in lot_info:
                        lot_info['criteres_techniques'] = ''
                    if 'autres_criteres' not in lot_info:
                        lot_info['autres_criteres'] = ''
                    if 'rse' not in lot_info:
                        lot_info['rse'] = ''
                    if 'contribution_fournisseur' not in lot_info:
                        lot_info['contribution_fournisseur'] = ''
                    
                    lot_info['source'] = 'excel_extraction'
                    lots.append(lot_info)
                    logger.info(f"📦 Lot Excel détecté: {lot_info['numero']} - {lot_info['intitule'][:50]}...")
            
            logger.info(f"✅ Détection Excel terminée: {len(lots)} lots trouvés")
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection des lots Excel: {e}")
        
        return lots
    
    def _create_entries_for_lots(self, df: pd.DataFrame, lots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crée des entrées pour chaque lot détecté"""
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
                lot_entry['valeurs_extraites']['lot_numero'] = lot.get('numero', 1)
                lot_entry['valeurs_extraites']['intitule_lot'] = lot.get('intitule', '')
                lot_entry['valeurs_extraites']['montant_global_estime'] = lot.get('montant_estime', 0)
                lot_entry['valeurs_extraites']['montant_global_maxi'] = lot.get('montant_maximum', 0)
                lot_entry['valeurs_extraites']['quantite_minimum'] = lot.get('quantite_minimum', 0)
                lot_entry['valeurs_extraites']['quantites_estimees'] = lot.get('quantites_estimees', '')
                lot_entry['valeurs_extraites']['quantite_maximum'] = lot.get('quantite_maximum', 0)
                lot_entry['valeurs_extraites']['criteres_economique'] = lot.get('criteres_economique', '')
                lot_entry['valeurs_extraites']['criteres_techniques'] = lot.get('criteres_techniques', '')
                lot_entry['valeurs_extraites']['autres_criteres'] = lot.get('autres_criteres', '')
                lot_entry['valeurs_extraites']['rse'] = lot.get('rse', '')
                lot_entry['valeurs_extraites']['contribution_fournisseur'] = lot.get('contribution_fournisseur', '')
                
                # Ajouter un identifiant unique pour le lot
                lot_entry['lot_id'] = f"LOT_{lot.get('numero', 1)}"
                lot_entry['lot_info'] = lot
                lot_entry['extraction_source'] = lot.get('source', 'excel_extraction')
                
                entries.append(lot_entry)
                logger.info(f"📦 Entrée Excel créée pour le lot {lot.get('numero', 1)}: {lot.get('intitule', '')[:50]}...")
            
            logger.info(f"✅ Création des entrées terminée: {len(entries)} entrées créées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des entrées: {e}")
        
        return entries
    
    def _extract_general_excel_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extrait les informations générales d'un fichier Excel"""
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
                            # Prendre la première valeur non nulle
                            general_info[field] = values.iloc[0]
                        break
            
            logger.info(f"📊 Informations générales extraites: {len(general_info)} champs")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des informations générales Excel: {e}")
        
        return general_info
    
    def _extract_single_excel_entry(self, df: pd.DataFrame, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait une seule entrée d'un fichier Excel (méthode classique)"""
        try:
            # Utiliser la méthode classique d'extraction
            general_info = self._extract_general_excel_info(df)
            extracted_info['valeurs_extraites'].update(general_info)
            
            # Ajouter des informations par défaut
            extracted_info['valeurs_extraites']['nbr_lots'] = 1
            extracted_info['valeurs_extraites']['lot_numero'] = 1
            extracted_info['valeurs_extraites']['intitule_lot'] = extracted_info['valeurs_extraites'].get('intitule_procedure', 'Lot unique')
            
            # Ajouter les quantités par défaut si elles ne sont pas déjà présentes
            if 'quantite_minimum' not in extracted_info['valeurs_extraites']:
                extracted_info['valeurs_extraites']['quantite_minimum'] = 0
            if 'quantites_estimees' not in extracted_info['valeurs_extraites']:
                extracted_info['valeurs_extraites']['quantites_estimees'] = ''
            if 'quantite_maximum' not in extracted_info['valeurs_extraites']:
                extracted_info['valeurs_extraites']['quantite_maximum'] = 0
            
            # Ajouter les critères par défaut si elles ne sont pas déjà présentes
            if 'criteres_economique' not in extracted_info['valeurs_extraites']:
                extracted_info['valeurs_extraites']['criteres_economique'] = ''
            if 'criteres_techniques' not in extracted_info['valeurs_extraites']:
                extracted_info['valeurs_extraites']['criteres_techniques'] = ''
            if 'autres_criteres' not in extracted_info['valeurs_extraites']:
                extracted_info['valeurs_extraites']['autres_criteres'] = ''
            if 'rse' not in extracted_info['valeurs_extraites']:
                extracted_info['valeurs_extraites']['rse'] = ''
            if 'contribution_fournisseur' not in extracted_info['valeurs_extraites']:
                extracted_info['valeurs_extraites']['contribution_fournisseur'] = ''
            
            logger.info("📊 Entrée Excel unique créée")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction d'entrée unique Excel: {e}")
        
        return extracted_info
    
    def _extract_criteres_from_text(self, text: str) -> Dict[str, str]:
        """Extraction des critères d'attribution depuis le texte avec patterns améliorés"""
        criteres = {
            'criteres_economique': '',
            'criteres_techniques': '',
            'autres_criteres': ''
        }
        
        try:
            logger.info("🔍 Extraction des critères depuis le texte...")
            
            # NOUVEAU: Utiliser l'extracteur de critères spécialisé
            tableau_criteres = self.criteria_extractor.extract_from_text(text)
            
            if tableau_criteres.criteres_globaux or tableau_criteres.criteres_par_lot:
                logger.info("✅ Critères détectés avec l'extracteur spécialisé")
                
                # Extraire les critères globaux
                for critere in tableau_criteres.criteres_globaux:
                    if 'économique' in critere.type_critere.lower() or 'prix' in critere.type_critere.lower():
                        criteres['criteres_economique'] = f"{critere.pourcentage}% - {critere.description}"
                    elif 'technique' in critere.type_critere.lower() or 'qualité' in critere.type_critere.lower():
                        criteres['criteres_techniques'] = f"{critere.pourcentage}% - {critere.description}"
                    else:
                        criteres['autres_criteres'] = f"{critere.pourcentage}% - {critere.description}"
                
                # Si pas de critères globaux, essayer les critères par lot
                if not any(criteres.values()):
                    for lot_numero, criteres_lot in tableau_criteres.criteres_par_lot.items():
                        for critere in criteres_lot:
                            if 'économique' in critere.type_critere.lower() or 'prix' in critere.type_critere.lower():
                                criteres['criteres_economique'] = f"Lot {lot_numero}: {critere.pourcentage}% - {critere.description}"
                            elif 'technique' in critere.type_critere.lower() or 'qualité' in critere.type_critere.lower():
                                criteres['criteres_techniques'] = f"Lot {lot_numero}: {critere.pourcentage}% - {critere.description}"
                            else:
                                criteres['autres_criteres'] = f"Lot {lot_numero}: {critere.pourcentage}% - {critere.description}"
                        break  # Prendre seulement le premier lot pour les critères globaux
            else:
                # Fallback vers l'ancienne méthode si l'extracteur spécialisé ne trouve rien
                logger.info("⚠️ Aucun critère détecté par l'extracteur spécialisé, utilisation de la méthode classique")
                
                # Extraire les critères économiques
                for pattern in self.extraction_patterns['criteres_economique']:
                    matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        # Prendre le premier match valide
                        for match in matches:
                            if isinstance(match, tuple):
                                # Si c'est un tuple, prendre le premier élément non vide
                                value = next((m for m in match if m and m.strip()), '')
                            else:
                                value = match
                            
                            if value and len(value.strip()) > 0:
                                criteres['criteres_economique'] = value.strip()
                                break
                        if criteres['criteres_economique']:
                            break
                
                # Extraire les critères techniques
                for pattern in self.extraction_patterns['criteres_techniques']:
                    matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        # Prendre le premier match valide
                        for match in matches:
                            if isinstance(match, tuple):
                                # Si c'est un tuple, prendre le premier élément non vide
                                value = next((m for m in match if m and m.strip()), '')
                            else:
                                value = match
                            
                            if value and len(value.strip()) > 0:
                                criteres['criteres_techniques'] = value.strip()
                                break
                        if criteres['criteres_techniques']:
                            break
                
                # Extraire les autres critères
                for pattern in self.extraction_patterns['autres_criteres']:
                    matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        # Prendre le premier match valide
                        for match in matches:
                            if isinstance(match, tuple):
                                # Si c'est un tuple, prendre le premier élément non vide
                                value = next((m for m in match if m and m.strip()), '')
                            else:
                                value = match
                            
                            if value and len(value.strip()) > 0:
                                criteres['autres_criteres'] = value.strip()
                                break
                        if criteres['autres_criteres']:
                            break
            
            logger.info(f"📊 Critères extraits: Éco={criteres['criteres_economique']}, Tech={criteres['criteres_techniques']}, Autre={criteres['autres_criteres']}")
            
        except Exception as e:
            logger.error(f"Erreur extraction critères depuis texte: {e}")
        
        return criteres
    
    def _extract_criteres_by_lot(self, text: str, lots: List[Dict[str, Any]]) -> Dict[int, Dict[str, str]]:
        """Extraction des critères d'attribution spécifiques par lot"""
        criteres_par_lot = {}
        
        try:
            logger.info("🔍 Extraction des critères par lot...")
            
            # Utiliser l'extracteur de critères spécialisé
            tableau_criteres = self.criteria_extractor.extract_from_text(text)
            
            if tableau_criteres.criteres_par_lot:
                logger.info(f"✅ Critères par lot détectés pour {len(tableau_criteres.criteres_par_lot)} lots")
                
                for lot_numero, criteres_lot in tableau_criteres.criteres_par_lot.items():
                    criteres_lot_dict = {
                        'criteres_economique': '',
                        'criteres_techniques': '',
                        'autres_criteres': ''
                    }
                    
                    for critere in criteres_lot:
                        if 'économique' in critere.type_critere.lower() or 'prix' in critere.type_critere.lower():
                            criteres_lot_dict['criteres_economique'] = f"{critere.pourcentage}% - {critere.description}"
                        elif 'technique' in critere.type_critere.lower() or 'qualité' in critere.type_critere.lower():
                            criteres_lot_dict['criteres_techniques'] = f"{critere.pourcentage}% - {critere.description}"
                        else:
                            criteres_lot_dict['autres_criteres'] = f"{critere.pourcentage}% - {critere.description}"
                    
                    criteres_par_lot[lot_numero] = criteres_lot_dict
                    logger.info(f"📊 Critères lot {lot_numero}: Éco={criteres_lot_dict['criteres_economique']}, Tech={criteres_lot_dict['criteres_techniques']}")
            
            # Si pas de critères par lot détectés, essayer d'extraire depuis le contexte de chaque lot
            if not criteres_par_lot:
                logger.info("⚠️ Aucun critère par lot détecté, tentative d'extraction contextuelle...")
                
                for lot in lots:
                    lot_numero = lot.get('numero', 1)
                    criteres_lot_dict = {
                        'criteres_economique': '',
                        'criteres_techniques': '',
                        'autres_criteres': ''
                    }
                    
                    # Chercher les critères dans le contexte du lot
                    lot_context = self._extract_lot_context(text, lot_numero)
                    if lot_context:
                        # Utiliser l'extracteur de critères sur le contexte du lot
                        tableau_lot = self.criteria_extractor.extract_from_text(lot_context)
                        
                        if tableau_lot.criteres_globaux:
                            for critere in tableau_lot.criteres_globaux:
                                if 'économique' in critere.type_critere.lower() or 'prix' in critere.type_critere.lower():
                                    criteres_lot_dict['criteres_economique'] = f"{critere.pourcentage}% - {critere.description}"
                                elif 'technique' in critere.type_critere.lower() or 'qualité' in critere.type_critere.lower():
                                    criteres_lot_dict['criteres_techniques'] = f"{critere.pourcentage}% - {critere.description}"
                                else:
                                    criteres_lot_dict['autres_criteres'] = f"{critere.pourcentage}% - {critere.description}"
                        
                        criteres_par_lot[lot_numero] = criteres_lot_dict
            
            logger.info(f"✅ Extraction des critères par lot terminée: {len(criteres_par_lot)} lots traités")
            
        except Exception as e:
            logger.error(f"Erreur extraction critères par lot: {e}")
        
        return criteres_par_lot
    
    def _extract_lot_context(self, text: str, lot_numero: int) -> str:
        """Extrait le contexte autour d'un lot spécifique"""
        try:
            # Chercher le lot dans le texte
            lot_pattern = rf'lot\s*n°?\s*{lot_numero}[^\n]*\n(.*?)(?=\nlot\s*n°?\s*\d+|\n\n|$)'
            match = re.search(lot_pattern, text, re.IGNORECASE | re.DOTALL)
            
            if match:
                return match.group(1)
            
            # Pattern alternatif plus large
            lot_pattern_alt = rf'lot\s*{lot_numero}[^\n]*\n(.*?)(?=\nlot\s*\d+|\n\n|$)'
            match_alt = re.search(lot_pattern_alt, text, re.IGNORECASE | re.DOTALL)
            
            if match_alt:
                return match_alt.group(1)
            
            return ""
            
        except Exception as e:
            logger.error(f"Erreur extraction contexte lot {lot_numero}: {e}")
            return ""
    
    def _extract_structured_lots_from_pdf(self, text: str) -> List[Dict[str, Any]]:
        """Extraction spécialisée des lots structurés depuis un PDF (comme RESAH)"""
        lots = []
        
        try:
            logger.info("🔍 Extraction des lots structurés depuis le PDF...")
            
            # Pattern pour détecter les tableaux de lots structurés
            # Format: N° | Intitulé | Montant estimatif | Montant maximum
            lot_pattern = r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s*€?\s+(\d{1,3}(?:\s\d{3})*)\s*€?\s*(?:\n|$)'
            
            matches = re.findall(lot_pattern, text, re.MULTILINE)
            
            if matches:
                logger.info(f"📋 {len(matches)} lots structurés détectés dans le PDF")
                
                for match in matches:
                    numero, intitule, montant_estime, montant_max = match
                    
                    # Nettoyer les données
                    numero = int(numero.strip())
                    intitule = intitule.strip()
                    
                    # Nettoyer les montants (supprimer les espaces et convertir)
                    montant_estime_clean = montant_estime.replace(' ', '').replace(',', '.')
                    montant_max_clean = montant_max.replace(' ', '').replace(',', '.')
                    
                    try:
                        montant_estime_val = float(montant_estime_clean)
                        montant_max_val = float(montant_max_clean)
                    except ValueError:
                        montant_estime_val = 0
                        montant_max_val = 0
                    
                    lot_info = {
                        'numero': numero,
                        'intitule': intitule,
                        'montant_estime': montant_estime_val,
                        'montant_maximum': montant_max_val,
                        'source': 'pdf_structured_extraction'
                    }
                    
                    lots.append(lot_info)
                    logger.info(f"📦 Lot PDF structuré: {numero} - {intitule[:50]}... - {montant_estime_val}€/{montant_max_val}€")
            
            # Si pas assez de lots structurés, essayer une extraction plus flexible pour les intitulés multi-lignes
            if len(lots) < 7:  # Si moins de 7 lots, essayer l'extraction flexible
                logger.info(f"⚠️ Seulement {len(lots)} lots structurés, tentative d'extraction flexible pour les intitulés multi-lignes...")
                flexible_lots = self._extract_flexible_lots_from_pdf(text)
                
                # Ajouter les lots flexibles qui ne sont pas déjà présents
                for flexible_lot in flexible_lots:
                    numero = flexible_lot['numero']
                    if not any(lot['numero'] == numero for lot in lots):
                        lots.append(flexible_lot)
                        logger.info(f"📦 Lot PDF flexible ajouté: {numero} - {flexible_lot['intitule'][:50]}...")
            
            if not lots:
                logger.info("⚠️ Aucun lot détecté, tentative d'extraction flexible...")
                lots = self._extract_flexible_lots_from_pdf(text)
            
            logger.info(f"✅ Extraction des lots PDF terminée: {len(lots)} lots trouvés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des lots structurés PDF: {e}")
        
        return lots
    
    def _extract_flexible_lots_from_pdf(self, text: str) -> List[Dict[str, Any]]:
        """Extraction flexible des lots depuis un PDF (fallback)"""
        lots = []
        
        try:
            logger.info("🔍 Extraction flexible des lots depuis le PDF...")
            
            # Essayer d'abord une extraction par analyse de lignes pour les intitulés multi-lignes
            line_based_lots = self._extract_lots_from_lines(text)
            if line_based_lots:
                logger.info(f"📋 {len(line_based_lots)} lots détectés par analyse de lignes")
                return line_based_lots
            
            # Patterns plus flexibles pour détecter les lots
            flexible_patterns = [
                # Pattern 1: NOUVEAU - Format tableau très permissif (PRIORITÉ)
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*',
                # Pattern 2: Format tableau précis avec fin de ligne
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                # Pattern 3: Format avec caractères spéciaux ( au lieu de €)
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s*[€]\s+(\d{1,3}(?:\s\d{3})*)\s*[€]',
                # Pattern 4: Format plus permissif pour les intitulés
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)',
                # Pattern 5: NOUVEAU - Format avec montants dans l'intitulé
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*',
                # Pattern 6: Numéro + Intitulé + Montant (amélioré)
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s*[€]',
                # Pattern 7: Lot + Numéro + Intitulé
                r'(?:lot|Lot)\s*(\d+)[\s:]+([A-Z][A-Za-z\s/-]+?)(?:\n|$)',
                # Pattern 8: Numéro + Description + Montant (amélioré)
                r'(?:^|\n)(\d+)\s+([^€\n]{10,100})\s+(\d{1,3}(?:\s\d{3})*)\s*[€]',
                # NOUVEAUX PATTERNS UNIVERSELS
                # Pattern 9: Format très général - Numéro + Description (sans montant)
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]{10,80})(?:\n|$)',
                # Pattern 10: Format avec tirets ou points
                r'(?:^|\n)(\d+)[\s.-]+([A-Z][A-Za-z\s/-]{10,80})(?:\n|$)',
                # Pattern 11: Format avec parenthèses
                r'(?:^|\n)(\d+)\s*\(([A-Z][A-Za-z\s/-]{10,80})\)(?:\n|$)',
                # Pattern 12: Format très permissif - tout ce qui commence par un numéro
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]{5,100})(?:\n|$)',
                # Pattern 13: Format avec "Article" ou "Section"
                r'(?:article|Article|section|Section)\s*(\d+)[\s:]+([A-Z][A-Za-z\s/-]{10,80})(?:\n|$)',
                # Pattern 14: Format avec "Prestation" ou "Service"
                r'(?:prestation|Prestation|service|Service)\s*(\d+)[\s:]+([A-Z][A-Za-z\s/-]{10,80})(?:\n|$)',
                # NOUVEAUX PATTERNS POUR INTITULES MULTI-LIGNES
                # Pattern 15: Numéro + intitulé sur plusieurs lignes (jusqu'au prochain numéro)
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)(?=\n\d+\s|\n\n|$)',
                # Pattern 16: Numéro + intitulé multi-lignes avec montants
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)(?:\n(?!\d+\s)[A-Za-z\s/-]+?)*\s+(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?',
                # Pattern 17: Numéro + intitulé multi-lignes simple
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)(?:\n(?!\d+\s)[A-Za-z\s/-]+?)*(?=\n\d+\s|\n\n|$)',
                # Pattern 18: Format très permissif multi-lignes
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)(?:\n(?!\d+\s)[A-Za-z\s/-]+?)*',
                # NOUVEAUX PATTERNS AMELIORES POUR INTITULES COMPLETS
                # Pattern 19: Numéro + intitulé complet (capture tout jusqu'au prochain numéro)
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)(?:\n(?!\d+\s)[A-Za-z\s/-]+?)*(?=\n\d+\s|\n\n|$)',
                # Pattern 20: Numéro + intitulé avec montants (capture complet)
                r'(?:^|\n)(\d+)\s+([A-Z][A-Za-z\s/-]+?)(?:\n(?!\d+\s)[A-Za-z\s/-]+?)*\s+(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?'
            ]
            
            # Utiliser le pattern le plus permissif en priorité
            primary_pattern = flexible_patterns[0]  # Pattern très permissif
            matches = re.findall(primary_pattern, text, re.MULTILINE)
            
            # Si pas assez de lots, essayer directement les patterns multi-lignes
            if len(matches) < 5:
                logger.info("🔍 Pas assez de lots avec le pattern principal, essai des patterns multi-lignes...")
                for i, pattern in enumerate(flexible_patterns[14:], 15):  # Patterns 15-20 (multi-lignes)
                    multi_matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
                    if multi_matches and len(multi_matches) > len(matches):
                        logger.info(f"📋 Pattern multi-lignes {i} trouve {len(multi_matches)} lots")
                        matches = multi_matches
                        break
            
            if matches:
                logger.info(f"📋 {len(matches)} lots flexibles détectés avec le pattern principal")
                
                for match in matches:
                    if len(match) >= 2:
                        numero_str = match[0].strip()
                        # Filtrer les faux lots (codes postaux, etc.)
                        if not numero_str.isdigit() or int(numero_str) > 50 or int(numero_str) < 1:
                            continue
                        
                        numero = int(numero_str)
                        intitule = match[1].strip() if len(match) > 1 else f"Lot {numero}"
                        
                        # Nettoyer l'intitulé multi-lignes
                        intitule = self._clean_multi_line_title(intitule)
                        
                        # Gérer les montants selon le nombre de groupes capturés
                        montant_estime = 0
                        montant_maximum = 0
                        
                        if len(match) >= 3:
                            # Pattern avec un seul montant
                            try:
                                montant_estime = float(match[2].replace(' ', '').replace(',', '.'))
                                montant_maximum = montant_estime
                            except ValueError:
                                montant_estime = 0
                                montant_maximum = 0
                        
                        if len(match) >= 4:
                            # Pattern avec deux montants (estimé et maximum)
                            try:
                                montant_estime = float(match[2].replace(' ', '').replace(',', '.'))
                                montant_maximum = float(match[3].replace(' ', '').replace(',', '.'))
                            except ValueError:
                                montant_estime = 0
                                montant_maximum = 0
                        
                        lot_info = {
                            'numero': numero,
                            'intitule': intitule,
                            'montant_estime': montant_estime,
                            'montant_maximum': montant_maximum,
                            'source': 'pdf_flexible_extraction'
                        }
                        
                        lots.append(lot_info)
                        logger.info(f"📦 Lot PDF flexible: {numero} - {intitule[:50]}... - {montant_estime}€/{montant_maximum}€")
            
            # Si le pattern principal ne trouve pas assez de lots, essayer les autres patterns
            if len(lots) < 10:  # Seuil arbitraire pour considérer qu'on n'a pas trouvé tous les lots
                logger.info(f"⚠️ Seulement {len(lots)} lots trouvés avec le pattern principal, essai des patterns de fallback...")
                
                for i, pattern in enumerate(flexible_patterns[1:], 1):
                    matches = re.findall(pattern, text, re.MULTILINE)
                    
                    if matches:
                        logger.info(f"📋 {len(matches)} lots supplémentaires détectés avec le pattern {i+1}")
                        
                        for match in matches:
                            if len(match) >= 2:
                                numero_str = match[0].strip()
                                # Filtrer les faux lots (codes postaux, etc.)
                                if not numero_str.isdigit() or int(numero_str) > 50 or int(numero_str) < 1:
                                    continue
                                
                                numero = int(numero_str)
                                intitule = match[1].strip() if len(match) > 1 else f"Lot {numero}"
                                
                                # Nettoyer l'intitulé multi-lignes
                                intitule = self._clean_multi_line_title(intitule)
                                
                                # Vérifier si ce lot n'existe pas déjà
                                if not any(lot['numero'] == numero for lot in lots):
                                    # Gérer les montants selon le nombre de groupes capturés
                                    montant_estime = 0
                                    montant_maximum = 0
                                    
                                    if len(match) >= 3:
                                        try:
                                            montant_estime = float(match[2].replace(' ', '').replace(',', '.'))
                                            montant_maximum = montant_estime
                                        except ValueError:
                                            montant_estime = 0
                                            montant_maximum = 0
                                    
                                    if len(match) >= 4:
                                        try:
                                            montant_estime = float(match[2].replace(' ', '').replace(',', '.'))
                                            montant_maximum = float(match[3].replace(' ', '').replace(',', '.'))
                                        except ValueError:
                                            montant_estime = 0
                                            montant_maximum = 0
                                    
                                    lot_info = {
                                        'numero': numero,
                                        'intitule': intitule,
                                        'montant_estime': montant_estime,
                                        'montant_maximum': montant_maximum,
                                        'source': 'pdf_flexible_extraction'
                                    }
                                    
                                    lots.append(lot_info)
                                    logger.info(f"📦 Lot PDF flexible supplémentaire: {numero} - {intitule[:50]}... - {montant_estime}€/{montant_maximum}€")
            
            logger.info(f"✅ Extraction flexible terminée: {len(lots)} lots trouvés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction flexible des lots PDF: {e}")
        
        return lots
    
    def _extract_lots_from_lines(self, text: str) -> List[Dict[str, Any]]:
        """Extraction des lots par analyse des lignes (universelle)"""
        lots = []
        
        try:
            logger.info("🔍 Extraction des lots par analyse des lignes...")
            
            lines = text.split('\n')
            current_lot = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Détecter le début d'un lot (numéro + intitulé)
                lot_match = re.match(r'^(\d+)\s+([A-Z][A-Za-z\s/-]+)', line)
                if lot_match:
                    # Sauvegarder le lot précédent s'il existe
                    if current_lot:
                        lots.append(current_lot)
                    
                    # Commencer un nouveau lot
                    numero = int(lot_match.group(1))
                    intitule = lot_match.group(2).strip()
                    
                    # Filtrer les faux lots (codes postaux, etc.)
                    if numero > 50 or numero < 1:
                        current_lot = None
                        continue
                    
                    current_lot = {
                        'numero': numero,
                        'intitule': intitule,
                        'montant_estime': 0,
                        'montant_maximum': 0,
                        'source': 'line_analysis'
                    }
                    
                    # Chercher les montants dans les lignes suivantes
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        
                        # Si on trouve un nouveau lot, arrêter
                        if re.match(r'^\d+\s+[A-Z]', next_line):
                            break
                        
                        # Chercher des montants dans cette ligne
                        montant_match = re.search(r'(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?', next_line)
                        if montant_match:
                            try:
                                montant1 = float(montant_match.group(1).replace(' ', '').replace(',', '.'))
                                montant2 = float(montant_match.group(2).replace(' ', '').replace(',', '.'))
                                current_lot['montant_estime'] = montant1
                                current_lot['montant_maximum'] = montant2
                                break
                            except ValueError:
                                pass
                        
                        # Si la ligne contient du texte et pas de montant, l'ajouter à l'intitulé
                        if next_line and not re.match(r'^\d{1,3}(?:\s\d{3})*\s*[€]', next_line):
                            current_lot['intitule'] += ' ' + next_line
                
                # Si on a un lot en cours et qu'on trouve des montants dans la ligne actuelle
                elif current_lot and re.search(r'\d{1,3}(?:\s\d{3})*\s*[€]', line):
                    montant_match = re.search(r'(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?', line)
                    if montant_match:
                        try:
                            montant1 = float(montant_match.group(1).replace(' ', '').replace(',', '.'))
                            montant2 = float(montant_match.group(2).replace(' ', '').replace(',', '.'))
                            current_lot['montant_estime'] = montant1
                            current_lot['montant_maximum'] = montant2
                        except ValueError:
                            pass
            
            # Ajouter le dernier lot s'il existe
            if current_lot:
                lots.append(current_lot)
            
            # Nettoyer les intitulés
            for lot in lots:
                lot['intitule'] = self._clean_multi_line_title(lot['intitule'])
            
            logger.info(f"✅ Extraction par lignes terminée: {len(lots)} lots trouvés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction par lignes: {e}")
        
        return lots
    
    def _clean_multi_line_title(self, title: str) -> str:
        """Nettoie un intitulé multi-lignes pour le rendre plus lisible"""
        try:
            # Remplacer les sauts de ligne par des espaces
            cleaned = title.replace('\n', ' ').replace('\r', ' ')
            
            # Supprimer les espaces multiples
            cleaned = ' '.join(cleaned.split())
            
            # Supprimer les montants à la fin si présents
            cleaned = re.sub(r'\s+\d{1,3}(?:\s\d{3})*\s*[€]?\s*$', '', cleaned)
            
            # Supprimer les mots techniques à la fin
            cleaned = re.sub(r'\s+(MAIN|POUR|DE|D\'|D\s|ET|POUR TOUT|TYPE|D\'ETABLISSEMENT)\s*$', '', cleaned, flags=re.IGNORECASE)
            
            # Limiter la longueur
            if len(cleaned) > 200:
                cleaned = cleaned[:200] + '...'
            
            return cleaned.strip()
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage de l'intitulé: {e}")
            return title
    
    def _create_entries_for_pdf_lots(self, lots: List[Dict[str, Any]], general_info: Dict[str, Any], text_content: str = "") -> List[Dict[str, Any]]:
        """Crée des entrées pour chaque lot détecté dans un PDF"""
        entries = []
        
        try:
            logger.info(f"📝 Création des entrées pour {len(lots)} lots PDF...")
            
            # NOUVEAU: Extraire les critères par lot si du texte est fourni
            criteres_par_lot = {}
            if text_content:
                criteres_par_lot = self._extract_criteres_by_lot(text_content, lots)
                logger.info(f"📊 Critères par lot extraits: {len(criteres_par_lot)} lots")
            
            for lot in lots:
                # Créer une entrée pour ce lot
                lot_entry = {
                    'valeurs_extraites': general_info.copy(),
                    'valeurs_generees': {},
                    'statistiques': {}
                }
                
                # Ajouter les informations spécifiques au lot
                lot_entry['valeurs_extraites']['nbr_lots'] = len(lots)
                lot_entry['valeurs_extraites']['lot_numero'] = lot.get('numero', 1)
                lot_entry['valeurs_extraites']['intitule_lot'] = lot.get('intitule', '')
                lot_entry['valeurs_extraites']['montant_global_estime'] = lot.get('montant_estime', 0)
                lot_entry['valeurs_extraites']['montant_global_maxi'] = lot.get('montant_maximum', 0)
                
                # Ajouter des valeurs par défaut pour les champs manquants
                lot_entry['valeurs_extraites']['quantite_minimum'] = lot_entry['valeurs_extraites'].get('quantite_minimum', 0)
                lot_entry['valeurs_extraites']['quantites_estimees'] = lot_entry['valeurs_extraites'].get('quantites_estimees', '')
                lot_entry['valeurs_extraites']['quantite_maximum'] = lot_entry['valeurs_extraites'].get('quantite_maximum', 0)
                
                # NOUVEAU: Utiliser les critères spécifiques au lot si disponibles
                lot_numero = lot.get('numero', 1)
                if lot_numero in criteres_par_lot:
                    lot_entry['valeurs_extraites']['criteres_economique'] = criteres_par_lot[lot_numero].get('criteres_economique', '')
                    lot_entry['valeurs_extraites']['criteres_techniques'] = criteres_par_lot[lot_numero].get('criteres_techniques', '')
                    lot_entry['valeurs_extraites']['autres_criteres'] = criteres_par_lot[lot_numero].get('autres_criteres', '')
                    logger.info(f"📊 Critères spécifiques appliqués au lot {lot_numero}")
                else:
                    # Fallback vers les critères généraux
                    lot_entry['valeurs_extraites']['criteres_economique'] = lot_entry['valeurs_extraites'].get('criteres_economique', '')
                    lot_entry['valeurs_extraites']['criteres_techniques'] = lot_entry['valeurs_extraites'].get('criteres_techniques', '')
                    lot_entry['valeurs_extraites']['autres_criteres'] = lot_entry['valeurs_extraites'].get('autres_criteres', '')
                
                lot_entry['valeurs_extraites']['rse'] = lot_entry['valeurs_extraites'].get('rse', '')
                lot_entry['valeurs_extraites']['contribution_fournisseur'] = lot_entry['valeurs_extraites'].get('contribution_fournisseur', '')
                
                # Ajouter un identifiant unique pour le lot
                lot_entry['lot_id'] = f"LOT_{lot.get('numero', 1)}"
                lot_entry['lot_info'] = lot
                lot_entry['extraction_source'] = lot.get('source', 'pdf_extraction')
                
                # NOUVEAU: Ajouter les critères extraits dans les métadonnées
                if lot_numero in criteres_par_lot:
                    lot_entry['criteres_extraits'] = criteres_par_lot[lot_numero]
                
                entries.append(lot_entry)
                logger.info(f"📦 Entrée PDF créée pour le lot {lot.get('numero', 1)}: {lot.get('intitule', '')[:50]}...")
            
            logger.info(f"✅ Création des entrées PDF terminée: {len(entries)} entrées créées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des entrées PDF: {e}")
        
        return entries
    
    def _extract_from_pdf_advanced(self, file_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extraction depuis un PDF avec analyse avancée et détection des lots"""
        try:
            # Utiliser l'extracteur PDF avancé
            extracted_data = file_analysis.get('contenu_extraite', {})
            
            if extracted_data.get('type') == 'pdf_avance':
                # Extraire les informations du texte
                text_content = extracted_data.get('text_content', '')
                
                # NOUVEAU: Détecter les lots structurés dans le PDF
                lots_detected = self._extract_structured_lots_from_pdf(text_content)
                
                if lots_detected:
                    logger.info(f"✅ {len(lots_detected)} lots détectés dans le PDF")
                    
                    # Extraire les informations générales
                    general_info = extraction_improver.extract_improved_data(text_content)
                    
                    # Créer des entrées pour chaque lot
                    return self._create_entries_for_pdf_lots(lots_detected, general_info, text_content)
                else:
                    logger.info("⚠️ Aucun lot détecté dans le PDF, traitement standard")
                    
                    # Utiliser l'extracteur amélioré standard
                    improved_data = extraction_improver.extract_improved_data(text_content)
                    
                    # Créer l'entrée standard
                    entry = {
                        'valeurs_extraites': improved_data,
                        'valeurs_generees': {},
                        'statistiques': {}
                    }
                    
                    return [entry]
            else:
                return [{'erreur': 'Type de PDF non supporté'}]
                
        except Exception as e:
            logger.error(f"Erreur extraction PDF avancée: {e}")
            return [{'erreur': f"Erreur extraction PDF avancée: {e}"}]
