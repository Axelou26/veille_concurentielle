"""
🏗️ Extracteur de Base - Classe Abstraite
========================================

Classe de base pour tous les extracteurs d'appels d'offres.
Fournit les fonctionnalités communes et l'interface standardisée.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
import logging
import re
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import asyncio
from datetime import datetime
import unicodedata

logger = logging.getLogger(__name__)

class BaseExtractor(ABC):
    """Classe de base abstraite pour tous les extracteurs"""
    
    def __init__(self, pattern_manager=None, validation_engine=None):
        """
        Initialise l'extracteur de base
        
        Args:
            pattern_manager: Gestionnaire de patterns (optionnel)
            validation_engine: Moteur de validation (optionnel)
        """
        self.pattern_manager = pattern_manager
        self.validation_engine = validation_engine
        self.extraction_cache = {}
        self.performance_metrics = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'extraction_errors': 0,
            'cache_hits': 0,
            'average_extraction_time': 0.0,
            'errors_by_type': {},
            'extraction_time_by_type': {
                'pdf': [],
                'excel': [],
                'text': [],
                'other': []
            }
        }
        
    @lru_cache(maxsize=128)
    def compile_pattern(self, pattern: str) -> re.Pattern:
        """
        Compile et met en cache un pattern regex
        
        Args:
            pattern: Pattern regex à compiler
            
        Returns:
            Pattern compilé
        """
        try:
            return re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        except re.error as e:
            logger.error(f"Erreur compilation pattern '{pattern}': {e}")
            return re.compile(r'.*')  # Pattern par défaut
    
    def extract_with_patterns(self, text: str, patterns: List[str], field_name: str = None) -> List[str]:
        """
        Extrait des valeurs avec plusieurs patterns
        
        Args:
            text: Texte à analyser
            patterns: Liste des patterns à essayer
            field_name: Nom du champ (pour le logging)
            
        Returns:
            Liste des valeurs extraites
        """
        extracted_values = []
        
        for pattern in patterns:
            try:
                # Déléguer à PatternManager si disponible pour éviter la double compilation
                if self.pattern_manager and hasattr(self.pattern_manager, 'compile_pattern'):
                    compiled_pattern = self.pattern_manager.compile_pattern(pattern)
                else:
                    compiled_pattern = self.compile_pattern(pattern)
                matches = compiled_pattern.findall(text)
                
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            # Si c'est un tuple, prendre le premier élément non vide
                            value = next((m for m in match if m and str(m).strip()), '')
                        else:
                            value = match
                        
                        if value and str(value).strip():
                            extracted_values.append(str(value).strip())
                            # Pour les dates et durées, prendre seulement la première valeur valide
                            if field_name and field_name in ['date_limite', 'date_attribution', 'duree_marche', 'fin_sans_reconduction', 'fin_avec_reconduction']:
                                break  # Prendre seulement la première date trouvée
                            
            except Exception as e:
                logger.warning(f"Erreur pattern '{pattern}' pour {field_name}: {e}")
                continue
        
        if field_name and extracted_values:
            logger.debug(f"Extraction {field_name}: {len(extracted_values)} valeurs trouvées")
        
        return extracted_values
    
    async def extract_parallel(self, text: str, pattern_groups: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Extraction parallèle de plusieurs groupes de patterns
        
        Args:
            text: Texte à analyser
            pattern_groups: Dictionnaire {champ: [patterns]}
            
        Returns:
            Dictionnaire {champ: [valeurs]}
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Créer les tâches
            tasks = {
                field: executor.submit(self.extract_with_patterns, text, patterns, field)
                for field, patterns in pattern_groups.items()
            }
            
            # Attendre les résultats
            for field, task in tasks.items():
                try:
                    results[field] = task.result(timeout=30)
                except Exception as e:
                    logger.error(f"Erreur extraction parallèle {field}: {e}")
                    results[field] = []
        
        return results
    
    def extract_parallel_sync(self, text: str, pattern_groups: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Version synchrone de l'extraction parallèle de plusieurs groupes de patterns
        
        Args:
            text: Texte à analyser
            pattern_groups: Dictionnaire {champ: [patterns]}
            
        Returns:
            Dictionnaire {champ: [valeurs]}
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            tasks = {
                field: executor.submit(self.extract_with_patterns, text, patterns, field)
                for field, patterns in pattern_groups.items()
            }
            for field, task in tasks.items():
                try:
                    results[field] = task.result(timeout=30)
                except Exception as e:
                    logger.error(f"Erreur extraction parallèle {field}: {e}")
                    results[field] = []
        
        return results
    
    def clean_extracted_value(self, value: str, field_type: str = None) -> Any:
        """
        Nettoie une valeur extraite selon son type
        
        Args:
            value: Valeur à nettoyer
            field_type: Type de champ (montant, date, etc.)
            
        Returns:
            Valeur nettoyée
        """
        if not value or not isinstance(value, str):
            return value
        
        # Normaliser les erreurs OCR courantes avant le traitement spécifique
        cleaned = self._normalize_ocr_errors(value.strip())
        
        if field_type == 'montant':
            # Nettoyer les montants avec support k€, M€
            cleaned = self._normalize_montant(cleaned)
            return cleaned
                
        elif field_type == 'date':
            # Nettoyer et normaliser les dates
            cleaned = self._normalize_date(cleaned)
            return cleaned
            
        elif field_type == 'reference':
            # Nettoyer les références
            cleaned = re.sub(r'[^\w\-]', '', cleaned)
            return cleaned.upper()
        
        elif field_type == 'duree':
            # Extraire et convertir la durée en mois
            # Détecter si c'est en années ou mois
            mois_match = re.search(r'(\d{1,3})\s*(?:mois|mois\.|m\.)', cleaned, re.IGNORECASE)
            ans_match = re.search(r'(\d{1,2})\s*(?:ans|an|année|annee|années|annees)', cleaned, re.IGNORECASE)
            
            if mois_match:
                # Déjà en mois
                try:
                    return int(mois_match.group(1))
                except ValueError:
                    pass
            elif ans_match:
                # En années, convertir en mois (1 an = 12 mois)
                try:
                    ans = int(ans_match.group(1))
                    # Chercher aussi des mois additionnels (ex: "2 ans et 3 mois")
                    mois_add = re.search(r'(\d{1,2})\s*(?:mois|mois\.|m\.)', cleaned, re.IGNORECASE)
                    mois_total = ans * 12
                    if mois_add:
                        mois_total += int(mois_add.group(1))
                    return mois_total
                except ValueError:
                    pass
            
            # Si pas de format reconnu, extraire juste le nombre (supposé en mois)
            m = re.search(r'(\d{1,3})', cleaned)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    return cleaned
            return cleaned
        
        elif field_type == 'reconduction':
            # Normaliser la reconduction : Oui, Non, ou Non spécifié
            cleaned_lower = cleaned.lower().strip()
            
            # Détecter "oui" ou variantes positives
            if re.search(r'\b(oui|possible|autorisée|autorisé|prévue|prevue|autorisée)\b', cleaned_lower):
                return 'Oui'
            
            # Détecter "non" ou variantes négatives
            if re.search(r'\b(non|impossible|non\s+autorisée|non\s+autorisé|non\s+prévue|non\s+prevue|sans\s+reconduction|sans\s+renouvellement)\b', cleaned_lower):
                return 'Non'
            
            # Si aucun pattern n'a matché mais qu'il y a du texte, retourner "Non spécifié"
            if cleaned and len(cleaned.strip()) > 0:
                # Si le pattern a détecté quelque chose (mention de reconduction), mais pas clairement oui/non
                if re.search(r'\b(reconduction|reconductible|renouvellement)\b', cleaned_lower):
                    return 'Non spécifié'
            
            # Sinon, valeur vide
            return cleaned
            
        else:
            # Nettoyage général
            cleaned = re.sub(r'\s+', ' ', cleaned)  # Espaces multiples
            return cleaned
    
    def _normalize_ocr_errors(self, text: str) -> str:
        """
        Corrige les erreurs OCR courantes de manière CONSERVATRICE
        pour ne pas casser la détection des lots
        
        Args:
            text: Texte à normaliser
            
        Returns:
            Texte corrigé
        """
        if not text:
            return text
        
        # Dictionnaire des remplacements OCR courants (version conservatrice)
        # REMARQUE: Éviter les règles qui peuvent casser la détection des lots
        ocr_replacements = [
            # Erreurs de reconnaissance de caractères (seulement cas sûrs)
            # NOTE: Pas de remplacement 'l'→'I' ni '0'→'O' car cela casse "lot" et numéros de lots
            
            # Espaces et ponctuation mal placés (conservateur)
            (r'\s+,', ','),  # Espace avant virgule
            (r'\s+\.', '.'),  # Espace avant point (seulement si suivi d'un espace)
            (r'\s+:', ':'),  # Espace avant deux-points
            # NOTE: Pas de remplacement automatique virgule/point sans espace car peut casser des formats
            
            # Corrections spécifiques aux appels d'offres (conservateur)
            (r'\bd\'offre\b', "d'offre"),  # Correction apostrophe
            # NOTE: Pas de corrections d'accents automatiques car peuvent casser des patterns
            
            # Correction des espaces multiples (conservateur)
            # NOTE: Pas de suppression des espaces dans les nombres (ex: "10 000") 
            # car cela peut casser des patterns de lots comme "Lot 1 234"
        ]
        
        normalized = text
        for pattern, replacement in ocr_replacements:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # Normalisation finale : seulement les espaces multiples EXTREMES (très conservateur)
        # Ne normaliser que les espaces multiples de 3+ espaces consécutifs
        # pour éviter de casser les formats avec double espaces légitimes
        normalized = re.sub(r'\s{3,}', ' ', normalized)  # Seulement 3+ espaces consécutifs
        
        return normalized
    
    def _normalize_montant(self, value: str) -> float:
        """
        Normalise un montant avec support des unités (k€, M€)
        
        Args:
            value: Valeur du montant à normaliser
            
        Returns:
            Montant normalisé en euros (float)
        """
        try:
            # Convertir en string si nécessaire
            cleaned = str(value).strip()
            
            # Détecter et extraire le multiplicateur
            multiplier = 1
            if re.search(r'\bk€?\b|\bkeuros?\b|\bk\s*€', cleaned, re.IGNORECASE):
                multiplier = 1000
                # Retirer les indicateurs de milliers
                cleaned = re.sub(r'\bk€?\b|\bkeuros?\b|\bk\s*€', '', cleaned, flags=re.IGNORECASE)
            elif re.search(r'\bm€?\b|\bmillions?\b|\bm\s*€', cleaned, re.IGNORECASE):
                multiplier = 1000000
                # Retirer les indicateurs de millions
                cleaned = re.sub(r'\bm€?\b|\bmillions?\b|\bm\s*€', '', cleaned, flags=re.IGNORECASE)
            
            # Supprimer les caractères non numériques sauf point, virgule et espace
            cleaned = re.sub(r'[^\d,.\s]', '', cleaned)
            
            # Retirer le symbole euro et ses variantes
            cleaned = cleaned.replace('€', '').replace('euros', '').replace('euro', '').replace('EUR', '')
            
            # Normaliser le séparateur décimal
            # Si on a une virgule comme séparateur (format français)
            if ',' in cleaned and '.' not in cleaned.replace(',', '', 1):
                # Probablement format français: "1 234,56"
                cleaned = cleaned.replace(' ', '').replace(',', '.')
            elif ',' in cleaned and '.' in cleaned:
                # Les deux présents : le dernier est le séparateur décimal
                if cleaned.rindex(',') > cleaned.rindex('.'):
                    # Virgule après point = séparateur décimal français
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    # Point après virgule = format anglais
                    cleaned = cleaned.replace(',', '')
            else:
                # Pas de virgule, ou virgule comme séparateur de milliers
                cleaned = cleaned.replace(' ', '')
            
            # Convertir en float
            if cleaned:
                amount = float(cleaned) * multiplier
                return round(amount, 2)
            else:
                return 0.0
                
        except (ValueError, AttributeError) as e:
            logger.debug(f"Erreur normalisation montant '{value}': {e}")
            return 0.0
    
    def _normalize_date(self, date_str: str) -> str:
        """
        Normalise une date en format standard DD/MM/YYYY
        
        Args:
            date_str: Date à normaliser
            
        Returns:
            Date normalisée au format DD/MM/YYYY
        """
        if not date_str:
            return date_str
        
        try:
            from dateutil import parser as date_parser
            
            # Essayer de parser avec dateutil (gère beaucoup de formats)
            parsed_date = date_parser.parse(date_str, fuzzy=True, dayfirst=True)
            
            # Valider que la date est dans une plage raisonnable
            if parsed_date.year >= 2000 and parsed_date.year <= 2100:
                return parsed_date.strftime('%d/%m/%Y')
            else:
                # Année invalide, retourner la date nettoyée
                cleaned = re.sub(r'[^\d/\-]', '', date_str)
                return cleaned
                
        except (ValueError, TypeError, ImportError):
            # Si dateutil n'est pas disponible ou parsing échoue, nettoyer manuellement
            # Supprimer les caractères non numériques sauf / et -
            cleaned = re.sub(r'[^\d/\-]', '', date_str)
            
            # Normaliser les séparateurs
            cleaned = cleaned.replace('-', '/')
            
            # Vérifier le format basique
            if re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', cleaned):
                return cleaned
            elif re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                # Format ISO, convertir en DD/MM/YYYY
                parts = date_str.split('-')
                if len(parts) == 3:
                    return f"{parts[2]}/{parts[1]}/{parts[0]}"
            
            return cleaned
    
    def generate_missing_values(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère uniquement les valeurs dérivées intelligemment depuis les données extraites
        Ne remplit PAS les champs avec des valeurs par défaut arbitraires
        
        Args:
            extracted_data: Données déjà extraites
            
        Returns:
            Données complétées (uniquement avec valeurs dérivées)
        """
        completed_data = extracted_data.copy()
        
        # Valeurs dérivées intelligemment depuis les données (si non présentes)
        # Ne remplir que si vraiment absent (pas de valeurs vides)
        if 'mots_cles' not in completed_data or not completed_data.get('mots_cles'):
            mots_cles = self._generate_keywords(extracted_data)
            if mots_cles:
                completed_data['mots_cles'] = mots_cles
        
        if 'univers' not in completed_data or not completed_data.get('univers'):
            univers = self._classify_universe(extracted_data)
            if univers:
                completed_data['univers'] = univers
        
        if 'groupement' not in completed_data or not completed_data.get('groupement'):
            groupement = self._detect_groupement(extracted_data)
            if groupement and groupement != 'AUTRE':
                completed_data['groupement'] = groupement
        
        # Générer le statut si possible (inférence intelligente)
        if 'statut' not in completed_data or not completed_data.get('statut'):
            statut = self._infer_statut(extracted_data)
            if statut:
                completed_data['statut'] = statut
        
        # Générer segment et famille intelligemment (si non extraits du document)
        if 'segment' not in completed_data or not completed_data.get('segment'):
            segment = self._classify_segment(extracted_data)
            if segment:
                completed_data['segment'] = segment
        
        if 'famille' not in completed_data or not completed_data.get('famille'):
            famille = self._classify_famille(extracted_data)
            if famille:
                completed_data['famille'] = famille
        
        # Ne PAS remplir avec des valeurs par défaut arbitraires :
        # - type_procedure, mono_multi doivent être extraits depuis le document
        # - quantites, criteres, rse, etc. doivent être extraits ou laissés vides
        
        return completed_data
    
    def _infer_statut(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Infère le statut basé sur les données disponibles
        
        Args:
            data: Données extraites
            
        Returns:
            Statut inféré ou None
        """
        try:
            # Si date d'attribution présente → marché attribué
            if data.get('date_attribution'):
                date_attr = str(data.get('date_attribution', ''))
                # Vérifier que c'est une vraie date (format date valide)
                if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', date_attr) or re.search(r'\d{4}-\d{2}-\d{2}', date_attr):
                    return 'Attribué'
            
            # Si attributaire présent → marché attribué
            if data.get('attributaire'):
                attributaire = str(data.get('attributaire', '')).strip()
                if attributaire and len(attributaire) > 2:
                    return 'Attribué'
            
            # Si date limite passée ET pas d'attribution → peut être "Clôturé" ou "En cours"
            if data.get('date_limite'):
                date_limite = str(data.get('date_limite', ''))
                # Essayer de parser la date (format simple)
                if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', date_limite) or re.search(r'\d{4}-\d{2}-\d{2}', date_limite):
                    from datetime import datetime
                    try:
                        # Parser selon le format
                        if '/' in date_limite:
                            parts = date_limite.split('/')
                            if len(parts) == 3:
                                day, month, year = parts
                                year = '20' + year if len(year) == 2 else year
                                date_obj = datetime(int(year), int(month), int(day))
                                if date_obj < datetime.now():
                                    # Date limite passée sans attribution → probablement clôturé
                                    if not data.get('date_attribution') and not data.get('attributaire'):
                                        return 'Clôturé'
                    except:
                        pass  # Si parsing échoue, continuer
            
            # Si référence et intitulé présents mais pas d'attribution → probablement "En cours"
            if data.get('reference_procedure') and data.get('intitule_procedure'):
                if not data.get('date_attribution') and not data.get('attributaire'):
                    return 'En cours'
            
            return None
            
        except Exception as e:
            logger.debug(f"Erreur inférence statut: {e}")
            return None
    
    def _generate_keywords(self, data: Dict[str, Any]) -> str:
        """Génère des mots-clés intelligents basés sur les données"""
        keywords = []
        
        # Liste des mots vides à exclure
        stop_words = {
            'appel', 'offres', 'offre', 'marche', 'marche', 'public', 'procédure', 'procedure',
            'achat', 'acquisition', 'fourniture', 'fournitures', 'prestation', 'prestations',
            'service', 'services', 'pour', 'dans', 'avec', 'sans', 'sous', 'sur', 'par',
            'depuis', 'selon', 'dans', 'vers', 'entre', 'donnees', 'données'
        }
        
        # Sources pour extraire les mots-clés
        sources = [
            data.get('intitule_procedure', ''),
            data.get('intitule_lot', ''),
            data.get('infos_complementaires', '')
        ]
        
        # Extraire les mots significatifs
        for source in sources:
            if not source:
                continue
            
            # Normaliser le texte
            text = str(source).lower()
            
            # Extraire les mots de 4+ caractères
            words = re.findall(r'\b[a-zàâäéèêëïîôöùûüÿç]{4,}\b', text)
            
            # Filtrer les mots vides et prendre les plus significatifs
            significant_words = [
                word for word in words 
                if word not in stop_words and len(word) >= 4
            ]
            
            keywords.extend(significant_words)
        
        # Ajouter des mots-clés contextuels basés sur le contenu
        text_combined = ' '.join(str(v) for v in sources if v).lower()
        
        # Détection contextuelle
        if 'formation' in text_combined:
            keywords.extend(['formation', 'apprentissage', 'développement'])
        if 'maintenance' in text_combined:
            keywords.extend(['maintenance', 'entretien', 'sav'])
        if 'logiciel' in text_combined or 'application' in text_combined:
            keywords.extend(['logiciel', 'application', 'si'])
        if 'médical' in text_combined or 'santé' in text_combined:
            keywords.extend(['médical', 'santé', 'soins'])
        if 'informatique' in text_combined or 'numérique' in text_combined:
            keywords.extend(['informatique', 'it', 'numérique'])
        if 'consommable' in text_combined:
            keywords.extend(['consommable', 'fourniture'])
        
        # Dédupliquer et limiter à 8-10 mots-clés les plus pertinents
        unique_keywords = []
        seen = set()
        for word in keywords:
            if word not in seen and word:
                unique_keywords.append(word)
                seen.add(word)
                if len(unique_keywords) >= 10:
                    break
        
        # Si peu de mots-clés, ajouter des génériques pertinents
        if len(unique_keywords) < 3:
            unique_keywords.extend(['appel', 'offres', 'marché'])
        
        return ', '.join(unique_keywords) if unique_keywords else 'appel, offres, marché, public'
    
    def _classify_universe(self, data: Dict[str, Any]) -> str:
        """Classifie l'univers de manière améliorée basé sur les données"""
        # Récupérer plusieurs sources de texte pour une meilleure détection
        sources = [
            data.get('intitule_procedure', ''),
            data.get('intitule_lot', ''),
            data.get('infos_complementaires', ''),
            data.get('execution_marche', '')
        ]
        
        text_combined = ' '.join(str(s) for s in sources if s).lower()
        
        if not text_combined:
            return 'Service'  # Par défaut
        
        # Normalisation sans accents pour des correspondances robustes
        def normalize(text: str) -> str:
            normalized = unicodedata.normalize('NFD', text)
            normalized = ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Mn')
            return normalized
        
        text_norm = normalize(text_combined)
        
        # Univers conformes à la BDD veille concurrentielle - avec scores de priorité
        # L'ordre est important : vérifier du plus spécifique au moins spécifique
        universe_keywords = {
            'Médical': [
                'medical', 'sante', 'soins', 'hopital', 'hospitalier', 'clinique', 'biomedical',
                'pharmacie', 'pharmaceutique', 'laboratoire', 'imagerie', 'radiologie', 'bloc', 
                'sterilisation', 'medecine', 'therapeutique', 'diagnostic', 'chirurgie', 'anesthesie'
            ],
            'Informatique': [
                'informatique', 'it', 'si', 'systeme information', 'logiciel', 'software',
                'application', 'applicatif', 'numerique', 'digital', 'reseau', 'cybersecurite',
                'securite informatique', 'cloud', 'data', 'donnees', 'serveur', 'poste', 
                'licence', 'erpg', 'pgi', 'erp', 'saas', 'ia', 'intelligence artificielle',
                'base de donnees', 'reseau', 'telecommunication'
            ],
            'Equipement': [
                'equipement', 'materiel', 'appareil', 'machine', 'outillage', 'dispositif', 
                'instrument', 'equipements', 'materiaux', 'outils', 'borne', 'terminal',
                'appareillage', 'installation technique'
            ],
            'Consommable': [
                'consommable', 'consommables', 'fourniture', 'fournitures', 'jetable', 
                'reactif', 'reactifs', 'cartouche', 'cartouches', 'toner', 'papier', 'encre', 
                'masque', 'gants', 'seringue', 'bandelette', 'reactif diagnostic'
            ],
            'Mobilier': [
                'mobilier', 'meuble', 'meubles', 'ameublement', 'fauteuil', 'chaise', 
                'bureau', 'armoire', 'table', 'rangement', 'banque accueil', 'siege', 
                'etagere', 'etagere', 'lit medical', 'brancard'
            ],
            'Vehicules': [
                'vehicule', 'vehicules', 'voiture', 'automobile', 'camion', 'utilitaire', 
                'bus', 'car', 'minibus', 'ambulance', 'fourgon', 'berline', 
                'vehicule electrique', 'vehicule hybride', 'engin', 'transport'
            ],
            'Service': [
                'service', 'prestations', 'prestation', 'maintenance', 'nettoyage', 
                'securite', 'gardiennage', 'restauration', 'hebergement', 'formation', 
                'assistance', 'support', 'infogerance', 'transport personnes', 'conseil',
                'prestation intellectuelle'
            ]
        }
        
        # Compter les occurrences pour chaque univers
        universe_scores = {}
        for universe, words in universe_keywords.items():
            score = sum(1 for word in words if word in text_norm)
            if score > 0:
                universe_scores[universe] = score
        
        # Retourner l'univers avec le score le plus élevé
        if universe_scores:
            # En cas d'égalité, prioriser dans l'ordre : Médical > Informatique > Equipement > etc.
            priority_order = ['Médical', 'Informatique', 'Equipement', 'Consommable', 'Mobilier', 'Vehicules', 'Service']
            max_score = max(universe_scores.values())
            candidates = [u for u, s in universe_scores.items() if s == max_score]
            
            # Prendre le premier selon l'ordre de priorité
            for priority in priority_order:
                if priority in candidates:
                    return priority
            
            # Sinon prendre le premier candidat
            return candidates[0]
        
        # Par défaut, classer en Service (pas de catégorie "Général" dans la BDD)
        return 'Service'
    
    def _detect_groupement(self, data: Dict[str, Any]) -> str:
        """Détecte le groupement de manière améliorée basé sur les données"""
        # Prioriser certains champs pour la détection
        priority_fields = [
            data.get('groupement', ''),  # Si déjà présent, le prendre
            data.get('intitule_procedure', ''),
            data.get('infos_complementaires', ''),
            data.get('execution_marche', '')
        ]
        
        text = ' '.join(str(f) for f in priority_fields if f).lower()
        
        if not text:
            # Si pas de texte dans les champs prioritaires, chercher partout
            text = ' '.join(str(v) for v in data.values() if v).lower()
        
        # Normalisation
        text = unicodedata.normalize('NFD', text)
        text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn').lower()
        
        # Patterns de détection améliorés avec variations
        groupement_patterns = {
            'RESAH': [
                r'\bresah\b',
                r'reseau.*sante.*hospitalier',
                r'reseau.*sante'
            ],
            'UGAP': [
                r'\bugap\b',
                r'union.*groupement.*achat.*public',
                r'union.*groupement'
            ],
            'UNIHA': [
                r'\buniha\b',
                r'union.*hospitaliere.*achat',
                r'union.*hospitaliere'
            ],
            'CAIH': [
                r'\bcaih\b',
                r'centre.*achat.*inter.*hospitalier'
            ]
        }
        
        # Rechercher dans l'ordre de priorité
        for groupement, patterns in groupement_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return groupement
        
        return 'AUTRE'
    
    def _classify_segment(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Classifie le segment de manière intelligente basé sur les données et la BDD
        
        Args:
            data: Données extraites
            
        Returns:
            Segment suggéré ou None
        """
        try:
            # 1. Utiliser le database_learner si disponible et entraîné
            if hasattr(self, 'database_learner') and self.database_learner and self.database_learner.is_trained:
                suggestion = self.database_learner.suggest_value('segment', data)
                if suggestion:
                    logger.debug(f"💡 Segment suggéré depuis BDD: {suggestion}")
                    return suggestion
            
            # Récupérer toutes les sources de texte pour une analyse complète
            sources = [
                data.get('intitule_procedure', ''),
                data.get('intitule_lot', ''),
                data.get('infos_complementaires', ''),
                data.get('execution_marche', ''),
                data.get('mots_cles', '')
            ]
            text_combined = ' '.join(str(s) for s in sources if s).lower()
            
            # Normalisation sans accents
            def normalize(text: str) -> str:
                normalized = unicodedata.normalize('NFD', text)
                normalized = ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Mn')
                return normalized
            
            text_norm = normalize(text_combined) if text_combined else ''
            
            # 2. Inférence basée sur l'univers avec scoring intelligent
            univers = data.get('univers', '')
            segment_scores = {}
            
            if univers:
                # Mapping segment -> mots-clés avec poids
                segment_keywords = {
                    'Médical': {
                        'Hospitalier': {
                            'words': ['hospitalier', 'hopital', 'chru', 'chu', 'ch', 'centre hospitalier', 
                                     'etablissement hospitalier', 'gh', 'ghp', 'ghps', 'clinique', 
                                     'centre de soins', 'bloc operatoire'],
                            'weight': 1.0
                        },
                        'Santé publique': {
                            'words': ['sante publique', 'santé publique', 'ars', 'collectivite', 
                                     'commune', 'mairie', 'departement', 'region', 'cnrs', 
                                     'etablissement public', 'service public'],
                            'weight': 1.0
                        },
                        'Santé privée': {
                            'words': ['prive', 'privé', 'sante privee', 'santé privée', 'cabinet', 
                                     'praticien', 'medecin prive'],
                            'weight': 1.0
                        },
                        'EHPAD': {
                            'words': ['ehpad', 'maison retraite', 'residence', 'personnes agees', 
                                     'personnes âgées', 'geriatrie', 'gériatrie'],
                            'weight': 1.0
                        }
                    },
                    'Informatique': {
                        'Logiciels': {
                            'words': ['logiciel', 'application', 'software', 'app', 'programme', 
                                     'erp', 'pgi', 'si', 'systeme information', 'licence'],
                            'weight': 1.0
                        },
                        'Infrastructure': {
                            'words': ['infrastructure', 'serveur', 'reseau', 'réseau', 'cloud', 
                                     'virtualisation', 'saas', 'iaas', 'paas', 'datacenter'],
                            'weight': 1.0
                        },
                        'Sécurité informatique': {
                            'words': ['securite', 'sécurité', 'cybersecurite', 'cybersécurité', 
                                     'firewall', 'antivirus', 'protection', 'securisation'],
                            'weight': 1.0
                        },
                        'Télécommunications': {
                            'words': ['telecommunication', 'télécommunication', 'telephonie', 
                                     'téléphonie', 'voip', 'fibre', 'reseaux telecom'],
                            'weight': 1.0
                        }
                    },
                    'Equipement': {
                        'Equipements techniques': {
                            'words': ['equipement technique', 'materiel technique', 'appareil technique', 
                                     'outillage', 'machine', 'installation'],
                            'weight': 1.0
                        },
                        'Matériels': {
                            'words': ['materiel', 'matériel', 'equipement', 'équipement', 'appareil'],
                            'weight': 0.8
                        },
                        'Dispositifs médicaux': {
                            'words': ['dispositif medical', 'dispositif médical', 'biomedical', 
                                     'biomédical', 'appareil medical'],
                            'weight': 1.0
                        }
                    },
                    'Service': {
                        'Services': {
                            'words': ['service', 'prestation', 'prestations', 'prestation de service'],
                            'weight': 0.5
                        },
                        'Prestations': {
                            'words': ['prestation', 'prestations', 'conseil', 'assistance', 'support'],
                            'weight': 1.0
                        },
                        'Maintenance': {
                            'words': ['maintenance', 'entretien', 'sav', 'reparation', 'réparation', 
                                     'intervention', 'depannage', 'dépannage'],
                            'weight': 1.0
                        },
                        'Formation': {
                            'words': ['formation', 'apprentissage', 'enseignement', 'pedagogie', 
                                     'pédagogie', 'cours', 'stage'],
                            'weight': 1.0
                        }
                    }
                }
                
                # Calculer les scores pour chaque segment possible
                if univers in segment_keywords:
                    for segment, config in segment_keywords[univers].items():
                        score = 0
                        words = config['words']
                        weight = config.get('weight', 1.0)
                        
                        for word in words:
                            if word in text_norm:
                                # Compter les occurrences et appliquer le poids
                                occurrences = text_norm.count(word)
                                score += occurrences * weight
                        
                        if score > 0:
                            segment_scores[segment] = score
                            logger.debug(f"  📊 Segment '{segment}': score={score:.2f}")
            
            # 3. Inférence basée sur le groupement (bonus)
            groupement = data.get('groupement', '')
            if groupement:
                groupement_segments = {
                    'RESAH': 'Hospitalier',
                    'UGAP': None,  # Peut être varié selon contenu
                    'UNIHA': 'Hospitalier',
                    'CAIH': 'Hospitalier'
                }
                if groupement in groupement_segments and groupement_segments[groupement]:
                    groupement_segment = groupement_segments[groupement]
                    # Ajouter un bonus au segment correspondant
                    if groupement_segment in segment_scores:
                        segment_scores[groupement_segment] += 2.0
                    else:
                        segment_scores[groupement_segment] = 2.0
            
            # Retourner le segment avec le score le plus élevé
            if segment_scores:
                best_segment = max(segment_scores.items(), key=lambda x: x[1])[0]
                logger.debug(f"✅ Segment sélectionné: {best_segment} (score: {segment_scores[best_segment]:.2f})")
                return best_segment
            
            # 4. Fallback : si aucun segment trouvé, utiliser le premier selon l'univers
            if univers:
                fallback_mapping = {
                    'Médical': 'Hospitalier',
                    'Informatique': 'Logiciels',
                    'Equipement': 'Equipements techniques',
                    'Consommable': 'Consommables médicaux',
                    'Mobilier': 'Mobilier hospitalier',
                    'Vehicules': 'Véhicules de service',
                    'Service': 'Services'
                }
                if univers in fallback_mapping:
                    logger.debug(f"⚠️ Segment fallback pour {univers}: {fallback_mapping[univers]}")
                    return fallback_mapping[univers]
            
            return None
            
        except Exception as e:
            logger.debug(f"Erreur classification segment: {e}")
            return None
    
    def _classify_famille(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Classifie la famille de manière intelligente basé sur les données et la BDD
        
        Args:
            data: Données extraites
            
        Returns:
            Famille suggérée ou None
        """
        try:
            # 1. Utiliser le database_learner si disponible et entraîné
            if hasattr(self, 'database_learner') and self.database_learner and self.database_learner.is_trained:
                suggestion = self.database_learner.suggest_value('famille', data)
                if suggestion:
                    logger.debug(f"💡 Famille suggérée depuis BDD: {suggestion}")
                    return suggestion
            
            # Récupérer toutes les sources de texte pour une analyse complète
            sources = [
                data.get('intitule_procedure', ''),
                data.get('intitule_lot', ''),
                data.get('infos_complementaires', ''),
                data.get('execution_marche', ''),
                data.get('mots_cles', '')
            ]
            text_combined = ' '.join(str(s) for s in sources if s).lower()
            
            # Normalisation sans accents
            def normalize(text: str) -> str:
                normalized = unicodedata.normalize('NFD', text)
                normalized = ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Mn')
                return normalized
            
            text_norm = normalize(text_combined) if text_combined else ''
            
            # 2. Inférence basée sur l'univers avec scoring intelligent
            univers = data.get('univers', '')
            famille_scores = {}
            
            if univers:
                # Mapping famille -> mots-clés avec poids
                famille_keywords = {
                    'Médical': {
                        'Stérilisation': {
                            'words': ['sterilisation', 'stérilisation', 'desinfection', 'autoclave', 
                                     'sterilisation centralisee', 'stérilisation centralisée', 'scs', 
                                     'laveur desinfecteur', 'laveur désinfecteur'],
                            'weight': 1.0
                        },
                        'Consommables médicaux': {
                            'words': ['consommable', 'jetable', 'reactif', 'réactif', 'bandelette', 
                                     'seringue', 'gant', 'masque', 'cathéter', 'sonde', 'compresse', 
                                     'gaze', 'champ operatoire', 'champ opératoire'],
                            'weight': 1.0
                        },
                        'Imagerie médicale': {
                            'words': ['imagerie', 'radiologie', 'scanner', 'irm', 'echographie', 
                                     'échographie', 'mammographie', 'tomodensitometrie', 
                                     'tomodensitométrie', 'imagerie medicale', 'imagerie médicale'],
                            'weight': 1.0
                        },
                        'Biologie médicale': {
                            'words': ['laboratoire', 'analyse', 'diagnostic', 'biologie', 'hematologie', 
                                     'hématologie', 'microbiologie', 'biochimie', 'serologie', 
                                     'sérologie', 'biologie medicale'],
                            'weight': 1.0
                        },
                        'Matériel médical': {
                            'words': ['materiel medical', 'matériel médical', 'equipement medical', 
                                     'équipement médical', 'appareil medical', 'dispositif medical'],
                            'weight': 0.8
                        },
                        'Bloc opératoire': {
                            'words': ['bloc operatoire', 'bloc opératoire', 'salle operation', 
                                     'salle opération', 'anesthesie', 'anesthésie', 'moniteur', 
                                     'table operation'],
                            'weight': 1.0
                        },
                        'Réanimation': {
                            'words': ['reanimation', 'réanimation', 'soins intensifs', 'si', 'rea', 
                                     'ventilateur', 'respirateur'],
                            'weight': 1.0
                        }
                    },
                    'Informatique': {
                        'Logiciels ERP/PGI': {
                            'words': ['erp', 'pgi', 'logiciel gestion', 'logiciel erp', 'progiciel', 
                                     'systeme gestion', 'système gestion', 'erp medical', 'erp hopital'],
                            'weight': 1.0
                        },
                        'Logiciels': {
                            'words': ['logiciel', 'software', 'application', 'app', 'licence', 
                                     'programme', 'outil informatique'],
                            'weight': 0.8
                        },
                        'Solutions Cloud': {
                            'words': ['cloud', 'saas', 'iaas', 'paas', 'azure', 'aws', 'gcp', 
                                     'hebergement cloud', 'hébergement cloud', 'infrastructure cloud'],
                            'weight': 1.0
                        },
                        'Cybersécurité': {
                            'words': ['securite', 'sécurité', 'cybersecurite', 'cybersécurité', 
                                     'firewall', 'antivirus', 'protection', 'securisation', 
                                     'intrusion detection', 'intrusion détection'],
                            'weight': 1.0
                        },
                        'Téléphonie': {
                            'words': ['telephonie', 'téléphonie', 'voip', 'pabx', 'ipbx', 
                                     'telecommunication', 'télécommunication'],
                            'weight': 1.0
                        },
                        'Infrastructure réseau': {
                            'words': ['reseau', 'réseau', 'switch', 'routeur', 'wifi', 'wlan', 
                                     'ethernet', 'infrastructure reseau'],
                            'weight': 1.0
                        }
                    },
                    'Equipement': {
                        'Équipements médicaux': {
                            'words': ['medical', 'médical', 'biomedical', 'biomédical', 
                                     'appareil medical', 'dispositif medical', 'equipement medical'],
                            'weight': 1.0
                        },
                        'Équipements techniques': {
                            'words': ['technique', 'industriel', 'outillage', 'machine', 'equipement technique', 
                                     'materiel technique', 'installation technique'],
                            'weight': 1.0
                        },
                        'Matériel et équipements': {
                            'words': ['materiel', 'matériel', 'equipement', 'équipement', 'appareil'],
                            'weight': 0.5
                        }
                    },
                    'Service': {
                        'Maintenance': {
                            'words': ['maintenance', 'entretien', 'sav', 'reparation', 'réparation', 
                                     'intervention', 'depannage', 'dépannage', 'maintenance preventive', 
                                     'maintenance préventive'],
                            'weight': 1.0
                        },
                        'Formation': {
                            'words': ['formation', 'apprentissage', 'enseignement', 'pedagogie', 
                                     'pédagogie', 'cours', 'stage', 'training', 'formation continue'],
                            'weight': 1.0
                        },
                        'Services de nettoyage': {
                            'words': ['nettoyage', 'hygiene', 'hygiène', 'proprete', 'propreté', 
                                     'nettoyage hospitalier', 'nettoyage industriel', 'prestations nettoyage'],
                            'weight': 1.0
                        },
                        'Conseil': {
                            'words': ['conseil', 'consulting', 'assistance technique', 'accompagnement', 
                                     'expertise', 'audit', 'conseil strategique'],
                            'weight': 1.0
                        },
                        'Services': {
                            'words': ['service', 'prestation', 'prestations'],
                            'weight': 0.3
                        }
                    }
                }
                
                # Calculer les scores pour chaque famille possible
                if univers in famille_keywords:
                    for famille, config in famille_keywords[univers].items():
                        score = 0
                        words = config['words']
                        weight = config.get('weight', 1.0)
                        
                        for word in words:
                            if word in text_norm:
                                # Compter les occurrences et appliquer le poids
                                occurrences = text_norm.count(word)
                                score += occurrences * weight
                        
                        if score > 0:
                            famille_scores[famille] = score
                            logger.debug(f"  📊 Famille '{famille}': score={score:.2f}")
            
            # Retourner la famille avec le score le plus élevé
            if famille_scores:
                best_famille = max(famille_scores.items(), key=lambda x: x[1])[0]
                logger.debug(f"✅ Famille sélectionnée: {best_famille} (score: {famille_scores[best_famille]:.2f})")
                return best_famille
            
            # 3. Fallback : utiliser les valeurs par défaut uniquement si vraiment nécessaire
            if univers:
                fallback_mapping = {
                    'Médical': 'Matériel médical',
                    'Informatique': 'Logiciels',
                    'Equipement': 'Équipements techniques',
                    'Consommable': 'Consommables médicaux',
                    'Mobilier': 'Mobilier',
                    'Vehicules': 'Véhicules',
                    'Service': 'Services'
                }
                if univers in fallback_mapping:
                    logger.debug(f"⚠️ Famille fallback pour {univers}: {fallback_mapping[univers]}")
                    return fallback_mapping[univers]
            
            return None
            
        except Exception as e:
            logger.debug(f"Erreur classification famille: {e}")
            return None
    
    def calculate_extraction_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule les statistiques d'extraction
        
        Args:
            data: Données extraites
            
        Returns:
            Statistiques d'extraction
        """
        total_fields = len(data)
        filled_fields = sum(1 for v in data.values() if v and str(v).strip())
        completion_rate = (filled_fields / total_fields * 100) if total_fields > 0 else 0
        
        return {
            'total_fields': total_fields,
            'filled_fields': filled_fields,
            'completion_rate': completion_rate,
            'extraction_timestamp': datetime.now().isoformat()
        }
    
    def validate_extraction(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Valide une extraction si un moteur de validation est disponible
        
        Args:
            data: Données à valider
            
        Returns:
            Résultat de validation ou None
        """
        if self.validation_engine:
            return self.validation_engine.validate_extraction(data)
        return None
    
    @abstractmethod
    def extract(self, source: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Méthode d'extraction abstraite à implémenter
        
        Args:
            source: Source de données (fichier, texte, etc.)
            **kwargs: Arguments supplémentaires
            
        Returns:
            Liste des données extraites
        """
        pass
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de performance"""
        return self.performance_metrics.copy()
    
    def reset_metrics(self):
        """Remet à zéro les métriques de performance"""
        self.performance_metrics = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'extraction_errors': 0,
            'cache_hits': 0,
            'average_extraction_time': 0.0,
            'errors_by_type': {},
            'extraction_time_by_type': {
                'pdf': [],
                'excel': [],
                'text': [],
                'other': []
            }
        }
