#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extracteur de critères d'attribution spécialisé pour les marchés publics
"""

import re
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import PyPDF2

logger = logging.getLogger(__name__)

@dataclass
class CritereAttribution:
    """Structure pour un critère d'attribution"""
    nom: str
    pourcentage: float
    description: str = ""
    lot_numero: Optional[int] = None
    type_critere: str = ""  # technique, economique, financier, etc.

@dataclass
class TableauCriteres:
    """Structure pour un tableau de critères"""
    lots: List[Dict[str, Any]]
    criteres_globaux: List[CritereAttribution]
    criteres_par_lot: Dict[int, List[CritereAttribution]]

class CriteriaExtractor:
    """Extracteur de critères d'attribution pour les marchés publics"""
    
    def __init__(self):
        self.patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, List[str]]:
        """Initialise les patterns de recherche"""
        return {
            'tableau_criteres': [
                r'critère[s]?\s*d\'attribution',
                r'critère[s]?\s*de\s*sélection',
                r'critère[s]?\s*technique[s]?',
                r'critère[s]?\s*économique[s]?',
                r'critère[s]?\s*financier[s]?',
                r'évaluation\s*des\s*offres',
                r'grille\s*d\'évaluation',
                r'barème\s*d\'évaluation',
                r'critères\s*d\'attribution\s*du\s*marché',
                r'modalités\s*d\'évaluation'
            ],
            'pourcentages': [
                r'(\d+(?:[.,]\d+)?)\s*%',
                r'(\d+(?:[.,]\d+)?)\s*pour\s*cent',
                r'(\d+(?:[.,]\d+)?)\s*pc',
                r'(\d+(?:[.,]\d+)?)\s*points',
                r'(\d+(?:[.,]\d+)?)\s*pts'
            ],
            'points': [
                r'(\d+(?:[.,]\d+)?)\s*points',
                r'(\d+(?:[.,]\d+)?)\s*pts',
                r'(\d+(?:[.,]\d+)?)\s*point'
            ],
            'lots': [
                r'lot\s*n°?\s*(\d+)',
                r'lot\s*(\d+)',
                r'lot\s*numéro\s*(\d+)',
                r'lot\s*(\d+)\s*:',
                r'lot\s*(\d+)\s*-'
            ],
            'types_criteres': [
                r'critère\s*technique[s]?',
                r'critère\s*économique[s]?',
                r'critère\s*financier[s]?',
                r'critère\s*de\s*prix',
                r'critère\s*de\s*qualité',
                r'critère\s*de\s*délai',
                r'critère\s*de\s*performance',
                r'critère\s*d\'expérience',
                r'critère\s*de\s*références'
            ]
        }
    
    def extract_from_pdf(self, pdf_path: str) -> TableauCriteres:
        """Extrait les critères d'un PDF"""
        try:
            text = self._extract_text_from_pdf(pdf_path)
            return self.extract_from_text(text)
        except Exception as e:
            logger.error(f"Erreur extraction PDF {pdf_path}: {e}")
            return TableauCriteres([], [], {})
    
    def extract_from_text(self, text: str) -> TableauCriteres:
        """Extrait les critères d'un texte"""
        try:
            # D'abord essayer d'extraire les critères structurés (tableaux) sur le texte original
            criteres_structures = self._extract_structured_table_criteria(text)
            
            if criteres_structures:
                # Si on trouve des critères structurés, les utiliser
                lots = self._extract_lots(text)
                return TableauCriteres(lots, criteres_structures, {})
            
            # Sinon, nettoyer le texte et utiliser la méthode classique
            text = self._clean_text(text)
            
            # Trouver les sections de critères
            sections_criteres = self._find_criteria_sections(text)
            
            # Extraire les lots
            lots = self._extract_lots(text)
            
            # Extraire les critères globaux
            criteres_globaux = self._extract_global_criteria(text, sections_criteres)
            
            # Extraire les critères par lot
            criteres_par_lot = self._extract_criteria_by_lot(text, lots, sections_criteres)
            
            return TableauCriteres(lots, criteres_globaux, criteres_par_lot)
            
        except Exception as e:
            logger.error(f"Erreur extraction critères: {e}")
            return TableauCriteres([], [], {})
    
    def _extract_structured_table_criteria(self, text: str) -> List[CritereAttribution]:
        """Extraction des critères depuis un tableau structuré (comme dans le PDF)"""
        criteres = []
        
        # Pattern pour capturer les critères structurés
        # Format: "CRITERE N° X : Nom du critère\nDescription\nY points"
        pattern = r'CRITERE\s+N°?\s*(\d+)\s*:\s*([^\n]+?)(?:\n[^\n]*)*?\n(\d+)\s*points?'
        
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            numero = match.group(1)
            nom_critere = match.group(2).strip()
            points = int(match.group(3))
            
            # Classifier le type de critère
            if 'valeur technique' in nom_critere.lower() or 'technique' in nom_critere.lower():
                type_critere = "critère technique"
            elif 'prix' in nom_critere.lower():
                type_critere = "critère économique"
            elif 'qualité' in nom_critere.lower() or 'services' in nom_critere.lower():
                type_critere = "autre critère"
            elif 'développement durable' in nom_critere.lower() or 'durable' in nom_critere.lower():
                type_critere = "critère RSE"
            else:
                type_critere = "autre critère"
            
            # Créer le critère
            critere = CritereAttribution(
                nom=f"Critère {numero}",
                pourcentage=float(points),
                description=nom_critere,
                type_critere=type_critere
            )
            criteres.append(critere)
        
        return criteres
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrait le texte d'un PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Erreur lecture PDF {pdf_path}: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte pour améliorer l'extraction"""
        # Remplacer les caractères problématiques
        text = text.replace('\x00', ' ')
        # Normaliser les espaces multiples mais préserver les sauts de ligne
        text = re.sub(r'[ \t]+', ' ', text)  # Normaliser les espaces et tabs
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Normaliser les sauts de ligne multiples
        # Garder les caractères utiles incluant les accents et symboles spéciaux
        text = re.sub(r'[^\w\s%.,()°éèêëàâäôöùûüçÉÈÊËÀÂÄÔÖÙÛÜÇ\n-]', ' ', text)
        return text
    
    def _find_criteria_sections(self, text: str) -> List[Tuple[int, int, str]]:
        """Trouve les sections contenant des critères"""
        sections = []
        
        for pattern in self.patterns['tableau_criteres']:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 1000)
                section_text = text[start:end]
                sections.append((start, end, section_text))
        
        return sections
    
    def _extract_lots(self, text: str) -> List[Dict[str, Any]]:
        """Extrait les informations sur les lots"""
        lots = []
        
        for pattern in self.patterns['lots']:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                lot_numero = int(match.group(1))
                
                # Chercher le contexte autour du lot
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 200)
                context = text[start:end]
                
                # Extraire l'intitulé du lot si possible
                intitule = self._extract_lot_title(context, lot_numero)
                
                lot_info = {
                    'numero': lot_numero,
                    'intitule': intitule,
                    'position': match.start()
                }
                
                # Éviter les doublons
                if not any(l['numero'] == lot_numero for l in lots):
                    lots.append(lot_info)
        
        return sorted(lots, key=lambda x: x['numero'])
    
    def _extract_lot_title(self, context: str, lot_numero: int) -> str:
        """Extrait l'intitulé d'un lot"""
        # Chercher des patterns d'intitulé après le numéro de lot
        patterns = [
            r'lot\s*n°?\s*{}\s*:?\s*([^\n\r]+)'.format(lot_numero),
            r'lot\s*{}\s*:?\s*([^\n\r]+)'.format(lot_numero),
            r'lot\s*numéro\s*{}\s*:?\s*([^\n\r]+)'.format(lot_numero)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Nettoyer le titre
                title = re.sub(r'[^\w\s-]', ' ', title)
                title = re.sub(r'\s+', ' ', title).strip()
                if len(title) > 10:  # Titre significatif
                    return title[:100]  # Limiter la longueur
        
        return f"Lot {lot_numero}"
    
    def _extract_global_criteria(self, text: str, sections: List[Tuple[int, int, str]]) -> List[CritereAttribution]:
        """Extrait les critères globaux"""
        criteres = []
        
        for start, end, section_text in sections:
            # Chercher les pourcentages dans la section
            pourcentages = self._find_percentages_in_section(section_text)
            
            # Chercher les types de critères
            types_criteres = self._find_criteria_types_in_section(section_text)
            
            # Associer les pourcentages aux types de critères
            for i, (pourcentage, pos) in enumerate(pourcentages):
                type_critere = ""
                if i < len(types_criteres):
                    type_critere = types_criteres[i][0]
                
                critere = CritereAttribution(
                    nom=f"Critère {i+1}",
                    pourcentage=pourcentage,
                    description=type_critere,
                    type_critere=type_critere
                )
                criteres.append(critere)
        
        return criteres
    
    def _extract_criteria_by_lot(self, text: str, lots: List[Dict[str, Any]], sections: List[Tuple[int, int, str]]) -> Dict[int, List[CritereAttribution]]:
        """Extrait les critères spécifiques à chaque lot"""
        criteres_par_lot = {}
        
        for lot in lots:
            lot_numero = lot['numero']
            criteres_lot = []
            
            # Chercher les critères autour de ce lot
            lot_start = lot['position']
            lot_end = min(len(text), lot_start + 1000)
            lot_context = text[lot_start:lot_end]
            
            # Chercher les pourcentages dans le contexte du lot
            pourcentages = self._find_percentages_in_section(lot_context)
            
            # Chercher les types de critères
            types_criteres = self._find_criteria_types_in_section(lot_context)
            
            # Associer les pourcentages aux types de critères
            for i, (pourcentage, pos) in enumerate(pourcentages):
                type_critere = ""
                if i < len(types_criteres):
                    type_critere = types_criteres[i][0]
                
                critere = CritereAttribution(
                    nom=f"Critère {i+1}",
                    pourcentage=pourcentage,
                    description=type_critere,
                    lot_numero=lot_numero,
                    type_critere=type_critere
                )
                criteres_lot.append(critere)
            
            if criteres_lot:
                criteres_par_lot[lot_numero] = criteres_lot
        
        return criteres_par_lot
    
    def _find_percentages_in_section(self, section_text: str) -> List[Tuple[float, int]]:
        """Trouve les pourcentages dans une section"""
        pourcentages = []
        
        # D'abord chercher les pourcentages directs
        for pattern in self.patterns['pourcentages']:
            for match in re.finditer(pattern, section_text, re.IGNORECASE):
                try:
                    # Convertir en float
                    value_str = match.group(1).replace(',', '.')
                    pourcentage = float(value_str)
                    
                    # Vérifier que c'est un pourcentage valide (0-100)
                    if 0 <= pourcentage <= 100:
                        pourcentages.append((pourcentage, match.start()))
                except ValueError:
                    continue
        
        # Chercher les tableaux de critères structurés (comme dans le PDF)
        # Pattern pour "Critère N° X : Description : Y points"
        structured_pattern = r'critère\s*n°?\s*\d+[^:]*:[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*points?'
        
        for match in re.finditer(structured_pattern, section_text, re.IGNORECASE):
            try:
                # Convertir en float
                value_str = match.group(1).replace(',', '.')
                points = float(value_str)
                
                # Convertir les points en pourcentage (35 points = 35%)
                # Vérifier que c'est un nombre de points valide (0-100)
                if 0 <= points <= 100:
                    pourcentages.append((points, match.start()))
            except ValueError:
                continue
        
        # Chercher les critères avec points dans un contexte plus large
        points_patterns = [
            r'(?:critère|criteres?)\s*n°?\s*\d+[^:]*:[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*points?',
            r'(?:valeur\s+technique|prix|qualité|développement\s+durable)[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*points?',
            r'(?:pondération|ponderation)[^:]*:?\s*(\d+(?:[.,]\d+)?)\s*points?'
        ]
        
        for pattern in points_patterns:
            for match in re.finditer(pattern, section_text, re.IGNORECASE):
                try:
                    # Convertir en float
                    value_str = match.group(1).replace(',', '.')
                    points = float(value_str)
                    
                    # Convertir les points en pourcentage (35 points = 35%)
                    # Vérifier que c'est un nombre de points valide (0-100)
                    if 0 <= points <= 100:
                        pourcentages.append((points, match.start()))
                except ValueError:
                    continue
        
        # Trier par position dans le texte
        pourcentages.sort(key=lambda x: x[1])
        return pourcentages
    
    def _find_criteria_types_in_section(self, section_text: str) -> List[Tuple[str, int]]:
        """Trouve les types de critères dans une section"""
        types = []
        
        # Patterns spécifiques pour les critères du tableau
        specific_patterns = [
            r'critère\s*n°?\s*\d+[^:]*:\s*([^:]+?)(?:\s*:|\s*pondération)',
            r'(?:valeur\s+technique|prix|qualité\s+des\s+services|développement\s+durable)',
            r'(?:technique|économique|prix|qualité|rse|développement\s+durable|durable)'
        ]
        
        for pattern in specific_patterns:
            for match in re.finditer(pattern, section_text, re.IGNORECASE):
                type_critere = match.group(1) if match.groups() else match.group(0)
                type_critere = type_critere.strip()
                
                # Nettoyer et classifier le type de critère
                if 'technique' in type_critere.lower() or 'valeur technique' in type_critere.lower():
                    types.append(('critère technique', match.start()))
                elif 'prix' in type_critere.lower() or 'économique' in type_critere.lower():
                    types.append(('critère économique', match.start()))
                elif 'qualité' in type_critere.lower() or 'services' in type_critere.lower():
                    types.append(('autre critère', match.start()))
                elif 'développement durable' in type_critere.lower() or 'durable' in type_critere.lower() or 'rse' in type_critere.lower():
                    types.append(('critère RSE', match.start()))
                else:
                    types.append((type_critere, match.start()))
        
        # Patterns génériques
        for pattern in self.patterns['types_criteres']:
            for match in re.finditer(pattern, section_text, re.IGNORECASE):
                type_critere = match.group(0).strip()
                types.append((type_critere, match.start()))
        
        # Trier par position dans le texte
        types.sort(key=lambda x: x[1])
        return types
    
    def format_criteria_summary(self, tableau: TableauCriteres) -> str:
        """Formate un résumé des critères extraits"""
        if not tableau.criteres_globaux and not tableau.criteres_par_lot:
            return "Aucun critère d'attribution détecté."
        
        summary = "## Critères d'attribution détectés\n\n"
        
        # Critères globaux
        if tableau.criteres_globaux:
            summary += "### Critères globaux\n"
            for critere in tableau.criteres_globaux:
                summary += f"- **{critere.nom}**: {critere.pourcentage}%"
                if critere.type_critere:
                    summary += f" ({critere.type_critere})"
                summary += "\n"
            summary += "\n"
        
        # Critères par lot
        if tableau.criteres_par_lot:
            summary += "### Critères par lot\n"
            for lot_numero, criteres in tableau.criteres_par_lot.items():
                summary += f"\n**Lot {lot_numero}**:\n"
                for critere in criteres:
                    summary += f"- **{critere.nom}**: {critere.pourcentage}%"
                    if critere.type_critere:
                        summary += f" ({critere.type_critere})"
                    summary += "\n"
        
        return summary

def test_criteria_extractor():
    """Test de l'extracteur de critères"""
    extractor = CriteriaExtractor()
    
    # Tester sur les PDFs disponibles
    rapport_dir = "rapports"
    pdf_files = [f for f in os.listdir(rapport_dir) if f.endswith('.pdf')]
    
    for pdf_file in pdf_files[:2]:  # Tester sur les 2 premiers PDFs
        pdf_path = os.path.join(rapport_dir, pdf_file)
        print(f"\n=== Test sur {pdf_file} ===")
        
        tableau = extractor.extract_from_pdf(pdf_path)
        summary = extractor.format_criteria_summary(tableau)
        print(summary)

if __name__ == "__main__":
    test_criteria_extractor()
