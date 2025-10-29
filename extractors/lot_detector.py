"""
🔍 Détecteur de Lots - Stratégies Multiples
==========================================

Détecteur intelligent de lots dans les documents d'appels d'offres
utilisant différentes stratégies de détection.
"""

import re
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DetectionStrategy(Enum):
    """Stratégies de détection"""
    STRUCTURED_TABLE = "structured_table"
    LINE_ANALYSIS = "line_analysis"
    MULTI_LINE_TITLES = "multi_line_titles"
    FLEXIBLE_PATTERNS = "flexible_patterns"
    EXCEL_TABLE = "excel_table"

@dataclass
class LotInfo:
    """Information sur un lot détecté"""
    numero: int
    intitule: str
    montant_estime: float = 0.0
    montant_maximum: float = 0.0
    quantite_minimum: int = 0
    quantites_estimees: str = ""
    quantite_maximum: int = 0
    criteres_economique: str = ""
    criteres_techniques: str = ""
    autres_criteres: str = ""
    rse: str = ""
    contribution_fournisseur: str = ""
    source: str = ""
    confidence: float = 1.0

class LotDetectionStrategy(ABC):
    """Stratégie de détection de lots abstraite"""
    
    @abstractmethod
    def detect_lots(self, text: str) -> List[LotInfo]:
        """
        Détecte les lots dans le texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Liste des lots détectés
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Retourne le nom de la stratégie"""
        pass
    
    def _clean_title(self, title: str) -> str:
        """Nettoie un intitulé de lot"""
        if not title or not isinstance(title, str):
            return ""
        
        # Remplacer les sauts de ligne par des espaces
        cleaned = title.replace('\n', ' ').replace('\r', ' ')
        
        # Supprimer les espaces multiples
        cleaned = ' '.join(cleaned.split())
        
        # Supprimer les montants à la fin si présents
        cleaned = re.sub(r'\s+\d{1,3}(?:\s\d{3})*(?:[.,]\d{2})?\s*[€]?\s*$', '', cleaned)
        cleaned = re.sub(r'\s+\d+(?:[.,]\d+)?\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s*$', '', cleaned)
        
        # Supprimer les mots techniques à la fin
        technical_words = [
            'MAIN', 'POUR', 'DE', 'D\'', 'D\\s', 'ET', 'POUR TOUT', 'TYPE', 
            'D\'ETABLISSEMENT', 'D\'ETABLISSEMENTS', 'ETABLISSEMENT', 'ETABLISSEMENTS',
            'SANTE', 'SANTÉ', 'PUBLIC', 'PRIVE', 'PRIVÉ', 'HOPITAL', 'HÔPITAL',
            'HOPITAUX', 'HÔPITAUX', 'CENTRE', 'CENTRES', 'SERVICE', 'SERVICES'
        ]
        
        for word in technical_words:
            cleaned = re.sub(r'\s+' + re.escape(word) + r'\s*$', '', cleaned, flags=re.IGNORECASE)
        
        # Supprimer les caractères de formatage
        cleaned = re.sub(r'[^\w\s\-/()]', ' ', cleaned)
        
        # Supprimer les espaces multiples après nettoyage
        cleaned = ' '.join(cleaned.split())
        
        # Supprimer les mots vides à la fin
        cleaned = re.sub(r'\s+(et|de|du|des|le|la|les|un|une|pour|avec|dans|sur|par|en|au|aux|à|d\'|l\')\s*$', '', cleaned, flags=re.IGNORECASE)
        
        # Limiter la longueur
        if len(cleaned) > 300:
            cleaned = cleaned[:300] + '...'
        
        return cleaned.strip()
    
    def _extract_montants_from_text(self, text: str) -> Tuple[float, float]:
        """Extrait les montants depuis un texte"""
        montant_estime = 0.0
        montant_maximum = 0.0
        
        try:
            # Patterns pour les montants
            montant_patterns = [
                r'(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?',
                r'(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)\s+(\d+(?:[.,]\d+)?)\s*(?:k€|keuros?|m€|meuros?|€|euros?)'
            ]
            
            for pattern in montant_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    try:
                        montant1 = float(matches[0][0].replace(' ', '').replace(',', '.'))
                        montant2 = float(matches[0][1].replace(' ', '').replace(',', '.'))
                        montant_estime = montant1
                        montant_maximum = montant2
                        break
                    except (ValueError, IndexError):
                        continue
        except Exception as e:
            logger.error(f"Erreur extraction montants: {e}")
        
        return montant_estime, montant_maximum

class StructuredTableStrategy(LotDetectionStrategy):
    """Détection dans les tableaux structurés"""
    
    def detect_lots(self, text: str) -> List[LotInfo]:
        """Détecte les lots dans les tableaux structurés"""
        lots = []
        
        try:
            logger.debug("🔍 Détection des lots dans les tableaux structurés...")
            
            # Pattern pour détecter les tableaux de lots structurés
            # Format: N° | Intitulé | Montant estimatif | Montant maximum
            lot_pattern = r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s*€?\s+(\d{1,3}(?:\s\d{3})*)\s*€?\s*(?:\n|$)'
            
            matches = re.findall(lot_pattern, text, re.MULTILINE)
            
            if matches:
                logger.debug(f"📋 {len(matches)} lots structurés détectés")
                
                for match in matches:
                    numero, intitule, montant_estime, montant_max = match
                    
                    # Nettoyer les données
                    numero = int(numero.strip())
                    intitule = self._clean_title(intitule.strip())
                    
                    # Nettoyer les montants
                    montant_estime_clean = montant_estime.replace(' ', '').replace(',', '.')
                    montant_max_clean = montant_max.replace(' ', '').replace(',', '.')
                    
                    try:
                        montant_estime_val = float(montant_estime_clean)
                        montant_max_val = float(montant_max_clean)
                    except ValueError:
                        montant_estime_val = 0.0
                        montant_max_val = 0.0
                    
                    lot_info = LotInfo(
                        numero=numero,
                        intitule=intitule,
                        montant_estime=montant_estime_val,
                        montant_maximum=montant_max_val,
                        source='structured_table'
                    )
                    
                    lots.append(lot_info)
                    logger.debug(f"📦 Lot structuré: {numero} - {intitule[:50]}...")
            
        except Exception as e:
            logger.error(f"Erreur détection tableaux structurés: {e}")
        
        return lots
    
    def get_strategy_name(self) -> str:
        return "StructuredTable"

