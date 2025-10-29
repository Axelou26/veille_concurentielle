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
        
        cleaned = value.strip()
        
        if field_type == 'montant':
            # Nettoyer les montants
            cleaned = re.sub(r'[^\d,.\s€]', '', cleaned)
            cleaned = cleaned.replace('€', '').replace('euros', '').replace('euro', '')
            cleaned = cleaned.replace(' ', '').replace(',', '.')
            try:
                return float(cleaned) if cleaned else 0
            except ValueError:
                return 0
                
        elif field_type == 'date':
            # Nettoyer les dates
            cleaned = re.sub(r'[^\d/\-]', '', cleaned)
            return cleaned
            
        elif field_type == 'reference':
            # Nettoyer les références
            cleaned = re.sub(r'[^\w\-]', '', cleaned)
            return cleaned.upper()
        
        elif field_type == 'duree':
            # Extraire un entier représentant la durée (mois si non précisé)
            m = re.search(r'(\d{1,3})', cleaned)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    return cleaned
            return cleaned
            
        else:
            # Nettoyage général
            cleaned = re.sub(r'\s+', ' ', cleaned)  # Espaces multiples
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
            
            # 2. Inférence basée sur l'univers (si disponible)
            univers = data.get('univers', '')
            if univers:
                segment_mapping = {
                    'Médical': ['Hospitalier', 'Santé publique', 'Santé privée', 'EHPAD'],
                    'Informatique': ['Logiciels', 'Infrastructure', 'Sécurité informatique', 'Télécommunications'],
                    'Equipement': ['Equipements techniques', 'Matériels', 'Dispositifs médicaux'],
                    'Consommable': ['Consommables médicaux', 'Fournitures', 'Réactifs'],
                    'Mobilier': ['Mobilier hospitalier', 'Mobilier de bureau', 'Ameublement'],
                    'Vehicules': ['Véhicules de service', 'Véhicules médicaux', 'Transport'],
                    'Service': ['Services', 'Prestations', 'Maintenance', 'Formation']
                }
                if univers in segment_mapping:
                    # Prendre le premier segment possible (ou pourrait être amélioré avec scoring)
                    return segment_mapping[univers][0]
            
            # 3. Inférence basée sur l'intitulé
            intitule = data.get('intitule_procedure', '') or data.get('intitule_lot', '')
            if intitule:
                intitule_lower = str(intitule).lower()
                
                # Détection par mots-clés dans l'intitulé
                if any(word in intitule_lower for word in ['hospitalier', 'hopital', 'clinique', 'etablissement']):
                    return 'Hospitalier'
                elif any(word in intitule_lower for word in ['sante publique', 'santé publique', 'collectivite']):
                    return 'Santé publique'
                elif any(word in intitule_lower for word in ['logiciel', 'application', 'si', 'informatique']):
                    return 'Logiciels'
                elif any(word in intitule_lower for word in ['maintenance', 'entretien', 'support']):
                    return 'Services'
                elif any(word in intitule_lower for word in ['equipement', 'materiel', 'appareil']):
                    return 'Equipements techniques'
            
            # 4. Inférence basée sur le groupement
            groupement = data.get('groupement', '')
            if groupement:
                # Certains groupements peuvent suggérer des segments
                if groupement == 'RESAH':
                    return 'Hospitalier'
                elif groupement in ['UGAP', 'UNIHA', 'CAIH']:
                    # Ces groupements peuvent avoir plusieurs segments, on prend une valeur par défaut
                    return 'Hospitalier'
            
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
            
            # 2. Inférence basée sur l'univers et l'intitulé
            univers = data.get('univers', '')
            intitule = data.get('intitule_procedure', '') or data.get('intitule_lot', '')
            intitule_lower = str(intitule).lower()
            
            if univers == 'Médical':
                if any(word in intitule_lower for word in ['sterilisation', 'stérilisation', 'desinfection']):
                    return 'Stérilisation'
                elif any(word in intitule_lower for word in ['consommable', 'jetable', 'reactif']):
                    return 'Consommables médicaux'
                elif any(word in intitule_lower for word in ['imagerie', 'radiologie', 'scanner']):
                    return 'Imagerie médicale'
                elif any(word in intitule_lower for word in ['laboratoire', 'analyse', 'diagnostic']):
                    return 'Biologie médicale'
                else:
                    return 'Matériel médical'
            
            elif univers == 'Informatique':
                if any(word in intitule_lower for word in ['erp', 'pgi', 'logiciel gestion', 'logiciel erp']):
                    return 'Logiciels ERP/PGI'
                elif any(word in intitule_lower for word in ['licence', 'software', 'application']):
                    return 'Logiciels'
                elif any(word in intitule_lower for word in ['cloud', 'saas', 'infrastructure']):
                    return 'Solutions Cloud'
                elif any(word in intitule_lower for word in ['securite', 'sécurité', 'cybersecurite']):
                    return 'Cybersécurité'
                else:
                    return 'Logiciels et applications'
            
            elif univers == 'Equipement':
                if any(word in intitule_lower for word in ['medical', 'médical', 'biomedical']):
                    return 'Équipements médicaux'
                elif any(word in intitule_lower for word in ['technique', 'industriel', 'outillage']):
                    return 'Équipements techniques'
                else:
                    return 'Matériel et équipements'
            
            elif univers == 'Consommable':
                if any(word in intitule_lower for word in ['medical', 'médical', 'hopital']):
                    return 'Consommables médicaux'
                elif any(word in intitule_lower for word in ['bureau', 'papier', 'toner', 'encre']):
                    return 'Fournitures de bureau'
                else:
                    return 'Consommables'
            
            elif univers == 'Mobilier':
                if any(word in intitule_lower for word in ['medical', 'médical', 'hopital', 'clinique']):
                    return 'Mobilier médical'
                else:
                    return 'Mobilier'
            
            elif univers == 'Vehicules':
                return 'Véhicules'
            
            elif univers == 'Service':
                if any(word in intitule_lower for word in ['maintenance', 'entretien', 'sav']):
                    return 'Maintenance'
                elif any(word in intitule_lower for word in ['formation', 'apprentissage']):
                    return 'Formation'
                elif any(word in intitule_lower for word in ['nettoyage', 'hygiene', 'propreté']):
                    return 'Services de nettoyage'
                else:
                    return 'Services'
            
            # 3. Inférence basée uniquement sur l'intitulé (si pas d'univers)
            if intitule and not univers:
                if any(word in intitule_lower for word in ['formation', 'apprentissage']):
                    return 'Formation'
                elif any(word in intitule_lower for word in ['maintenance', 'entretien']):
                    return 'Maintenance'
                elif any(word in intitule_lower for word in ['logiciel', 'application', 'erp']):
                    return 'Logiciels'
            
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
