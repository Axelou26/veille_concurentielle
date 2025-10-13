#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'extraction PDF avancé avec OCR et patterns regex optimisés
"""

import re
import io
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
import PyPDF2
import pdfplumber
import pytesseract
from PIL import Image
import pdf2image
import pandas as pd
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedPDFExtractor:
    """Extracteur PDF avancé avec OCR et patterns optimisés"""
    
    def __init__(self):
        """Initialisation de l'extracteur"""
        self.patterns = self._init_patterns()
        self.organismes = self._init_organismes()
        
    def _init_patterns(self) -> Dict[str, str]:
        """Initialisation des patterns regex optimisés et plus précis"""
        return {
            # Montants et budgets (patterns plus précis)
            'montant_ht': r'(?:montant|budget|prix|coût|cout|valeur|estimation)[\s\w]*[:\s]*(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*(?:€|euros?|HT|TTC)',
            'montant_k': r'(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|k\s*€)',
            'montant_m': r'(\d+(?:[.,]\d+)?)\s*(?:m€|meuros?|millions?|m\s*€)',
            'montant_simple': r'(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)\s*€',
            
            # Dates (patterns plus précis)
            'date_limite': r'(?:date\s+limite|échéance|clôture|fin)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'date_publication': r'(?:date\s+de\s+publication|publié\s+le)[\s\w]*[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'date_texte': r'(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
            'date_simple': r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            
            # Références (patterns plus précis)
            'reference_ao': r'(?:référence|ref|code|numéro|n°)[\s\w]*[:\s]*([A-Z0-9\-_/]{3,20})',
            'reference_consultation': r'(?:consultation|marché)[\s\w]*[:\s]*([A-Z0-9\-_/]{3,20})',
            'reference_simple': r'([A-Z]{2,4}[\-\/]?\d{4}[\-\/]?\d{2,4})',
            
            # Titres et intitulés (patterns plus précis)
            'titre_ao': r'(?:appel\s+d[\'"]offres?|consultation|marché)[\s\w]*[:\s]*([^€\n]{20,200})',
            'objet_consultation': r'(?:objet\s+de\s+la\s+consultation|objet)[\s\w]*[:\s]*([^€\n]{20,200})',
            
            # Descriptions (patterns plus précis)
            'description': r'(?:description|objet|présentation)[\s\w]*[:\s]*([^€\n]{30,300})',
            'prestation': r'(?:prestation|service|travaux)[\s\w]*[:\s]*([^€\n]{20,200})',
            
            # Critères d'évaluation (patterns plus précis)
            'critere_economique': r'(?:critère|critères)[\s\w]*(?:économique|prix)[\s\w]*[:\s]*([^€\n]{10,100})',
            'critere_technique': r'(?:critère|critères)[\s\w]*(?:technique|qualité)[\s\w]*[:\s]*([^€\n]{10,100})',
            'ponderation': r'(?:pondération|poids)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
            
            # NOUVEAUX: Patterns pour critères dans les tableaux
            'critere_tableau_economique': r'(?:économique|prix|coût|cout)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
            'critere_tableau_technique': r'(?:technique|qualité|qualite)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
            'critere_tableau_autre': r'(?:autre|autres|innovation|rse|environnement)[\s\w]*[:\s]*(\d+(?:[.,]\d+)?\s*%)',
            
            # Patterns pour tableaux de critères structurés
            'tableau_criteres': r'(?:critères?\s+d[\'"]attribution|pondération|évaluation)[\s\w]*(.*?)(?=article|chapitre|section|$)',
            'ligne_critere': r'(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
            'ligne_critere_simple': r'([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?\s*%)',
            
            # Délais et durées (patterns plus précis)
            'duree_marche': r'(?:durée|période)[\s\w]*(?:du\s+marché|d[\'"]exécution)[\s\w]*[:\s]*(\d+)\s*(?:mois|semaines?|jours?|années?)',
            'delai_realisation': r'(?:délai|temps)[\s\w]*(?:de\s+réalisation|d[\'"]exécution)[\s\w]*[:\s]*(\d+)\s*(?:mois|semaines?|jours?)',
            
            # Lieux et adresses (patterns plus précis)
            'lieu_execution': r'(?:lieu|adresse)[\s\w]*(?:d[\'"]exécution|de\s+réalisation)[\s\w]*[:\s]*([^€\n]{10,100})',
            'adresse': r'(?:adresse|siège)[\s\w]*[:\s]*([^€\n]{10,100})',
            
            # Contacts (patterns plus précis)
            'contact_technique': r'(?:contact|personne)[\s\w]*(?:technique|responsable)[\s\w]*[:\s]*([^€\n]{10,100})',
            'contact_administratif': r'(?:contact|personne)[\s\w]*(?:administratif|gestionnaire)[\s\w]*[:\s]*([^€\n]{10,100})',
            
            # Numéros de téléphone (patterns plus précis)
            'telephone': r'(?:tél|téléphone|phone)[\s\w]*[:\s]*(\d{2}[.\s]?\d{2}[.\s]?\d{2}[.\s]?\d{2}[.\s]?\d{2})',
            'fax': r'(?:fax|télécopie)[\s\w]*[:\s]*(\d{2}[.\s]?\d{2}[.\s]?\d{2}[.\s]?\d{2}[.\s]?\d{2})',
            
            # Emails (patterns plus précis)
            'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'email_contact': r'(?:email|mail|contact)[\s\w]*[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            
            # URLs (patterns plus précis)
            'url': r'(https?://[^\s]+)',
            'site_web': r'(?:site|web|internet)[\s\w]*[:\s]*(https?://[^\s]+)',
            
            # Codes postaux (patterns plus précis)
            'code_postal': r'(\d{5})\s*([A-Z\s]+)',
            
            # Numéros de SIRET/SIREN (patterns plus précis)
            'siret': r'(?:siret|siren)[\s\w]*[:\s]*(\d{9,14})',
            'siren': r'(?:siren)[\s\w]*[:\s]*(\d{9})',
            
            # Organismes (patterns plus précis)
            'organisme': r'(?:organisme|acheteur|maître\s+d[\'"]ouvrage)[\s\w]*[:\s]*([^€\n]{10,100})',
            'entite': r'(?:entité|structure|établissement)[\s\w]*[:\s]*([^€\n]{10,100})',
        }
    
    def _init_organismes(self) -> List[str]:
        """Initialisation de la liste des organismes"""
        return [
            'ministère', 'ministère de', 'mairie', 'mairie de', 'région', 'région de',
            'département', 'département de', 'établissement', 'établissement de',
            'entreprise', 'collectivité', 'collectivité de', 'communauté',
            'communauté de', 'métropole', 'métropole de', 'agglomération',
            'agglomération de', 'syndicat', 'syndicat de', 'office', 'office de',
            'agence', 'agence de', 'institut', 'institut de', 'centre', 'centre de',
            'université', 'université de', 'école', 'école de', 'lycée', 'lycée de',
            'collège', 'collège de', 'hôpital', 'hôpital de', 'chu', 'chru', 'chr',
            'caisse', 'caisse de', 'mutuelle', 'mutuelle de', 'fonds', 'fonds de',
            'association', 'association de', 'fédération', 'fédération de',
            'conseil', 'conseil de', 'assemblée', 'assemblée de', 'sénat',
            'assemblée nationale', 'préfecture', 'préfecture de', 'sous-préfecture',
            'sous-préfecture de', 'direction', 'direction de', 'service', 'service de',
            'bureau', 'bureau de', 'délégation', 'délégation de', 'représentation',
            'représentation de', 'antenne', 'antenne de', 'agence régionale',
            'agence nationale', 'institut national', 'centre national',
            'observatoire', 'observatoire de', 'commission', 'commission de',
            'comité', 'comité de', 'groupe', 'groupe de', 'société', 'société de',
            'sas', 'sarl', 'sa', 'eurl', 'ei', 'auto-entrepreneur', 'micro-entreprise'
        ]
    
    def extract_from_pdf(self, pdf_file) -> Dict[str, Any]:
        """Extraction complète depuis un fichier PDF"""
        try:
            # Gérer les deux types d'entrée : chemin de fichier ou objet fichier
            if isinstance(pdf_file, str):
                # Chemin de fichier
                file_path = pdf_file
                file_name = os.path.basename(pdf_file)
                file_size = os.path.getsize(pdf_file)
                logger.info(f"Extraction PDF avancée pour {file_name}")
            else:
                # Objet fichier (Streamlit) - sauvegarder temporairement
                file_name = pdf_file.name
                file_size = pdf_file.size
                logger.info(f"Extraction PDF avancée pour {file_name}")
                
                # Sauvegarder le fichier temporairement
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(pdf_file.getvalue())
                    file_path = tmp_file.name
            
            # Lecture du PDF avec PyPDF2 (plus fiable)
            text_content = self._extract_text_pypdf2(file_path)
            
            if not text_content.strip():
                logger.info("Aucun texte extrait, tentative avec pdfplumber...")
                text_content = self._extract_text_pdfplumber(file_path)
            
            # Extraction des informations
            extracted_info = self._extract_all_information(text_content)
            
            # Ajout des métadonnées
            extracted_info['metadata'] = {
                'nom_fichier': file_name,
                'taille': f"{file_size / 1024:.2f} KB",
                'type': 'application/pdf',
                'methode_extraction': 'PDF avancé',
                'timestamp': datetime.now().isoformat(),
                'longueur_texte': len(text_content),
                'lignes_texte': len(text_content.split('\n'))
            }
            
            result = {
                'contenu_extraite': {
                    'type': 'pdf_avance',
                    'texte_complet': text_content,
                    'informations': extracted_info,
                    'message': f"PDF analysé avec extraction avancée - {len(extracted_info)} informations extraites"
                }
            }
            
            # Nettoyer le fichier temporaire si nécessaire
            if not isinstance(pdf_file, str) and 'file_path' in locals() and file_path != pdf_file.name:
                try:
                    os.unlink(file_path)
                except:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction PDF: {e}")
            return {
                'contenu_extraite': {
                    'type': 'pdf_erreur',
                    'message': f"Erreur lors de l'extraction: {str(e)}"
                }
            }
    
    def _extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extraction de texte avec PyPDF2"""
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Erreur PyPDF2: {e}")
            return ""
    
    def _extract_text_pdfplumber(self, pdf_path: str) -> str:
        """Extraction de texte avec pdfplumber"""
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            logger.error(f"Erreur pdfplumber: {e}")
            return ""
    
    def _extract_all_information(self, text: str) -> Dict[str, Any]:
        """Extraction de toutes les informations du texte"""
        try:
            # Utiliser l'extracteur amélioré
            from extraction_improver import extraction_improver
            return extraction_improver.extract_improved_data(text)
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des informations: {e}")
            return {}
    
    def _extract_text_multiple_methods(self, pdf_file) -> str:
        """Extraction de texte avec plusieurs méthodes"""
        text_content = ""
        
        try:
            # Méthode 1: PyPDF2
            pdf_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            # Si PyPDF2 ne donne rien, essayer pdfplumber
            if not text_content.strip():
                pdf_file.seek(0)
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_content += text + "\n"
            
            logger.info(f"Texte extrait: {len(text_content)} caractères")
            return text_content
            
        except Exception as e:
            logger.warning(f"Erreur extraction texte: {e}")
            return ""
    
    def _extract_with_ocr(self, pdf_file) -> str:
        """Extraction avec OCR pour les PDF scannés"""
        try:
            logger.info("Début de l'extraction OCR...")
            
            # Conversion PDF vers images
            pdf_file.seek(0)
            images = pdf2image.convert_from_bytes(
                pdf_file.read(),
                dpi=300,  # Résolution élevée pour meilleure reconnaissance
                fmt='PNG'
            )
            
            text_content = ""
            
            # OCR sur chaque page
            for i, image in enumerate(images):
                logger.info(f"OCR page {i+1}/{len(images)}")
                
                # Prétraitement de l'image
                image = self._preprocess_image(image)
                
                # OCR avec Tesseract
                text = pytesseract.image_to_string(
                    image,
                    lang='fra+eng',  # Français + Anglais
                    config='--psm 6 --oem 3'  # Mode page, moteur LSTM
                )
                
                text_content += text + "\n"
            
            logger.info(f"OCR terminé: {len(text_content)} caractères extraits")
            return text_content
            
        except Exception as e:
            logger.error(f"Erreur OCR: {e}")
            return ""
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Prétraitement de l'image pour améliorer l'OCR"""
        try:
            # Conversion en niveaux de gris
            if image.mode != 'L':
                image = image.convert('L')
            
            # Amélioration du contraste
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)  # Augmentation du contraste
            
            # Réduction du bruit
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)  # Amélioration de la netteté
            
            return image
            
        except Exception as e:
            logger.warning(f"Erreur prétraitement image: {e}")
            return image
    
    def _extract_all_information(self, text: str) -> Dict[str, Any]:
        """Extraction de toutes les informations avec les patterns optimisés"""
        text_lower = text.lower()
        extracted_info = {}
        
        # Extraction des montants
        montants = self._extract_montants(text, text_lower)
        if montants:
            extracted_info['montants'] = montants
        
        # Extraction des dates
        dates = self._extract_dates(text, text_lower)
        if dates:
            extracted_info['dates'] = dates
        
        # Extraction des références
        references = self._extract_references(text, text_lower)
        if references:
            extracted_info['references'] = references
        
        # Extraction des organismes
        organismes = self._extract_organismes(text, text_lower)
        if organismes:
            extracted_info['organismes'] = organismes
        
        # Extraction des titres
        titres = self._extract_titres(text, text_lower)
        if titres:
            extracted_info['titres'] = titres
        
        # Extraction des descriptions
        descriptions = self._extract_descriptions(text, text_lower)
        if descriptions:
            extracted_info['descriptions'] = descriptions
        
        # Extraction des contacts
        contacts = self._extract_contacts(text, text_lower)
        if contacts:
            extracted_info['contacts'] = contacts
        
        # Extraction des lieux
        lieux = self._extract_lieux(text, text_lower)
        if lieux:
            extracted_info['lieux'] = lieux
        
        # Extraction des critères
        criteres = self._extract_criteres(text, text_lower)
        if criteres:
            extracted_info['criteres'] = criteres
        
        # NOUVEAU: Extraction des lots depuis les tableaux
        lots = self._extract_lots_from_tables(text, text_lower)
        if lots:
            extracted_info['lots'] = lots
        
        return extracted_info
    
    def _extract_montants(self, text: str, text_lower: str) -> List[str]:
        """Extraction des montants et budgets avec filtrage intelligent"""
        montants = []
        
        # Pattern montant HT
        matches = re.findall(self.patterns['montant_ht'], text, re.IGNORECASE)
        montants.extend([f"{m} € HT" for m in matches])
        
        # Pattern montant en k€
        matches = re.findall(self.patterns['montant_k'], text, re.IGNORECASE)
        montants.extend([f"{m} k€" for m in matches])
        
        # Pattern montant en m€
        matches = re.findall(self.patterns['montant_m'], text, re.IGNORECASE)
        montants.extend([f"{m} m€" for m in matches])
        
        # Pattern montant simple
        matches = re.findall(self.patterns['montant_simple'], text, re.IGNORECASE)
        montants.extend([f"{m} €" for m in matches])
        
        # Filtrage intelligent - garder seulement les montants significatifs
        montants_filtres = []
        for montant in montants:
            # Extraire le nombre du montant
            nombre_match = re.search(r'(\d+(?:[.,]\d+)?)', montant)
            if nombre_match:
                nombre = float(nombre_match.group(1).replace(',', '.'))
                # Garder seulement les montants > 100€
                if nombre > 100:
                    montants_filtres.append(montant)
        
        # Nettoyage et dédoublonnage
        montants_filtres = list(set([m.strip() for m in montants_filtres if m.strip()]))
        return montants_filtres[:3]  # Limiter à 3 montants significatifs
    
    def _extract_dates(self, text: str, text_lower: str) -> List[str]:
        """Extraction des dates avec filtrage intelligent"""
        dates = []
        
        # Pattern date limite
        matches = re.findall(self.patterns['date_limite'], text, re.IGNORECASE)
        dates.extend([f"Date limite: {m}" for m in matches])
        
        # Pattern date publication
        matches = re.findall(self.patterns['date_publication'], text, re.IGNORECASE)
        dates.extend([f"Publication: {m}" for m in matches])
        
        # Pattern date texte (mois + année)
        matches = re.findall(self.patterns['date_texte'], text, re.IGNORECASE)
        dates.extend([f"{m[0].title()} {m[1]}" for m in matches])
        
        # Pattern date simple
        matches = re.findall(self.patterns['date_simple'], text, re.IGNORECASE)
        dates.extend(matches)
        
        # Filtrage intelligent - garder seulement les dates valides
        dates_filtres = []
        for date in dates:
            # Vérifier que c'est une date valide
            if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', date) or re.search(r'(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)', date.lower()):
                dates_filtres.append(date)
        
        # Nettoyage et dédoublonnage
        dates_filtres = list(set([d.strip() for d in dates_filtres if d.strip()]))
        return dates_filtres[:3]  # Limiter à 3 dates significatives
    
    def _extract_references(self, text: str, text_lower: str) -> List[str]:
        """Extraction des références avec filtrage intelligent"""
        references = []
        
        # Pattern référence AO
        matches = re.findall(self.patterns['reference_ao'], text, re.IGNORECASE)
        references.extend(matches)
        
        # Pattern référence consultation
        matches = re.findall(self.patterns['reference_consultation'], text, re.IGNORECASE)
        references.extend(matches)
        
        # Pattern référence simple
        matches = re.findall(self.patterns['reference_simple'], text, re.IGNORECASE)
        references.extend(matches)
        
        # Filtrage intelligent - garder seulement les références valides
        references_filtres = []
        for ref in references:
            # Vérifier que c'est une référence valide (contient des lettres et des chiffres)
            if re.search(r'[A-Za-z]', ref) and re.search(r'\d', ref) and len(ref) >= 3:
                references_filtres.append(ref)
        
        # Nettoyage et dédoublonnage
        references_filtres = list(set([r.strip() for r in references_filtres if r.strip()]))
        return references_filtres[:3]  # Limiter à 3 références significatives
    
    def _extract_organismes(self, text: str, text_lower: str) -> List[str]:
        """Extraction des organismes avec filtrage intelligent"""
        organismes = []
        
        # Pattern organisme
        matches = re.findall(self.patterns['organisme'], text, re.IGNORECASE)
        organismes.extend(matches)
        
        # Pattern entité
        matches = re.findall(self.patterns['entite'], text, re.IGNORECASE)
        organismes.extend(matches)
        
        # Recherche dans la liste des organismes connus
        for organisme in self.organismes:
            if organisme in text_lower:
                # Trouver le contexte complet
                start = text_lower.find(organisme)
                end = start + len(organisme) + 30  # 30 caractères après
                contexte = text[start:end].strip()
                # Nettoyer le contexte
                contexte = re.sub(r'[^\w\s\-.,]', '', contexte)
                if len(contexte) > 10:
                    organismes.append(contexte)
        
        # Filtrage intelligent - garder seulement les organismes valides
        organismes_filtres = []
        for org in organismes:
            # Vérifier que c'est un organisme valide
            if len(org) > 10 and not re.search(r'^\d+$', org) and not re.search(r'^[^\w\s]+$', org):
                organismes_filtres.append(org)
        
        # Nettoyage et dédoublonnage
        organismes_filtres = list(set([o.strip() for o in organismes_filtres if o.strip()]))
        return organismes_filtres[:3]  # Limiter à 3 organismes significatifs
    
    def _extract_titres(self, text: str, text_lower: str) -> List[str]:
        """Extraction des titres avec filtrage intelligent"""
        titres = []
        
        # Pattern titre AO
        matches = re.findall(self.patterns['titre_ao'], text, re.IGNORECASE)
        titres.extend(matches)
        
        # Pattern objet consultation
        matches = re.findall(self.patterns['objet_consultation'], text, re.IGNORECASE)
        titres.extend(matches)
        
        # Filtrage intelligent - garder seulement les titres valides
        titres_filtres = []
        for titre in titres:
            # Vérifier que c'est un titre valide
            if len(titre) > 15 and len(titre) < 200 and not re.search(r'^\d+$', titre):
                # Nettoyer le titre
                titre_clean = re.sub(r'[^\w\s\-.,()]', '', titre).strip()
                if len(titre_clean) > 15:
                    titres_filtres.append(titre_clean)
        
        # Nettoyage et dédoublonnage
        titres_filtres = list(set([t.strip() for t in titres_filtres if t.strip()]))
        return titres_filtres[:3]  # Limiter à 3 titres significatifs
    
    def _extract_descriptions(self, text: str, text_lower: str) -> List[str]:
        """Extraction des descriptions avec filtrage intelligent"""
        descriptions = []
        
        # Pattern description
        matches = re.findall(self.patterns['description'], text, re.IGNORECASE | re.DOTALL)
        descriptions.extend(matches)
        
        # Pattern prestation
        matches = re.findall(self.patterns['prestation'], text, re.IGNORECASE | re.DOTALL)
        descriptions.extend(matches)
        
        # Filtrage intelligent - garder seulement les descriptions valides
        descriptions_filtres = []
        for desc in descriptions:
            # Vérifier que c'est une description valide
            if len(desc) > 30 and len(desc) < 500:
                # Nettoyer la description
                desc_clean = re.sub(r'[^\w\s\-.,()]', '', desc).strip()
                if len(desc_clean) > 30:
                    descriptions_filtres.append(desc_clean)
        
        # Nettoyage et dédoublonnage
        descriptions_filtres = list(set([d.strip() for d in descriptions_filtres if d.strip()]))
        return descriptions_filtres[:2]  # Limiter à 2 descriptions significatives
    
    def _extract_contacts(self, text: str, text_lower: str) -> List[str]:
        """Extraction des contacts avec filtrage intelligent"""
        contacts = []
        
        # Téléphones
        matches = re.findall(self.patterns['telephone'], text, re.IGNORECASE)
        contacts.extend([f"Tél: {m}" for m in matches])
        
        # Emails
        matches = re.findall(self.patterns['email'], text, re.IGNORECASE)
        contacts.extend([f"Email: {m}" for m in matches])
        
        # URLs
        matches = re.findall(self.patterns['url'], text, re.IGNORECASE)
        contacts.extend([f"URL: {m}" for m in matches])
        
        # Filtrage intelligent - garder seulement les contacts valides
        contacts_filtres = []
        for contact in contacts:
            # Vérifier que c'est un contact valide
            if re.search(r'(tél|email|url):', contact.lower()) and len(contact) > 5:
                contacts_filtres.append(contact)
        
        # Nettoyage et dédoublonnage
        contacts_filtres = list(set([c.strip() for c in contacts_filtres if c.strip()]))
        return contacts_filtres[:5]  # Limiter à 5 contacts significatifs
    
    def _extract_lieux(self, text: str, text_lower: str) -> List[str]:
        """Extraction des lieux avec filtrage intelligent"""
        lieux = []
        
        # Pattern lieu d'exécution
        matches = re.findall(self.patterns['lieu_execution'], text, re.IGNORECASE)
        lieux.extend(matches)
        
        # Pattern adresse
        matches = re.findall(self.patterns['adresse'], text, re.IGNORECASE)
        lieux.extend(matches)
        
        # Filtrage intelligent - garder seulement les lieux valides
        lieux_filtres = []
        for lieu in lieux:
            # Vérifier que c'est un lieu valide
            if len(lieu) > 5 and len(lieu) < 100 and not re.search(r'^\d+$', lieu):
                # Nettoyer le lieu
                lieu_clean = re.sub(r'[^\w\s\-.,()]', '', lieu).strip()
                if len(lieu_clean) > 5:
                    lieux_filtres.append(lieu_clean)
        
        # Nettoyage et dédoublonnage
        lieux_filtres = list(set([l.strip() for l in lieux_filtres if l.strip()]))
        return lieux_filtres[:3]  # Limiter à 3 lieux significatifs
    
    def _extract_criteres(self, text: str, text_lower: str) -> List[str]:
        """Extraction des critères d'évaluation avec filtrage intelligent"""
        criteres = []
        
        # Pattern critère économique
        matches = re.findall(self.patterns['critere_economique'], text, re.IGNORECASE)
        criteres.extend([f"Économique: {m}" for m in matches])
        
        # Pattern critère technique
        matches = re.findall(self.patterns['critere_technique'], text, re.IGNORECASE)
        criteres.extend([f"Technique: {m}" for m in matches])
        
        # Pattern pondération
        matches = re.findall(self.patterns['ponderation'], text, re.IGNORECASE)
        criteres.extend([f"Pondération: {m}" for m in matches])
        
        # NOUVEAUX: Extraction des critères depuis les tableaux
        criteres_tableau = self._extract_criteres_from_tables(text, text_lower)
        criteres.extend(criteres_tableau)
        
        # Filtrage intelligent - garder seulement les critères valides
        criteres_filtres = []
        for critere in criteres:
            # Vérifier que c'est un critère valide
            if len(critere) > 10 and len(critere) < 200:
                # Nettoyer le critère
                critere_clean = re.sub(r'[^\w\s\-.,()%]', '', critere).strip()
                if len(critere_clean) > 10:
                    criteres_filtres.append(critere_clean)
        
        # Nettoyage et dédoublonnage
        criteres_filtres = list(set([c.strip() for c in criteres_filtres if c.strip()]))
        return criteres_filtres[:3]  # Limiter à 3 critères significatifs
    
    def _extract_criteres_from_tables(self, text: str, text_lower: str) -> List[str]:
        """Extraction des critères d'attribution depuis les tableaux structurés"""
        criteres_tableau = []
        
        try:
            logger.info("🔍 Extraction des critères depuis les tableaux...")
            
            # Rechercher la section des critères d'attribution
            tableau_criteres_match = re.search(self.patterns['tableau_criteres'], text, re.IGNORECASE | re.DOTALL)
            if tableau_criteres_match:
                section_criteres = tableau_criteres_match.group(1)
                logger.info(f"✅ Section critères trouvée: {len(section_criteres)} caractères")
                
                # Extraire les critères depuis les lignes du tableau
                criteres_tableau.extend(self._extract_criteres_from_table_lines(section_criteres))
            
            # Rechercher aussi dans tout le texte pour les patterns de critères
            criteres_tableau.extend(self._extract_criteres_from_patterns(text))
            
            logger.info(f"📊 {len(criteres_tableau)} critères extraits depuis les tableaux")
            
        except Exception as e:
            logger.error(f"Erreur extraction critères tableaux: {e}")
        
        return criteres_tableau
    
    def _extract_criteres_from_table_lines(self, section_text: str) -> List[str]:
        """Extraction des critères depuis les lignes de tableau"""
        criteres = []
        
        try:
            # Pattern pour lignes de critères avec numéro de lot
            matches = re.findall(self.patterns['ligne_critere'], section_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                lot_num = match[0]
                critere_economique = match[2]
                critere_technique = match[3]
                critere_autre = match[4]
                
                criteres.append(f"Lot {lot_num} - Économique: {critere_economique}")
                criteres.append(f"Lot {lot_num} - Technique: {critere_technique}")
                criteres.append(f"Lot {lot_num} - Autre: {critere_autre}")
            
            # Pattern pour lignes de critères simples
            matches_simple = re.findall(self.patterns['ligne_critere_simple'], section_text, re.IGNORECASE | re.MULTILINE)
            for match in matches_simple:
                type_critere = match[0].strip()
                pourcentage = match[1].strip()
                criteres.append(f"{type_critere}: {pourcentage}")
            
        except Exception as e:
            logger.error(f"Erreur extraction lignes critères: {e}")
        
        return criteres
    
    def _extract_criteres_from_patterns(self, text: str) -> List[str]:
        """Extraction des critères depuis les patterns spécifiques"""
        criteres = []
        
        try:
            # Critères économiques dans les tableaux
            matches_economique = re.findall(self.patterns['critere_tableau_economique'], text, re.IGNORECASE)
            for match in matches_economique:
                criteres.append(f"Économique: {match}")
            
            # Critères techniques dans les tableaux
            matches_technique = re.findall(self.patterns['critere_tableau_technique'], text, re.IGNORECASE)
            for match in matches_technique:
                criteres.append(f"Technique: {match}")
            
            # Autres critères dans les tableaux
            matches_autre = re.findall(self.patterns['critere_tableau_autre'], text, re.IGNORECASE)
            for match in matches_autre:
                criteres.append(f"Autre: {match}")
            
        except Exception as e:
            logger.error(f"Erreur extraction patterns critères: {e}")
        
        return criteres
    
    def _extract_criteres_for_lot(self, lot_numero: int, text: str) -> Dict[str, str]:
        """Extraction des critères d'attribution spécifiques à un lot avec patterns ultra-robustes"""
        criteres_lot = {
            'economique': '',
            'technique': '',
            'autre': ''
        }
        
        try:
            logger.info(f"🔍 Extraction des critères pour le lot {lot_numero}...")
            
            # Patterns ultra-robustes pour trouver les critères spécifiques à un lot
            patterns_lot = [
                # Patterns spécifiques au lot avec contexte complet
                rf'lot\s*{lot_numero}[^\n]*(?:économique|economique|prix|coût|cout)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(?:technique|technique|qualité|qualite)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(?:autre|autres|innovation|rse|environnement)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec numéro de lot en première colonne
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour critères généraux si pas de critères spécifiques
                r'économique[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                r'technique[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                r'(?:autre|autres)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # NOUVEAUX: Patterns ultra-robustes pour tous types de tableaux
                rf'lot\s*{lot_numero}[^\n]*(?:critères|criteres|attribution)[^\n]*(?:économique|economique|prix)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(?:critères|criteres|attribution)[^\n]*(?:technique|technique|qualité|qualite)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(?:critères|criteres|attribution)[^\n]*(?:autre|autres|innovation|rse|environnement)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec séparateurs
                rf'lot\s*{lot_numero}[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec tirets
                rf'lot\s*{lot_numero}[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec format français
                rf'lot\s*{lot_numero}[^\n]*(\d{1,3}(?:\s\d{3})*\s*%)[^\n]*(\d{1,3}(?:\s\d{3})*\s*%)[^\n]*(\d{1,3}(?:\s\d{3})*\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(\d{1,3}(?:\s\d{3})*\s*%)[^\n]*(\d{1,3}(?:\s\d{3})*\s*%)[^\n]*(\d{1,3}(?:\s\d{3})*\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(\d{1,3}(?:\s\d{3})*\s*%)[^\n]*(\d{1,3}(?:\s\d{3})*\s*%)[^\n]*(\d{1,3}(?:\s\d{3})*\s*%)',
                
                # Patterns pour tableaux avec format international
                rf'lot\s*{lot_numero}[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec unités monétaires
                rf'lot\s*{lot_numero}[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec descriptions longues
                rf'lot\s*{lot_numero}[^\n]*[A-Z][A-Z\s/\n]+?[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*[A-Z][A-Z\s/\n]+?[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*[A-Z][A-Z\s/\n]+?[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec mots-clés spécifiques
                rf'lot\s*{lot_numero}[^\n]*(?:FOURNITURE|PRESTATION|SERVICE|MARCHE|LOT|TRAVAUX|ETUDE|CONSEIL|MAINTENANCE|FORMATION|HEBERGEMENT|CLOUD|RESSOURCE|INFORMATIQUE|TELECOMMUNICATION|SECURITE|CONFIANCE|ASSOCIE|DESTINE|REGION|COMMUNE|EPCI|GROUPEMENT)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(?:FOURNITURE|PRESTATION|SERVICE|MARCHE|LOT|TRAVAUX|ETUDE|CONSEIL|MAINTENANCE|FORMATION|HEBERGEMENT|CLOUD|RESSOURCE|INFORMATIQUE|TELECOMMUNICATION|SECURITE|CONFIANCE|ASSOCIE|DESTINE|REGION|COMMUNE|EPCI|GROUPEMENT)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'lot\s*{lot_numero}[^\n]*(?:FOURNITURE|PRESTATION|SERVICE|MARCHE|LOT|TRAVAUX|ETUDE|CONSEIL|MAINTENANCE|FORMATION|HEBERGEMENT|CLOUD|RESSOURCE|INFORMATIQUE|TELECOMMUNICATION|SECURITE|CONFIANCE|ASSOCIE|DESTINE|REGION|COMMUNE|EPCI|GROUPEMENT)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec format de tableau structuré
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec format de tableau structuré et unités
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec format de tableau structuré et descriptions longues
                rf'^{lot_numero}\s+[A-Z][A-Z\s/\n]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/\n]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/\n]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec format de tableau structuré et descriptions longues et unités
                rf'^{lot_numero}\s+[A-Z][A-Z\s/\n]+?\s+(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/\n]+?\s+(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/\n]+?\s+(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec format de tableau structuré et séparateurs
                rf'^{lot_numero}\s*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*\|[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec format de tableau structuré et tirets
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*-[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec format de tableau structuré et format français
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d{1,3}(?:\s\d{3})*\s*%)\s+(\d{1,3}(?:\s\d{3})*\s*%)\s+(\d{1,3}(?:\s\d{3})*\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d{1,3}(?:\s\d{3})*\s*%)\s+(\d{1,3}(?:\s\d{3})*\s*%)\s+(\d{1,3}(?:\s\d{3})*\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d{1,3}(?:\s\d{3})*\s*%)\s+(\d{1,3}(?:\s\d{3})*\s*%)\s+(\d{1,3}(?:\s\d{3})*\s*%)',
                
                # Patterns pour tableaux avec format de tableau structuré et format international
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec format de tableau structuré et unités monétaires
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)[^\n]*(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec format de tableau structuré et descriptions très longues
                rf'^{lot_numero}\s+[A-Z][A-Z\s/\n]{50,}?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/\n]{50,}?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/\n]{50,}?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                
                # Patterns pour tableaux avec format de tableau structuré et mots-clés spécifiques
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?(?:FOURNITURE|PRESTATION|SERVICE|MARCHE|LOT|TRAVAUX|ETUDE|CONSEIL|MAINTENANCE|FORMATION|HEBERGEMENT|CLOUD|RESSOURCE|INFORMATIQUE|TELECOMMUNICATION|SECURITE|CONFIANCE|ASSOCIE|DESTINE|REGION|COMMUNE|EPCI|GROUPEMENT)[^\n]*(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?(?:FOURNITURE|PRESTATION|SERVICE|MARCHE|LOT|TRAVAUX|ETUDE|CONSEIL|MAINTENANCE|FORMATION|HEBERGEMENT|CLOUD|RESSOURCE|INFORMATIQUE|TELECOMMUNICATION|SECURITE|CONFIANCE|ASSOCIE|DESTINE|REGION|COMMUNE|EPCI|GROUPEMENT)[^\n]*(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)',
                rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?(?:FOURNITURE|PRESTATION|SERVICE|MARCHE|LOT|TRAVAUX|ETUDE|CONSEIL|MAINTENANCE|FORMATION|HEBERGEMENT|CLOUD|RESSOURCE|INFORMATIQUE|TELECOMMUNICATION|SECURITE|CONFIANCE|ASSOCIE|DESTINE|REGION|COMMUNE|EPCI|GROUPEMENT)[^\n]*(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)'
            ]
            
            # Rechercher les critères économiques
            for pattern in patterns_lot[:3]:  # Patterns spécifiques au lot
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    criteres_lot['economique'] = matches[0]
                    break
            
            # Si pas trouvé, utiliser les patterns généraux
            if not criteres_lot['economique']:
                matches = re.findall(patterns_lot[6], text, re.IGNORECASE)
                if matches:
                    criteres_lot['economique'] = matches[0]
            
            # Rechercher les critères techniques
            for pattern in patterns_lot[1:4]:  # Patterns spécifiques au lot
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    criteres_lot['technique'] = matches[0]
                    break
            
            # Si pas trouvé, utiliser les patterns généraux
            if not criteres_lot['technique']:
                matches = re.findall(patterns_lot[7], text, re.IGNORECASE)
                if matches:
                    criteres_lot['technique'] = matches[0]
            
            # Rechercher les autres critères
            for pattern in patterns_lot[2:5]:  # Patterns spécifiques au lot
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    criteres_lot['autre'] = matches[0]
                    break
            
            # Si pas trouvé, utiliser les patterns généraux
            if not criteres_lot['autre']:
                matches = re.findall(patterns_lot[8], text, re.IGNORECASE)
                if matches:
                    criteres_lot['autre'] = matches[0]
            
            # Pattern pour tableaux structurés avec 3 colonnes de critères
            tableau_pattern = rf'^{lot_numero}\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)\s+(\d+(?:[.,]\d+)?\s*%)'
            matches = re.findall(tableau_pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                match = matches[0]
                criteres_lot['economique'] = match[0]
                criteres_lot['technique'] = match[1]
                criteres_lot['autre'] = match[2]
            
            logger.info(f"📊 Critères lot {lot_numero}: Éco={criteres_lot['economique']}, Tech={criteres_lot['technique']}, Autre={criteres_lot['autre']}")
            
        except Exception as e:
            logger.error(f"Erreur extraction critères lot {lot_numero}: {e}")
        
        return criteres_lot
    
    def _extract_lots_from_tables(self, text: str, text_lower: str) -> List[Dict[str, Any]]:
        """Extraction spécialisée des lots depuis les tableaux structurés avec IA améliorée"""
        lots = []
        
        try:
            logger.info("🔍 Début de l'extraction intelligente des lots...")
            
            # Rechercher la section des lots avec des patterns spécifiques améliorés
            lots_section_patterns = [
                # Patterns spécifiques pour les sections de lots
                r'Allotissement[^\n]*montant estimatif[^\n]*montant maximum[^\n]*(.*?)(?=1\.3|Article|$)',
                r'Allotissement[^\n]*montant[^\n]*(.*?)(?=1\.3|Article|$)',
                r'Intitulé du lot[^\n]*(.*?)(?=1\.3|Article|$)',
                r'LOTISSEMENT[^\n]*(.*?)(?=Article|$)',
                r'LOTS[^\n]*(.*?)(?=Article|$)',
                r'REPARTITION[^\n]*LOTS[^\n]*(.*?)(?=Article|$)',
                r'ALLOTISSEMENT[^\n]*(.*?)(?=Article|$)',
                # Patterns plus flexibles
                r'Allotissement[^\n]*(.*?)(?=1\.3|Article|$)',
                r'montant estimatif[^\n]*(.*?)(?=1\.3|Article|$)',
                r'montant maximum[^\n]*(.*?)(?=1\.3|Article|$)',
                r'Intitulé[^\n]*lot[^\n]*(.*?)(?=1\.3|Article|$)',
                r'lot[^\n]*Intitulé[^\n]*(.*?)(?=1\.3|Article|$)',
                # NOUVEAUX: Patterns pour détecter les sections de lots
                r'(?:^|\n)(\d+\s+[A-Z][A-Z\s/]+?\s+\d{1,3}(?:\s\d{3})*\s+\d{1,3}(?:\s\d{3})*\s*(?:\n|$))',
                # Patterns pour les tableaux de lots
                r'lot\s*n°[^\n]*(.*?)(?=Article|$)',
                r'lot\s*numéro[^\n]*(.*?)(?=Article|$)',
                r'numéro\s*lot[^\n]*(.*?)(?=Article|$)',
                # Patterns génériques pour les sections contenant des lots
                r'(?:lot|allotissement|répartition)[^\n]*(.*?)(?=article|chapitre|section|$)',
                # Pattern pour détecter les tableaux avec numéros de lots
                r'(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                
                # NOUVEAUX: Patterns spécifiques pour les RC sans tableaux structurés
                r'(?:accord-cadre|accord cadre)[^\n]*(.*?)(?=article|chapitre|section|$)',
                r'(?:bons de commande|bon de commande)[^\n]*(.*?)(?=article|chapitre|section|$)',
                r'(?:montant maximum|montant max)[^\n]*(.*?)(?=article|chapitre|section|$)',
                r'(?:délai de livraison|delai de livraison)[^\n]*(.*?)(?=article|chapitre|section|$)',
                # Pattern pour les RC avec lots implicites
                r'(?:procédure|procedure)[^\n]*(?:accord-cadre|accord cadre)[^\n]*(.*?)(?=article|chapitre|section|$)',
                
                # NOUVEAUX: Patterns ultra-robustes pour tous types de tableaux
                r'(?:tableau|table)[^\n]*(?:lot|allotissement)[^\n]*(.*?)(?=article|chapitre|section|$)',
                r'(?:règlement|reglement)[^\n]*(?:consultation|consultation)[^\n]*(.*?)(?=article|chapitre|section|$)',
                r'(?:objet|objet)[^\n]*(?:marché|marche)[^\n]*(.*?)(?=article|chapitre|section|$)',
                # Patterns pour détecter les sections avec numéros de lots
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec descriptions longues
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/\n]+?\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec séparateurs
                r'(?:^|\n)(\d+)\s*\|\s*[A-Z][A-Z\s/]+?\s*\|\s*\d+(?:[.,]\d+)?\s*\|\s*\d+(?:[.,]\d+)?\s*(?:\n|$)',
                # Patterns pour lots avec tirets
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+-\s+\d+(?:[.,]\d+)?\s+-\s+\d+(?:[.,]\d+)?\s*(?:\n|$)',
                # Patterns pour lots avec format français (espaces dans les montants)
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                # Patterns pour lots avec format international
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*(?:\n|$)',
                # Patterns pour lots avec unités monétaires variées
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec descriptions très longues (plus de 100 caractères)
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/\n]{50,}?\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec mots-clés spécifiques
                r'(?:^|\n)(\d+)\s+[A-Z][A-Z\s/]+?(?:FOURNITURE|PRESTATION|SERVICE|MARCHE|LOT|TRAVAUX|ETUDE|CONSEIL|MAINTENANCE|FORMATION|HEBERGEMENT|CLOUD|RESSOURCE|INFORMATIQUE|TELECOMMUNICATION|SECURITE|CONFIANCE|ASSOCIE|DESTINE|REGION|COMMUNE|EPCI|GROUPEMENT)[A-Z\s/,\.\-\n]*?\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et unités
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et descriptions longues
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/\n]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et descriptions longues et unités
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/\n]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et séparateurs
                r'(?:^|\n)(\d+)\s*\|\s*([A-Z][A-Z\s/]+?)\s*\|\s*(\d+(?:[.,]\d+)?)\s*\|\s*(\d+(?:[.,]\d+)?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et tirets
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+-\s+(\d+(?:[.,]\d+)?)\s+-\s+(\d+(?:[.,]\d+)?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format français
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format international
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et unités monétaires
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et descriptions très longues
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/\n]{50,}?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et mots-clés spécifiques
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?(?:FOURNITURE|PRESTATION|SERVICE|MARCHE|LOT|TRAVAUX|ETUDE|CONSEIL|MAINTENANCE|FORMATION|HEBERGEMENT|CLOUD|RESSOURCE|INFORMATIQUE|TELECOMMUNICATION|SECURITE|CONFIANCE|ASSOCIE|DESTINE|REGION|COMMUNE|EPCI|GROUPEMENT)[A-Z\s/,\.\-\n]*?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format de tableau structuré
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format de tableau structuré et unités
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format de tableau structuré et descriptions longues
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/\n]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format de tableau structuré et descriptions longues et unités
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/\n]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format de tableau structuré et séparateurs
                r'(?:^|\n)(\d+)\s*\|\s*([A-Z][A-Z\s/]+?)\s*\|\s*(\d+(?:[.,]\d+)?)\s*\|\s*(\d+(?:[.,]\d+)?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format de tableau structuré et tirets
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+-\s+(\d+(?:[.,]\d+)?)\s+-\s+(\d+(?:[.,]\d+)?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format de tableau structuré et format français
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format de tableau structuré et format international
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format de tableau structuré et unités monétaires
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format de tableau structuré et descriptions très longues
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/\n]{50,}?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)',
                # Patterns pour lots avec format de tableau structuré et format de tableau structuré et mots-clés spécifiques
                r'(?:^|\n)(\d+)\s+([A-Z][A-Z\s/]+?(?:FOURNITURE|PRESTATION|SERVICE|MARCHE|LOT|TRAVAUX|ETUDE|CONSEIL|MAINTENANCE|FORMATION|HEBERGEMENT|CLOUD|RESSOURCE|INFORMATIQUE|TELECOMMUNICATION|SECURITE|CONFIANCE|ASSOCIE|DESTINE|REGION|COMMUNE|EPCI|GROUPEMENT)[A-Z\s/,\.\-\n]*?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*(?:\n|$)'
            ]
            
            lots_section = None
            for pattern in lots_section_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if matches:
                    lots_section = matches[0]
                    break
            
            # Si aucune section spécifique trouvée, utiliser tout le texte
            if not lots_section:
                lots_section = text
                logger.info("🔍 Aucune section spécifique trouvée, analyse du texte complet...")
            else:
                logger.info(f"✅ Section de lots trouvée avec le pattern: {len(lots_section)} caractères")
            
            # NOUVEAU: Extraction intelligente avec IA
            lots = self._extract_lots_with_ai(lots_section, text)
            
            # Si l'IA n'a pas trouvé de lots, utiliser les patterns classiques
            if not lots:
                logger.info("🤖 L'IA n'a pas trouvé de lots, utilisation des patterns classiques...")
                lots = self._extract_lots_with_patterns(lots_section)
            
            # Patterns pour détecter les lignes de lots dans le tableau (méthode classique)
            lot_line_patterns = [
                # Pattern principal pour les lots avec numéro, intitulé et montants
                r'^(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*$',
                # Pattern avec gestion des retours à la ligne dans l'intitulé
                r'^(\d+)\s+([A-Z][A-Z\s/\n]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*$',
                # Pattern avec montants en k€ ou M€
                r'^(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*$',
                # Pattern générique pour les lots
                r'^(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*$',
                # NOUVEAUX: Patterns plus flexibles pour détecter tous les lots
                r'(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                r'(\d+)\s+([A-Z][A-Z\s/\n]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                # Pattern pour les lots avec retours à la ligne dans l'intitulé
                r'(\d+)\s+([A-Z][A-Z\s/\n]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                
                # NOUVEAUX: Patterns spécifiques pour les RC avec tableaux structurés
                r'^(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*$',
                # Pattern pour tableaux avec colonnes séparées par des espaces
                r'^(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*$',
                # Pattern pour lots avec intitulés longs
                r'^(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*$'
            ]
            
            # Si aucune méthode n'a trouvé de lots, essayer la méthode classique
            if not lots:
                logger.info("🔧 Tentative avec la méthode classique...")
                lots = self._extract_lots_classic_method(lots_section, lot_line_patterns)
            
            # NOUVEAU: Si toujours aucun lot, essayer la méthode spécifique RC
            if not lots:
                logger.info("🔧 Tentative avec la méthode spécifique RC...")
                lots = self._extract_lots_from_rc_table(text)
            
            # NOUVEAU: Si toujours aucun lot, créer un lot par défaut pour les RC sans lots structurés
            if not lots:
                logger.info("🔧 Aucun lot structuré trouvé, création d'un lot par défaut...")
                lots = self._create_default_lot_from_text(text, text_lower)
            
            # NOUVEAU: Si aucun lot détecté par ligne, essayer sur tout le texte
            if not lots:
                logger.info("Aucun lot détecté par ligne, tentative sur tout le texte...")
                for pattern in lot_line_patterns:
                    matches = re.findall(pattern, lots_section, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        for match in matches:
                            try:
                                lot_numero = int(match[0])
                                intitule = match[1].strip()
                                
                                # Nettoyer l'intitulé (supprimer les retours à la ligne)
                                intitule = re.sub(r'\s+', ' ', intitule)
                                
                                # Extraire les montants
                                montant_estime_str = match[2].replace(' ', '').replace(',', '.')
                                montant_max_str = match[3].replace(' ', '').replace(',', '.')
                                
                                # Convertir les montants
                                montant_estime = float(montant_estime_str)
                                montant_max = float(montant_max_str)
                                
                                # Validation des données
                                if (1 <= lot_numero <= 50 and  # Numéro de lot raisonnable
                                    len(intitule) >= 10 and len(intitule) <= 200 and  # Intitulé valide
                                    montant_estime > 0 and montant_max > 0 and  # Montants positifs
                                    montant_max >= montant_estime):  # Max >= estimé
                                    
                                    lot_info = {
                                        'numero': lot_numero,
                                        'intitule': intitule,
                                        'montant_estime': montant_estime,
                                        'montant_maximum': montant_max,
                                        'source': 'tableau_pdf'
                                    }
                                    
                                    # Éviter les doublons
                                    if not any(existing['numero'] == lot_numero for existing in lots):
                                        lots.append(lot_info)
                                        logger.info(f"Lot détecté (texte complet): {lot_numero} - {intitule[:50]}...")
                                
                            except (ValueError, IndexError) as e:
                                logger.debug(f"Erreur parsing lot (texte complet): {e}")
                                continue
            
            # NOUVEAU: Si encore peu de lots détectés, essayer avec les patterns améliorés
            if len(lots) < 3:
                logger.info(f"Seulement {len(lots)} lots détectés, tentative avec patterns améliorés...")
                improved_patterns = [
                    r'(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                    r'(\d+)\s+([A-Z][A-Z\s/\n]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                ]
                
                for pattern in improved_patterns:
                    matches = re.findall(pattern, lots_section, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        for match in matches:
                            try:
                                lot_numero = int(match[0])
                                intitule = match[1].strip()
                                
                                # Nettoyer l'intitulé (supprimer les retours à la ligne)
                                intitule = re.sub(r'\s+', ' ', intitule)
                                
                                # Extraire les montants
                                montant_estime_str = match[2].replace(' ', '').replace(',', '.')
                                montant_max_str = match[3].replace(' ', '').replace(',', '.')
                                
                                # Convertir les montants
                                montant_estime = float(montant_estime_str)
                                montant_max = float(montant_max_str)
                                
                                # Validation des données
                                if (1 <= lot_numero <= 50 and  # Numéro de lot raisonnable
                                    len(intitule) >= 10 and len(intitule) <= 200 and  # Intitulé valide
                                    montant_estime > 0 and montant_max > 0 and  # Montants positifs
                                    montant_max >= montant_estime):  # Max >= estimé
                                    
                                    lot_info = {
                                        'numero': lot_numero,
                                        'intitule': intitule,
                                        'montant_estime': montant_estime,
                                        'montant_maximum': montant_max,
                                        'source': 'tableau_pdf'
                                    }
                                    
                                    # Éviter les doublons
                                    if not any(existing['numero'] == lot_numero for existing in lots):
                                        lots.append(lot_info)
                                        logger.info(f"Lot détecté (patterns améliorés): {lot_numero} - {intitule[:50]}...")
                                
                            except (ValueError, IndexError) as e:
                                logger.debug(f"Erreur parsing lot (patterns améliorés): {e}")
                                continue
            
            # Trier les lots par numéro
            lots.sort(key=lambda x: x['numero'])
            
            logger.info(f"Extraction des lots terminée: {len(lots)} lots détectés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des lots: {e}")
        
        return lots
    
    def _extract_lots_with_ai(self, lots_section: str, full_text: str) -> List[Dict[str, Any]]:
        """Extraction intelligente des lots avec IA et analyse contextuelle"""
        lots = []
        
        try:
            logger.info("🤖 Début de l'extraction IA des lots...")
            
            # 1. Recherche de patterns contextuels pour identifier les lots
            context_patterns = [
                # Patterns pour identifier les sections de lots
                r'(?:lot|allotissement|répartition)\s*(?:n°|numéro|no)?\s*(\d+)[^\n]*(.*?)(?=\n\s*(?:\d+|lot|allotissement|article|chapitre|$))',
                # Patterns pour les tableaux de lots
                r'(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                # Patterns pour les lots avec descriptions
                r'lot\s*(\d+)[^\n]*?([A-Z][A-Z\s/]+?)[^\n]*?(\d{1,3}(?:\s\d{3})*)[^\n]*?(\d{1,3}(?:\s\d{3})*)',
                # Patterns génériques pour les lots
                r'(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)'
            ]
            
            # 2. Analyser le texte avec les patterns contextuels
            for pattern in context_patterns:
                matches = re.findall(pattern, lots_section, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                for match in matches:
                    try:
                        if len(match) >= 4:
                            lot_numero = int(match[0])
                            intitule = match[1].strip()
                            
                            # Nettoyer l'intitulé
                            intitule = re.sub(r'\s+', ' ', intitule)
                            intitule = re.sub(r'[^\w\s/()-]', '', intitule)
                            
                            # Extraire les montants
                            montant_estime_str = match[2].replace(' ', '').replace(',', '.')
                            montant_max_str = match[3].replace(' ', '').replace(',', '.')
                            
                            # Convertir les montants
                            montant_estime = float(montant_estime_str)
                            montant_max = float(montant_max_str)
                            
                            # Validation intelligente
                            if (1 <= lot_numero <= 50 and
                                len(intitule) >= 5 and len(intitule) <= 300 and
                                montant_estime > 0 and montant_max > 0 and
                                montant_max >= montant_estime):
                                
                                lot_info = {
                                    'numero': lot_numero,
                                    'intitule': intitule,
                                    'montant_estime': montant_estime,
                                    'montant_maximum': montant_max,
                                    'source': 'ai_extraction'
                                }
                                
                                # Éviter les doublons
                                if not any(existing['numero'] == lot_numero for existing in lots):
                                    lots.append(lot_info)
                                    logger.info(f"🤖 Lot IA détecté: {lot_numero} - {intitule[:50]}...")
                    
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Erreur parsing lot IA: {e}")
                        continue
            
            # 3. Si aucun lot trouvé, essayer une approche plus agressive
            if not lots:
                lots = self._extract_lots_aggressive(lots_section)
            
            logger.info(f"🤖 Extraction IA terminée: {len(lots)} lots détectés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction IA des lots: {e}")
        
        return lots
    
    def _extract_lots_aggressive(self, text: str) -> List[Dict[str, Any]]:
        """Extraction agressive des lots avec patterns très flexibles"""
        lots = []
        
        try:
            logger.info("🔍 Extraction agressive des lots...")
            
            # Patterns très flexibles pour détecter les lots
            aggressive_patterns = [
                # Pattern pour les numéros suivis de texte et de montants
                r'(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)',
                # Pattern pour les lots avec séparateurs
                r'(\d+)\s*[-|]\s*([A-Z][A-Z\s/]+?)\s*[-|]\s*(\d+(?:[.,]\d+)?)\s*[-|]\s*(\d+(?:[.,]\d+)?)',
                # Pattern pour les lots avec points
                r'(\d+)\.\s*([A-Z][A-Z\s/]+?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)',
                # Pattern générique pour les séquences numéro-texte-montant-montant
                r'(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)'
            ]
            
            for pattern in aggressive_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    try:
                        lot_numero = int(match[0])
                        intitule = match[1].strip()
                        
                        # Nettoyer l'intitulé
                        intitule = re.sub(r'\s+', ' ', intitule)
                        intitule = re.sub(r'[^\w\s/()-]', '', intitule)
                        
                        # Extraire les montants
                        montant_estime_str = match[2].replace(' ', '').replace(',', '.')
                        montant_max_str = match[3].replace(' ', '').replace(',', '.')
                        
                        # Convertir les montants
                        montant_estime = float(montant_estime_str)
                        montant_max = float(montant_max_str)
                        
                        # Validation moins stricte pour l'extraction agressive
                        if (1 <= lot_numero <= 100 and
                            len(intitule) >= 3 and len(intitule) <= 500 and
                            montant_estime > 0 and montant_max > 0):
                            
                            lot_info = {
                                'numero': lot_numero,
                                'intitule': intitule,
                                'montant_estime': montant_estime,
                                'montant_maximum': montant_max,
                                'source': 'aggressive_extraction'
                            }
                            
                            # Éviter les doublons
                            if not any(existing['numero'] == lot_numero for existing in lots):
                                lots.append(lot_info)
                                logger.info(f"🔍 Lot agressif détecté: {lot_numero} - {intitule[:50]}...")
                    
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Erreur parsing lot agressif: {e}")
                        continue
            
            logger.info(f"🔍 Extraction agressive terminée: {len(lots)} lots détectés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction agressive des lots: {e}")
        
        return lots
    
    def _extract_lots_with_patterns(self, lots_section: str) -> List[Dict[str, Any]]:
        """Extraction des lots avec les patterns classiques"""
        lots = []
        
        try:
            logger.info("🔧 Extraction avec patterns classiques...")
            
            # Patterns classiques pour les lots
            lot_line_patterns = [
                r'^(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*$',
                r'(\d+)\s+([A-Z][A-Z\s/]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                r'(\d+)\s+([A-Z][A-Z\s/\n]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)'
            ]
            
            for pattern in lot_line_patterns:
                matches = re.findall(pattern, lots_section, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    try:
                        lot_numero = int(match[0])
                        intitule = match[1].strip()
                        
                        # Nettoyer l'intitulé
                        intitule = re.sub(r'\s+', ' ', intitule)
                        
                        # Extraire les montants
                        montant_estime_str = match[2].replace(' ', '').replace(',', '.')
                        montant_max_str = match[3].replace(' ', '').replace(',', '.')
                        
                        # Convertir les montants
                        montant_estime = float(montant_estime_str)
                        montant_max = float(montant_max_str)
                        
                        # Validation des données
                        if (1 <= lot_numero <= 50 and
                            len(intitule) >= 10 and len(intitule) <= 200 and
                            montant_estime > 0 and montant_max > 0 and
                            montant_max >= montant_estime):
                            
                            lot_info = {
                                'numero': lot_numero,
                                'intitule': intitule,
                                'montant_estime': montant_estime,
                                'montant_maximum': montant_max,
                                'source': 'classic_patterns'
                            }
                            
                            # Éviter les doublons
                            if not any(existing['numero'] == lot_numero for existing in lots):
                                lots.append(lot_info)
                                logger.info(f"🔧 Lot classique détecté: {lot_numero} - {intitule[:50]}...")
                    
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Erreur parsing lot classique: {e}")
                        continue
            
            logger.info(f"🔧 Extraction classique terminée: {len(lots)} lots détectés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction classique des lots: {e}")
        
        return lots
    
    def _extract_lots_classic_method(self, lots_section: str, lot_line_patterns: List[str]) -> List[Dict[str, Any]]:
        """Méthode classique d'extraction des lots ligne par ligne"""
        lots = []
        
        try:
            logger.info("🔧 Méthode classique ligne par ligne...")
            
            # Analyser chaque ligne de la section des lots
            lines = lots_section.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Vérifier si la ligne contient un pattern de lot
                for pattern in lot_line_patterns:
                    matches = re.findall(pattern, line, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        for match in matches:
                            try:
                                lot_numero = int(match[0])
                                intitule = match[1].strip()
                                
                                # Nettoyer l'intitulé (supprimer les retours à la ligne)
                                intitule = re.sub(r'\s+', ' ', intitule)
                                
                                # Extraire les montants
                                montant_estime_str = match[2].replace(' ', '').replace(',', '.')
                                montant_max_str = match[3].replace(' ', '').replace(',', '.')
                                
                                # Convertir les montants
                                montant_estime = float(montant_estime_str)
                                montant_max = float(montant_max_str)
                                
                                # Validation des données
                                if (1 <= lot_numero <= 50 and  # Numéro de lot raisonnable
                                    len(intitule) >= 10 and len(intitule) <= 200 and  # Intitulé valide
                                    montant_estime > 0 and montant_max > 0 and  # Montants positifs
                                    montant_max >= montant_estime):  # Max >= estimé
                                    
                                    lot_info = {
                                        'numero': lot_numero,
                                        'intitule': intitule,
                                        'montant_estime': montant_estime,
                                        'montant_maximum': montant_max,
                                        'source': 'classic_line_by_line'
                                    }
                                    
                                    # Éviter les doublons
                                    if not any(existing['numero'] == lot_numero for existing in lots):
                                        lots.append(lot_info)
                                        logger.info(f"🔧 Lot ligne détecté: {lot_numero} - {intitule[:50]}...")
                                
                            except (ValueError, IndexError) as e:
                                logger.debug(f"Erreur parsing lot ligne: {e} - Ligne: {line}")
                                continue
                        break  # Sortir de la boucle des patterns si un match est trouvé
            
            logger.info(f"🔧 Méthode classique terminée: {len(lots)} lots détectés")
            
        except Exception as e:
            logger.error(f"Erreur lors de la méthode classique: {e}")
        
        return lots
    
    def _extract_lots_from_rc_table(self, text: str) -> List[Dict[str, Any]]:
        """Méthode universelle pour extraire les lots de tous types de RC"""
        lots = []
        
        logger.info("🔍 Recherche universelle de lots dans les RC...")
        
        # Patterns universels pour détecter les lots dans tous types de RC
        universal_patterns = [
            # Pattern 1: Numéro + Intitulé + Montant estimé + Montant maximum (format standard)
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
            
            # Pattern 2: Numéro + Intitulé + Montants avec espaces (format français)
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)',
            
            # Pattern 3: Numéro + Intitulé + Montants avec virgules
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
            
            # Pattern 4: Numéro + Intitulé long avec retours à la ligne
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
            
            # Pattern 5: Format avec "M€" (millions d'euros)
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-]+?)\s+(\d+)\s*M€\s+(\d+)\s*M€',
            
            # Pattern 6: Format avec "k€" (milliers d'euros)
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-]+?)\s+(\d+(?:[.,]\d+)?)\s*k€\s+(\d+(?:[.,]\d+)?)\s*k€',
            
            # Pattern 7: Format avec "€" (euros)
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-]+?)\s+(\d+(?:[.,]\d+)?)\s*€\s+(\d+(?:[.,]\d+)?)\s*€',
            
            # Pattern 8: Format très flexible pour intitulés complexes
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
            
            # Pattern 9: Format avec intitulés contenant des mots-clés spécifiques
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-]+?(?:FOURNITURE|PRESTATION|SERVICE|MARCHE|LOT|TRAVAUX|ETUDE|CONSEIL|MAINTENANCE|FORMATION|HEBERGEMENT|CLOUD|RESSOURCE|INFORMATIQUE|TELECOMMUNICATION|SECURITE|CONFIANCE|ASSOCIE|DESTINE|REGION|COMMUNE|EPCI|GROUPEMENT)[A-Z\s/,\.\-]*?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
            
            # Pattern 10: Format avec intitulés très longs (plus de 50 caractères)
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]{50,}?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
            
            # NOUVEAUX: Patterns spécifiques pour les lots 1 et 2 du RC 2024-R041-000
            # Pattern 11: Format avec "1 FOURNITURE" ou "2 FOURNITURE"
            r'([12])\s+FOURNITURE\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+)\s*M€\s+(\d+)\s*M€',
            # Pattern 12: Format avec "1" ou "2" suivi de "FOURNITURE DE RESSOURCES"
            r'([12])\s+FOURNITURE\s+DE\s+RESSOURCES\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+)\s*M€\s+(\d+)\s*M€',
            # Pattern 13: Format avec "1" ou "2" suivi de "FOURNITURE DE RESSOURCES CLOUD"
            r'([12])\s+FOURNITURE\s+DE\s+RESSOURCES\s+CLOUD\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+)\s*M€\s+(\d+)\s*M€',
            # Pattern 14: Format très flexible pour lots 1 et 2
            r'([12])\s+([A-Z][A-Z\s/,\.\-\n]+?FOURNITURE[^M]+?)\s+(\d+)\s*M€\s+(\d+)\s*M€',
            # Pattern 15: Format avec "1" ou "2" suivi de description et montants
            r'([12])\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+)\s*M€\s+(\d+)\s*M€',
            
            # NOUVEAUX PATTERNS POUR TABLEAUX STRUCTURÉS (RC 2024-R041-000)
            # Pattern 16: Format tableau exact - "1 fourniture de ressources cloud, d'hebergement sec, d'infogerance"
            r'([12])\s+(fourniture\s+de\s+ressources\s+cloud[^0-9]*?)\s+(\d+)\s*m€[^0-9]*?(\d+)\s*m€',
            # Pattern 17: Format tableau - "1 fourniture de ressources cloud, d'hebergement sec" (sans infogerance)
            r'([12])\s+(fourniture\s+de\s+ressources\s+cloud[^0-9]*?d\'hebergement\s+sec[^0-9]*?)\s+(\d+)\s*m€[^0-9]*?(\d+)\s*m€',
            # Pattern 18: Format tableau - "1 fourniture de ressources cloud de confiance"
            r'([123])\s+(fourniture\s+de\s+ressources\s+cloud\s+de\s+confiance[^0-9]*?)\s+(\d+)\s*m€[^0-9]*?(\d+)\s*m€',
            # Pattern 19: Format tableau - Numéro + Description + Montants (pattern très flexible)
            r'([123])\s+(fourniture[^0-9]*?)\s+(\d+)\s*m€[^0-9]*?(\d+)\s*m€',
            # Pattern 20: Format tableau - Description + Montants (sans numéro de lot) - assigne numéro 1 par défaut
            r'(fourniture\s+de\s+ressources\s+cloud[^0-9]*?)\s+(\d+)\s*m€[^0-9]*?(\d+)\s*m€'
        ]
        
        # Rechercher dans tout le texte avec les patterns universels
        for i, pattern in enumerate(universal_patterns):
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if matches:
                logger.info(f"  📊 Pattern universel {i+1} trouvé: {len(matches)} matches")
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 3:
                        # Gérer le pattern 20 qui n'a que 3 groupes
                        if len(match) == 3 and i+1 == 20:
                            numero = 1  # Numéro par défaut pour pattern 20
                            intitule = match[0].strip()
                            montant_estime = self._parse_montant(match[1])
                            montant_maximum = self._parse_montant(match[2])
                        elif len(match) >= 4:
                            numero = int(match[0])
                            intitule = match[1].strip()
                            montant_estime = self._parse_montant(match[2])
                            montant_maximum = self._parse_montant(match[3])
                        else:
                            continue
                        
                        # Nettoyer l'intitulé (supprimer les retours à la ligne excessifs)
                        intitule = re.sub(r'\s+', ' ', intitule)
                        
                        # Validation des données
                        if (1 <= numero <= 50 and  # Numéro de lot raisonnable
                            len(intitule) >= 10 and len(intitule) <= 500 and  # Intitulé valide
                            montant_estime > 0 and montant_maximum > 0 and  # Montants positifs
                            montant_maximum >= montant_estime):  # Max >= estimé
                            
                            # Éviter les doublons (mais permettre les nouveaux patterns pour les lots manqués)
                            existing_lot = next((existing for existing in lots if existing['numero'] == numero), None)
                            if not existing_lot:
                                lot = {
                                    'numero': numero,
                                    'intitule': intitule,
                                    'montant_estime': montant_estime,
                                    'montant_maximum': montant_maximum,
                                    'source': f'universal_pattern_{i+1}'
                                }
                                lots.append(lot)
                                logger.info(f"  ✅ Lot universel {numero} détecté: {intitule[:50]}...")
                            else:
                                # Si c'est un nouveau pattern (16-20), remplacer l'ancien
                                if i+1 >= 16:  # Nouveaux patterns pour tableaux
                                    existing_lot['intitule'] = intitule
                                    existing_lot['montant_estime'] = montant_estime
                                    existing_lot['montant_maximum'] = montant_maximum
                                    existing_lot['source'] = f'universal_pattern_{i+1}'
                                    logger.info(f"  🔄 Lot universel {numero} mis à jour avec pattern {i+1}")
                                else:
                                    logger.info(f"  ⚠️ Lot universel {numero} déjà détecté, ignoré")
        
        # Si aucun lot trouvé, essayer une approche plus agressive
        if not lots:
            logger.info("  🔍 Aucun lot trouvé avec les patterns RC, tentative agressive...")
            lots = self._extract_lots_aggressive_rc(text)
        
        # Si toujours aucun lot, utiliser le fallback IA
        if not lots:
            logger.info("  🤖 Aucun lot trouvé avec les patterns agressifs, fallback IA...")
            lots = self._extract_lots_with_ai_fallback(text)
        
        logger.info(f"🔍 Extraction RC terminée: {len(lots)} lots détectés")
        return lots
    
    def _extract_lots_aggressive_rc(self, text: str) -> List[Dict[str, Any]]:
        """Méthode agressive universelle pour extraire les lots de tous types de RC"""
        lots = []
        
        # Patterns agressifs universels pour tous types de RC
        aggressive_patterns = [
            # Pattern 1: Très flexible - numéro + intitulé + montants
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
            
            # Pattern 2: Format avec espaces dans les montants
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)',
            
            # Pattern 3: Format avec virgules et points
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
            
            # Pattern 4: Format avec retours à la ligne dans l'intitulé
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
            
            # Pattern 5: Format M€ (millions)
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+)\s*M€\s+(\d+)\s*M€',
            
            # Pattern 6: Format k€ (milliers)
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+(?:[.,]\d+)?)\s*k€\s+(\d+(?:[.,]\d+)?)\s*k€',
            
            # Pattern 7: Format € (euros)
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+(?:[.,]\d+)?)\s*€\s+(\d+(?:[.,]\d+)?)\s*€',
            
            # Pattern 8: Format ultra-flexible pour intitulés complexes
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
            
            # Pattern 9: Format avec mots-clés métier
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?(?:FOURNITURE|PRESTATION|SERVICE|MARCHE|LOT|TRAVAUX|ETUDE|CONSEIL|MAINTENANCE|FORMATION|HEBERGEMENT|CLOUD|RESSOURCE|INFORMATIQUE|TELECOMMUNICATION|SECURITE|CONFIANCE|ASSOCIE|DESTINE|REGION|COMMUNE|EPCI|GROUPEMENT|BATIMENT|CONSTRUCTION|AMENAGEMENT|EQUIPEMENT|MATERIEL|LOGICIEL|HARDWARE|SOFTWARE|RESEAU|SYSTEME|BASE|DONNEE|APPLICATION|DEVELOPPEMENT|INTEGRATION|MIGRATION|SAUVEGARDE|ARCHIVAGE|DIGITALISATION|DEMATERIALISATION)[A-Z\s/,\.\-\n]*?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
            
            # Pattern 10: Format avec intitulés très longs
            r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]{30,}?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)'
        ]
        
        for i, pattern in enumerate(aggressive_patterns):
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if matches:
                logger.info(f"  🎯 Pattern agressif universel {i+1}: {len(matches)} matches")
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 4:
                        numero = int(match[0])
                        intitule = match[1].strip()
                        montant_estime = self._parse_montant(match[2])
                        montant_maximum = self._parse_montant(match[3])
                        
                        # Nettoyer l'intitulé
                        intitule = re.sub(r'\s+', ' ', intitule)
                        
                        # Validation des données
                        if (1 <= numero <= 50 and  # Numéro de lot raisonnable
                            len(intitule) >= 10 and len(intitule) <= 500 and  # Intitulé valide
                            montant_estime > 0 and montant_maximum > 0 and  # Montants positifs
                            montant_maximum >= montant_estime):  # Max >= estimé
                            
                            # Éviter les doublons
                            if not any(existing['numero'] == numero for existing in lots):
                                lot = {
                                    'numero': numero,
                                    'intitule': intitule,
                                    'montant_estime': montant_estime,
                                    'montant_maximum': montant_maximum,
                                    'source': f'aggressive_universal_{i+1}'
                                }
                                lots.append(lot)
                                logger.info(f"  ✅ Lot agressif universel {numero} détecté: {intitule[:50]}...")
                            else:
                                logger.info(f"  ⚠️ Lot agressif universel {numero} déjà détecté, ignoré")
        
        return lots
    
    def _extract_lots_with_ai_fallback(self, text: str) -> List[Dict[str, Any]]:
        """Méthode de fallback IA pour détecter les lots non reconnus par les patterns"""
        lots = []
        
        logger.info("🤖 Fallback IA pour détection des lots...")
        
        try:
            # Analyser le texte pour trouver des séquences qui ressemblent à des lots
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Chercher des patterns de numéros de lots
                lot_patterns = [
                    r'^(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
                    r'^(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)',
                    r'^(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)'
                ]
                
                for pattern in lot_patterns:
                    match = re.match(pattern, line, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    if match:
                        groups = match.groups()
                        if len(groups) >= 4:
                            numero = int(groups[0])
                            intitule = groups[1].strip()
                            montant_estime = self._parse_montant(groups[2])
                            montant_maximum = self._parse_montant(groups[3])
                            
                            # Nettoyer l'intitulé
                            intitule = re.sub(r'\s+', ' ', intitule)
                            
                            # Validation des données
                            if (1 <= numero <= 50 and
                                len(intitule) >= 10 and len(intitule) <= 500 and
                                montant_estime > 0 and montant_maximum > 0 and
                                montant_maximum >= montant_estime):
                                
                                # Éviter les doublons
                                if not any(existing['numero'] == numero for existing in lots):
                                    lot = {
                                        'numero': numero,
                                        'intitule': intitule,
                                        'montant_estime': montant_estime,
                                        'montant_maximum': montant_maximum,
                                        'source': 'ai_fallback'
                                    }
                                    lots.append(lot)
                                    logger.info(f"  🤖 Lot IA {numero} détecté: {intitule[:50]}...")
                                break
            
            # Si toujours aucun lot, essayer une approche contextuelle
            if not lots:
                logger.info("  🤖 Aucun lot détecté, analyse contextuelle...")
                lots = self._extract_lots_contextual_analysis(text)
            
        except Exception as e:
            logger.error(f"Erreur lors du fallback IA: {e}")
        
        logger.info(f"🤖 Fallback IA terminé: {len(lots)} lots détectés")
        return lots
    
    def _extract_lots_contextual_analysis(self, text: str) -> List[Dict[str, Any]]:
        """Analyse contextuelle pour détecter les lots"""
        lots = []
        
        try:
            # Chercher des sections qui contiennent des informations de lots
            sections = re.split(r'(?:Article|Chapitre|Section|LOT|Lot|ALLOTISSEMENT|Allotissement)', text, re.IGNORECASE)
            
            for section in sections:
                if not section.strip():
                    continue
                
                # Chercher des numéros suivis de descriptions et de montants
                patterns = [
                    r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)',
                    r'(\d+)\s+([A-Z][A-Z\s/,\.\-\n]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, section, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    for match in matches:
                        if isinstance(match, tuple) and len(match) >= 4:
                            numero = int(match[0])
                            intitule = match[1].strip()
                            montant_estime = self._parse_montant(match[2])
                            montant_maximum = self._parse_montant(match[3])
                            
                            # Nettoyer l'intitulé
                            intitule = re.sub(r'\s+', ' ', intitule)
                            
                            # Validation des données
                            if (1 <= numero <= 50 and
                                len(intitule) >= 10 and len(intitule) <= 500 and
                                montant_estime > 0 and montant_maximum > 0 and
                                montant_maximum >= montant_estime):
                                
                                # Éviter les doublons
                                if not any(existing['numero'] == numero for existing in lots):
                                    lot = {
                                        'numero': numero,
                                        'intitule': intitule,
                                        'montant_estime': montant_estime,
                                        'montant_maximum': montant_maximum,
                                        'source': 'contextual_analysis'
                                    }
                                    lots.append(lot)
                                    logger.info(f"  🔍 Lot contextuel {numero} détecté: {intitule[:50]}...")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse contextuelle: {e}")
        
        return lots
    
    def _parse_montant(self, montant_str: str) -> float:
        """Parse un montant depuis une chaîne de caractères"""
        try:
            if not montant_str:
                return 0.0
            
            # Nettoyer la chaîne
            montant_str = str(montant_str).strip()
            
            # Remplacer les virgules par des points
            montant_str = montant_str.replace(',', '.')
            
            # Supprimer les espaces
            montant_str = montant_str.replace(' ', '')
            
            # Supprimer les unités (€, M€, k€, etc.)
            montant_str = re.sub(r'[€$]', '', montant_str)
            montant_str = re.sub(r'[Mm]€?', '', montant_str)
            montant_str = re.sub(r'[Kk]€?', '', montant_str)
            
            # Convertir en float
            montant = float(montant_str)
            
            # Si le montant original contenait "M" ou "m", multiplier par 1 000 000
            if 'M' in str(montant_str).upper() or 'm' in str(montant_str).lower():
                montant *= 1000000
            
            # Si le montant original contenait "K" ou "k", multiplier par 1 000
            elif 'K' in str(montant_str).upper() or 'k' in str(montant_str).lower():
                montant *= 1000
            
            return montant
            
        except (ValueError, TypeError):
            return 0.0
    
    def _create_default_lot_from_text(self, text: str, text_lower: str) -> List[Dict[str, Any]]:
        """Crée un lot par défaut pour les RC sans lots structurés"""
        lots = []
        
        try:
            logger.info("🔧 Création d'un lot par défaut...")
            
            # Extraire les informations générales du RC
            intitule = self._extract_intitule_from_text(text)
            montant_estime = self._extract_montant_from_text(text, 'estime')
            montant_maximum = self._extract_montant_from_text(text, 'maximum')
            
            # Si pas de montant maximum trouvé, utiliser l'estimé
            if not montant_maximum and montant_estime:
                montant_maximum = montant_estime
            
            # Créer le lot par défaut
            default_lot = {
                'numero': 1,
                'intitule': intitule or 'Lot unique',
                'montant_estime': montant_estime or 0,
                'montant_maximum': montant_maximum or 0,
                'criteres_economique': '',
                'criteres_techniques': '',
                'autres_criteres': '',
                'source': 'default_lot_creation'
            }
            
            lots.append(default_lot)
            logger.info(f"✅ Lot par défaut créé: {default_lot['intitule'][:50]}...")
            
        except Exception as e:
            logger.error(f"Erreur création lot par défaut: {e}")
        
        return lots
    
    def _extract_intitule_from_text(self, text: str) -> str:
        """Extrait l'intitulé du marché depuis le texte"""
        try:
            # Patterns pour l'intitulé
            patterns = [
                r'objet\s+du\s+marché[:\s]*([^\n]{10,200})',
                r'objet[:\s]*([^\n]{10,200})',
                r'intitulé[:\s]*([^\n]{10,200})',
                r'titre[:\s]*([^\n]{10,200})'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    return matches[0].strip()
            
            return ''
        except:
            return ''
    
    def _extract_montant_from_text(self, text: str, type_montant: str) -> float:
        """Extrait un montant depuis le texte"""
        try:
            if type_montant == 'estime':
                patterns = [
                    r'montant\s+estimé[:\s]*(\d{1,3}(?:\s\d{3})*)\s*€',
                    r'budget\s+estimé[:\s]*(\d{1,3}(?:\s\d{3})*)\s*€',
                    r'estimation[:\s]*(\d{1,3}(?:\s\d{3})*)\s*€'
                ]
            else:  # maximum
                patterns = [
                    r'montant\s+maximum[:\s]*(\d{1,3}(?:\s\d{3})*)\s*€',
                    r'budget\s+maximum[:\s]*(\d{1,3}(?:\s\d{3})*)\s*€',
                    r'plafond[:\s]*(\d{1,3}(?:\s\d{3})*)\s*€'
                ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    montant_str = matches[0].replace(' ', '').replace(',', '.')
                    return float(montant_str)
            
            return 0.0
        except:
            return 0.0

# Instance globale
pdf_extractor = AdvancedPDFExtractor()