class LineAnalysisStrategy(LotDetectionStrategy):
    """Détection par analyse de lignes avec support des lots collés"""
    
    def detect_lots(self, text: str) -> List[LotInfo]:
        """Détecte les lots par analyse des lignes"""
        lots = []
        
        try:
            logger.debug("🔍 Détection des lots par analyse des lignes...")
            
            lines = text.split('\n')
            current_lot = None
            in_lot_section = False
            
            # Détecter si on est dans une section de lots - Mots-clés élargis
            lot_section_keywords = [
                'allotissement', 'lotissement', 'répartition', 'lots', 'lot n°', 'lot numéro',
                'lot:', 'lots:', 'numéro du lot', 'n° lot', 'lot n', 'lot numero',
                'prestation', 'prestations', 'description des lots', 'liste des lots',
                'tableau', 'table', 'annexe', 'détail', 'détails'
            ]
            
            # Détection auto: si on trouve un pattern de lot au début, considérer qu'on est dans une section
            auto_detect_lot_section = False
            
            for i, line in enumerate(lines):
                line = line.strip()
                line_lower = line.lower()
                
                # Détecter l'entrée dans une section de lots
                if any(keyword in line_lower for keyword in lot_section_keywords):
                    in_lot_section = True
                    auto_detect_lot_section = True
                    logger.debug(f"📋 Section de lots détectée: {line[:50]}...")
                    continue
                
                # Auto-détection: Si on trouve un pattern de lot (numéro + texte), on est probablement dans une section
                if not in_lot_section and re.match(r'^(\d{1,3})\s+[A-Za-zÀ-ÖØ-öø-ÿ]', line):
                    auto_detect_lot_section = True
                
                # Détecter la sortie de la section de lots - Conditions plus strictes pour éviter les faux positifs
                if in_lot_section and any(keyword in line_lower for keyword in ['article', 'chapitre', 'section', 'annexe']) and len(line) > 20:
                    # Vérifier que ce n'est pas juste un titre dans une liste de lots
                    if not re.match(r'^\d+', line):
                        in_lot_section = False
                        logger.debug(f"📋 Fin de section de lots détectée: {line[:50]}...")
                        continue
                
                # Détecter les lots collés sur la même ligne (dans la section de lots OU auto-détectée)
                if in_lot_section or auto_detect_lot_section:
                    # Chercher tous les lots sur cette ligne (y compris ceux collés)
                    lots_in_line = self._extract_multiple_lots_from_line(line, i)
                    
                    if lots_in_line:
                        # Sauvegarder le lot précédent s'il existe
                        if current_lot:
                            lots.append(current_lot)
                            current_lot = None
                        
                        # Ajouter tous les lots trouvés sur cette ligne
                        for lot in lots_in_line:
                            lots.append(lot)
                            logger.debug(f"📦 Lot collé (ligne): {lot.numero} - {lot.intitule[:50]}...")
                        continue
                    
                    # NOUVEAU: Détecter les lots collés à la fin d'une ligne (cas spécial)
                    collated_lot = self._extract_collated_lot_at_end(line, i)
                    if collated_lot:
                        # Sauvegarder le lot précédent s'il existe
                        if current_lot:
                            lots.append(current_lot)
                            current_lot = None
                        
                        # Ajouter le lot collé détecté
                        lots.append(collated_lot)
                        logger.debug(f"📦 Lot collé (fin de ligne): {collated_lot.numero} - {collated_lot.intitule[:50]}...")
                    continue
                
                # Détecter le début d'un lot (numéro + intitulé) - Patterns multiples
                lot_match = None
                
                # Pattern 1: Format standard - capture jusqu'à la fin de ligne (amélioré pour multi-lignes)
                lot_match = re.match(r'^(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s+\d{1,3}(?:\s\d{3})*|$)', line)
                
                # Pattern 1b: Format pour lots sur plusieurs lignes (sans montants sur la première ligne)
                if not lot_match:
                    lot_match = re.match(r'^(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s*$)', line)
                
                # Pattern 1b: Format avec montants sur la même ligne
                if not lot_match:
                    lot_match = re.match(r'^(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)\s*-\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*-\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?', line)
                
                # Pattern 2: Format avec "LOT" ou "Lot" - capture jusqu'à la fin
                if not lot_match:
                    lot_match = re.match(r'^(?:LOT|Lot)\s*(\d+)[\s:-]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s+\d|$)', line)
                
                # Pattern 2b: Format "LOT" avec montants sur la même ligne
                if not lot_match:
                    lot_match = re.match(r'^(?:LOT|Lot)\s*(\d+)[\s:-]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)\s*-\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*-\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?', line)
                
                # Pattern 3: Format avec tirets ou points - capture jusqu'à la fin
                if not lot_match:
                    lot_match = re.match(r'^(\d+)[\s.-]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s+\d|$)', line)
                
                # Pattern 4: Format très permissif - capture tout le reste
                if not lot_match:
                    lot_match = re.match(r'^(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+)', line)
                
                # Pattern 5: Format spécifique pour lots 13 et 14 (multi-lignes)
                if not lot_match:
                    lot_match = re.match(r'^(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s*$)', line)
                
                # Pattern 6: Format avec parenthèses - NOUVEAU
                if not lot_match:
                    lot_match = re.match(r'^(\d+)\s*[)]\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+)', line)
                
                # Pattern 7: Format avec numéro entre parenthèses - NOUVEAU
                if not lot_match:
                    lot_match = re.match(r'^\s*[\(]?\s*(\d+)\s*[\)]\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+)', line)
                
                # Pattern 8: Format avec "N°" ou "n°" - NOUVEAU
                if not lot_match:
                    lot_match = re.match(r'^(?:N°|n°|N|n)\s*(\d+)[\s:-]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+)', line)
                
                # Pattern 9: Format très permissif sans majuscule au début - NOUVEAU
                if not lot_match:
                    lot_match = re.match(r'^(\d+)\s+([a-zà-öø-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+)', line)
                
                # Pattern 10: Format avec tabulation ou espaces multiples - NOUVEAU
                if not lot_match:
                    lot_match = re.match(r'^(\d+)\s{2,}([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+)', line)
                
                # Détecter les lots partout dans le document (même sans section explicite)
                # Mais avec une priorité plus élevée si on est dans une section
                if lot_match and (in_lot_section or auto_detect_lot_section or i < len(lines) * 0.95):
                    # Sauvegarder le lot précédent s'il existe
                    if current_lot:
                        lots.append(current_lot)
                    
                    # Commencer un nouveau lot
                    numero = int(lot_match.group(1))
                    intitule = lot_match.group(2).strip()
                    
                    # Filtrer les faux lots (codes postaux, etc.) - Limite assouplie à 200 lots
                    if numero > 200 or numero < 1:
                        current_lot = None
                        continue
                    
                    current_lot = LotInfo(
                        numero=numero,
                        intitule=intitule,
                        source='line_analysis'
                    )
                    
                    # Si le pattern contient des montants, les extraire directement
                    if len(lot_match.groups()) >= 4:
                        try:
                            montant1_str = lot_match.group(3).replace(' ', '').replace(',', '.')
                            montant2_str = lot_match.group(4).replace(' ', '').replace(',', '.')
                            montant1 = float(montant1_str)
                            montant2 = float(montant2_str)
                            current_lot.montant_estime = montant1
                            current_lot.montant_maximum = montant2
                            logger.debug(f"💰 Montants détectés pour lot {numero}: {montant1} € - {montant2} €")
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Erreur extraction montants lot {numero}: {e}")
                    
                    # Chercher les montants et continuer l'intitulé sur plusieurs lignes
                    self._extend_lot_title(current_lot, lines, i)
                
                # Si on a un lot en cours et qu'on trouve des montants dans la ligne actuelle
                elif current_lot and re.search(r'\d{1,3}(?:\s\d{3})*\s*[€]', line):
                    montant_match = re.search(r'(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*-\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?', line)
                    if montant_match:
                        try:
                            montant1 = float(montant_match.group(1).replace(' ', '').replace(',', '.'))
                            montant2 = float(montant_match.group(2).replace(' ', '').replace(',', '.'))
                            current_lot.montant_estime = montant1
                            current_lot.montant_maximum = montant2
                            logger.debug(f"💰 Montants détectés pour lot {current_lot.numero}: {montant1} € - {montant2} €")
                        except ValueError:
                            pass
            
            # Ajouter le dernier lot s'il existe
            if current_lot:
                lots.append(current_lot)
            
            # Supprimer les doublons basés sur le numéro de lot
            unique_lots = []
            seen_numbers = set()
            for lot in lots:
                if lot.numero not in seen_numbers:
                    lot.intitule = self._clean_title(lot.intitule)
                    unique_lots.append(lot)
                    seen_numbers.add(lot.numero)
                else:
                    logger.debug(f"Doublon ignoré: lot {lot.numero}")
            
            logger.info(f"✅ Détection par lignes terminée: {len(unique_lots)} lots uniques trouvés (sur {len(lots)} total)")
            return unique_lots
            
        except Exception as e:
            logger.error(f"Erreur détection par lignes: {e}")
            return []
    
    def _extract_multiple_lots_from_line(self, line: str, line_index: int) -> List[LotInfo]:
        """
        Extrait plusieurs lots d'une même ligne (cas des lots collés)
        
        Args:
            line: Ligne à analyser
            line_index: Index de la ligne
            
        Returns:
            Liste des lots détectés sur cette ligne
        """
        lots = []
        
        try:
            # Pattern pour détecter les lots collés sur la même ligne
            # Exemple: "20 Micro-manipulateur... 400 000 € 800 000 € 21 Station complète..."
            collated_lots_pattern = r'(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s+(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?)?(?=\s+\d+\s+[A-Za-zÀ-ÖØ-öø-ÿ]|$)'
            
            matches = re.findall(collated_lots_pattern, line)
            
            if len(matches) > 1:  # Plusieurs lots sur la même ligne
                logger.debug(f"🔗 Détection de {len(matches)} lots collés sur la ligne {line_index + 1}")

                for match in matches:
                    numero_str = match[0].strip()
                    intitule_raw = match[1].strip()
                    montant1_str = match[2] if match[2] else ""
                    montant2_str = match[3] if match[3] else ""
                    
                    # Filtrer les faux lots - Limite assouplie à 200 lots pour capturer tous les lots
                    if not numero_str.isdigit() or int(numero_str) > 200 or int(numero_str) < 1:
                        continue
                    
                    numero = int(numero_str)
                    intitule = self._clean_title(intitule_raw)
                    
                    lot = LotInfo(
                        numero=numero,
                        intitule=intitule,
                        source='line_analysis_collated'
                    )
                    
                    # Extraire les montants si présents
                    if montant1_str and montant2_str:
                        try:
                            montant1 = float(montant1_str.replace(' ', '').replace(',', '.'))
                            montant2 = float(montant2_str.replace(' ', '').replace(',', '.'))
                            lot.montant_estime = montant1
                            lot.montant_maximum = montant2
                            logger.debug(f"💰 Lot {numero} collé: {intitule[:30]}... - {montant1}€/{montant2}€")
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Erreur extraction montants lot collé {numero}: {e}")
                    else:
                        logger.debug(f"📦 Lot {numero} collé: {intitule[:30]}... (sans montants)")
                    
                    lots.append(lot)
            
        except Exception as e:
            logger.error(f"Erreur extraction lots collés ligne {line_index + 1}: {e}")
        
        return lots
    
    def _extract_collated_lot_at_end(self, line: str, line_index: int) -> Optional[LotInfo]:
        """
        Extrait un lot collé à la fin d'une ligne
        
        Args:
            line: Ligne à analyser
            line_index: Index de la ligne
            
        Returns:
            Lot détecté ou None
        """
        try:
            # Pattern pour détecter un lot collé à la fin d'une ligne
            # Pattern amélioré pour détecter les lots sans montants
            collated_patterns = [
                r'(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*\d+\s+sur\s+\d+\s+(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s|$)',
                r'\d+\s+sur\s+\d+\s+(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s|$)',
                r'(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?=\s+\d+\s+[A-Za-zÀ-ÖØ-öø-ÿ]|$)',
                r'(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?=\s*$)',
                # Pattern pour capturer l'intitulé complet jusqu'à la fin de ligne
                r'(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+)'
            ]
            
            # Tester tous les patterns
            for pattern in collated_patterns:
                match = re.search(pattern, line)
                
                if match:
                    # Adapter selon le pattern utilisé
                    if len(match.groups()) >= 4:  # Pattern avec montants
                        numero_str = match.group(3).strip()
                        intitule_raw = match.group(4).strip()
                    elif len(match.groups()) == 2:  # Pattern simple
                        numero_str = match.group(1).strip()
                        intitule_raw = match.group(2).strip()
                    
                    else:
                        continue
                    
                    # Filtrer les faux lots - Limite assouplie à 200 lots pour capturer tous les lots
                    if not numero_str.isdigit() or int(numero_str) > 200 or int(numero_str) < 1:
                        continue
                    
                    numero = int(numero_str)
                    intitule = self._clean_title(intitule_raw)
                    
                    # Vérifier que c'est bien un lot (pas un numéro de page, etc.)
                    if len(intitule) < 3:
                        continue
                    
                    # Filtrer les faux lots (titres de sections, etc.)
                    faux_lots_keywords = [
                        'objet de la consultation', 'nomenclature communautaire', 'lieux d',
                        'contenu du dossier', 'mise', 'modification du dce', 'questions des candidats',
                        'modalit', 'horodatage', 'copie de sauvegarde', 'antivirus',
                        'documents', 'examen des candidatures', 'jugement des offres', 'mise au point'
                    ]
                    
                    intitule_lower = intitule.lower()
                    if any(keyword in intitule_lower for keyword in faux_lots_keywords):
                        logger.debug(f"Faux lot ignoré: {numero} - {intitule[:30]}...")
                        continue
                    
                    lot = LotInfo(
                        numero=numero,
                        intitule=intitule,
                        source='line_analysis_collated_end'
                    )
                    
                    logger.debug(f"🔗 Lot collé détecté à la fin de la ligne {line_index + 1}: {numero} - {intitule[:50]}... (pattern: {pattern[:50]}...)")
                    
                    return lot
            
        except Exception as e:
            logger.error(f"Erreur extraction lot collé fin ligne {line_index + 1}: {e}")
        
        return None
    
    def _extend_lot_title(self, current_lot, lines: List[str], start_index: int):
        """
        Étend l'intitulé d'un lot sur plusieurs lignes
        
        Args:
            current_lot: Lot en cours de traitement
            lines: Liste des lignes du texte
            start_index: Index de la ligne de début
        """
        try:
            for j in range(start_index + 1, min(start_index + 5, len(lines))):
                next_line = lines[j].strip()

                # Si on trouve un nouveau lot, arrêter
                if (
                    re.match(r'^\d+\s+[A-Za-zÀ-ÖØ-öø-ÿ]', next_line)
                    or re.match(r'^(?:LOT|Lot)\s*\d+', next_line)
                    or re.match(r'^\d+[.-]', next_line)
                ):
                    break

                # Si la ligne est vide, continuer
                if not next_line:
                    continue

                # Chercher des montants dans cette ligne
                montant_match = re.search(r'(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?', next_line)
                if montant_match:
                    try:
                        montant1 = float(montant_match.group(1).replace(' ', '').replace(',', '.'))
                        montant2 = float(montant_match.group(2).replace(' ', '').replace(',', '.'))
                        current_lot.montant_estime = montant1
                        current_lot.montant_maximum = montant2
                        logger.debug(f"💰 Montants trouvés pour lot {current_lot.numero}: {montant1}€/{montant2}€")
                        break  # Arrêter après avoir trouvé les montants
                    except ValueError:
                        pass

                # Si la ligne contient du texte et pas de montant, l'ajouter à l'intitulé
                if (
                    next_line
                    and not re.match(r'^\d{1,3}(?:\s\d{3})*\s*[€]', next_line)
                    and not re.match(r'^[€\s\d,.-]+$', next_line)
                    and not re.match(r'^[A-Z\s]+$', next_line)
                    and len(next_line) > 3
                    and not re.match(r'^[A-Z]{2,}\s*$', next_line)
                    and not re.match(r'^(?:LOT|Lot)\s*\d+', next_line)
                    and not re.match(r'^\d+[.-]', next_line)
                    and not re.match(r'^\d+\s+[A-Za-zÀ-ÖØ-öø-ÿ]', next_line)
                ):
                    # Vérifier que ce n'est pas un nouveau lot (pattern plus strict)
                    if not re.match(r'^\d+\s+[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ]', next_line):
                        if current_lot.intitule and not current_lot.intitule.endswith(' '):
                            current_lot.intitule += ' '
                        current_lot.intitule += next_line
                    logger.debug(f"Intitulé étendu pour lot {current_lot.numero}: {current_lot.intitule[:50]}...")

        except Exception as e:
            logger.error(f"Erreur extension intitulé lot {current_lot.numero}: {e}")
    
    
    
    
    
    def get_strategy_name(self) -> str:
        return "LineAnalysis"

