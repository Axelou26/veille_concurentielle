#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Test des Patterns PDF
=======================

Test des patterns pour le PDF de règlement de consultation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import PyPDF2
import re

def test_pdf_patterns():
    """Test des patterns pour le PDF"""
    
    print("🔍 **Test des Patterns PDF**\n")
    
    # Chemin vers le PDF
    pdf_path = "rapports/2024-R001-000-000_RC.pdf"
    
    # Extraire le texte
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    
    print(f"📄 **Texte extrait**: {len(text)} caractères")
    print(f"📄 **Aperçu du texte**: {text[:500]}...")
    
    # Analyser le contenu pour identifier les patterns
    print(f"\n🔍 **Analyse du contenu:**")
    
    # Chercher des patterns spécifiques
    patterns_to_test = {
        'Référence': [
            r'N°(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',
            r'(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',
            r'N°\s*(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',
            r'Référence[:\s]*(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})',
            r'Code[:\s]*(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})'
        ],
        'Titre': [
            r'REALISATION DE PRESTATIONS DE FORMATION',
            r'PRESTATIONS DE FORMATION',
            r'FORMATION PROFESSIONNELLE',
            r'PRESTATIONS ASSOCIEES'
        ],
        'Type de procédure': [
            r'PROCEDURE ADAPTEE',
            r'ACCORD -CADRE',
            r'ACCORD-CADRE',
            r'FOURNITURES COURANTES ET SERVICES'
        ],
        'Dates': [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
            r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})'
        ],
        'Montants': [
            r'(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?|HT|TTC)',
            r'(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|k\s*€)',
            r'(\d+(?:[.,]\d+)?)\s*(?:m€|meuros?|millions?|m\s*€)'
        ],
        'Groupement': [
            r'Centrale d\'Achat',
            r'Intermédiaire',
            r'RESAH',
            r'UNIHA',
            r'CAIH',
            r'UGAP'
        ]
    }
    
    for category, patterns in patterns_to_test.items():
        print(f"\n📋 **{category}:**")
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                print(f"  ✅ Pattern '{pattern}': {matches[:3]}")  # Afficher les 3 premiers matches
            else:
                print(f"  ❌ Pattern '{pattern}': Aucun match")
    
    # Chercher des sections spécifiques
    print(f"\n🔍 **Sections identifiées:**")
    
    section_patterns = {
        'Titre principal': r'REALISATION DE PRESTATIONS DE FORMATION',
        'Sous-titre': r'PROFESSIONNELLE ET PRESTATIONS ASSOCIEES',
        'Type de procédure': r'PROCEDURE ADAPTEE',
        'Accord-cadre': r'ACCORD -CADRE DE FOURNITURES COURANTES ET SERVICES',
        'Code de la commande publique': r'Code de la commande publique',
        'Centrale d\'achat': r'Centrale d\'Achat',
        'Intermédiaire': r'Intermédiaire'
    }
    
    for section, pattern in section_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            print(f"  ✅ {section}: Trouvé")
        else:
            print(f"  ❌ {section}: Non trouvé")
    
    # Extraire des informations spécifiques
    print(f"\n🔍 **Informations extraites:**")
    
    # Référence
    ref_match = re.search(r'N°(\d{4}-[A-Z]\d{3}-\d{3}-\d{3})', text)
    if ref_match:
        print(f"  ✅ Référence: {ref_match.group(1)}")
    else:
        print(f"  ❌ Référence: Non trouvée")
    
    # Titre
    title_match = re.search(r'REALISATION DE PRESTATIONS DE FORMATION[^\n]*', text)
    if title_match:
        print(f"  ✅ Titre: {title_match.group(0).strip()}")
    else:
        print(f"  ❌ Titre: Non trouvé")
    
    # Type de procédure
    type_match = re.search(r'PROCEDURE ADAPTEE', text)
    if type_match:
        print(f"  ✅ Type de procédure: Procédure adaptée")
    else:
        print(f"  ❌ Type de procédure: Non trouvé")
    
    # Accord-cadre
    accord_match = re.search(r'ACCORD -CADRE DE FOURNITURES COURANTES ET SERVICES', text)
    if accord_match:
        print(f"  ✅ Accord-cadre: Oui")
    else:
        print(f"  ❌ Accord-cadre: Non trouvé")
    
    print(f"\n🎉 **Test terminé !**")

if __name__ == "__main__":
    test_pdf_patterns()




