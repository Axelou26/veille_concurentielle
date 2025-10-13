#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Debug de l'extraction
=======================

Script pour déboguer les problèmes d'extraction
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extraction_improver import extraction_improver

def debug_extraction():
    """Debug de l'extraction"""
    
    # Texte de test avec les dates problématiques
    test_text = """
    Date limite de remise des offres: 15/12/2024
    Date d'attribution du marché: 20/12/2024
    Intitulé de la procédure: Fourniture d'équipements médicaux pour les hôpitaux du réseau RESAH
    Intitulé du lot: Fourniture de congélateurs -80°C pour laboratoires
    """
    
    print("🔍 **Debug de l'extraction**\n")
    print("📄 **Texte de test:**")
    print(test_text)
    print("\n" + "="*50 + "\n")
    
    # Test des patterns de dates
    print("📅 **Test des patterns de dates:**")
    
    date_patterns = [
        r'(?:date|échéance|clôture)[\s\w]*(?:limite|remise|offres)[\s\w]*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(?:date|échéance|clôture)[\s\w]*(?:limite|remise|offres)[\s\w]*[:]\s*(\d{4}-\d{2}-\d{2})',
        r'(?:date|échéance|clôture)[\s\w]*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(?:date|échéance|clôture)[\s\w]*[:]\s*(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{4}-\d{2}-\d{2})'
    ]
    
    for i, pattern in enumerate(date_patterns):
        matches = re.findall(pattern, test_text, re.IGNORECASE)
        print(f"Pattern {i+1}: {pattern}")
        print(f"  Matches: {matches}")
        print()
    
    # Test des patterns d'intitulés
    print("📝 **Test des patterns d'intitulés:**")
    
    intitule_patterns = [
        r'(?:intitulé|intitule|titre|objet)[\s\w]*(?:procédure|procedure)[\s\w]*[:]\s*([^.\n]{10,200})(?:\n|$)',
        r'(?:procédure|procedure)[\s\w]*(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,200})(?:\n|$)',
        r'(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,200})(?:\n|$)',
        r'(?:procédure|procedure)[\s\w]*[:]\s*([^.\n]{10,200})(?:\n|$)',
        r'(?:appel|offre|consultation)[\s\w]*(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,200})(?:\n|$)',
        r'(?:appel|offre|consultation)[\s\w]*[:]\s*([^.\n]{10,200})(?:\n|$)',
        r'(?:marché|marche)[\s\w]*(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,200})(?:\n|$)',
        r'(?:marché|marche)[\s\w]*[:]\s*([^.\n]{10,200})(?:\n|$)'
    ]
    
    for i, pattern in enumerate(intitule_patterns):
        matches = re.findall(pattern, test_text, re.IGNORECASE | re.MULTILINE)
        print(f"Pattern {i+1}: {pattern}")
        print(f"  Matches: {matches}")
        print()
    
    # Test de l'extraction complète
    print("🔧 **Test de l'extraction complète:**")
    extracted_data = extraction_improver.extract_improved_data(test_text)
    
    print("Résultats:")
    for field, value in extracted_data.items():
        print(f"  {field}: {value}")
    
    print(f"\nTotal: {len(extracted_data)} champs extraits")

if __name__ == "__main__":
    debug_extraction()