class MultiLineTitlesStrategy(LotDetectionStrategy):
    """Détection spécialisée pour les intitulés multi-lignes"""
    
    def detect_lots(self, text: str) -> List[LotInfo]:
        """Détecte les lots avec intitulés multi-lignes"""
        lots = []
        
        try:
            logger.debug("🔍 Détection des intitulés multi-lignes...")
            
            # Pattern très permissif pour capturer les intitulés multi-lignes
            multi_line_pattern = r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)(?:\n(?!\d+\s)[A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)*(?=\n\d+\s|\n\n|$)'
            
            matches = re.findall(multi_line_pattern, text, re.MULTILINE | re.DOTALL)
            
            if matches:
                logger.debug(f"📋 {len(matches)} intitulés multi-lignes détectés")
                
                for match in matches:
                    numero_str = match[0].strip()
                    intitule_raw = match[1].strip()
                    
                    # Filtrer les faux lots - Limite assouplie à 200 lots pour capturer tous les lots
                    if not numero_str.isdigit() or int(numero_str) > 200 or int(numero_str) < 1:
                        continue
                    
                    numero = int(numero_str)
                    intitule = self._clean_title(intitule_raw)
                    
                    # Chercher les montants dans le contexte du lot
                    lot_context = self._extract_lot_context(text, numero)
                    montant_estime, montant_maximum = self._extract_montants_from_text(lot_context)
                    
                    lot_info = LotInfo(
                        numero=numero,
                        intitule=intitule,
                        montant_estime=montant_estime,
                        montant_maximum=montant_maximum,
                        source='multi_line_titles'
                    )
                    
                    lots.append(lot_info)
                    logger.debug(f"📦 Lot multi-lignes: {numero} - {intitule[:50]}...")
            
        except Exception as e:
            logger.error(f"Erreur détection multi-lignes: {e}")
        
        return lots
    
    def _extract_lot_context(self, text: str, lot_numero: int) -> str:
        """Extrait le contexte autour d'un lot spécifique"""
        try:
            # Chercher le lot dans le texte
            lot_pattern = rf'lot\s*n°?\s*{lot_numero}[^\n]*\n(.*?)(?=\nlot\s*n°?\s*\d+|\n\n|$)'
            match = re.search(lot_pattern, text, re.IGNORECASE | re.DOTALL)
            
            if match:
                return match.group(1)
            
            # Pattern alternatif plus large
            lot_pattern_alt = rf'lot\s*{lot_numero}[^\n]*\n(.*?)(?=\nlot\s*\d+|\n\n|$)'
            match_alt = re.search(lot_pattern_alt, text, re.IGNORECASE | re.DOTALL)
            
            if match_alt:
                return match_alt.group(1)
            
            return ""
            
        except Exception as e:
            logger.error(f"Erreur extraction contexte lot {lot_numero}: {e}")
            return ""
    
    def get_strategy_name(self) -> str:
        return "MultiLineTitles"

class FlexiblePatternsStrategy(LotDetectionStrategy):
    """Détection avec patterns flexibles (fallback)"""
    
    def detect_lots(self, text: str) -> List[LotInfo]:
        """Détecte les lots avec des patterns flexibles"""
        lots = []
        
        try:
            logger.debug("🔍 Détection avec patterns flexibles...")
            
            # Limiter l'analyse à la section des lots si détectable
            section_pattern = r'(allotissement|lotissement|répartition|lots?\b|lot\s*n°|lot\s*numéro)([\s\S]*?)(?=\n\s*(article|chapitre|section|annexe)\b|\Z)'
            section_match = re.search(section_pattern, text, re.IGNORECASE)
            search_text = section_match.group(0) if section_match else text

            # Patterns flexibles pour détecter les lots
            flexible_patterns = [
                # Pattern 1: Numéro + intitulé multi-lignes complet
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\n(?!\d+\s)[A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)*(?=\n\d+\s|\n\n|$)',
                # Pattern 2: Numéro + intitulé multi-lignes avec montants
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\n(?!\d+\s)[A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)*\s+(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?',
                # Pattern 3: Format tableau très permissif
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)(?:\n(?!\d+\s)[A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)*\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*',
                # Pattern 4: Format très permissif multi-lignes
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\n(?!\d+\s)[A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)*',
                # Pattern 5: Format tableau précis
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*(?:\n|$)',
                # Pattern 6: Format avec caractères spéciaux
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s*[€]\s+(\d{1,3}(?:\s\d{3})*)\s*[€]',
                # Pattern 7: Format plus permissif
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)',
                # Pattern 8: Format avec montants dans l'intitulé
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s+(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*',
                # Pattern 9: Numéro + Intitulé + Montant
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)\s+(\d{1,3}(?:\s\d{3})*)\s*[€]',
                # Pattern 10: Lot + Numéro + Intitulé
                r'(?:lot|Lot)\s*(\d+)[\s:]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)(?:\n|$)',
                # Pattern 11: Numéro + Description + Montant
                r'(?:^|\n)(\d+)\s+([^€\n]{10,100})\s+(\d{1,3}(?:\s\d{3})*)\s*[€]',
                # Pattern 12: Format très général
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]{10,80})(?:\n|$)',
                # Pattern 13: Format avec tirets ou points
                r'(?:^|\n)(\d+)[\s.-]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]{10,80})(?:\n|$)',
                # Pattern 14: Format avec parenthèses
                r'(?:^|\n)(\d+)\s*\(([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]{10,80})\)(?:\n|$)',
                # Pattern 15: Format très permissif
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]{5,100})(?:\n|$)',
                # Pattern 16: Format avec "Article" ou "Section"
                r'(?:article|Article|section|Section)\s*(\d+)[\s:]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]{10,80})(?:\n|$)',
                # Pattern 17: Format très permissif pour noms longs
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/()-]{15,150})(?:\s+\d|$|\n)',
                # Pattern 18: Format avec caractères spéciaux étendus
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/()-]{10,120})(?:\s+\d|$|\n)',
                # Pattern 19: Format multi-mots avec continuation
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/()-]+?)(?:\s+\d{1,3}(?:\s\d{3})*|$|\n)',
                # Pattern 20: Format très général pour descriptions longues
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]{10,200})(?:\s+\d|$|\n)',
                # Pattern 21: Format avec "Prestation" ou "Service"
                r'(?:prestation|Prestation|service|Service)\s*(\d+)[\s:]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]{10,80})(?:\n|$)',
                # Pattern 22: Format simple pour noms courts
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]{5,50})(?:\s|$)',
                # Pattern 23: Format très simple
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s|$)',
                # Pattern 24: Format avec "LOT" ou "Lot" - capture jusqu'à la fin
                r'(?:^|\n)(?:LOT|Lot)\s*(\d+)[\s:-]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s+\d|$)',
                # Pattern 25: Format "LOT" très permissif
                r'(?:^|\n)(?:LOT|Lot)\s*(\d+)[\s:-]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+)',
                # Pattern 26: Format ultra-permissif pour noms très longs
                r'(?:^|\n)(?:LOT|Lot)\s*(\d+)[\s:-]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s|$)',
                # Pattern 27: Format avec numéro seul
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)(?:\s|$)',
                # Pattern 28: Format ultra-simple
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+)',
                # Pattern 29: Format avec montants sur la même ligne
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)\s*-\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*-\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?',
                # Pattern 30: Format "LOT" avec montants
                r'(?:^|\n)(?:LOT|Lot)\s*(\d+)[\s:-]+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)\s*-\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?\s*-\s*(\d{1,3}(?:\s\d{3})*)\s*[€]?',
                # Pattern 31: Format générique avec montants (virgules)
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)\s*-\s*(\d{1,3}(?:,\d{3})*)\s*[€]?\s*-\s*(\d{1,3}(?:,\d{3})*)\s*[€]?',
                # Pattern 32: Format générique avec montants (sans espaces)
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)\s*-\s*(\d+)[€]?\s*-\s*(\d+)[€]?',
                # Pattern 33: Format générique avec montants (k€)
                r'(?:^|\n)(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/().-]+?)\s*-\s*(\d+(?:\.\d+)?k)[€]?\s*-\s*(\d+(?:\.\d+)?k)[€]?'
            ]
            
            # Essayer tous les patterns et garder le meilleur résultat
            best_matches = []
            best_pattern = None
            best_quality_score = 0
            
            for i, pattern in enumerate(flexible_patterns):
                try:
                    pattern_matches = re.findall(pattern, search_text, re.MULTILINE | re.DOTALL)
                    if pattern_matches:
                        # Calculer un score de qualité basé sur la longueur moyenne des noms
                        avg_name_length = sum(len(match[1]) for match in pattern_matches) / len(pattern_matches)
                        quality_score = len(pattern_matches) * avg_name_length
                        
                        # Bonus pour les patterns avec montants (patterns 29-33)
                        if i >= 28:  # Patterns 29-33 (index 28-32)
                            # Vérifier si le pattern capture des montants
                            has_amounts = any(len(match) >= 4 for match in pattern_matches)
                            if has_amounts:
                                quality_score *= 2  # Double le score pour les patterns avec montants
                                logger.debug(f"📈 Pattern {i+1}: {len(pattern_matches)} lots trouvés (qualité: {quality_score:.1f}) - AVEC MONTANTS")
                            else:
                                logger.debug(f"📈 Pattern {i+1}: {len(pattern_matches)} lots trouvés (qualité: {quality_score:.1f})")
                        else:
                            logger.info(f"📈 Pattern {i+1}: {len(pattern_matches)} lots trouvés (qualité: {quality_score:.1f})")
                        
                        # Choisir le pattern avec le meilleur score de qualité
                        if quality_score > best_quality_score:
                            best_matches = pattern_matches
                            best_pattern = f"Pattern {i+1}"
                            best_quality_score = quality_score
                except Exception as e:
                    logger.warning(f"Erreur avec le pattern {i+1}: {e}")
            
            matches = best_matches
            
            if matches:
                logger.debug(f"📋 {len(matches)} lots flexibles détectés")
                
                for match in matches:
                    if len(match) >= 2:
                        numero_str = match[0].strip()
                        # Filtrer les faux lots - Limite assouplie à 200 lots pour capturer tous les lots
                        if not numero_str.isdigit() or int(numero_str) > 200 or int(numero_str) < 1:
                            continue
                        
                        numero = int(numero_str)
                        intitule = self._clean_title(match[1].strip() if len(match) > 1 else f"Lot {numero}")
                        
                        # Gérer les montants selon le nombre de groupes capturés
                        montant_estime = 0.0
                        montant_maximum = 0.0
                        
                        if len(match) >= 3:
                            try:
                                montant_str = match[2].replace(' ', '')
                                # Gérer les formats k€
                                if 'k' in montant_str.lower():
                                    montant_estime = float(montant_str.lower().replace('k', '')) * 1000
                                else:
                                    # Gérer les virgules comme séparateurs de milliers
                                    montant_str = montant_str.replace(',', '')
                                    montant_estime = float(montant_str)
                                montant_maximum = montant_estime
                                logger.debug(f"💰 Montant unique détecté pour lot {numero}: {montant_estime} €")
                            except ValueError:
                                pass
                        
                        if len(match) >= 4:
                            try:
                                # Gérer les formats k€ et virgules
                                montant1_str = match[2].replace(' ', '')
                                montant2_str = match[3].replace(' ', '')
                                
                                # Convertir k€ en € et gérer les virgules
                                if 'k' in montant1_str.lower():
                                    montant_estime = float(montant1_str.lower().replace('k', '')) * 1000
                                else:
                                    # Gérer les virgules comme séparateurs de milliers
                                    montant1_str = montant1_str.replace(',', '')
                                    montant_estime = float(montant1_str)
                                
                                if 'k' in montant2_str.lower():
                                    montant_maximum = float(montant2_str.lower().replace('k', '')) * 1000
                                else:
                                    # Gérer les virgules comme séparateurs de milliers
                                    montant2_str = montant2_str.replace(',', '')
                                    montant_maximum = float(montant2_str)
                                
                                logger.debug(f"💰 Montants détectés pour lot {numero}: {montant_estime} € - {montant_maximum} €")
                            except ValueError:
                                pass
                        
                        lot_info = LotInfo(
                            numero=numero,
                            intitule=intitule,
                            montant_estime=montant_estime,
                            montant_maximum=montant_maximum,
                            source='flexible_patterns'
                        )
                        
                        lots.append(lot_info)
                        logger.debug(f"📦 Lot flexible: {numero} - {intitule[:50]}...")
            
        except Exception as e:
            logger.error(f"Erreur détection patterns flexibles: {e}")
        
        return lots
    
    def get_strategy_name(self) -> str:
        return "FlexiblePatterns"

