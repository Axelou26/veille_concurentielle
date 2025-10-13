#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple de la conversion des points
"""

import re

def test_simple_points_conversion():
    """Test simple de la conversion des points"""
    print("Test simple de la conversion des points")
    print("=" * 50)
    
    # Texte de test
    test_text = """
    Critères d'attribution du marché :
    
    Lot 1 :
    - Critère économique : 35 points
    - Critère technique : 40 points
    - Autres critères : 25 points
    
    Lot 2 :
    - Critère économique : 30 points
    - Critère technique : 45 points
    - Autres critères : 25 points
    """
    
    print("Texte de test :")
    print(test_text)
    print("\n" + "=" * 50)
    
    # Pattern simple pour détecter les points
    pattern = r'(?:critère|criteres?)[\s\w]*(?:économique|technique|prix|qualité|autre)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?)\s*points?'
    
    matches = re.findall(pattern, test_text, re.IGNORECASE)
    
    print(f"Matches trouvés : {len(matches)}")
    for i, match in enumerate(matches):
        points = float(match.replace(',', '.'))
        print(f"  {i+1}. {points} points = {points}%")
    
    # Test avec un pattern plus large
    pattern2 = r'(\d+(?:[.,]\d+)?)\s*points?(?=\s*$|\s*\n|\s*[^\w])'
    matches2 = re.findall(pattern2, test_text, re.IGNORECASE)
    
    print(f"\nPattern plus large : {len(matches2)} matches")
    for i, match in enumerate(matches2):
        points = float(match.replace(',', '.'))
        print(f"  {i+1}. {points} points = {points}%")

if __name__ == "__main__":
    test_simple_points_conversion()
