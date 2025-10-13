#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Test simple des intitulés
===========================

Test spécifique pour les intitulés
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extraction_improver import extraction_improver

def test_intitules_simple():
    """Test simple des intitulés"""
    
    # Texte de test simple
    test_text = """
    Intitulé de la procédure: Fourniture d'équipements médicaux pour les hôpitaux du réseau RESAH
    Intitulé du lot: Fourniture de congélateurs -80°C pour laboratoires
    """
    
    print("🔍 **Test simple des intitulés**\n")
    print(f"📄 **Texte de test:** {test_text}\n")
    
    # Test des patterns d'intitulés
    print("📝 **Test des patterns d'intitulés:**")
    
    intitule_patterns = [
        r'(?:intitulé|intitule|titre|objet)[\s\w]*(?:procédure|procedure)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
        r'(?:procédure|procedure)[\s\w]*(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
        r'(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
        r'(?:procédure|procedure)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
        r'(?:intitulé|intitule|titre|objet)[\s\w]*(?:lot|prestation)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
        r'(?:lot|prestation)[\s\w]*(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
        r'(?:lot|prestation)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)',
        r'(?:intitulé|intitule|titre|objet)[\s\w]*[:]\s*([^.\n]{10,100})(?:\n|$)'
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
        if 'intitule' in field.lower():
            print(f"  {field}: {value}")
    
    print(f"\nTotal: {len(extracted_data)} champs extraits")

if __name__ == "__main__":
    test_intitules_simple()