class ExcelTableStrategy(LotDetectionStrategy):
    """Détection dans les tableaux Excel"""
    
    def detect_lots(self, text: str) -> List[LotInfo]:
        """Détecte les lots dans les données Excel"""
        lots = []
        
        try:
            logger.debug("🔍 Détection des lots dans les données Excel...")
            
            # Pour les données Excel, on suppose que le texte contient des informations structurées
            # On cherche des patterns spécifiques aux tableaux Excel
            
            # Pattern pour les lignes de tableau Excel
            excel_patterns = [
                r'(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)',
                r'(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)\s+(\d+(?:[.,]\d+)?)',
                r'(\d+)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s/-]+?)'
            ]
            
            for pattern in excel_patterns:
                matches = re.findall(pattern, text, re.MULTILINE)
                
                if matches and len(matches) >= 3:  # Seuil minimum pour considérer l'extraction réussie
                    logger.debug(f"📋 {len(matches)} lots Excel détectés avec pattern")
                    
                    for match in matches:
                        if len(match) >= 2:
                            numero_str = match[0].strip()
                            # Filtrer les faux lots - Limite assouplie à 200 lots pour capturer tous les lots
                            if not numero_str.isdigit() or int(numero_str) > 200 or int(numero_str) < 1:
                                continue
                            
                            numero = int(numero_str)
                            intitule = self._clean_title(match[1].strip())
                            
                            # Gérer les montants
                            montant_estime = 0.0
                            montant_maximum = 0.0
                            
                            if len(match) >= 3:
                                try:
                                    montant_estime = float(match[2].replace(',', '.'))
                                    montant_maximum = montant_estime
                                except ValueError:
                                    pass
                            
                            if len(match) >= 4:
                                try:
                                    montant_estime = float(match[2].replace(',', '.'))
                                    montant_maximum = float(match[3].replace(',', '.'))
                                except ValueError:
                                    pass
                            
                            lot_info = LotInfo(
                                numero=numero,
                                intitule=intitule,
                                montant_estime=montant_estime,
                                montant_maximum=montant_maximum,
                                source='excel_table'
                            )
                            
                            lots.append(lot_info)
                            logger.debug(f"📦 Lot Excel: {numero} - {intitule[:50]}...")
                    
                    break  # Utiliser le premier pattern qui fonctionne
            
        except Exception as e:
            logger.error(f"Erreur détection Excel: {e}")
        
        return lots
    
    def get_strategy_name(self) -> str:
        return "ExcelTable"

