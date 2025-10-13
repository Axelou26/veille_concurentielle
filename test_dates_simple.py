#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Test simple des dates
=======================

Test spécifique pour les dates
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extraction_improver import extraction_improver

def test_dates_simple():
    """Test simple des dates"""
    
    # Texte de test simple
    test_text = "Date limite de remise des offres: 15/12/2024"
    
    print("🔍 **Test simple des dates**\n")
    print(f"📄 **Texte de test:** {test_text}\n")
    
    # Test de la validation des dates
    print("📅 **Test de validation des dates:**")
    test_dates = ["15/12/2024", "20/12/2024", "2024-12-15", "15 décembre 2024"]
    
    for date_str in test_dates:
        is_valid = extraction_improver._is_valid_date_format(date_str)
        print(f"  {date_str}: {'✅' if is_valid else '❌'}")
    
    print()
    
    # Test de l'extraction des dates
    print("🔧 **Test de l'extraction des dates:**")
    extracted_data = extraction_improver.extract_improved_data(test_text)
    
    print("Résultats:")
    for field, value in extracted_data.items():
        if 'date' in field.lower():
            print(f"  {field}: {value}")
    
    print(f"\nTotal: {len(extracted_data)} champs extraits")

if __name__ == "__main__":
    test_dates_simple()
