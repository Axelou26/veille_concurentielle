#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Test d'Extraction PDF Corrigé
===============================

Test de l'extraction avec le PDF en utilisant directement PyPDF2
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import PyPDF2
from extraction_improver import extraction_improver

def test_pdf_extraction_fixed():
    """Test d'extraction PDF corrigé"""
    
    print("🔍 **Test d'extraction PDF corrigé**\n")
    
    # Chemin vers le PDF
    pdf_path = "rapports/2024-R001-000-000_RC.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ **Erreur**: Le fichier {pdf_path} n'existe pas")
        return
    
    print(f"📄 **Fichier PDF**: {pdf_path}")
    
    # Extraire le texte du PDF avec PyPDF2
    print(f"\n🔧 **1. Extraction du texte PDF:**")
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            print(f"✅ **Extraction réussie**")
            print(f"📊 **Texte extrait**: {len(text)} caractères")
            print(f"📄 **Aperçu du texte**: {text[:500]}...")
            
    except Exception as e:
        print(f"❌ **Erreur lors de l'extraction**: {e}")
        return
    
    # Utiliser l'améliorateur d'extraction
    print(f"\n🔧 **2. Extraction intelligente:**")
    try:
        extracted_data = extraction_improver.extract_improved_data(text)
        
        print(f"✅ **Extraction intelligente réussie**")
        print(f"📊 **Champs extraits**: {len(extracted_data)}")
        
        # Afficher les résultats par catégorie
        categories = {
            'Identité': ['mots_cles', 'univers', 'segment', 'famille', 'statut', 'groupement'],
            'Procédure': ['reference_procedure', 'type_procedure', 'mono_multi', 'execution_marche', 'nbr_lots', 'intitule_procedure', 'intitule_lot'],
            'Temporel': ['date_limite', 'date_attribution', 'duree_marche', 'reconduction', 'fin_sans_reconduction', 'fin_avec_reconduction'],
            'Financier': ['montant_global_estime', 'montant_global_maxi', 'achat', 'credit_bail', 'credit_bail_duree', 'location', 'location_duree', 'mad'],
            'Quantités': ['quantite_minimum', 'quantites_estimees', 'quantite_maximum'],
            'Critères': ['criteres_economique', 'criteres_techniques', 'autres_criteres', 'rse', 'contribution_fournisseur'],
            'Résultats': ['attributaire', 'produit_retenu'],
            'Notes': ['infos_complementaires', 'remarques', 'notes_acheteur_procedure', 'notes_acheteur_fournisseur', 'notes_acheteur_positionnement', 'note_veille']
        }
        
        for category, fields in categories.items():
            print(f"\n📋 **{category}:**")
            for field in fields:
                if field in extracted_data:
                    value = extracted_data[field]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"  ✅ {field}: {value}")
                else:
                    print(f"  ❌ {field}: Non trouvé")
        
        # Statistiques
        total_fields = sum(len(fields) for fields in categories.values())
        extracted_count = len(extracted_data)
        percentage = (extracted_count / total_fields) * 100
        
        print(f"\n📈 **Statistiques:**")
        print(f"- Champs extraits: {extracted_count}/{total_fields} ({percentage:.1f}%)")
        print(f"- Champs manquants: {total_fields - extracted_count}")
        
    except Exception as e:
        print(f"❌ **Erreur lors de l'extraction intelligente**: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 **Test terminé !**")

if __name__ == "__main__":
    test_pdf_extraction_fixed()




