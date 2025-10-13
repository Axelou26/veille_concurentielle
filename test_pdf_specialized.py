#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Test PDF Spécialisé
=====================

Test avec des patterns spécialisés pour les règlements de consultation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import PyPDF2
import re
from extraction_improver import extraction_improver

def test_pdf_specialized():
    """Test avec des patterns spécialisés"""
    
    print("🔍 **Test PDF Spécialisé**\n")
    
    # Chemin vers le PDF
    pdf_path = "rapports/2024-R001-000-000_RC.pdf"
    
    # Extraire le texte
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    
    print(f"📄 **Texte extrait**: {len(text)} caractères")
    
    # Créer un contexte spécialisé pour les règlements de consultation
    context = {
        'document_type': 'reglement_consultation',
        'has_reference': True,
        'has_title': True,
        'has_dates': True,
        'has_amounts': False,  # Ce document ne contient pas de montants
        'is_accord_cadre': True
    }
    
    # Test avec l'extracteur amélioré et contexte spécialisé
    print(f"\n🔧 **Test avec contexte spécialisé:**")
    try:
        extracted_data = extraction_improver.extract_improved_data(text)
        
        print(f"✅ **Extraction réussie**")
        print(f"📊 **Champs extraits**: {len(extracted_data)}")
        
        # Afficher les résultats importants
        important_fields = [
            'reference_procedure', 'intitule_procedure', 'intitule_lot',
            'type_procedure', 'groupement', 'univers', 'segment',
            'date_limite', 'date_attribution', 'duree_marche',
            'montant_global_estime', 'montant_global_maxi'
        ]
        
        print(f"\n📋 **Champs importants:**")
        for field in important_fields:
            if field in extracted_data:
                value = extracted_data[field]
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                print(f"  ✅ {field}: {value}")
            else:
                print(f"  ❌ {field}: Non trouvé")
        
        # Test manuel des patterns spécifiques
        print(f"\n🔍 **Test manuel des patterns spécifiques:**")
        
        # Référence
        ref_patterns = [
            r'N°(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',
            r'(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',
            r'Référence[:\s]*(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})'
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text)
            if match:
                print(f"  ✅ Référence trouvée avec pattern '{pattern}': {match.group(1)}")
                break
        else:
            print(f"  ❌ Aucune référence trouvée")
        
        # Titre
        title_patterns = [
            r'REALISATION DE PRESTATIONS DE FORMATION[^\n]*',
            r'PRESTATIONS DE FORMATION[^\n]*',
            r'FORMATION PROFESSIONNELLE[^\n]*'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                print(f"  ✅ Titre trouvé avec pattern '{pattern}': {match.group(0).strip()}")
                break
        else:
            print(f"  ❌ Aucun titre trouvé")
        
        # Type de procédure
        if 'PROCEDURE ADAPTEE' in text:
            print(f"  ✅ Type de procédure: Procédure adaptée")
        else:
            print(f"  ❌ Type de procédure: Non trouvé")
        
        # Groupement
        if 'RESAH' in text:
            print(f"  ✅ Groupement: RESAH")
        else:
            print(f"  ❌ Groupement: Non trouvé")
        
        # Dates
        date_patterns = [
            r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates_found.extend(matches)
        
        if dates_found:
            print(f"  ✅ Dates trouvées: {dates_found[:3]}")
        else:
            print(f"  ❌ Aucune date trouvée")
        
        # Montants
        montant_patterns = [
            r'(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?|HT|TTC)',
            r'(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|k\s*€)',
            r'(\d+(?:[.,]\d+)?)\s*(?:m€|meuros?|millions?|m\s*€)'
        ]
        
        montants_found = []
        for pattern in montant_patterns:
            matches = re.findall(pattern, text)
            montants_found.extend(matches)
        
        if montants_found:
            print(f"  ✅ Montants trouvés: {montants_found[:3]}")
        else:
            print(f"  ❌ Aucun montant trouvé (normal pour un règlement de consultation)")
        
        # Statistiques
        total_fields = len(important_fields)
        extracted_count = sum(1 for field in important_fields if field in extracted_data)
        percentage = (extracted_count / total_fields) * 100
        
        print(f"\n📈 **Statistiques des champs importants:**")
        print(f"- Champs extraits: {extracted_count}/{total_fields} ({percentage:.1f}%)")
        print(f"- Champs manquants: {total_fields - extracted_count}")
        
    except Exception as e:
        print(f"❌ **Erreur lors de l'extraction**: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 **Test terminé !**")

if __name__ == "__main__":
    test_pdf_specialized()




