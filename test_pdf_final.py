#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Test PDF Final
================

Test de l'extracteur PDF corrigé
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import AdvancedPDFExtractor

def test_pdf_final():
    """Test de l'extracteur PDF corrigé"""
    
    print("🔍 **Test PDF Final**\n")
    
    # Chemin vers le PDF
    pdf_path = "rapports/2024-R001-000-000_RC.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ **Erreur**: Le fichier {pdf_path} n'existe pas")
        return
    
    print(f"📄 **Fichier PDF**: {pdf_path}")
    
    # Test avec l'extracteur PDF corrigé
    print(f"\n🔧 **Test avec l'extracteur PDF corrigé:**")
    try:
        extractor = AdvancedPDFExtractor()
        result = extractor.extract_from_pdf(pdf_path)
        
        print(f"✅ **Extraction réussie**")
        print(f"📊 **Type de résultat**: {type(result)}")
        
        if 'contenu_extraite' in result:
            content = result['contenu_extraite']
            print(f"📝 **Type de contenu**: {content.get('type', 'N/A')}")
            print(f"📄 **Message**: {content.get('message', 'N/A')}")
            
            if 'texte_complet' in content:
                text = content['texte_complet']
                print(f"📊 **Texte extrait**: {len(text)} caractères")
                print(f"📄 **Aperçu du texte**: {text[:300]}...")
            
            if 'informations' in content:
                info = content['informations']
                print(f"📊 **Informations extraites**: {len(info)} champs")
                
                # Afficher les informations par catégorie
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
                        if field in info:
                            value = info[field]
                            if isinstance(value, str) and len(value) > 50:
                                value = value[:50] + "..."
                            print(f"  ✅ {field}: {value}")
                        else:
                            print(f"  ❌ {field}: Non trouvé")
                
                # Statistiques
                total_fields = sum(len(fields) for fields in categories.values())
                extracted_count = len(info)
                percentage = (extracted_count / total_fields) * 100
                
                print(f"\n📈 **Statistiques:**")
                print(f"- Champs extraits: {extracted_count}/{total_fields} ({percentage:.1f}%)")
                print(f"- Champs manquants: {total_fields - extracted_count}")
        
        else:
            print("❌ **Aucun contenu extrait**")
            
    except Exception as e:
        print(f"❌ **Erreur lors de l'extraction**: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 **Test terminé !**")

if __name__ == "__main__":
    test_pdf_final()
