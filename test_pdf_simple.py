#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Test PDF Simple
=================

Test simple pour diagnostiquer l'extraction PDF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pdf_simple():
    """Test simple d'extraction PDF"""
    
    print("🔍 **Test PDF Simple**\n")
    
    # Chemin vers le PDF
    pdf_path = "rapports/2024-R001-000-000_RC.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ **Erreur**: Le fichier {pdf_path} n'existe pas")
        return
    
    print(f"📄 **Fichier PDF**: {pdf_path}")
    print(f"📊 **Taille du fichier**: {os.path.getsize(pdf_path)} octets")
    
    # Test 1: PyPDF2
    print(f"\n🔧 **1. Test avec PyPDF2:**")
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"📊 **Nombre de pages**: {len(pdf_reader.pages)}")
            
            text = ""
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += page_text
                print(f"📄 **Page {i+1}**: {len(page_text)} caractères")
                if i == 0:  # Afficher le début de la première page
                    print(f"📝 **Aperçu page {i+1}**: {page_text[:200]}...")
            
            print(f"📝 **Texte total**: {len(text)} caractères")
            if text.strip():
                print(f"📄 **Aperçu du texte**: {text[:300]}...")
            else:
                print("❌ **Aucun texte extrait avec PyPDF2**")
                
    except Exception as e:
        print(f"❌ **Erreur PyPDF2**: {e}")
    
    # Test 2: pdfplumber
    print(f"\n🔧 **2. Test avec pdfplumber:**")
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📊 **Nombre de pages**: {len(pdf.pages)}")
            
            text = ""
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                    print(f"📄 **Page {i+1}**: {len(page_text)} caractères")
                    if i == 0:  # Afficher le début de la première page
                        print(f"📝 **Aperçu page {i+1}**: {page_text[:200]}...")
                else:
                    print(f"❌ **Page {i+1}**: Aucun texte extrait")
            
            print(f"📝 **Texte total**: {len(text)} caractères")
            if text.strip():
                print(f"📄 **Aperçu du texte**: {text[:300]}...")
            else:
                print("❌ **Aucun texte extrait avec pdfplumber**")
                
    except Exception as e:
        print(f"❌ **Erreur pdfplumber**: {e}")
    
    # Test 3: pdf2image + OCR
    print(f"\n🔧 **3. Test avec pdf2image + OCR:**")
    try:
        import pdf2image
        from PIL import Image
        import pytesseract
        
        # Convertir PDF en images
        images = pdf2image.convert_from_path(pdf_path)
        print(f"📊 **Nombre d'images**: {len(images)}")
        
        text = ""
        for i, image in enumerate(images):
            # Extraire le texte avec OCR
            page_text = pytesseract.image_to_string(image, lang='fra')
            text += page_text
            print(f"📄 **Page {i+1}**: {len(page_text)} caractères")
            if i == 0:  # Afficher le début de la première page
                print(f"📝 **Aperçu page {i+1}**: {page_text[:200]}...")
        
        print(f"📝 **Texte total OCR**: {len(text)} caractères")
        if text.strip():
            print(f"📄 **Aperçu du texte OCR**: {text[:300]}...")
        else:
            print("❌ **Aucun texte extrait avec OCR**")
            
    except Exception as e:
        print(f"❌ **Erreur OCR**: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_simple()




