#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier les améliorations de l'extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import AdvancedPDFExtractor
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_improved_extraction():
    """Test des améliorations de l'extraction"""
    
    pdf_path = "rapports/M_3132_DCE_RC.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Fichier PDF non trouve: {pdf_path}")
        return
    
    print(f"Test des ameliorations pour: {pdf_path}")
    
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
            
            # Tester l'extraction des lots avec les nouvelles améliorations
            print("\nTest de l'extraction des lots avec ameliorations...")
            lots = extractor._extract_lots_from_tables(text, text.lower())
            
            if lots:
                print(f"SUCCESS: {len(lots)} lots detectes:")
                for lot in lots:
                    print(f"  - Lot {lot.get('numero', 'N/A')}: {lot.get('intitule', 'N/A')[:50]}...")
                    print(f"    Montant estime: {lot.get('montant_estime', 0)}")
                    print(f"    Montant maximum: {lot.get('montant_maximum', 0)}")
                    print(f"    Source: {lot.get('source', 'N/A')}")
            else:
                print("Aucun lot detecte")
            
            # Tester l'extraction des critères
            print("\nTest de l'extraction des criteres...")
            criteres = extractor._extract_criteres(text, text.lower())
            
            if criteres:
                print(f"SUCCESS: {len(criteres)} criteres detectes:")
                for critere in criteres:
                    print(f"  - {critere}")
            else:
                print("Aucun critere detecte")
            
            # Tester l'extraction des informations générales
            print("\nTest de l'extraction des informations generales...")
            infos = contenu.get('informations', {})
            
            if infos:
                print("Informations extraites:")
                for key, value in infos.items():
                    if value:
                        print(f"  - {key}: {value}")
            
        else:
            print("Erreur lors de l'extraction du PDF")
            
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_extraction()
