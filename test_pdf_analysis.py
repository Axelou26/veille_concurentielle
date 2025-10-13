#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour analyser le fichier PDF M_3132_DCE_RC.pdf
et comprendre pourquoi l'IA ne trouve pas de lots
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import AdvancedPDFExtractor
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_pdf_file():
    """Analyse le fichier PDF pour comprendre la structure"""
    
    pdf_path = "rapports/M_3132_DCE_RC.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier PDF non trouvé: {pdf_path}")
        return
    
    print(f"Analyse du fichier PDF: {pdf_path}")
    
    try:
        # Initialiser l'extracteur
        extractor = AdvancedPDFExtractor()
        
        # Extraire le contenu du PDF
        print("Extraction du contenu PDF...")
        result = extractor.extract_from_pdf(pdf_path)
        
        if result and 'contenu_extraite' in result:
            contenu = result['contenu_extraite']
            text = contenu.get('texte_complet', '')
            
            print(f"Texte extrait: {len(text)} caracteres")
            
            # Analyser le contenu pour les lots
            print("\nAnalyse des sections de lots...")
            
            # Rechercher les mots-clés liés aux lots
            keywords_lots = [
                'lot', 'lots', 'allotissement', 'allotissement', 'répartition', 
                'montant estimatif', 'montant maximum', 'intitulé du lot'
            ]
            
            text_lower = text.lower()
            found_keywords = []
            for keyword in keywords_lots:
                if keyword.lower() in text_lower:
                    count = text_lower.count(keyword.lower())
                    found_keywords.append((keyword, count))
                    print(f"  - '{keyword}': {count} occurrences")
                else:
                    print(f"  - '{keyword}': non trouve")
            
            # Rechercher les patterns de lots
            print("\nRecherche des patterns de lots...")
            
            import re
            
            # Patterns pour détecter les lots
            lot_patterns = [
                r'lot\s*n°?\s*(\d+)',
                r'lot\s*numéro\s*(\d+)',
                r'(\d+)\s+[A-Z][A-Z\s/]+?\s+\d{1,3}(?:\s\d{3})*',
                r'allotissement[^\n]*(\d+)',
                r'répartition[^\n]*(\d+)'
            ]
            
            for i, pattern in enumerate(lot_patterns):
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    print(f"  - Pattern {i+1}: {len(matches)} matches trouves")
                    for match in matches[:5]:  # Afficher les 5 premiers
                        print(f"    - {match}")
                else:
                    print(f"  - Pattern {i+1}: aucun match")
            
            # Rechercher les montants
            print("\nRecherche des montants...")
            
            montant_patterns = [
                r'(\d{1,3}(?:\s\d{3})*)\s*€',
                r'(\d+(?:[.,]\d+)?)\s*(?:k€|m€)',
                r'montant[^\n]*(\d{1,3}(?:\s\d{3})*)',
                r'budget[^\n]*(\d{1,3}(?:\s\d{3})*)'
            ]
            
            for i, pattern in enumerate(montant_patterns):
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    print(f"  - Montant Pattern {i+1}: {len(matches)} matches")
                    for match in matches[:5]:  # Afficher les 5 premiers
                        print(f"    - {match}")
                else:
                    print(f"  - Montant Pattern {i+1}: aucun match")
            
            # Afficher un echantillon du texte
            print(f"\nEchantillon du texte (premiers 1000 caracteres):")
            print("-" * 80)
            print(text[:1000])
            print("-" * 80)
            
            # Rechercher les sections importantes
            print(f"\nRecherche des sections importantes...")
            
            sections = [
                'article', 'chapitre', 'section', 'titre', 'allotissement',
                'lotissement', 'répartition', 'montant', 'budget'
            ]
            
            for section in sections:
                pattern = rf'{section}[^\n]*'
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    print(f"  - Section '{section}': {len(matches)} occurrences")
                    for match in matches[:3]:  # Afficher les 3 premiers
                        print(f"    - {match.strip()[:100]}...")
                else:
                    print(f"  - Section '{section}': non trouvee")
            
            # Tester l'extraction des lots
            print(f"\nTest de l'extraction des lots...")
            lots = extractor._extract_lots_from_tables(text, text_lower)
            
            if lots:
                print(f"  - {len(lots)} lots detectes:")
                for lot in lots:
                    print(f"    - Lot {lot.get('numero', 'N/A')}: {lot.get('intitule', 'N/A')[:50]}...")
            else:
                print(f"  - Aucun lot detecte par l'extracteur")
                
                # Essayer des methodes alternatives
                print(f"\nTentative avec methodes alternatives...")
                
                # Methode agressive
                lots_aggressive = extractor._extract_lots_aggressive(text)
                if lots_aggressive:
                    print(f"  - Methode agressive: {len(lots_aggressive)} lots")
                    for lot in lots_aggressive:
                        print(f"    - Lot {lot.get('numero', 'N/A')}: {lot.get('intitule', 'N/A')[:50]}...")
                else:
                    print(f"  - Methode agressive: aucun lot")
            
        else:
            print("Erreur lors de l'extraction du PDF")
            
    except Exception as e:
        print(f"Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_pdf_file()
