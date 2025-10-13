#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Test d'amélioration de l'extraction
====================================

Script de test pour démontrer l'amélioration de l'extraction de données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extraction_improver import extraction_improver
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_extraction_improvement():
    """Test de l'amélioration de l'extraction"""
    
    # Texte d'exemple similaire à celui qui pose problème
    sample_text = """
    APPEL D'OFFRES PUBLIC
    Groupement: RESAH
    Intitulé de la procédure: Fourniture d'équipements médicaux pour les hôpitaux
    Type de procédure: Appel d'offres ouvert
    Intitulé du lot: Fourniture de congélateurs -80°C
    Montant global estimé: 2 500 000 €
    Date limite de remise des offres: 15/12/2024
    Statut: En cours
    Nombre de lots: 3
    Quantité minimum: 5
    Quantités estimées: 10
    Quantité maximum: 15
    Critères économiques: Prix (70%), Qualité (30%)
    Critères techniques: Conformité aux normes CE
    Informations complémentaires: Installation incluse
    """
    
    print("🧪 **Test d'amélioration de l'extraction**\n")
    
    # Test de l'extraction améliorée
    print("📝 **Texte d'exemple:**")
    print(sample_text)
    print("\n" + "="*50 + "\n")
    
    # Extraction avec le nouvel améliorateur
    print("🔧 **Extraction améliorée:**")
    improved_data = extraction_improver.extract_improved_data(sample_text)
    
    for field, value in improved_data.items():
        print(f"✅ {field}: {value}")
    
    print(f"\n📊 **Résultats:** {len(improved_data)} champs extraits")
    
    # Test avec un texte problématique
    print("\n" + "="*50 + "\n")
    print("⚠️ **Test avec texte problématique:**")
    
    problematic_text = """
    , certifiée par laccusé de
    ['Procédure : Appel', 'Type De Proc...
    ['................................
    attribution. Les attributaires en so...
    (Attestation De Régularité Fiscale, ...
    [2, 4, 3]
    -Traitant Proposé
    9
    [1, 20, 9]
    15
    """
    
    print("📝 **Texte problématique:**")
    print(problematic_text)
    print("\n🔧 **Extraction améliorée:**")
    
    improved_problematic = extraction_improver.extract_improved_data(problematic_text)
    
    if improved_problematic:
        for field, value in improved_problematic.items():
            print(f"✅ {field}: {value}")
    else:
        print("❌ Aucune donnée valide extraite (comportement attendu)")
    
    print(f"\n📊 **Résultats:** {len(improved_problematic)} champs extraits")
    
    # Test de validation
    print("\n" + "="*50 + "\n")
    print("🔍 **Test de validation:**")
    
    test_cases = [
        ("intitule_procedure", "Fourniture d'équipements médicaux", True),
        ("intitule_procedure", "certifiée par laccusé de", False),
        ("intitule_procedure", "['Procédure : Appel', 'Type De Proc...", False),
        ("intitule_lot", "Fourniture de congélateurs -80°C", True),
        ("intitule_lot", "['................................", False),
        ("groupement", "RESAH", True),
        ("groupement", "(Attestation De Régularité Fiscale, ...", False),
        ("montant_global_estime", "2500000", True),
        ("montant_global_estime", "attribution. Les attributaires en so...", False),
        ("nbr_lots", "3", True),
        ("nbr_lots", "[2, 4, 3]", False)
    ]
    
    for field, value, expected in test_cases:
        is_valid = extraction_improver._is_valid_match(value, field)
        status = "✅" if is_valid == expected else "❌"
        print(f"{status} {field}: '{value}' -> {is_valid} (attendu: {expected})")
    
    print("\n🎉 **Test terminé !**")

if __name__ == "__main__":
    test_extraction_improvement()

