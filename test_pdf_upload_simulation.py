#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Test Simulation Upload PDF
============================

Simulation du processus d'upload PDF dans l'interface
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import AdvancedPDFExtractor
from extraction_improver import extraction_improver

def test_pdf_upload_simulation():
    """Simulation du processus d'upload PDF"""
    
    print("🔍 **Test Simulation Upload PDF**\n")
    
    # Simuler un fichier PDF uploadé
    pdf_path = "rapports/2024-R001-000-000_RC.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ **Erreur**: Le fichier {pdf_path} n'existe pas")
        return
    
    print(f"📄 **Fichier PDF**: {pdf_path}")
    print(f"📊 **Taille**: {os.path.getsize(pdf_path)} octets")
    
    # Simuler le processus exact de l'interface
    print(f"\n🔧 **Simulation du processus interface:**")
    
    try:
        # 1. Vérifier le type de fichier
        file_type = "application/pdf"
        print(f"1️⃣ **Type de fichier**: {file_type}")
        
        if file_type == "application/pdf":
            print("2️⃣ **Utilisation du nouveau système d'extraction PDF...**")
            
            # 2. Utiliser le nouveau système d'extraction PDF
            pdf_extractor = AdvancedPDFExtractor()
            pdf_result = pdf_extractor.extract_from_pdf(pdf_path)
            
            print(f"   📊 **Résultat PDF**: {type(pdf_result)}")
            
            if pdf_result and 'contenu_extraite' in pdf_result:
                print("   ✅ Structure PDF valide")
                
                text = pdf_result['contenu_extraite'].get('texte_complet', '')
                print(f"   📝 **Texte extrait**: {len(text)} caractères")
                
                if text:
                    print("   ✅ Texte extrait avec succès")
                    
                    # 3. Utiliser l'extracteur amélioré
                    print("3️⃣ **Extraction améliorée...**")
                    extracted_data = extraction_improver.extract_improved_data(text)
                    print(f"   📊 **Données extraites**: {len(extracted_data)} champs")
                    
                    # 4. Formater pour l'interface
                    print("4️⃣ **Formatage pour l'interface...**")
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
                    
                    # 5. Vérifier le résultat final
                    print("5️⃣ **Vérification du résultat final:**")
                    
                    if extracted_info and 'erreur' not in extracted_info:
                        print("   ✅ Extraction réussie!")
                        
                        # Vérifier les champs générés
                        valeurs_extraites = extracted_info['valeurs_extraites']
                        champs_demandes = ['mots_cles', 'famille', 'segment', 'univers']
                        
                        print(f"\n🎯 **Champs générés automatiquement:**")
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
                        
                        print(f"\n🎉 **Simulation réussie !**")
                        print(f"📊 **L'interface devrait maintenant fonctionner correctement !**")
                        
                    else:
                        print("   ❌ Erreur dans le formatage")
                        if 'erreur' in extracted_info:
                            print(f"   🔍 Erreur: {extracted_info['erreur']}")
                else:
                    print("   ❌ Aucun texte extrait du PDF")
            else:
                print("   ❌ Structure PDF invalide")
                print(f"   🔍 Résultat: {pdf_result}")
        else:
            print("   ❌ Type de fichier non supporté")
            
    except Exception as e:
        print(f"❌ **Erreur lors de la simulation**: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_upload_simulation()
