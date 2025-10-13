#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la conversion des points en pourcentage
"""

from criteria_extractor import CriteriaExtractor

def test_points_conversion():
    """Test de la conversion des points en pourcentage"""
    print("Test de la conversion des points en pourcentage")
    print("=" * 50)
    
    # Initialiser l'extracteur
    extractor = CriteriaExtractor()
    
    # Texte de test avec des points
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
    
    Lot 3 :
    - Critère économique : 25 points
    - Critère technique : 50 points
    - Autres critères : 25 points
    """
    
    print("Texte de test :")
    print(test_text)
    print("\n" + "=" * 50)
    
    # Extraire les critères
    tableau = extractor.extract_from_text(test_text)
    
    print("Résultats de l'extraction :")
    print(f"Critères globaux : {len(tableau.criteres_globaux)}")
    print(f"Critères par lot : {len(tableau.criteres_par_lot)}")
    
    # Afficher les critères globaux
    if tableau.criteres_globaux:
        print("\nCritères globaux :")
        for i, critere in enumerate(tableau.criteres_globaux):
            print(f"  {i+1}. {critere.nom}: {critere.pourcentage}% - {critere.description}")
    
    # Afficher les critères par lot
    if tableau.criteres_par_lot:
        print("\nCritères par lot :")
        for lot_numero, criteres in tableau.criteres_par_lot.items():
            print(f"\n  Lot {lot_numero}:")
            for i, critere in enumerate(criteres):
                print(f"    {i+1}. {critere.nom}: {critere.pourcentage}% - {critere.description}")
    
    # Test avec un PDF réel
    print("\n" + "=" * 50)
    print("Test avec un PDF réel...")
    
    pdf_path = "rapports/2024-R041-000_RC.pdf"
    if pdf_path:
        try:
            tableau_pdf = extractor.extract_from_pdf(pdf_path)
            summary = extractor.format_criteria_summary(tableau_pdf)
            print("\nRésultats du PDF :")
            print(summary)
        except Exception as e:
            print(f"Erreur lors du test PDF: {e}")

if __name__ == "__main__":
    test_points_conversion()
