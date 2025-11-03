"""
🎯 Gestionnaire de Patterns - Configuration Modulaire
====================================================

Gestion centralisée et modulaire des patterns regex pour l'extraction
d'informations depuis les documents d'appels d'offres.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from functools import lru_cache
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class PatternManager:
    """Gestionnaire centralisé des patterns d'extraction"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialise le gestionnaire de patterns
        
        Args:
            config_file: Fichier de configuration JSON (optionnel)
        """
        self.patterns = self._initialize_patterns()
        self.compiled_patterns = {}
        self.performance_stats = {
            'total_compilations': 0,
            'cache_hits': 0,
            'compilation_errors': 0
        }
        
        if config_file:
            self.load_from_file(config_file)
    
    def _initialize_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialise les patterns par défaut"""
        return {
            'montants': {
                'estime': [
                    # Patterns avec contexte complet
                    r'(?:montant|budget|prix|coût|cout|valeur|estimation|enveloppe|allocation)[\s\w]*(?:global|total|estimé|estime|prévisionnel|previsionnel)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?|HT|TTC|HTA|TVA)',
                    r'(?:budget|montant|prix|coût|cout|estimation|enveloppe)[\s\w]*(?:global|total|estimé|estime)[\s\w]*[:\s]*(\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                    r'(?:montant|budget|prix|coût|cout|estimation)[\s\w]*[:\s]*(\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                    # Patterns avec unités
                    r'(?:budget|montant|prix|coût|cout|estimation)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|k\s*€|milliers)',
                    r'(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|k\s*€|milliers)',
                    r'(?:budget|montant|prix|coût|cout|estimation)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)\s*(?:m€|meuros?|millions?|m\s*€)',
                    r'(\d+(?:[.,]\d+)?)\s*(?:m€|meuros?|millions?|m\s*€)',
                    # Patterns avec contexte de marché
                    r'(?:marché|marche|contrat|prestation)[\s\w]*(?:montant|budget|prix|coût|cout|estimation)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                    # Patterns avec contexte d'appel d'offres
                    r'(?:appel|offre|ao|consultation)[\s\w]*(?:montant|budget|prix|coût|cout|estimation)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)'
                ],
                'maxi': [
                    # Patterns avec contexte de maximum/plafond
                    r'(?:maximum|maxi|plafond|limite|seuil|seuil)[\s\w]*(?:budgetaire|budgetaire|global|total|montant)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?|HT|TTC)',
                    r'(?:budget|montant|prix|coût|cout)[\s\w]*(?:maximum|maxi|plafond|limite|seuil)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                    r'(?:enveloppe|allocation|dotation)[\s\w]*(?:maximum|maxi|plafond|limite)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                    # Patterns avec unités
                    r'(?:montant|budget|prix|coût|cout)[\s\w]*(?:maximum|maxi|plafond|limite|seuil)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|k\s*€)',
                    r'(?:montant|budget|prix|coût|cout)[\s\w]*(?:maximum|maxi|plafond|limite|seuil)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)\s*(?:m€|meuros?|millions?|m\s*€)',
                    # Patterns avec contexte de marché
                    r'(?:marché|marche|contrat)[\s\w]*(?:maximum|maxi|plafond|limite)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)',
                    # Patterns avec contexte d'appel d'offres
                    r'(?:appel|offre|ao|consultation)[\s\w]*(?:maximum|maxi|plafond|limite)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?)'
                ]
            },
            'dates': {
                'limite': [
                    # Patterns très spécifiques avec contexte complet (priorité haute)
                    r'(?:date|échéance|clôture|cloture|fin|expiration|dernière)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot|réception|reception)[\s\w]*[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(?:date|échéance|clôture|cloture|fin|expiration|dernière)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot|réception|reception)[\s\w]*[:\s\-]*(\d{4}-\d{2}-\d{2})',
                    r'(?:date|échéance|clôture|cloture|fin|expiration|dernière)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot|réception|reception)[\s\w]*[:\s\-]*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
                    # Patterns avec variations de format (mois abrégés)
                    r'(?:date|échéance|clôture|cloture|fin|expiration|dernière)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot|réception|reception)[\s\w]*[:\s\-]*(\d{1,2}\s+(?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)\.?\s+\d{4})',
                    # Patterns avec "au plus tard"
                    r'(?:au\s+plus\s+tard|avant\s+le|jusqu[\'"]?au)[\s\w]*[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(?:au\s+plus\s+tard|avant\s+le|jusqu[\'"]?au)[\s\w]*[:\s\-]*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
                    # Patterns avec contexte d'appel d'offres
                    r'(?:appel|offre|ao|consultation|marché|marche|rc)[\s\w]*(?:date|échéance|clôture|cloture|fin)[\s\w]*(?:limite|remise|offres|candidature|soumission|dépôt|depot)[\s\w]*[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    # Patterns avec format "JJ/MM/YYYY" ou "DD/MM/YY"
                    r'(?:remise|dépôt|depot|soumission)[\s\w]*(?:des?\s+)?(?:offres|candidatures)[\s\w]*[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    # Patterns génériques (moins prioritaires)
                    r'(?:date|échéance|clôture|cloture|fin|expiration)[\s\w]*[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(?:date|échéance|clôture|cloture|fin|expiration)[\s\w]*[:\s\-]*(\d{4}-\d{2}-\d{2})'
                ],
                'attribution': [
                    # Patterns très spécifiques avec contexte complet (priorité haute)
                    r'(?:date|jour)[\s\w]*(?:d[\'"]?attribution|attribué|attribue)[\s\w]*(?:du\s+)?(?:marché|marche|contrat|prestation|lot)[\s\w]*[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(?:date|jour)[\s\w]*(?:d[\'"]?attribution|attribué|attribue)[\s\w]*(?:du\s+)?(?:marché|marche|contrat|prestation|lot)[\s\w]*[:\s\-]*(\d{4}-\d{2}-\d{2})',
                    r'(?:marché|marche|contrat|prestation|lot)[\s\w]*(?:attribué|attribue|attribution)[\s\w]*(?:le|le\s+)?[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(?:marché|marche|contrat|prestation|lot)[\s\w]*(?:attribué|attribue|attribution)[\s\w]*(?:le|le\s+)?[:\s\-]*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
                    # Patterns avec "attribué le"
                    r'(?:attribué|attribue|attribution)[\s\w]*(?:le|en|du)[\s\w]*[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(?:attribué|attribue|attribution)[\s\w]*(?:le|en|du)[\s\w]*[:\s\-]*(\d{4}-\d{2}-\d{2})',
                    r'(?:attribué|attribue|attribution)[\s\w]*(?:le|en|du)[\s\w]*[:\s\-]*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
                    # Patterns avec contexte d'appel d'offres
                    r'(?:appel|offre|ao|consultation|rc)[\s\w]*(?:attribué|attribue|attribution)[\s\w]*(?:le|en)[\s\w]*[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(?:appel|offre|ao|consultation|rc)[\s\w]*(?:attribué|attribue|attribution)[\s\w]*(?:le|en)[\s\w]*[:\s\-]*(\d{4}-\d{2}-\d{2})',
                    # Patterns génériques (moins prioritaires)
                    r'(?:attribution|attribué|attribue)[\s\w]*[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(?:attribution|attribué|attribue)[\s\w]*[:\s\-]*(\d{4}-\d{2}-\d{2})'
                ]
            },
            'references': {
                'procedure': [
                    # Patterns spécifiques aux formats RESAH/UGAP
                    r'(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*(\d{4}-[A-Z]\d{3})',
                    r'(?:ao|marché|marche|contrat|prestation)[\s\w]*(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*[:\s]*(\d{4}-[A-Z]\d{3})',
                    r'(\d{4}-[A-Z]\d{3})',  # Format direct 2024-R001
                    r'(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',  # Format complet 2024-R001-000-000
                    # Patterns génériques
                    r'(?:ref|réf|référence|code|identifiant|identifiant|numéro|numero|no)[\s\w]*(?:procédure|procedure|ao|marché|marche|contrat|prestation)[\s\w]*[:\s]*([A-Z0-9\-_]+)',
                    r'([A-Z]{2,}\d{4,})',  # Pattern pour codes comme AO2024001
                    r'([A-Z]{2,}-\d{4,})',  # Pattern pour codes comme AO-2024-001
                    r'([A-Z]{2,}_\d{4,})',  # Pattern pour codes comme AO_2024_001
                    r'([A-Z]{2,}\.\d{4,})',  # Pattern pour codes comme AO.2024.001
                    r'([A-Z]{2,}\s\d{4,})'   # Pattern pour codes comme AO 2024 001
                ],
                'intitule': [
                    # Patterns avec contexte complet
                    r'(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*(?:procédure|procedure|marché|marche|ao|contrat|prestation)[\s\w]*[:\s]*([^,\n]{10,200})',
                    r'(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})',
                    r'(?:appel|offre|marché|marche|contrat|prestation)[\s\w]*[:\s]*([^,\n]{10,200})',
                    # Patterns avec contexte d'appel d'offres
                    r'(?:appel|offre|ao|consultation)[\s\w]*(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})',
                    # Patterns avec contexte de marché
                    r'(?:marché|marche|contrat|prestation)[\s\w]*(?:intitulé|intitule|titre|objet|libellé|libelle|dénomination|denomination|nom)[\s\w]*[:\s]*([^,\n]{10,200})'
                ]
            },
            'procedures': {
                'type_procedure': [
                    # Patterns spécifiques avec contexte
                    r'(?:type|mode|forme)[\s\w]*(?:procédure|procedure|marché|marche|ao)[\s\w]*[:\s]*([^,\n]{5,100})',
                    r'(?:procédure|procedure)[\s\w]*(?:type|mode|forme)[\s\w]*[:\s]*([^,\n]{5,100})',
                    # Patterns directs pour les types courants
                    r'(appel\s+d[\'"]offres?\s+ouvert)',
                    r'(appel\s+d[\'"]offres?\s+restreint)',
                    r'(consultation)',
                    r'(marché\s+de\s+services)',
                    r'(achat\s+direct)',
                    r'(commande)',
                    r'(convention)',
                    r'(accord\s+cadre)',
                    # Patterns avec contexte complet
                    r'(?:procédure|procedure)[\s\w]*[:\s]*([^,\n]{5,100})',
                    r'(?:appel|offre|ao|consultation)[\s\w]*[:\s]*([^,\n]{5,100})'
                ],
                'mono_multi': [
                    # Patterns spécifiques avec contexte
                    r'(?:allotissement|lotissement)[\s\w]*[:\s]*(oui|non|unique|multiple|mono|multi)',
                    r'(?:attribution)[\s\w]*(?:mono|multi|unique|multiple)[\s\w]*[:\s]*([^,\n]{1,50})',
                    # Patterns directs
                    r'(mono[\s-]?attributif)',
                    r'(multi[\s-]?attributif)',
                    r'(marché\s+unique)',
                    r'(marché\s+alloti)',
                    r'(lotissement|allotissement)',
                    # Patterns avec contexte complet
                    r'(?:marché|marche|procédure|procedure)[\s\w]*(?:unique|multiple|mono|multi|alloti|loti)[\s\w]*',
                    r'(?:unique|multiple|mono|multi)[\s\w]*(?:marché|marche|procédure|procedure)',
                    # Patterns de détection intelligente (si plusieurs lots)
                    r'(?:nombre|nbr|nb)[\s\w]*(?:lots?)[\s\w]*[:\s]*(\d+)'
                ]
            },
            'groupements': {
                'groupement': [
                    # Patterns spécifiques aux groupements connus
                    r'(?:groupement|consortium|alliance|partenariat|réseau|reseau|organisme|acheteur|client|maître|donneur)[\s\w]*[:\s]*(RESAH|UGAP|CNRS|UNIHA|CAIH)',
                    r'(RESAH|UGAP|CNRS|UNIHA|CAIH)',  # Direct match
                    r'(?:groupement|consortium|alliance|partenariat|réseau|reseau|organisme|acheteur|client|maître|donneur)[\s\w]*[:\s]*([A-Z]{2,})',
                    # Patterns génériques
                    r'(?:groupement|consortium|alliance|partenariat|réseau|reseau)[\s\w]*[:\s]*([^,\n]{5,100})',
                    r'(?:ministère|mairie|région|département|établissement|collectivité|entreprise|université|hôpital|cnrs|ugap|resah|uniha)',
                    r'(?:organisme|acheteur|client|maître|donneur)[\s\w]*[:\s]*([^,\n]{5,100})'
                ]
            },
            'lots': {
                'nbr_lots': [
                    # Patterns avec contexte complet
                    r'(?:nombre|nbr|nb)[\s\w]*(?:lots|lot)[\s\w]*[:\s]*(\d+)',
                    r'(?:lots|lot)[\s\w]*[:\s]*(\d+)',
                    r'(\d+)[\s\w]*(?:lots|lot)',
                    # Patterns avec contexte de marché
                    r'(?:marché|marche|contrat|prestation)[\s\w]*(?:nombre|nbr|nb)[\s\w]*(?:lots|lot)[\s\w]*[:\s]*(\d+)',
                    # Patterns avec contexte d'appel d'offres
                    r'(?:appel|offre|ao|consultation)[\s\w]*(?:nombre|nbr|nb)[\s\w]*(?:lots|lot)[\s\w]*[:\s]*(\d+)',
                    # Patterns spécifiques aux tableaux de lots
                    r'Allotissement[^\n]*(\d+)[\s\w]*(?:lots|lot)',
                    r'LOTISSEMENT[^\n]*(\d+)[\s\w]*(?:lots|lot)',
                    r'REPARTITION[^\n]*(\d+)[\s\w]*(?:lots|lot)'
                ],
                'lot_numero': [
                    # Patterns avec contexte de lot
                    r'(?:lot|lot)[\s\w]*(?:n°|numero|numéro|no)[\s\w]*[:\s]*(\d+)',
                    r'(?:lot|lot)[\s\w]*[:\s]*(\d+)',
                    r'lot[\s\w]*(\d+)',
                    # Patterns avec contexte de marché
                    r'(?:marché|marche|contrat|prestation)[\s\w]*(?:lot|lot)[\s\w]*(?:n°|numero|numéro|no)[\s\w]*[:\s]*(\d+)',
                    # Patterns génériques
                    r'(\d+)[\s\w]*(?:lot|lot)'
                ],
                'intitule_lot': [
                    # Patterns avec contexte de lot
                    r'(?:intitulé|intitule|titre|objet|libellé|libelle)[\s\w]*(?:lot|lot)[\s\w]*[:\s]*([^,\n]{5,200})',
                    r'(?:lot|lot)[\s\w]*[:\s]*([^,\n]{5,200})',
                    # Patterns spécifiques aux formations
                    r'(?:réalisation|realisation)[\s\w]*(?:prestations|prestation)[\s\w]*(?:formations|formation)[\s\w]*(?:transverses|transverse|santé|sante|soins)[\s\w]*[:\s]*([^,\n]{5,200})',
                    # Patterns génériques
                    r'(?:intitulé|intitule|titre|objet|libellé|libelle)[\s\w]*[:\s]*([^,\n]{5,200})',
                    # Patterns spécifiques aux tableaux de lots
                    r'(?:^|\n)\d+\s+([A-Z][A-Z\s/]+?)\s+\d{1,3}(?:\s\d{3})*\s+\d{1,3}(?:\s\d{3})*\s*(?:\n|$)',
                    r'(?:^|\n)\d+\s+([A-Z][A-Z\s/\n]+?)\s+\d{1,3}(?:\s\d{3})*\s+\d{1,3}(?:\s\d{3})*\s*(?:\n|$)'
                ]
            },
            'criteres': {
                'economique': [
                    # Patterns spécifiques aux tableaux de critères
                    r'(?:lot\s*\d+[^\n]*)?(?:économique|prix|coût|cout)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:économique|prix|coût|cout)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    # Patterns pour les points (35 points = 35%)
                    r'(?:lot\s*\d+[^\n]*)?(?:économique|prix|coût|cout)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                    r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:économique|prix|coût|cout)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                    # Patterns spécifiques aux pourcentages
                    r'(?:critères|critères|critères)[\s\w]*(?:économique|economique|prix|coût|cout|attribution)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    r'(?:prix|coût|cout|économique|economique)[\s\w]*(?:critères|critères)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    r'(\d+(?:[.,]\d+)?\s*%)',  # Format direct 40%
                    # Patterns génériques
                    r'(?:critères|critères|critères)[\s\w]*(?:économique|economique|prix|coût|cout|attribution)[\s\w]*[:\s]*([^,\n]{5,200})',
                    r'(?:prix|coût|cout|économique|economique)[\s\w]*(?:critères|critères)[\s\w]*[:\s]*([^,\n]{5,200})'
                ],
                'techniques': [
                    # Patterns spécifiques aux tableaux de critères
                    r'(?:lot\s*\d+[^\n]*)?(?:technique|qualité|qualite)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:technique|qualité|qualite)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    # Patterns pour les points (35 points = 35%)
                    r'(?:lot\s*\d+[^\n]*)?(?:technique|qualité|qualite)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                    r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:technique|qualité|qualite)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                    # Patterns spécifiques aux pourcentages
                    r'(?:critères|critères|critères)[\s\w]*(?:techniques|technique|attribution)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    r'(?:techniques|technique)[\s\w]*(?:critères|critères)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    r'(\d+(?:[.,]\d+)?\s*%)',  # Format direct 35%
                    # Patterns génériques
                    r'(?:critères|critères|critères)[\s\w]*(?:techniques|technique|attribution)[\s\w]*[:\s]*([^,\n]{5,200})',
                    r'(?:techniques|technique)[\s\w]*(?:critères|critères)[\s\w]*[:\s]*([^,\n]{5,200})'
                ],
                'autres': [
                    # Patterns spécifiques aux tableaux de critères
                    r'(?:lot\s*\d+[^\n]*)?(?:autre|autres|innovation|rse|environnement)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:autre|autres|innovation|rse|environnement)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    # Patterns pour les points (35 points = 35%)
                    r'(?:lot\s*\d+[^\n]*)?(?:autre|autres|innovation|rse|environnement)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                    r'(?:critères?\s+d[\'"]attribution[^\n]*)?(?:autre|autres|innovation|rse|environnement)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*points?)',
                    # Patterns spécifiques aux pourcentages
                    r'(?:autres|autres)[\s\w]*(?:critères|critères|attribution)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    r'(?:critères|critères)[\s\w]*(?:autres|autres)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
                    r'(\d+(?:[.,]\d+)?\s*%)',  # Format direct 15%
                    # Patterns génériques
                    r'(?:autres|autres)[\s\w]*(?:critères|critères|attribution)[\s\w]*[:\s]*([^,\n]{5,200})',
                    r'(?:critères|critères)[\s\w]*(?:autres|autres)[\s\w]*[:\s]*([^,\n]{5,200})'
                ]
            },
            'quantites': {
                'minimum': [
                    # Patterns avec contexte
                    r'(?:quantité|quantite|qte)[\s\w]*(?:minimum|min)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                    r'(?:minimum|min)[\s\w]*(?:quantité|quantite|qte)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                    # Patterns génériques
                    r'(\d+(?:[.,]\d+)?)[\s\w]*(?:minimum|min)',
                    r'(\d+(?:[.,]\d+)?)[\s\w]*(?:quantité|quantite|qte)[\s\w]*(?:minimum|min)'
                ],
                'estimees': [
                    # Patterns avec contexte
                    r'(?:quantités|quantites|qte)[\s\w]*(?:estimées|estimees)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                    r'(?:estimées|estimees)[\s\w]*(?:quantités|quantites|qte)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                    # Patterns spécifiques aux formations
                    r'(?:quantités|quantites|qte)[\s\w]*(?:estimées|estimees)[\s\w]*[:\s]*(\d+(?:\s*x\s*\d+)?)',
                    r'(\d+(?:\s*x\s*\d+)?)',  # Format 3 x 12
                    # Patterns génériques
                    r'(?:quantités|quantites|qte)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                    r'(\d+(?:[.,]\d+)?)[\s\w]*(?:quantités|quantites|qte)'
                ],
                'maximum': [
                    # Patterns avec contexte
                    r'(?:quantité|quantite|qte)[\s\w]*(?:maximum|max)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                    r'(?:maximum|max)[\s\w]*(?:quantité|quantite|qte)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)',
                    # Patterns génériques
                    r'(\d+(?:[.,]\d+)?)[\s\w]*(?:maximum|max)',
                    r'(\d+(?:[.,]\d+)?)[\s\w]*(?:quantité|quantite|qte)[\s\w]*(?:maximum|max)'
                ]
            },
            'durees': {
                'duree_marche': [
                    # Patterns très spécifiques avec contexte complet (priorité haute)
                    r'(?:durée|duree)[\s\w]{0,40}?(?:du\s+)?(?:marché|marche|contrat|prestation)[\s\w]{0,20}[:\s\-]*(\d{1,3})\s*(?:mois|mois\.|m\.?)',
                    r'(?:durée|duree)[\s\w]{0,40}?(?:du\s+)?(?:marché|marche|contrat|prestation)[\s\w]{0,20}[:\s\-]*(\d{1,3})\s*(?:ans|an|année|annee|années|annees)',
                    r'(?:marché|marche|contrat|prestation)[\s\w]{0,40}?(?:d[\'"]?une?\s+)?(?:durée|duree)[\s\w]{0,20}[:\s\-]*(\d{1,3})\s*(?:mois|mois\.|m\.?)',
                    r'(?:marché|marche|contrat|prestation)[\s\w]{0,40}?(?:d[\'"]?une?\s+)?(?:durée|duree)[\s\w]{0,20}[:\s\-]*(\d{1,3})\s*(?:ans|an|année|annee|années|annees)',
                    # Patterns avec conversion ans -> mois
                    r'(?:durée|duree)[\s\w]{0,40}?(?:du\s+)?(?:marché|marche|contrat|prestation)[\s\w]{0,20}[:\s\-]*(\d{1,2})\s*(?:ans|an|année|annee)(?:\s+(?:et|,)?\s*(\d{1,2})\s*(?:mois|mois\.|m\.?))?',
                    # Patterns avec format "X mois renouvelable"
                    r'(?:durée|duree)[\s\w]{0,40}?[:\s\-]*(\d{1,3})\s*(?:mois|mois\.|m\.?)(?:[\s\w]{0,20}?(?:renouvelable|reconduction))?',
                    # Patterns avec format "X ans"
                    r'(?:durée|duree)[\s\w]{0,40}?[:\s\-]*(\d{1,2})\s*(?:ans|an|année|annee)',
                    # Patterns génériques
                    r'(\d{1,3})\s*(?:mois|mois\.|m\.?)[\s\w]{0,20}?(?:durée|duree|de\s+marche|du\s+marche)',
                    r'(\d{1,2})\s*(?:ans|an|année|annee)[\s\w]{0,20}?(?:durée|duree|de\s+marche|du\s+marche)'
                ],
                'execution_marche': [
                    r'(?:modalités?|modalites?|conditions?)\s+d[\'\"]?ex[ée]cution[\s\w:,-]{0,10}(.+)',
                    r'ex[ée]cution\s+du\s+march[é|e]\s*[:\-]?\s*(.+)'
                ],
                'reconduction': [
                    # Patterns très spécifiques pour oui/non
                    r'(?:reconduction|reconductible|renouvellement)[\s\w:,-]{0,20}[:\s\-]*\s*(oui|non|possible|impossible|autorisée|autorisé|autorisée|non\s+autorisée|non\s+autorisé)',
                    r'(?:marché|marche|contrat)[\s\w]{0,20}?(?:reconduction|reconductible|renouvellement)[\s\w:,-]{0,20}[:\s\-]*\s*(oui|non|possible|impossible|autorisée|autorisé|autorisée)',
                    r'(?:reconduction|reconductible|renouvellement)[\s\w]{0,20}?(?:prévue|prevue|possible|autorisée|autorisé)[\s\w:,-]{0,10}[:\s\-]*\s*(oui|non|possible|impossible)',
                    # Patterns pour détecter l'absence (sans mention = non spécifié)
                    r'(?:sans\s+reconduction|sans\s+renouvellement|non\s+reconduction|non\s+renouvellement)',
                    r'(?:reconduction|renouvellement)[\s\w]{0,20}?(?:non\s+prévue|non\s+prevue|non\s+autorisée|non\s+autorisé)',
                    # Patterns pour nombre de reconductions
                    r'(?:reconduction|reconductible|renouvellement)[\s\w:,-]{0,50}?[:\s\-]*\s*(\d{1,2})\s*(?:fois|fois\.?|fois\s+de\s+\d{1,2}\s+mois)',
                    r'(?:reconduction|reconductible|renouvellement)[\s\w:,-]{0,50}?[:\s\-]*\s*(\d{1,2})\s*(?:ans|an|année|annee)',
                    # Pattern pour détecter si mentionné (même sans oui/non explicite)
                    r'(?:reconduction|reconductible|renouvellement)[\s\w]{0,30}?(?:possible|prévue|prevue|autorisée|autorisé)'
                ],
                'fin_sans_reconduction': [
                    # Patterns très spécifiques
                    r'(?:fin|échéance|expiration)[\s\w]{0,10}?(?:sans|non\s+)?(?:reconduction|renouvellement)[\s\w:,-]{0,20}[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(?:fin|échéance|expiration)[\s\w]{0,10}?(?:sans|non\s+)?(?:reconduction|renouvellement)[\s\w:,-]{0,20}[:\s\-]*(\d{4}-\d{2}-\d{2})',
                    r'(?:fin|échéance|expiration)[\s\w]{0,10}?(?:sans|non\s+)?(?:reconduction|renouvellement)[\s\w:,-]{0,20}[:\s\-]*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
                    # Patterns avec "du marché"
                    r'(?:fin|échéance|expiration)[\s\w]{0,10}?(?:du\s+)?(?:marché|marche|contrat)[\s\w]{0,10}?(?:sans|non\s+)?(?:reconduction|renouvellement)[\s\w:,-]{0,20}[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    # Patterns directs
                    r'fin\s+sans\s+reconduction[\s\w:,-]{0,20}[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'fin\s+sans\s+reconduction[\s\w:,-]{0,20}[:\s\-]*(\d{4}-\d{2}-\d{2})',
                    r'fin\s+sans\s+renouvellement[\s\w:,-]{0,20}[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
                ],
                'fin_avec_reconduction': [
                    # Patterns très spécifiques
                    r'(?:fin|échéance|expiration)[\s\w]{0,10}?(?:avec|en\s+tenant\s+compte\s+de|incluant)[\s\w]{0,10}?(?:la\s+)?(?:reconduction|renouvellement)[\s\w:,-]{0,20}[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(?:fin|échéance|expiration)[\s\w]{0,10}?(?:avec|en\s+tenant\s+compte\s+de|incluant)[\s\w]{0,10}?(?:la\s+)?(?:reconduction|renouvellement)[\s\w:,-]{0,20}[:\s\-]*(\d{4}-\d{2}-\d{2})',
                    r'(?:fin|échéance|expiration)[\s\w]{0,10}?(?:avec|en\s+tenant\s+compte\s+de|incluant)[\s\w]{0,10}?(?:la\s+)?(?:reconduction|renouvellement)[\s\w:,-]{0,20}[:\s\-]*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
                    # Patterns avec "du marché"
                    r'(?:fin|échéance|expiration)[\s\w]{0,10}?(?:du\s+)?(?:marché|marche|contrat)[\s\w]{0,10}?(?:avec|incluant)[\s\w]{0,10}?(?:la\s+)?(?:reconduction|renouvellement)[\s\w:,-]{0,20}[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    # Patterns directs
                    r'fin\s+avec\s+reconduction[\s\w:,-]{0,20}[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'fin\s+avec\s+reconduction[\s\w:,-]{0,20}[:\s\-]*(\d{4}-\d{2}-\d{2})',
                    r'fin\s+avec\s+renouvellement[\s\w:,-]{0,20}[:\s\-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
                ]
            },
            'rse': {
                'rse': [
                    r'(?:rse|responsabilit[ée]\s+soci[ée]tale|d[ée]veloppement\s+durable)[\s\w:,-]{0,10}(.+)',
                    r'crit[è|e]res?\s+rse[\s\w:,-]{0,10}(.+)'
                ]
            },
            'contribution': {
                'fournisseur': [
                    r'(?:contribution\s+fournisseur|participation\s+fournisseur)[\s\w:,-]{0,10}(.+)'
                ]
            },
            'metadonnees': {
                'infos_complementaires': [
                    r'(?:informations?|renseignements?)\s+compl[ée]mentaires?[\s\w:,-]{0,10}(.+)',
                    r'(?:infos?)\s+compl[ée]mentaires?[\s\w:,-]{0,10}(.+)'
                ],
                'remarques': [
                    r'(?:remarques?|commentaires?|observations?)\s*[:\-]\s*([^\n]{10,500})',
                    r'(?:remarque|commentaire|observation)\s+([^\n]{10,500})',
                    r'(?:note|remarque)\s*(?:générale|generale|finale)\s*[:\-]\s*([^\n]{10,500})'
                ],
                'notes_acheteur_procedure': [
                    r'(?:note|avis|commentaire)\s+(?:de\s+)?l[\'"]?acheteur[\s\w]*(?:sur\s+)?(?:la\s+)?(?:proc[ée]dure|procedure)[\s\w]*[:\-]\s*([^\n]{10,500})',
                    r'(?:note|avis)\s+(?:acheteur)[\s\w]*(?:proc[ée]dure|procedure)[\s\w]*[:\-]\s*([^\n]{10,500})'
                ],
                'notes_acheteur_fournisseur': [
                    r'(?:note|avis|commentaire)\s+(?:de\s+)?l[\'"]?acheteur[\s\w]*(?:sur\s+)?(?:le\s+)?(?:fournisseur|prestataire)[\s\w]*[:\-]\s*([^\n]{10,500})',
                    r'(?:note|avis)\s+(?:acheteur)[\s\w]*(?:fournisseur|prestataire)[\s\w]*[:\-]\s*([^\n]{10,500})'
                ],
                'notes_acheteur_positionnement': [
                    r'(?:note|avis|commentaire)\s+(?:de\s+)?l[\'"]?acheteur[\s\w]*(?:sur\s+)?(?:le\s+)?(?:positionnement)[\s\w]*[:\-]\s*([^\n]{10,500})',
                    r'(?:note|avis)\s+(?:acheteur)[\s\w]*(?:positionnement)[\s\w]*[:\-]\s*([^\n]{10,500})'
                ]
            },
            'acquisition': {
                'achat': [
                    r'\bachat\b[\s\w:,-]{0,10}(oui|non)',
                    r'\bacquisition\b[\s\w:,-]{0,10}(oui|non)'
                ],
                'credit_bail': [
                    r'cr[é|e]dit[-\s]?bail[\s\w:,-]{0,10}(oui|non)'
                ],
                'credit_bail_duree': [
                    r'cr[é|e]dit[-\s]?bail[\s\w:,-]{0,30}?(\d{1,3})\s*(?:mois|ans|an)'
                ],
                'location': [
                    r'\blocation\b[\s\w:,-]{0,10}(oui|non)'
                ],
                'location_duree': [
                    r'\blocation\b[\s\w:,-]{0,30}?(\d{1,3})\s*(?:mois|ans|an)'
                ],
                'mad': [
                    r'\bmad\b[\s\w:,-]{0,10}(oui|non)',
                    r'mise\s+[àa]\s+disposition[\s\w:,-]{0,10}(oui|non)'
                ]
            },
            'attribution': {
                'attributaire': [
                    r'(?:attributaire|titulaire|adjudicataire)[\s:\-]*([^\n]{3,200})'
                ],
                'produit_retenu': [
                    r'(?:produit\s+retenu|solution\s+retenue)[\s:\-]*([^\n]{3,200})'
                ]
            },
            'classification': {
                'segment': [
                    r'(?:segment)\s*[:\-]\s*([^\n]{3,120})',
                    r'(?:segment)\s+([^\n]{3,120})'
                ],
                'famille': [
                    r'(?:famille)\s*[:\-]\s*([^\n]{3,120})',
                    r'(?:famille)\s+([^\n]{3,120})'
                ]
            }
        }
    
    @lru_cache(maxsize=256)
    def get_patterns(self, category: str, subcategory: str = None) -> List[str]:
        """
        Récupère les patterns pour une catégorie et sous-catégorie
        
        Args:
            category: Catégorie de patterns (montants, dates, etc.)
            subcategory: Sous-catégorie (estime, limite, etc.)
            
        Returns:
            Liste des patterns
        """
        try:
            if subcategory:
                return self.patterns.get(category, {}).get(subcategory, [])
            else:
                # Retourner tous les patterns de la catégorie
                all_patterns = []
                for subcat_patterns in self.patterns.get(category, {}).values():
                    all_patterns.extend(subcat_patterns)
                return all_patterns
        except Exception as e:
            logger.error(f"Erreur récupération patterns {category}.{subcategory}: {e}")
            return []
    
    def get_field_patterns(self, field_name: str) -> List[str]:
        """
        Récupère les patterns pour un champ spécifique
        
        Args:
            field_name: Nom du champ (montant_global_estime, date_limite, etc.)
            
        Returns:
            Liste des patterns
        """
        # Mapping des champs vers les catégories
        field_mapping = {
            'montant_global_estime': ('montants', 'estime'),
            'montant_global_maxi': ('montants', 'maxi'),
            'date_limite': ('dates', 'limite'),
            'date_attribution': ('dates', 'attribution'),
            'reference_procedure': ('references', 'procedure'),
            'intitule_procedure': ('references', 'intitule'),
            'type_procedure': ('procedures', 'type_procedure'),
            'mono_multi': ('procedures', 'mono_multi'),
            'groupement': ('groupements', 'groupement'),
            'nbr_lots': ('lots', 'nbr_lots'),
            'lot_numero': ('lots', 'lot_numero'),
            'intitule_lot': ('lots', 'intitule_lot'),
            'criteres_economique': ('criteres', 'economique'),
            'criteres_techniques': ('criteres', 'techniques'),
            'autres_criteres': ('criteres', 'autres'),
            'quantite_minimum': ('quantites', 'minimum'),
            'quantites_estimees': ('quantites', 'estimees'),
            'quantite_maximum': ('quantites', 'maximum'),
            'duree_marche': ('durees', 'duree_marche'),
            'execution_marche': ('durees', 'execution_marche'),
            'reconduction': ('durees', 'reconduction'),
            'fin_sans_reconduction': ('durees', 'fin_sans_reconduction'),
            'fin_avec_reconduction': ('durees', 'fin_avec_reconduction'),
            'rse': ('rse', 'rse'),
            'contribution_fournisseur': ('contribution', 'fournisseur'),
            'infos_complementaires': ('metadonnees', 'infos_complementaires'),
            'remarques': ('metadonnees', 'remarques'),
            'notes_acheteur_procedure': ('metadonnees', 'notes_acheteur_procedure'),
            'notes_acheteur_fournisseur': ('metadonnees', 'notes_acheteur_fournisseur'),
            'notes_acheteur_positionnement': ('metadonnees', 'notes_acheteur_positionnement'),
            'achat': ('acquisition', 'achat'),
            'credit_bail': ('acquisition', 'credit_bail'),
            'credit_bail_duree': ('acquisition', 'credit_bail_duree'),
            'location': ('acquisition', 'location'),
            'location_duree': ('acquisition', 'location_duree'),
            'mad': ('acquisition', 'mad'),
            'attributaire': ('attribution', 'attributaire'),
            'produit_retenu': ('attribution', 'produit_retenu'),
            'segment': ('classification', 'segment'),
            'famille': ('classification', 'famille')
        }
        
        if field_name in field_mapping:
            category, subcategory = field_mapping[field_name]
            return self.get_patterns(category, subcategory)
        else:
            logger.warning(f"Champ non reconnu: {field_name}")
            return []
    
    def compile_pattern(self, pattern: str) -> re.Pattern:
        """
        Compile un pattern avec mise en cache
        
        Args:
            pattern: Pattern regex à compiler
            
        Returns:
            Pattern compilé
        """
        if pattern in self.compiled_patterns:
            self.performance_stats['cache_hits'] += 1
            return self.compiled_patterns[pattern]
        
        try:
            compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            self.compiled_patterns[pattern] = compiled
            self.performance_stats['total_compilations'] += 1
            return compiled
        except re.error as e:
            self.performance_stats['compilation_errors'] += 1
            logger.error(f"Erreur compilation pattern '{pattern}': {e}")
            return re.compile(r'.*')  # Pattern par défaut
    
    def extract_with_patterns(self, text: str, field_name: str) -> List[str]:
        """
        Extrait des valeurs avec les patterns d'un champ
        
        Args:
            text: Texte à analyser
            field_name: Nom du champ
            
        Returns:
            Liste des valeurs extraites
        """
        patterns = self.get_field_patterns(field_name)
        extracted_values = []
        
        for pattern in patterns:
            try:
                compiled_pattern = self.compile_pattern(pattern)
                matches = compiled_pattern.findall(text)
                
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            # Si c'est un tuple, prendre le premier élément non vide
                            value = next((m for m in match if m and str(m).strip()), '')
                        else:
                            value = match
                        
                        if value and str(value).strip():
                            extracted_values.append(str(value).strip())
                            
            except Exception as e:
                logger.warning(f"Erreur pattern '{pattern}' pour {field_name}: {e}")
                continue
        
        return extracted_values
    
    def add_pattern(self, category: str, subcategory: str, pattern: str):
        """
        Ajoute un nouveau pattern
        
        Args:
            category: Catégorie du pattern
            subcategory: Sous-catégorie du pattern
            pattern: Pattern regex
        """
        if category not in self.patterns:
            self.patterns[category] = {}
        if subcategory not in self.patterns[category]:
            self.patterns[category][subcategory] = []
        
        self.patterns[category][subcategory].append(pattern)
        logger.info(f"Pattern ajouté: {category}.{subcategory}")
    
    def remove_pattern(self, category: str, subcategory: str, pattern: str):
        """
        Supprime un pattern
        
        Args:
            category: Catégorie du pattern
            subcategory: Sous-catégorie du pattern
            pattern: Pattern regex à supprimer
        """
        if (category in self.patterns and 
            subcategory in self.patterns[category] and 
            pattern in self.patterns[category][subcategory]):
            self.patterns[category][subcategory].remove(pattern)
            logger.info(f"Pattern supprimé: {category}.{subcategory}")
    
    def load_from_file(self, config_file: str):
        """
        Charge les patterns depuis un fichier JSON
        
        Args:
            config_file: Chemin vers le fichier de configuration
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if 'patterns' in config:
                self.patterns.update(config['patterns'])
                logger.info(f"Patterns chargés depuis {config_file}")
        except Exception as e:
            logger.error(f"Erreur chargement patterns depuis {config_file}: {e}")
    
    def save_to_file(self, config_file: str):
        """
        Sauvegarde les patterns dans un fichier JSON
        
        Args:
            config_file: Chemin vers le fichier de configuration
        """
        try:
            config = {
                'patterns': self.patterns,
                'metadata': {
                    'version': '2.0.0',
                    'created_at': '2024-01-01',
                    'description': 'Configuration des patterns d\'extraction'
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Patterns sauvegardés dans {config_file}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde patterns dans {config_file}: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de performance"""
        return self.performance_stats.copy()
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        self.performance_stats = {
            'total_compilations': 0,
            'cache_hits': 0,
            'compilation_errors': 0
        }
