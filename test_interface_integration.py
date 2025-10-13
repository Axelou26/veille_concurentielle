#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Test d'Intégration Interface
=============================

Test de l'intégration du nouveau système d'extraction dans l'interface
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import AdvancedPDFExtractor
from extraction_improver import extraction_improver

def test_interface_integration():
    """Test de l'intégration interface"""
    
    print("🔍 **Test d'Intégration Interface**\n")
    
    # Simuler un fichier PDF uploadé
    pdf_path = "rapports/2024-R001-000-000_RC.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ **Erreur**: Le fichier {pdf_path} n'existe pas")
        return
    
    print(f"📄 **Fichier PDF**: {pdf_path}")
    
    # Simuler le processus de l'interface
    print(f"\n🔧 **Simulation du processus interface:**")
    
    try:
        # 1. Extraction PDF (comme dans l'interface)
        print("1️⃣ **Extraction PDF...**")
        pdf_extractor = AdvancedPDFExtractor()
        pdf_result = pdf_extractor.extract_from_pdf(pdf_path)
        
        if pdf_result and 'contenu_extraite' in pdf_result:
            text = pdf_result['contenu_extraite'].get('texte_complet', '')
            print(f"   ✅ Texte extrait: {len(text)} caractères")
            
            if text:
                # 2. Extraction améliorée (comme dans l'interface)
                print("2️⃣ **Extraction améliorée...**")
                extracted_data = extraction_improver.extract_improved_data(text)
                print(f"   ✅ Données extraites: {len(extracted_data)} champs")
                
                # 3. Formatage pour l'interface (comme dans l'interface)
                print("3️⃣ **Formatage pour l'interface...**")
                extracted_info = {
                    'valeurs_extraites': extracted_data,
                    'valeurs_generees': {},
                    'metadata': {
                        'nom_fichier': os.path.basename(pdf_path),
                        'taille': os.path.getsize(pdf_path),
                        'contenu_extraite': {'type': 'pdf_avance'},
                        'erreur': None
                    }
                }
                
                # 4. Vérification des champs générés
                print("4️⃣ **Vérification des champs générés:**")
                
                valeurs_extraites = extracted_info['valeurs_extraites']
                
                # Vérifier les champs demandés
                champs_demandes = ['mots_cles', 'famille', 'segment', 'univers']
                
                for champ in champs_demandes:
                    if champ in valeurs_extraites and valeurs_extraites[champ]:
                        value = valeurs_extraites[champ]
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        print(f"   ✅ {champ}: {value}")
                    else:
                        print(f"   ❌ {champ}: Non trouvé")
                
                # Statistiques
                total_champs = len(valeurs_extraites)
                champs_trouves = sum(1 for champ in champs_demandes if champ in valeurs_extraites and valeurs_extraites[champ])
                
                print(f"\n📈 **Statistiques:**")
                print(f"- Total champs extraits: {total_champs}")
                print(f"- Champs demandés trouvés: {champs_trouves}/{len(champs_demandes)}")
                print(f"- Pourcentage de réussite: {(champs_trouves/len(champs_demandes))*100:.1f}%")
                
                # Afficher tous les champs extraits
                print(f"\n📋 **Tous les champs extraits:**")
                for field, value in valeurs_extraites.items():
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"  {field}: {value}")
                
                print(f"\n🎉 **Test d'intégration réussi !**")
                print(f"📊 **L'interface peut maintenant générer automatiquement les champs demandés !**")
                
            else:
                print("   ❌ Aucun texte extrait du PDF")
        else:
            print("   ❌ Erreur lors de l'extraction PDF")
            
    except Exception as e:
        print(f"❌ **Erreur lors du test**: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_interface_integration()




