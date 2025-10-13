#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Test de Génération Améliorée
==============================

Test de la génération automatique des mots-clés, famille, segment et univers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import PyPDF2
from extraction_improver import extraction_improver

def test_improved_generation():
    """Test de la génération améliorée"""
    
    print("🔍 **Test de Génération Améliorée**\n")
    
    # Chemin vers le PDF
    pdf_path = "rapports/2024-R001-000-000_RC.pdf"
    
    # Extraire le texte
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    
    print(f"📄 **Texte extrait**: {len(text)} caractères")
    
    # Test avec l'extracteur amélioré
    print(f"\n🔧 **Test avec génération améliorée:**")
    try:
        extracted_data = extraction_improver.extract_improved_data(text)
        
        print(f"✅ **Extraction réussie**")
        print(f"📊 **Champs extraits**: {len(extracted_data)}")
        
        # Afficher les champs générés automatiquement
        generated_fields = ['mots_cles', 'famille', 'segment', 'univers']
        
        print(f"\n🎯 **Champs générés automatiquement:**")
        for field in generated_fields:
            if field in extracted_data:
                value = extracted_data[field]
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"  ✅ {field}: {value}")
            else:
                print(f"  ❌ {field}: Non trouvé")
        
        # Afficher tous les champs extraits
        print(f"\n📋 **Tous les champs extraits:**")
        for field, value in extracted_data.items():
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  {field}: {value}")
        
        # Statistiques
        total_fields = 43
        extracted_count = len(extracted_data)
        percentage = (extracted_count / total_fields) * 100
        
        print(f"\n📈 **Statistiques:**")
        print(f"- Champs extraits: {extracted_count}/{total_fields} ({percentage:.1f}%)")
        print(f"- Champs manquants: {total_fields - extracted_count}")
        
        # Vérifier la qualité de la génération
        print(f"\n🔍 **Qualité de la génération:**")
        
        # Vérifier les mots-clés
        if 'mots_cles' in extracted_data:
            mots_cles = extracted_data['mots_cles']
            if mots_cles and len(mots_cles.split(',')) >= 3:
                print(f"  ✅ Mots-clés: {len(mots_cles.split(','))} mots-clés générés")
            else:
                print(f"  ⚠️ Mots-clés: Peu de mots-clés générés")
        else:
            print(f"  ❌ Mots-clés: Non générés")
        
        # Vérifier la famille
        if 'famille' in extracted_data:
            famille = extracted_data['famille']
            if famille and len(famille) > 5:
                print(f"  ✅ Famille: {famille} (générée)")
            else:
                print(f"  ⚠️ Famille: {famille} (trop courte)")
        else:
            print(f"  ❌ Famille: Non générée")
        
        # Vérifier le segment
        if 'segment' in extracted_data:
            segment = extracted_data['segment']
            if segment and len(segment) > 5:
                print(f"  ✅ Segment: {segment} (généré)")
            else:
                print(f"  ⚠️ Segment: {segment} (trop court)")
        else:
            print(f"  ❌ Segment: Non généré")
        
        # Vérifier l'univers
        if 'univers' in extracted_data:
            univers = extracted_data['univers']
            if univers and len(univers) > 3:
                print(f"  ✅ Univers: {univers} (généré)")
            else:
                print(f"  ⚠️ Univers: {univers} (trop court)")
        else:
            print(f"  ❌ Univers: Non généré")
        
    except Exception as e:
        print(f"❌ **Erreur lors de l'extraction**: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 **Test terminé !**")

if __name__ == "__main__":
    test_improved_generation()




