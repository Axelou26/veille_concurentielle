#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Test PDF Amélioré
===================

Test avec des patterns adaptés aux règlements de consultation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import PyPDF2
import re
from extraction_improver import extraction_improver

def test_pdf_improved():
    """Test avec des patterns améliorés"""
    
    print("🔍 **Test PDF Amélioré**\n")
    
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
    print(f"\n🔧 **Test avec l'extracteur amélioré:**")
    try:
        extracted_data = extraction_improver.extract_improved_data(text)
        
        print(f"✅ **Extraction réussie**")
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
        
        # Analyser les patterns spécifiques pour ce type de document
        print(f"\n🔍 **Analyse spécifique du document:**")
        
        # Vérifier si c'est un règlement de consultation
        if 'REGLEMENT DE LA CONSULATION' in text or 'RC' in text:
            print("  ✅ Type de document: Règlement de Consultation (RC)")
        
        # Vérifier la référence
        ref_match = re.search(r'N°(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})', text)
        if ref_match:
            print(f"  ✅ Référence trouvée: {ref_match.group(1)}")
        
        # Vérifier le titre
        title_match = re.search(r'REALISATION DE PRESTATIONS DE FORMATION[^\n]*', text)
        if title_match:
            print(f"  ✅ Titre trouvé: {title_match.group(0).strip()}")
        
        # Vérifier le type de procédure
        if 'PROCEDURE ADAPTEE' in text:
            print("  ✅ Type de procédure: Procédure adaptée")
        
        # Vérifier l'accord-cadre
        if 'ACCORD -CADRE' in text:
            print("  ✅ Accord-cadre: Oui")
        
        # Vérifier le groupement
        if 'RESAH' in text:
            print("  ✅ Groupement: RESAH")
        
        # Vérifier les dates
        date_matches = re.findall(r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})', text)
        if date_matches:
            print(f"  ✅ Dates trouvées: {date_matches[:3]}")  # Afficher les 3 premières
        
        # Vérifier les montants
        montant_matches = re.findall(r'(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?|HT|TTC)', text)
        if montant_matches:
            print(f"  ✅ Montants trouvés: {montant_matches[:3]}")
        else:
            print("  ❌ Aucun montant trouvé dans ce document")
        
    except Exception as e:
        print(f"❌ **Erreur lors de l'extraction**: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 **Test terminé !**")

if __name__ == "__main__":
    test_pdf_improved()