class LotDetector:
    """Détecteur de lots principal utilisant plusieurs stratégies"""
    
    def __init__(self):
        """Initialise le détecteur avec toutes les stratégies"""
        self.strategies = [
            LineAnalysisStrategy(),  # Priorité à l'analyse de lignes pour les PDF
            StructuredTableStrategy(),
            MultiLineTitlesStrategy(),
            FlexiblePatternsStrategy(),
            ExcelTableStrategy()
        ]
        
        self.performance_metrics = {
            'total_detections': 0,
            'successful_detections': 0,
            'strategy_usage': {},
            'average_detection_time': 0.0
        }
    
    def detect_lots(self, text: str, preferred_strategy: Optional[DetectionStrategy] = None) -> List[LotInfo]:
        """
        Détecte les lots en utilisant les stratégies disponibles
        NOUVELLE APPROCHE: Fusionne les résultats de TOUTES les stratégies pour ne manquer aucun lot
        
        Args:
            text: Texte à analyser
            preferred_strategy: Stratégie préférée (optionnel)
            
        Returns:
            Liste des lots détectés (fusionnée de toutes les stratégies)
        """
        start_time = time.time()
        
        try:
            self.performance_metrics['total_detections'] += 1
            
            if preferred_strategy:
                # Utiliser la stratégie préférée
                strategy = self._get_strategy_by_name(preferred_strategy.value)
                if strategy:
                    lots = strategy.detect_lots(text)
                    if lots:
                        self.performance_metrics['successful_detections'] += 1
                        self.performance_metrics['strategy_usage'][strategy.get_strategy_name()] = \
                            self.performance_metrics['strategy_usage'].get(strategy.get_strategy_name(), 0) + 1
                        return lots
            
            # NOUVEAU: Essayer TOUTES les stratégies et fusionner les résultats
            all_lots_by_strategy = {}
            
            for strategy in self.strategies:
                try:
                    lots = strategy.detect_lots(text)
                    if lots:
                        strategy_name = strategy.get_strategy_name()
                        all_lots_by_strategy[strategy_name] = lots
                        logger.debug(f"📈 {strategy_name}: {len(lots)} lots détectés")
                        self.performance_metrics['strategy_usage'][strategy_name] = \
                            self.performance_metrics['strategy_usage'].get(strategy_name, 0) + 1
                except Exception as e:
                    logger.warning(f"Erreur avec la stratégie {strategy.get_strategy_name()}: {e}")
            
            # Fusionner intelligemment tous les lots détectés
            if all_lots_by_strategy:
                merged_lots = self._merge_lots_from_all_strategies(all_lots_by_strategy)
                
                if merged_lots:
                    # Mettre à jour le temps moyen de détection
                    detection_time = time.time() - start_time
                    self.performance_metrics['average_detection_time'] = (
                        (self.performance_metrics['average_detection_time'] * 
                         (self.performance_metrics['total_detections'] - 1) + detection_time) /
                        self.performance_metrics['total_detections']
                    )
                    
                    logger.info(f"✅ Fusion: {len(merged_lots)} lots uniques détectés depuis {len(all_lots_by_strategy)} stratégies")
                    self.performance_metrics['successful_detections'] += 1
                    return merged_lots
            
            logger.warning("⚠️ Aucune stratégie n'a réussi à détecter des lots")
            return []
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection des lots: {e}")
            return []
    
    def _merge_lots_from_all_strategies(self, all_lots_by_strategy: Dict[str, List[LotInfo]]) -> List[LotInfo]:
        """
        Fusionne intelligemment les lots détectés par toutes les stratégies
        
        Args:
            all_lots_by_strategy: Dictionnaire {nom_strategie: [lots]}
            
        Returns:
            Liste fusionnée des lots uniques avec les meilleures données
        """
        merged_lots = {}
        
        # Parcourir toutes les stratégies par ordre de priorité
        strategy_priority = ['LineAnalysis', 'StructuredTable', 'FlexiblePatterns', 
                           'MultiLineTitles', 'ExcelTable']
        
        for strategy_name in strategy_priority:
            if strategy_name not in all_lots_by_strategy:
                continue
            
            lots = all_lots_by_strategy[strategy_name]
            logger.debug(f"🔗 Fusion depuis {strategy_name}: {len(lots)} lots")
            
            for lot in lots:
                numero = lot.numero
                
                # Si le lot n'existe pas encore, l'ajouter
                if numero not in merged_lots:
                    merged_lots[numero] = lot
                    logger.debug(f"  ➕ Lot {numero} ajouté depuis {strategy_name}")
                else:
                    # Le lot existe déjà, améliorer les données si possible
                    existing_lot = merged_lots[numero]
                    
                    # Préférer un intitulé plus long (plus complet)
                    if len(lot.intitule) > len(existing_lot.intitule) and lot.intitule:
                        existing_lot.intitule = lot.intitule
                        logger.debug(f"  ✏️ Lot {numero}: intitulé amélioré depuis {strategy_name}")
                    
                    # Préférer des montants si non présents
                    if (existing_lot.montant_estime == 0 and lot.montant_estime > 0):
                        existing_lot.montant_estime = lot.montant_estime
                        logger.debug(f"  💰 Lot {numero}: montant estimé ajouté depuis {strategy_name}")
                    
                    if (existing_lot.montant_maximum == 0 and lot.montant_maximum > 0):
                        existing_lot.montant_maximum = lot.montant_maximum
                        logger.debug(f"  💰 Lot {numero}: montant maximum ajouté depuis {strategy_name}")
                    
                    # Combiner les sources
                    if strategy_name not in existing_lot.source:
                        existing_lot.source += f",{strategy_name}"
        
        # Convertir le dictionnaire en liste triée par numéro
        result = sorted(merged_lots.values(), key=lambda l: l.numero)
        
        logger.info(f"🔗 Fusion terminée: {len(result)} lots uniques (sur {sum(len(lots) for lots in all_lots_by_strategy.values())} détections totales)")
        
        return result
    
    def _get_strategy_by_name(self, strategy_name: str) -> Optional[LotDetectionStrategy]:
        """Récupère une stratégie par son nom"""
        # Mapping des noms d'enum vers les noms de stratégie
        strategy_mapping = {
            "structured_table": "StructuredTable",
            "line_analysis": "LineAnalysis", 
            "multi_line_titles": "MultiLineTitles",
            "flexible_patterns": "FlexiblePatterns",
            "excel_table": "ExcelTable"
        }
        
        # Convertir le nom d'enum en nom de stratégie
        strategy_class_name = strategy_mapping.get(strategy_name.lower(), strategy_name)
        
        for strategy in self.strategies:
            if strategy.get_strategy_name().lower() == strategy_class_name.lower():
                return strategy
        return None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de performance"""
        return self.performance_metrics.copy()
    
    def reset_metrics(self):
        """Remet à zéro les métriques"""
        self.performance_metrics = {
            'total_detections': 0,
            'successful_detections': 0,
            'strategy_usage': {},
            'average_detection_time': 0.0
        }
    
    def update_lot(self, lots: List[LotInfo], lot_numero: int, updates: Dict[str, Any]) -> bool:
        """
        Met à jour un lot spécifique dans une liste de lots
        
        Args:
            lots: Liste des lots à modifier
            lot_numero: Numéro du lot à mettre à jour
            updates: Dictionnaire des champs à mettre à jour
            
        Returns:
            True si la mise à jour a réussi, False sinon
        """
        try:
            for lot in lots:
                if lot.numero == lot_numero:
                    # Mettre à jour les champs disponibles
                    if 'intitule' in updates:
                        lot.intitule = str(updates['intitule'])
                    if 'montant_estime' in updates:
                        lot.montant_estime = float(updates['montant_estime']) if updates['montant_estime'] else 0.0
                    if 'montant_maximum' in updates:
                        lot.montant_maximum = float(updates['montant_maximum']) if updates['montant_maximum'] else 0.0
                    if 'quantite_minimum' in updates:
                        lot.quantite_minimum = int(updates['quantite_minimum']) if updates['quantite_minimum'] else 0
                    if 'quantites_estimees' in updates:
                        lot.quantites_estimees = str(updates['quantites_estimees'])
                    if 'quantite_maximum' in updates:
                        lot.quantite_maximum = int(updates['quantite_maximum']) if updates['quantite_maximum'] else 0
                    if 'criteres_economique' in updates:
                        lot.criteres_economique = str(updates['criteres_economique'])
                    if 'criteres_techniques' in updates:
                        lot.criteres_techniques = str(updates['criteres_techniques'])
                    if 'autres_criteres' in updates:
                        lot.autres_criteres = str(updates['autres_criteres'])
                    if 'rse' in updates:
                        lot.rse = str(updates['rse'])
                    if 'contribution_fournisseur' in updates:
                        lot.contribution_fournisseur = str(updates['contribution_fournisseur'])
                    if 'source' in updates:
                        lot.source = str(updates['source'])
                    if 'confidence' in updates:
                        lot.confidence = float(updates['confidence']) if updates['confidence'] else 1.0
                    
                    logger.debug(f"✅ Lot {lot_numero} mis à jour avec succès")
                    return True
            
            logger.warning(f"⚠️ Lot {lot_numero} non trouvé dans la liste")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la mise à jour du lot {lot_numero}: {e}")
            return False
    
    def update_lots(self, lots: List[LotInfo], updates_dict: Dict[int, Dict[str, Any]]) -> int:
        """
        Met à jour plusieurs lots à la fois
        
        Args:
            lots: Liste des lots à modifier
            updates_dict: Dictionnaire {numero_lot: {champs: valeurs}}
            
        Returns:
            Nombre de lots mis à jour avec succès
        """
        updated_count = 0
        for lot_numero, updates in updates_dict.items():
            if self.update_lot(lots, lot_numero, updates):
                updated_count += 1
        
        logger.info(f"✅ {updated_count}/{len(updates_dict)} lots mis à jour")
        return updated_count
    
    def convert_lot_to_dict(self, lot: LotInfo) -> Dict[str, Any]:
        """
        Convertit un objet LotInfo en dictionnaire pour faciliter l'édition
        
        Args:
            lot: Objet LotInfo à convertir
            
        Returns:
            Dictionnaire avec toutes les données du lot
        """
        return {
            'numero': lot.numero,
            'intitule': lot.intitule,
            'montant_estime': lot.montant_estime,
            'montant_maximum': lot.montant_maximum,
            'quantite_minimum': lot.quantite_minimum,
            'quantites_estimees': lot.quantites_estimees,
            'quantite_maximum': lot.quantite_maximum,
            'criteres_economique': lot.criteres_economique,
            'criteres_techniques': lot.criteres_techniques,
            'autres_criteres': lot.autres_criteres,
            'rse': lot.rse,
            'contribution_fournisseur': lot.contribution_fournisseur,
            'source': lot.source,
            'confidence': lot.confidence
        }
    
    def convert_dict_to_lot(self, lot_dict: Dict[str, Any]) -> LotInfo:
        """
        Convertit un dictionnaire en objet LotInfo
        
        Args:
            lot_dict: Dictionnaire avec les données du lot
            
        Returns:
            Objet LotInfo créé à partir du dictionnaire
        """
        return LotInfo(
            numero=int(lot_dict.get('numero', 1)),
            intitule=str(lot_dict.get('intitule', '')),
            montant_estime=float(lot_dict.get('montant_estime', 0)) if lot_dict.get('montant_estime') else 0.0,
            montant_maximum=float(lot_dict.get('montant_maximum', 0)) if lot_dict.get('montant_maximum') else 0.0,
            quantite_minimum=int(lot_dict.get('quantite_minimum', 0)) if lot_dict.get('quantite_minimum') else 0,
            quantites_estimees=str(lot_dict.get('quantites_estimees', '')),
            quantite_maximum=int(lot_dict.get('quantite_maximum', 0)) if lot_dict.get('quantite_maximum') else 0,
            criteres_economique=str(lot_dict.get('criteres_economique', '')),
            criteres_techniques=str(lot_dict.get('criteres_techniques', '')),
            autres_criteres=str(lot_dict.get('autres_criteres', '')),
            rse=str(lot_dict.get('rse', '')),
            contribution_fournisseur=str(lot_dict.get('contribution_fournisseur', '')),
            source=str(lot_dict.get('source', '')),
            confidence=float(lot_dict.get('confidence', 1.0)) if lot_dict.get('confidence') else 1.0
        )