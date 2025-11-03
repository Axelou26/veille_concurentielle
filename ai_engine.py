"""
🤖 Moteur IA Avancé - Veille Concurrentielle
===========================================

Moteur d'IA complet capable de répondre à n'importe quelle question sur la base de données :
- Statistiques avancées
- Filtrage intelligent
- Affichage de données
- Analyses croisées
- Détection automatique d'intention
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
import logging
from datetime import datetime
import re
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VeilleAIEngine:
    """Moteur d'IA avancé pour l'analyse de veille concurrentielle"""
    
    # Colonnes de la base de données
    COLONNES_DB = {
        'identifiants': ['id', 'reference_procedure', 'lot_numero'],
        'classification': ['mots_cles', 'univers', 'segment', 'famille', 'statut', 'groupement'],
        'procedure': ['type_procedure', 'mono_multi', 'execution_marche', 'nbr_lots', 'intitule_procedure', 'intitule_lot'],
        'dates': ['date_limite', 'date_attribution', 'duree_marche', 'reconduction', 'fin_sans_reconduction', 'fin_avec_reconduction'],
        'financier': ['montant_global_estime', 'montant_global_maxi', 'achat', 'credit_bail', 'credit_bail_duree', 'location', 'location_duree', 'mad'],
        'quantites': ['quantite_minimum', 'quantites_estimees', 'quantite_maximum'],
        'criteres': ['criteres_economique', 'criteres_techniques', 'autres_criteres', 'rse', 'contribution_fournisseur'],
        'resultats': ['attributaire', 'produit_retenu'],
        'notes': ['infos_complementaires', 'remarques', 'notes_acheteur_procedure', 'notes_acheteur_fournisseur', 'notes_acheteur_positionnement', 'note_veille'],
        'metadata': ['created_at', 'updated_at']
    }
    
    # Synonymes pour mieux comprendre les questions
    SYNONYMES = {
        'montant': ['montant', 'budget', 'prix', 'coût', 'cout', 'valeur', 'financier', 'euro', '€'],
        'date': ['date', 'quand', 'période', 'periode', 'année', 'annee', 'mois', 'jour'],
        'groupement': ['groupement', 'organisme', 'organisation', 'acheteur', 'entité', 'entite'],
        'univers': ['univers', 'domaine', 'secteur', 'catégorie', 'categorie'],
        'statut': ['statut', 'état', 'etat', 'status', 'situation'],
        'lot': ['lot', 'lots', 'nbr_lots', 'nombre de lots'],
        'attributaire': ['attributaire', 'gagnant', 'fournisseur', 'entreprise', 'société', 'societe', 'titulaire'],
        'procedure': ['procédure', 'procedure', 'appel', 'ao', 'marché', 'marche'],
    }
    
    def __init__(self):
        self.initialized = False
        self.data = None
        self.conversation_history = []
        self.db_connection = None
        
        # Métriques de performance
        self.performance_metrics = {
            'total_questions': 0,
            'successful_answers': 0,
            'failed_answers': 0,
            'average_response_time': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Cache des résultats
        self.cache = {}
        
    def initialize(self, data: pd.DataFrame, load_heavy_models: bool = False):
        """Initialise le moteur d'IA avec les données"""
        try:
            logger.info("🚀 Initialisation du moteur d'IA avancé...")
            self.data = data.copy()
            
            # Prétraitement des données
            self._preprocess_data()
            
            self.initialized = True
            logger.info(f"✅ Moteur d'IA initialisé avec {len(self.data)} enregistrements!")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            raise
    
    def _preprocess_data(self):
        """Prétraite les données pour optimiser les analyses"""
        try:
            # Convertir les colonnes numériques
            numeric_cols = ['montant_global_estime', 'montant_global_maxi', 'duree_marche', 
                          'nbr_lots', 'lot_numero', 'quantite_minimum', 'quantites_estimees', 
                          'quantite_maximum', 'credit_bail_duree', 'location_duree']
            
            for col in numeric_cols:
                if col in self.data.columns:
                    self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
            
            # Convertir les colonnes de dates
            date_cols = ['date_limite', 'date_attribution', 'fin_sans_reconduction', 'fin_avec_reconduction']
            for col in date_cols:
                if col in self.data.columns:
                    self.data[col] = pd.to_datetime(self.data[col], errors='coerce')
            
            # Nettoyer les colonnes texte
            text_cols = self.data.select_dtypes(include=['object']).columns
            for col in text_cols:
                self.data[col] = self.data[col].fillna('').astype(str).str.strip()
            
            logger.info("✅ Données prétraitées avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur prétraitement: {e}")
    
    def ask_question(self, question: str) -> str:
        """Répond intelligemment à n'importe quelle question avec contexte conversationnel"""
        if not self.initialized:
            return "❌ Le moteur d'IA n'est pas initialisé. Veuillez d'abord l'initialiser."
        
        start_time = datetime.now()
        
        try:
            logger.info(f"🤔 Question posée: {question}")
            self.performance_metrics['total_questions'] += 1
            
            # Vérifier le cache (désactivé pour les questions contextuelles)
            cache_key = question.lower().strip()
            is_contextual = self._is_contextual_question(question)
            
            if not is_contextual and cache_key in self.cache:
                self.performance_metrics['cache_hits'] += 1
                logger.info("💾 Réponse trouvée dans le cache")
                return self.cache[cache_key]
            
            self.performance_metrics['cache_misses'] += 1
            
            # Enrichir la question avec le contexte si nécessaire
            enriched_question = self._enrich_with_context(question)
            logger.info(f"📝 Question enrichie: {enriched_question}")
            
            # Analyser la question et déterminer l'intention
            intention = self._detect_intention(enriched_question)
            logger.info(f"🎯 Intention détectée: {intention['type']}")
            
            # Router vers la bonne méthode selon l'intention
            response = self._route_question(enriched_question, intention)
            
            # Ajouter un indicateur si la question était contextuelle
            if is_contextual and enriched_question != question:
                response = f"🔗 *Question interprétée: \"{enriched_question}\"*\n\n{response}"
            
            # Mettre en cache seulement si pas contextuel
            if not is_contextual:
                self.cache[cache_key] = response
            
            # Ajouter à l'historique
            self.conversation_history.append({
                'question': question,
                'enriched_question': enriched_question,
                'response': response,
                'intention': intention,
                'timestamp': datetime.now(),
                'filters': intention.get('filters', {}),
                'is_contextual': is_contextual
            })
            
            # Mettre à jour les métriques
            self.performance_metrics['successful_answers'] += 1
            elapsed_time = (datetime.now() - start_time).total_seconds()
            self._update_average_response_time(elapsed_time)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de la question: {e}")
            self.performance_metrics['failed_answers'] += 1
            return f"❌ Désolé, une erreur est survenue: {str(e)}\n\n💡 Essayez de reformuler votre question."
    
    def _is_contextual_question(self, question: str) -> bool:
        """Détecte si la question fait référence au contexte précédent"""
        question_lower = question.lower().strip()
        
        # Mots-clés indiquant une référence contextuelle
        contextual_keywords = [
            'ceux de', 'celles de', 'celui de', 'celle de',
            'pour lui', 'pour eux', 'pour elles',
            'et pour', 'et avec', 'et du', 'et de', 'et le', 'et la', 'et les',
            'aussi', 'également', 'même chose',
            'compare avec', 'comparé à', 'par rapport à',
            'maintenant', 'ensuite', 'puis', 'après',
            'et celui', 'et celle', 'et ceux', 'et celles',
            'même pour', 'idem pour',
            'pareil pour', 'identique pour'
        ]
        
        # Pronoms démonstratifs et possessifs
        pronouns = ['il', 'elle', 'ils', 'elles', 'le', 'la', 'les', 'leur', 'leurs', 'lui', 'eux']
        
        # Vérifier les mots-clés contextuels
        for keyword in contextual_keywords:
            if keyword in question_lower:
                return True
        
        # Questions très courtes qui semblent contextuelles
        words = question_lower.split()
        if len(words) <= 5:
            # Vérifier les pronoms
            for pronoun in pronouns:
                if pronoun in words:
                    return True
            
            # Vérifier les univers/groupements connus
            known_entities = ['resah', 'uniha', 'ugap', 'médical', 'medical', 'informatique', 'mobilier', 'en cours', 'attribué', 'attribue']
            for entity in known_entities:
                if entity in question_lower:
                    return True
        
        # Questions commençant par "et"
        if question_lower.startswith('et '):
            return True
        
        # Questions très courtes avec "en" (ex: "en médical", "en informatique")
        if len(words) <= 3 and any(word in question_lower for word in ['en médical', 'en medical', 'en informatique', 'en mobilier']):
            return True
        
        # Questions avec "pour" + entité connue
        if 'pour' in question_lower and any(entity in question_lower for entity in ['resah', 'uniha', 'ugap', 'médical', 'medical', 'informatique']):
            return True
        
        return False
    
    def _enrich_with_context(self, question: str) -> str:
        """Enrichit la question avec le contexte de la conversation précédente"""
        if not self.conversation_history:
            return question
        
        question_lower = question.lower()
        
        # Récupérer le dernier échange
        last_exchange = self.conversation_history[-1]
        last_filters = last_exchange.get('filters', {})
        last_intention = last_exchange.get('intention', {})
        
        # Si la question ne semble pas contextuelle, retourner telle quelle
        if not self._is_contextual_question(question):
            return question
        
        logger.info(f"🔗 Question contextuelle détectée. Contexte précédent: {last_filters}")
        
        enriched = question
        
        # Gérer les références directes à un autre groupement/univers/etc
        # Ex: "et pour l'UNIHA" -> "montre les lots pour l'UNIHA"
        if any(phrase in question_lower for phrase in ['et pour', 'et du', 'et de', 'et le', 'et la', 'et avec']):
            # Extraire le nouveau sujet
            new_subject = self._extract_subject_from_contextual(question)
            if new_subject:
                # Reconstruire la question avec l'action de la question précédente
                last_question = last_exchange.get('question', '')
                action = self._extract_action(last_question)
                enriched = f"{action} {new_subject}"
                logger.info(f"✨ Question reconstruite: {enriched}")
        
        # Gérer "ceux de" / "celles de"
        elif any(phrase in question_lower for phrase in ['ceux de', 'celles de', 'celui de', 'celle de']):
            # Ex: "ceux de l'UNIHA" -> on remplace le filtre précédent
            new_subject = question_lower.split('de ')[-1].strip()
            last_question = last_exchange.get('question', '')
            action = self._extract_action(last_question)
            enriched = f"{action} {new_subject}"
            logger.info(f"✨ Question reconstruite: {enriched}")
        
        # Gérer les comparaisons
        elif any(phrase in question_lower for phrase in ['compare avec', 'comparé à', 'par rapport à']):
            # Ex: "compare avec l'UNIHA" -> "compare RESAH et UNIHA"
            if last_filters.get('groupement'):
                new_subject = question_lower.split('avec ')[-1].strip() if 'avec' in question_lower else question_lower.split('à ')[-1].strip()
                enriched = f"compare {last_filters['groupement']} et {new_subject}"
                logger.info(f"✨ Comparaison reconstruite: {enriched}")
        
        # Gérer "même chose pour" / "pareil pour"
        elif any(phrase in question_lower for phrase in ['même chose', 'pareil pour', 'idem pour', 'identique pour']):
            new_subject = question_lower.split('pour ')[-1].strip() if 'pour' in question_lower else ''
            last_question = last_exchange.get('question', '')
            action = self._extract_action(last_question)
            enriched = f"{action} {new_subject}"
            logger.info(f"✨ Question reconstruite: {enriched}")
        
        # Gérer les questions très courtes (hériter des filtres précédents mais avec nouveau sujet)
        elif len(question.split()) <= 5:
            # Essayer d'identifier le nouveau filtre dans la question courte
            new_filter = self._extract_new_filter(question)
            if new_filter and last_intention.get('action'):
                last_question = last_exchange.get('question', '')
                action = self._extract_action(last_question)
                
                # Construire la question en combinant les filtres précédents + nouveau filtre
                enriched_parts = [action]
                
                # Garder les filtres précédents et ajouter le nouveau
                if 'groupement' in new_filter:
                    # Remplacer le groupement précédent par le nouveau
                    enriched_parts.append(new_filter['groupement'])
                    # Garder l'univers précédent s'il existe
                    if last_filters.get('univers'):
                        enriched_parts.append(last_filters['univers'])
                elif 'univers' in new_filter:
                    # Garder le groupement précédent et remplacer l'univers
                    if last_filters.get('groupement'):
                        enriched_parts.append(last_filters['groupement'])
                    enriched_parts.append(new_filter['univers'])
                elif 'statut' in new_filter:
                    # Garder groupement et univers précédents, ajouter le statut
                    if last_filters.get('groupement'):
                        enriched_parts.append(last_filters['groupement'])
                    if last_filters.get('univers'):
                        enriched_parts.append(last_filters['univers'])
                    enriched_parts.append(new_filter['statut'])
                else:
                    enriched = f"{action} {question}"
                
                if 'enriched_parts' in locals():
                    enriched = ' '.join(enriched_parts)
                
                logger.info(f"✨ Question courte enrichie (filtres combinés): {enriched}")
        
        # Gérer les questions avec "en" (ex: "en médical", "en informatique")
        elif any(phrase in question_lower for phrase in ['en médical', 'en medical', 'en informatique', 'en mobilier']):
            last_question = last_exchange.get('question', '')
            action = self._extract_action(last_question)
            
            # Construire la question en gardant les filtres précédents + nouveau filtre univers
            enriched_parts = [action]
            
            # Garder le groupement précédent s'il existe
            if last_filters.get('groupement'):
                enriched_parts.append(last_filters['groupement'])
            
            # Ajouter le nouvel univers
            if 'en médical' in question_lower or 'en medical' in question_lower:
                enriched_parts.append('médical')
            elif 'en informatique' in question_lower:
                enriched_parts.append('informatique')
            elif 'en mobilier' in question_lower:
                enriched_parts.append('mobilier')
            
            # Garder le statut précédent s'il existe
            if last_filters.get('statut'):
                enriched_parts.append(last_filters['statut'])
            
            enriched = ' '.join(enriched_parts)
            logger.info(f"✨ Question 'en' enrichie (filtres combinés): {enriched}")
        
        return enriched
    
    def _extract_action(self, question: str) -> str:
        """Extrait l'action principale d'une question"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['montre', 'affiche', 'voir']):
            return 'montre les lots pour'
        elif any(word in question_lower for word in ['liste', 'lister']):
            return 'liste les lots pour'
        elif any(word in question_lower for word in ['combien', 'nombre']):
            return 'combien de lots pour'
        elif any(word in question_lower for word in ['somme', 'total montant']):
            return 'somme des montants pour'
        elif any(word in question_lower for word in ['moyenne', 'moyen']):
            return 'montant moyen pour'
        elif any(word in question_lower for word in ['analyse', 'statistique']):
            return 'analyse pour'
        else:
            return 'montre les lots pour'
    
    def _extract_subject_from_contextual(self, question: str) -> str:
        """Extrait le sujet d'une question contextuelle"""
        question_lower = question.lower()
        
        # Supprimer les mots de liaison
        for phrase in ['et pour', 'et du', 'et de', 'et le', 'et la', 'et avec', 'ceux de', 'celles de']:
            if phrase in question_lower:
                subject = question_lower.split(phrase)[-1].strip()
                return subject
        
        return question_lower.strip()
    
    def _extract_new_filter(self, question: str) -> Dict[str, str]:
        """Extrait le nouveau filtre d'une question courte"""
        question_lower = question.lower()
        new_filter = {}
        
        # Détecter les groupements
        if 'resah' in question_lower:
            new_filter['groupement'] = 'RESAH'
        elif 'uniha' in question_lower:
            new_filter['groupement'] = 'UNIHA'
        elif 'ugap' in question_lower:
            new_filter['groupement'] = 'UGAP'
        
        # Détecter les univers
        if any(word in question_lower for word in ['médical', 'medical']):
            new_filter['univers'] = 'Médical'
        elif 'informatique' in question_lower:
            new_filter['univers'] = 'Informatique'
        elif 'mobilier' in question_lower:
            new_filter['univers'] = 'Mobilier'
        
        # Détecter les statuts
        if 'en cours' in question_lower:
            new_filter['statut'] = 'En cours'
        elif any(word in question_lower for word in ['attribué', 'attribue']):
            new_filter['statut'] = 'Attribué'
        
        return new_filter
    
    def _extract_base_question(self, question: str, filters: Dict[str, Any]) -> str:
        """Extrait la question de base sans les filtres spécifiques"""
        # Simplifier en retournant la question telle quelle
        # Les filtres seront détectés à nouveau
        return question
    
    def _detect_intention(self, question: str) -> Dict[str, Any]:
        """Détecte l'intention de la question"""
        question_lower = question.lower()
        
        intention = {
            'type': 'general',
            'action': None,
            'entities': [],
            'filters': {},
            'aggregation': None
        }
        
        # Si c'est une recherche spécifique, ignorer les filtres généraux
        if self._should_skip_filters_for_search(question):
            intention['skip_general_filters'] = True
        
        # Détection de l'action principale
        if any(word in question_lower for word in ['combien', 'nombre', 'total', 'compter', 'compte', 'nb', 'quantité']):
            intention['type'] = 'count'
            intention['action'] = 'compter'
        
        elif any(word in question_lower for word in ['somme', 'total montant', 'budget total', 'additionner']):
            intention['type'] = 'sum'
            intention['action'] = 'sommer'
        
        elif any(word in question_lower for word in ['moyenne', 'moyen', 'mean', 'avg']):
            intention['type'] = 'average'
            intention['action'] = 'moyenner'
        
        elif any(word in question_lower for word in ['maximum', 'max', 'plus grand', 'plus élevé', 'plus eleve']):
            intention['type'] = 'max'
            intention['action'] = 'maximum'
        
        elif any(word in question_lower for word in ['minimum', 'min', 'plus petit', 'plus bas', 'moins']):
            intention['type'] = 'min'
            intention['action'] = 'minimum'
        
        elif any(word in question_lower for word in ['liste', 'montre', 'affiche', 'voir', 'donne', 'trouve', 'cherche', 'recherche']):
            intention['type'] = 'list'
            intention['action'] = 'lister'
        
        elif any(word in question_lower for word in ['répartition', 'repartition', 'distribution', 'grouper', 'group by', 'par']):
            intention['type'] = 'distribution'
            intention['action'] = 'répartir'
        
        elif any(word in question_lower for word in ['compare', 'comparaison', 'différence', 'difference', 'vs', 'versus']):
            intention['type'] = 'comparison'
            intention['action'] = 'comparer'
        
        elif any(word in question_lower for word in ['analyse', 'statistique', 'stat', 'résumé', 'resume', 'overview']):
            intention['type'] = 'analysis'
            intention['action'] = 'analyser'
        
        elif any(phrase in question_lower for phrase in ['fin de marché', 'fin de marche', 'expire', 'se termine', 'bientôt', 'prochainement', 'proche']):
            if any(word in question_lower for word in ['bientôt', 'proche', 'prochainement', 'expire', 'se termine']):
                intention['type'] = 'expiring_lots'
                intention['action'] = 'expiration'
        
        elif any(word in question_lower for word in ['bonjour', 'salut', 'hello', 'hi', 'merci', 'au revoir']):
            intention['type'] = 'conversation'
            intention['action'] = 'converser'
        
        # Extraction des entités (colonnes, valeurs)
        intention['entities'] = self._extract_entities(question_lower)
        
        # Extraction des filtres (seulement si ce n'est pas une recherche spécifique)
        if not intention.get('skip_general_filters', False):
            intention['filters'] = self._extract_filters(question_lower)
        
        # Détection d'agrégation
        intention['aggregation'] = self._detect_aggregation(question_lower)
        
        return intention
    
    def _extract_entities(self, question: str) -> List[str]:
        """Extrait les entités (colonnes) mentionnées dans la question"""
        entities = []
        
        # Chercher les colonnes mentionnées
        all_columns = [col for cat in self.COLONNES_DB.values() for col in cat]
        
        for col in all_columns:
            col_variants = [col, col.replace('_', ' '), col.replace('_', '')]
            if any(variant in question for variant in col_variants):
                entities.append(col)
        
        # Chercher via les synonymes
        for key, synonyms in self.SYNONYMES.items():
            if any(syn in question for syn in synonyms):
                # Trouver les colonnes correspondantes
                for col in all_columns:
                    if key in col or col in key:
                        if col not in entities:
                            entities.append(col)
        
        return entities
    
    def _extract_filters(self, question: str) -> Dict[str, Any]:
        """Extrait les filtres de la question"""
        filters = {}
        question_lower = question.lower()
        
        # Détecter les groupements spécifiques
        if 'resah' in question_lower:
            filters['groupement'] = 'RESAH'
        elif 'uniha' in question_lower:
            filters['groupement'] = 'UNIHA'
        elif 'ugap' in question_lower:
            filters['groupement'] = 'UGAP'
        
        # Détecter les univers
        if any(word in question_lower for word in ['médical', 'medical', 'santé', 'sante']):
            filters['univers'] = 'Médical'
        elif 'informatique' in question_lower or 'it' in question_lower:
            filters['univers'] = 'Informatique'
        elif 'mobilier' in question_lower or 'meuble' in question_lower:
            filters['univers'] = 'Mobilier'
        
        # Détecter les statuts
        if any(word in question_lower for word in ['en cours', 'actif', 'actifs']):
            filters['statut'] = 'En cours'
        elif any(word in question_lower for word in ['attribué', 'attribue', 'terminé', 'termine']):
            filters['statut'] = 'Attribué'
        elif any(word in question_lower for word in ['annulé', 'annule', 'infructueux']):
            filters['statut'] = 'Annulé'
        
        # Détecter les années
        year_pattern = r'20\d{2}'
        years = re.findall(year_pattern, question_lower)
        if years:
            filters['year'] = int(years[0])
        
        # Détecter les plages de montants
        montant_pattern = r'(\d+[\s,.]?\d*)\s*(?:€|euros?|k€|M€)'
        montants = re.findall(montant_pattern, question_lower)
        if montants:
            try:
                montant = float(montants[0].replace(' ', '').replace(',', '.'))
                if 'k€' in question_lower:
                    montant *= 1000
                elif 'M€' in question_lower:
                    montant *= 1000000
                
                if any(word in question_lower for word in ['supérieur', 'superieur', 'plus de', 'au-dessus', 'au dessus', '>']):
                    filters['montant_min'] = montant
                elif any(word in question_lower for word in ['inférieur', 'inferieur', 'moins de', 'en-dessous', 'en dessous', '<']):
                    filters['montant_max'] = montant
                else:
                    filters['montant_approx'] = montant
            except:
                pass
        
        return filters
    
    def _detect_aggregation(self, question: str) -> Optional[str]:
        """Détecte si la question demande une agrégation par colonne"""
        if any(phrase in question for phrase in ['par univers', 'par groupement', 'par statut', 'par segment', 'par famille']):
            if 'univers' in question:
                return 'univers'
            elif 'groupement' in question:
                return 'groupement'
            elif 'statut' in question:
                return 'statut'
            elif 'segment' in question:
                return 'segment'
            elif 'famille' in question:
                return 'famille'
        return None
    
    def _route_question(self, question: str, intention: Dict[str, Any]) -> str:
        """Route la question vers la bonne méthode de traitement"""
        
        if intention['type'] == 'conversation':
            return self._handle_conversation(question)
        
        elif intention['type'] == 'count':
            return self._handle_count(question, intention)
        
        elif intention['type'] == 'sum':
            return self._handle_sum(question, intention)
        
        elif intention['type'] == 'average':
            return self._handle_average(question, intention)
        
        elif intention['type'] == 'max':
            return self._handle_max(question, intention)
        
        elif intention['type'] == 'min':
            return self._handle_min(question, intention)
        
        elif intention['type'] == 'list':
            return self._handle_list(question, intention)
        
        elif intention['type'] == 'distribution':
            return self._handle_distribution(question, intention)
        
        elif intention['type'] == 'comparison':
            return self._handle_comparison(question, intention)
        
        elif intention['type'] == 'analysis':
            return self._handle_analysis(question, intention)
        
        elif intention['type'] == 'expiring_lots':
            return self._handle_expiring_lots(question, intention)
        
        else:
            return self._handle_general(question, intention)
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Applique les filtres au DataFrame"""
        filtered_df = df.copy()
        
        for key, value in filters.items():
            if key == 'groupement' and 'groupement' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['groupement'].str.contains(value, case=False, na=False)]
            
            elif key == 'univers' and 'univers' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['univers'].str.contains(value, case=False, na=False)]
            
            elif key == 'statut' and 'statut' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['statut'].str.contains(value, case=False, na=False)]
            
            elif key == 'year' and 'date_limite' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['date_limite'].dt.year == value]
            
            elif key == 'montant_min' and 'montant_global_estime' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['montant_global_estime'] >= value]
            
            elif key == 'montant_max' and 'montant_global_estime' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['montant_global_estime'] <= value]
            
            elif key == 'montant_approx' and 'montant_global_estime' in filtered_df.columns:
                # Rechercher les montants proches (±20%)
                margin = value * 0.2
                filtered_df = filtered_df[
                    (filtered_df['montant_global_estime'] >= value - margin) &
                    (filtered_df['montant_global_estime'] <= value + margin)
                ]
        
        return filtered_df
    
    def _handle_count(self, question: str, intention: Dict[str, Any]) -> str:
        """Gère les questions de comptage"""
        try:
            df = self._apply_filters(self.data, intention['filters'])
            
            if len(df) == 0:
                return "❌ Aucun enregistrement ne correspond à vos critères."
            
            # Si agrégation demandée
            if intention['aggregation']:
                col = intention['aggregation']
                if col in df.columns:
                    counts = df[col].value_counts()
                    
                    response = f"📊 **Répartition par {col}:**\n\n"
                    for val, count in counts.items():
                        if val and str(val).strip():
                            response += f"- **{val}**: {count} lots\n"
                    
                    response += f"\n**Total**: {len(df)} lots"
                return response
            
            # Comptage simple
            filters_desc = self._describe_filters(intention['filters'])
            response = f"📊 **Résultat du comptage**\n\n"
            
            if filters_desc:
                response += f"**Filtres appliqués**: {filters_desc}\n\n"
            
            response += f"**Nombre total de lots**: {len(df)}\n"
            
            # Ajouter des statistiques supplémentaires
            if 'univers' in df.columns:
                top_univers = df['univers'].value_counts().head(3)
                response += f"\n**Top 3 univers**:\n"
                for univ, count in top_univers.items():
                    if univ and str(univ).strip():
                        response += f"- {univ}: {count}\n"
            
                return response
            
        except Exception as e:
            logger.error(f"❌ Erreur comptage: {e}")
            return f"❌ Erreur lors du comptage: {str(e)}"
    
    def _handle_sum(self, question: str, intention: Dict[str, Any]) -> str:
        """Gère les questions de somme"""
        try:
            df = self._apply_filters(self.data, intention['filters'])
            
            if len(df) == 0:
                return "❌ Aucun enregistrement ne correspond à vos critères."
            
            # Déterminer la colonne à sommer
            if 'montant_global_estime' in df.columns:
                col = 'montant_global_estime'
            elif 'montant_global_maxi' in df.columns:
                col = 'montant_global_maxi'
            else:
                return "❌ Aucune colonne de montant trouvée."
            
            total = df[col].sum()
            filters_desc = self._describe_filters(intention['filters'])
            
            response = f"💰 **Analyse financière**\n\n"
            
            if filters_desc:
                response += f"**Filtres appliqués**: {filters_desc}\n\n"
            
            response += f"**Montant total**: {total:,.2f} €\n"
            response += f"**Nombre de lots**: {len(df)}\n"
            
            # Ajouter la répartition si agrégation demandée
            if intention['aggregation']:
                agg_col = intention['aggregation']
                if agg_col in df.columns:
                    grouped = df.groupby(agg_col)[col].sum().sort_values(ascending=False)
                    response += f"\n**Répartition par {agg_col}**:\n"
                    for val, amount in grouped.head(10).items():
                        if val and str(val).strip():
                            response += f"- **{val}**: {amount:,.2f} €\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur somme: {e}")
            return f"❌ Erreur lors du calcul de la somme: {str(e)}"
    
    def _handle_average(self, question: str, intention: Dict[str, Any]) -> str:
        """Gère les questions de moyenne"""
        try:
            df = self._apply_filters(self.data, intention['filters'])
            
            if len(df) == 0:
                return "❌ Aucun enregistrement ne correspond à vos critères."
            
            # Déterminer la colonne pour la moyenne
            if 'montant_global_estime' in df.columns:
                col = 'montant_global_estime'
            elif 'duree_marche' in df.columns and 'durée' in question.lower():
                col = 'duree_marche'
            else:
                col = 'montant_global_estime'
            
            if col not in df.columns:
                return "❌ Colonne non trouvée pour calculer la moyenne."
            
            avg = df[col].mean()
            median = df[col].median()
            filters_desc = self._describe_filters(intention['filters'])
            
            response = f"📊 **Analyse statistique - {col.replace('_', ' ').title()}**\n\n"
            
            if filters_desc:
                response += f"**Filtres appliqués**: {filters_desc}\n\n"
            
            if 'montant' in col:
                response += f"**Moyenne**: {avg:,.2f} €\n"
                response += f"**Médiane**: {median:,.2f} €\n"
            else:
                response += f"**Moyenne**: {avg:.2f}\n"
                response += f"**Médiane**: {median:.2f}\n"
            
            response += f"**Nombre de lots**: {len(df)}\n"
            
            # Ajouter la répartition si agrégation demandée
            if intention['aggregation']:
                agg_col = intention['aggregation']
                if agg_col in df.columns:
                    grouped = df.groupby(agg_col)[col].mean().sort_values(ascending=False)
                    response += f"\n**Moyenne par {agg_col}**:\n"
                    for val, amount in grouped.head(10).items():
                        if val and str(val).strip():
                            if 'montant' in col:
                                response += f"- **{val}**: {amount:,.2f} €\n"
                            else:
                                response += f"- **{val}**: {amount:.2f}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur moyenne: {e}")
            return f"❌ Erreur lors du calcul de la moyenne: {str(e)}"
    
    def _handle_max(self, question: str, intention: Dict[str, Any]) -> str:
        """Gère les questions de maximum"""
        try:
            df = self._apply_filters(self.data, intention['filters'])
            
            if len(df) == 0:
                return "❌ Aucun enregistrement ne correspond à vos critères."
            
            # Déterminer la colonne
            if 'montant_global_estime' in df.columns:
                col = 'montant_global_estime'
            else:
                return "❌ Colonne non trouvée."
            
            max_val = df[col].max()
            max_row = df[df[col] == max_val].iloc[0]
            
            response = f"📈 **Maximum trouvé**\n\n"
            response += f"**Valeur maximum**: {max_val:,.2f} €\n\n"
            response += f"**Détails du lot**:\n"
            
            if 'intitule_lot' in max_row:
                response += f"- **Intitulé**: {max_row['intitule_lot']}\n"
            if 'groupement' in max_row:
                response += f"- **Groupement**: {max_row['groupement']}\n"
            if 'univers' in max_row:
                response += f"- **Univers**: {max_row['univers']}\n"
            if 'reference_procedure' in max_row:
                response += f"- **Référence**: {max_row['reference_procedure']}\n"
            
                return response
            
        except Exception as e:
            logger.error(f"❌ Erreur max: {e}")
            return f"❌ Erreur lors de la recherche du maximum: {str(e)}"
    
    def _handle_min(self, question: str, intention: Dict[str, Any]) -> str:
        """Gère les questions de minimum"""
        try:
            df = self._apply_filters(self.data, intention['filters'])
            df = df[df['montant_global_estime'] > 0]  # Exclure les 0
            
            if len(df) == 0:
                return "❌ Aucun enregistrement ne correspond à vos critères."
            
            # Déterminer la colonne
            if 'montant_global_estime' in df.columns:
                col = 'montant_global_estime'
            else:
                return "❌ Colonne non trouvée."
            
            min_val = df[col].min()
            min_row = df[df[col] == min_val].iloc[0]
            
            response = f"📉 **Minimum trouvé**\n\n"
            response += f"**Valeur minimum**: {min_val:,.2f} €\n\n"
            response += f"**Détails du lot**:\n"
            
            if 'intitule_lot' in min_row:
                response += f"- **Intitulé**: {min_row['intitule_lot']}\n"
            if 'groupement' in min_row:
                response += f"- **Groupement**: {min_row['groupement']}\n"
            if 'univers' in min_row:
                response += f"- **Univers**: {min_row['univers']}\n"
            if 'reference_procedure' in min_row:
                response += f"- **Référence**: {min_row['reference_procedure']}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur min: {e}")
            return f"❌ Erreur lors de la recherche du minimum: {str(e)}"
    
    def _handle_list(self, question: str, intention: Dict[str, Any]) -> str:
        """Gère les questions de liste/affichage et de recherche"""
        try:
            # Vérifier si c'est une recherche spécifique par référence ou intitulé
            if self._is_search_question(question):
                search_result = self._handle_specific_search(question, intention)
                if search_result:
                    return search_result
            
            df = self._apply_filters(self.data, intention['filters'])
            
            if len(df) == 0:
                return "❌ Aucun enregistrement ne correspond à vos critères."
            
            filters_desc = self._describe_filters(intention['filters'])
            
            # Stocker les données pour l'affichage en tableau
            self._last_table_data = self._prepare_table_data(df)
            
            # Préparer les données pour les graphiques
            self._last_graph_data = self._prepare_graph_data(df, 'list')
            logger.info(f"📊 Graphiques préparés: {len(self._last_graph_data.get('data', {}))} types disponibles")
            
            response = f"📋 **Liste des résultats**\n\n"
            
            if filters_desc:
                response += f"**Filtres appliqués**: {filters_desc}\n"
            
            response += f"**Nombre de résultats**: {len(df)}\n\n"
            
            # Ajouter un indicateur spécial pour l'affichage en tableau
            response += "```TABLEAU_STREAMLIT```\n\n"
            
            # Ajouter un indicateur pour les graphiques
            response += "```GRAPHIQUES_STREAMLIT```\n\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur liste: {e}")
            return f"❌ Erreur lors de l'affichage de la liste: {str(e)}"
    
    def _handle_specific_search(self, question: str, intention: Dict[str, Any]) -> Optional[str]:
        """Gère les recherches spécifiques par référence ou intitulé"""
        try:
            # Extraire le terme de recherche
            search_term = self._extract_search_term(question)
            if not search_term:
                return None
            
            # Rechercher dans les colonnes pertinentes
            search_columns = ['reference_procedure', 'intitule_lot', 'intitule_procedure']
            results = []
            
            for col in search_columns:
                if col in self.data.columns:
                    # Recherche insensible à la casse
                    mask = self.data[col].astype(str).str.contains(search_term, case=False, na=False)
                    col_results = self.data[mask]
                    if not col_results.empty:
                        results.append((col, col_results))
            
            if not results:
                return f"❌ Aucun résultat trouvé pour '{search_term}'"
            
            # Combiner tous les résultats
            all_results = pd.concat([df for _, df in results], ignore_index=True)
            all_results = all_results.drop_duplicates()
            
            # Stocker les données pour l'affichage en tableau
            self._last_table_data = self._prepare_table_data(all_results)
            
            # Préparer les données pour les graphiques
            self._last_graph_data = self._prepare_graph_data(all_results, 'search')
            logger.info(f"📊 Graphiques préparés: {len(self._last_graph_data.get('data', {}))} types disponibles")
            
            response = f"🔍 **Résultats de recherche pour '{search_term}'**\n\n"
            
            # Afficher les colonnes où le terme a été trouvé
            found_in = []
            for col, df in results:
                if not df.empty:
                    col_name = col.replace('_', ' ').title()
                    found_in.append(f"{col_name} ({len(df)} résultats)")
            
            response += f"**Trouvé dans**: {', '.join(found_in)}\n"
            response += f"**Total de résultats**: {len(all_results)}\n\n"
            
            # Ajouter un indicateur spécial pour l'affichage en tableau
            response += "```TABLEAU_STREAMLIT```\n\n"
            
            # Ajouter un indicateur pour les graphiques
            response += "```GRAPHIQUES_STREAMLIT```\n\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche spécifique: {e}")
            return None
    
    def _extract_search_term(self, question: str) -> Optional[str]:
        """Extrait le terme de recherche de la question"""
        try:
            question_lower = question.lower()
            
            # Mots-clés à ignorer
            ignore_words = ['cherche', 'trouve', 'recherche', 'rechercher', 'pour', 'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'dans', 'avec']
            
            # Diviser la question en mots
            words = question_lower.split()
            
            # Trouver le mot-clé de recherche
            search_keyword = None
            for keyword in ['cherche', 'trouve', 'recherche', 'rechercher']:
                if keyword in words:
                    search_keyword = keyword
                    break
            
            if not search_keyword:
                return None
            
            # Extraire les mots après le mot-clé de recherche
            keyword_index = words.index(search_keyword)
            search_words = words[keyword_index + 1:]
            
            # Filtrer les mots à ignorer
            search_words = [word for word in search_words if word not in ignore_words]
            
            if not search_words:
                return None
            
            # Rejoindre les mots pour former le terme de recherche
            search_term = ' '.join(search_words)
            
            # Nettoyer le terme
            search_term = search_term.strip('.,!?')
            
            return search_term if search_term else None
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction terme recherche: {e}")
            return None
    
    def _is_search_question(self, question: str) -> bool:
        """Détermine si c'est une question de recherche spécifique"""
        question_lower = question.lower()
        
        # Mots-clés de recherche
        search_keywords = ['cherche', 'trouve', 'recherche', 'rechercher']
        
        # Vérifier si la question contient un mot-clé de recherche
        if not any(keyword in question_lower for keyword in search_keywords):
            return False
        
        # Extraire le terme de recherche
        search_term = self._extract_search_term(question)
        if not search_term:
            return False
        
        # Vérifier si c'est une référence de procédure (format: 2024-R059, 24AOOSIA, etc.)
        ref_pattern = r'^\d{4}-[A-Z]\d{2,3}$|^\d{2}[A-Z]{2,}\d{2,}$|^[A-Z]\d{2,}$'
        if re.match(ref_pattern, search_term.upper()):
            return True
        
        # Vérifier si c'est un terme de recherche court (probablement une recherche spécifique)
        if len(search_term.split()) <= 3:
            return True
        
        return False
    
    def _should_skip_filters_for_search(self, question: str) -> bool:
        """Détermine si on doit ignorer les filtres généraux pour une recherche spécifique"""
        return self._is_search_question(question)
    
    def _prepare_table_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prépare les données pour l'affichage en tableau"""
        try:
            # Sélectionner les colonnes importantes
            important_cols = ['intitule_lot', 'groupement', 'univers', 'montant_global_estime', 
                            'statut', 'reference_procedure', 'date_limite', 'intitule_procedure']
            
            cols_to_show = [col for col in important_cols if col in df.columns]
            display_df = df[cols_to_show].copy()
            
            # Renommer les colonnes pour l'affichage
            display_df.columns = [col.replace('_', ' ').title() for col in display_df.columns]
            
            # Formater les montants
            if 'Montant Global Estime' in display_df.columns:
                display_df['Montant Global Estime'] = display_df['Montant Global Estime'].apply(
                    lambda x: f"{x:,.2f} €" if pd.notna(x) and x != 0 else "N/A"
                )
            
            # Formater les dates
            if 'Date Limite' in display_df.columns:
                display_df['Date Limite'] = display_df['Date Limite'].apply(
                    lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else "N/A"
                )
            
            return display_df
            
        except Exception as e:
            logger.error(f"❌ Erreur préparation tableau: {e}")
            return df.head(10)
    
    def get_last_table_data(self) -> Optional[pd.DataFrame]:
        """Retourne les dernières données préparées pour l'affichage en tableau"""
        return getattr(self, '_last_table_data', None)
    
    def get_last_graph_data(self) -> Optional[Dict[str, Any]]:
        """Retourne les dernières données préparées pour l'affichage de graphiques"""
        return getattr(self, '_last_graph_data', None)
    
    def _prepare_graph_data(self, df: pd.DataFrame, graph_type: str = 'distribution') -> Dict[str, Any]:
        """Prépare les données pour différents types de graphiques"""
        try:
            graph_data = {
                'type': graph_type,
                'data': {}
            }
            
            # Graphique de répartition par univers
            if 'univers' in df.columns:
                univers_dist = df['univers'].value_counts()
                graph_data['data']['univers'] = {
                    'labels': univers_dist.index.tolist(),
                    'values': univers_dist.values.tolist(),
                    'title': 'Répartition par Univers'
                }
            
            # Graphique de répartition par groupement
            if 'groupement' in df.columns:
                groupement_dist = df['groupement'].value_counts()
                graph_data['data']['groupement'] = {
                    'labels': groupement_dist.index.tolist(),
                    'values': groupement_dist.values.tolist(),
                    'title': 'Répartition par Groupement'
                }
            
            # Graphique de répartition par statut
            if 'statut' in df.columns:
                statut_dist = df['statut'].value_counts()
                graph_data['data']['statut'] = {
                    'labels': statut_dist.index.tolist(),
                    'values': statut_dist.values.tolist(),
                    'title': 'Répartition par Statut'
                }
            
            # Graphique de distribution des montants (histogramme)
            if 'montant_global_estime' in df.columns:
                montants = df['montant_global_estime'].dropna()
                if len(montants) > 0:
                    # Créer des bins pour l'histogramme
                    max_montant = montants.max()
                    if max_montant > 0:
                        bins = 20
                        graph_data['data']['montants'] = {
                            'values': montants.tolist(),
                            'bins': bins,
                            'title': 'Distribution des Montants',
                            'xlabel': 'Montant (€)',
                            'ylabel': 'Nombre de lots'
                        }
            
            return graph_data
            
        except Exception as e:
            logger.error(f"❌ Erreur préparation graphiques: {e}")
            return {'type': graph_type, 'data': {}}
    
    def _prepare_expiring_graph_data(self, expiring_lots: pd.DataFrame) -> Dict[str, Any]:
        """Prépare les données de graphiques pour les lots expirants"""
        try:
            graph_data = {
                'type': 'expiring_lots',
                'data': {}
            }
            
            # Graphique par niveau d'urgence
            urgent_count = len(expiring_lots[expiring_lots['jours_restants'] <= 30])
            warning_count = len(expiring_lots[(expiring_lots['jours_restants'] > 30) & (expiring_lots['jours_restants'] <= 60)])
            normal_count = len(expiring_lots[expiring_lots['jours_restants'] > 60])
            
            graph_data['data']['urgence'] = {
                'labels': ['🔴 Urgent (≤30j)', '🟠 Attention (31-60j)', '🟡 À surveiller (>60j)'],
                'values': [urgent_count, warning_count, normal_count],
                'title': 'Répartition par Niveau d\'Urgence'
            }
            
            # Graphique timeline (dates d'expiration)
            if 'date_fin' in expiring_lots.columns:
                expiring_lots_sorted = expiring_lots.sort_values('date_fin')
                graph_data['data']['timeline'] = {
                    'dates': expiring_lots_sorted['date_fin'].dt.strftime('%Y-%m-%d').tolist(),
                    'jours_restants': expiring_lots_sorted['jours_restants'].tolist(),
                    'montants': expiring_lots_sorted['montant_global_estime'].fillna(0).tolist(),
                    'title': 'Timeline des Expirations',
                    'xlabel': 'Date de fin',
                    'ylabel': 'Jours restants'
                }
            
            # Graphique par univers pour les lots expirants
            if 'univers' in expiring_lots.columns:
                univers_dist = expiring_lots['univers'].value_counts()
                graph_data['data']['univers'] = {
                    'labels': univers_dist.index.tolist(),
                    'values': univers_dist.values.tolist(),
                    'title': 'Répartition par Univers (Lots Expirants)'
                }
            
            # Graphique par groupement pour les lots expirants
            if 'groupement' in expiring_lots.columns:
                groupement_dist = expiring_lots['groupement'].value_counts()
                graph_data['data']['groupement'] = {
                    'labels': groupement_dist.index.tolist(),
                    'values': groupement_dist.values.tolist(),
                    'title': 'Répartition par Groupement (Lots Expirants)'
                }
            
            return graph_data
            
        except Exception as e:
            logger.error(f"❌ Erreur préparation graphiques expirants: {e}")
            return {'type': 'expiring_lots', 'data': {}}
    
    def _handle_distribution(self, question: str, intention: Dict[str, Any]) -> str:
        """Gère les questions de répartition/distribution"""
        try:
            df = self._apply_filters(self.data, intention['filters'])
            
            if len(df) == 0:
                return "❌ Aucun enregistrement ne correspond à vos critères."
            
            # Déterminer la colonne de regroupement
            group_col = intention['aggregation']
            if not group_col:
                # Essayer de détecter automatiquement
                if 'univers' in question.lower():
                    group_col = 'univers'
                elif 'groupement' in question.lower():
                    group_col = 'groupement'
                elif 'statut' in question.lower():
                    group_col = 'statut'
                elif 'segment' in question.lower():
                    group_col = 'segment'
                else:
                    group_col = 'univers'  # Par défaut
            
            if group_col not in df.columns:
                return f"❌ Colonne '{group_col}' non trouvée."
            
            # Calcul de la distribution
            distribution = df[group_col].value_counts()
            total = len(df)
            
            response = f"📊 **Répartition par {group_col.replace('_', ' ').title()}**\n\n"
            response += f"**Total**: {total} lots\n\n"
            
            for val, count in distribution.items():
                if val and str(val).strip():
                    percentage = (count / total) * 100
                    response += f"- **{val}**: {count} lots ({percentage:.1f}%)\n"
            
            # Ajouter des statistiques de montant si disponible
            if 'montant_global_estime' in df.columns:
                response += f"\n**Montants par {group_col.replace('_', ' ').title()}**:\n\n"
                grouped_amounts = df.groupby(group_col)['montant_global_estime'].agg(['sum', 'mean', 'count'])
                
                for val, row in grouped_amounts.iterrows():
                    if val and str(val).strip():
                        response += f"- **{val}**:\n"
                        response += f"  - Total: {row['sum']:,.2f} €\n"
                        response += f"  - Moyenne: {row['mean']:,.2f} €\n"
                        response += f"  - Lots: {int(row['count'])}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur distribution: {e}")
            return f"❌ Erreur lors du calcul de la distribution: {str(e)}"
    
    def _handle_comparison(self, question: str, intention: Dict[str, Any]) -> str:
        """Gère les questions de comparaison"""
        try:
            # Comparaison entre groupements ou univers
            compare_col = None
            if 'groupement' in question.lower():
                compare_col = 'groupement'
            elif 'univers' in question.lower():
                compare_col = 'univers'
            
            if not compare_col or compare_col not in self.data.columns:
                return "❌ Impossible de déterminer quoi comparer."
            
            # Statistiques par groupe
            grouped = self.data.groupby(compare_col).agg({
                'montant_global_estime': ['sum', 'mean', 'count'],
                'id': 'count'
            }).round(2)
            
            grouped.columns = ['Montant Total', 'Montant Moyen', 'Count_montant', 'Nombre Lots']
            grouped = grouped.sort_values('Montant Total', ascending=False)
            
            response = f"⚖️ **Comparaison par {compare_col.replace('_', ' ').title()}**\n\n"
            
            for idx, row in grouped.iterrows():
                if idx and str(idx).strip():
                    response += f"**{idx}**:\n"
                    response += f"  - Montant total: {row['Montant Total']:,.2f} €\n"
                    response += f"  - Montant moyen: {row['Montant Moyen']:,.2f} €\n"
                    response += f"  - Nombre de lots: {int(row['Nombre Lots'])}\n\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur comparaison: {e}")
            return f"❌ Erreur lors de la comparaison: {str(e)}"
    
    def _handle_analysis(self, question: str, intention: Dict[str, Any]) -> str:
        """Gère les demandes d'analyse globale"""
        try:
            df = self._apply_filters(self.data, intention['filters'])
            
            if len(df) == 0:
                return "❌ Aucun enregistrement ne correspond à vos critères."
            
            response = f"📊 **Analyse Complète**\n\n"
            
            # Statistiques générales
            response += f"### 📈 Vue d'ensemble\n"
            response += f"- **Nombre total de lots**: {len(df)}\n"
            
            if 'montant_global_estime' in df.columns:
                total_montant = df['montant_global_estime'].sum()
                avg_montant = df['montant_global_estime'].mean()
                response += f"- **Montant total**: {total_montant:,.2f} €\n"
                response += f"- **Montant moyen**: {avg_montant:,.2f} €\n"
            
            # Par univers
            if 'univers' in df.columns:
                response += f"\n### 🌍 Par Univers\n"
                univers_dist = df['univers'].value_counts().head(5)
                for univ, count in univers_dist.items():
                    if univ and str(univ).strip():
                        response += f"- **{univ}**: {count} lots\n"
            
            # Par groupement
            if 'groupement' in df.columns:
                response += f"\n### 🏢 Par Groupement\n"
                groupe_dist = df['groupement'].value_counts().head(5)
                for grp, count in groupe_dist.items():
                    if grp and str(grp).strip():
                        response += f"- **{grp}**: {count} lots\n"
            
            # Par statut
            if 'statut' in df.columns:
                response += f"\n### ⚡ Par Statut\n"
                statut_dist = df['statut'].value_counts()
                for stat, count in statut_dist.items():
                    if stat and str(stat).strip():
                        response += f"- **{stat}**: {count} lots\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse: {e}")
            return f"❌ Erreur lors de l'analyse: {str(e)}"
    
    def _handle_expiring_lots(self, question: str, intention: Dict[str, Any]) -> str:
        """Gère les questions sur les lots dont la fin de marché approche"""
        try:
            from datetime import timedelta
            
            # Appliquer les filtres de base
            df = self._apply_filters(self.data, intention['filters'])
            
            if len(df) == 0:
                return "❌ Aucun enregistrement ne correspond à vos critères."
            
            # Déterminer la période d'alerte (par défaut 3 mois)
            question_lower = question.lower()
            
            # Extraire le nombre de mois si mentionné
            import re
            months_match = re.search(r'(\d+)\s*mois', question_lower)
            if months_match:
                months_threshold = int(months_match.group(1))
            elif 'semaine' in question_lower:
                weeks_match = re.search(r'(\d+)\s*semaine', question_lower)
                months_threshold = int(weeks_match.group(1)) / 4 if weeks_match else 0.25
            elif 'jour' in question_lower:
                days_match = re.search(r'(\d+)\s*jour', question_lower)
                months_threshold = int(days_match.group(1)) / 30 if days_match else 0.1
            else:
                months_threshold = 3  # Par défaut : 3 mois
            
            # Calculer la date limite
            today = pd.Timestamp.now()
            threshold_date = today + timedelta(days=months_threshold * 30)
            
            # Diagnostic des colonnes de dates disponibles
            date_columns = ['fin_avec_reconduction', 'fin_sans_reconduction', 'date_limite', 'date_attribution']
            available_date_cols = [col for col in date_columns if col in df.columns]
            
            # Analyser les données de dates
            date_analysis = {}
            for col in available_date_cols:
                non_null_count = df[col].notna().sum()
                date_analysis[col] = {
                    'total': len(df),
                    'non_null': non_null_count,
                    'null_percent': (1 - non_null_count / len(df)) * 100 if len(df) > 0 else 100
                }
            
            # Utiliser la colonne avec le plus de données valides
            best_date_col = None
            max_valid_dates = 0
            
            for col in available_date_cols:
                if date_analysis[col]['non_null'] > max_valid_dates:
                    max_valid_dates = date_analysis[col]['non_null']
                    best_date_col = col
            
            if not best_date_col or max_valid_dates == 0:
                # Aucune colonne de date valide, utiliser date_limite comme fallback
                if 'date_limite' in df.columns:
                    best_date_col = 'date_limite'
                else:
                    return f"""❌ **Problème de données détecté**

**Diagnostic des colonnes de dates :**
{chr(10).join([f"- {col}: {info['non_null']}/{info['total']} ({info['null_percent']:.1f}% vides)" for col, info in date_analysis.items()])}

**Recommandations :**
1. Vérifiez que les colonnes 'fin_avec_reconduction' et 'fin_sans_reconduction' contiennent des dates
2. Assurez-vous que les dates sont au format YYYY-MM-DD
3. Importez des données avec des dates de fin de marché valides

**Colonnes disponibles :** {', '.join(df.columns.tolist())}"""
            
            # Convertir la colonne de date en datetime
            df_temp = df.copy()
            df_temp[best_date_col] = pd.to_datetime(df_temp[best_date_col], errors='coerce')
            
            # Filtrer les lots valides (avec dates non nulles)
            valid_dates_mask = df_temp[best_date_col].notna()
            df_with_dates = df_temp[valid_dates_mask].copy()
            
            if len(df_with_dates) == 0:
                return f"""❌ **Aucune date valide trouvée**

**Colonne analysée :** {best_date_col}
**Total de lots :** {len(df)}
**Lots avec dates valides :** 0

**Exemples de données dans cette colonne :**
{df[best_date_col].head(10).tolist()}

**Vérifiez le format des dates dans votre base de données.**"""
            
            # Filtrer les lots qui expirent bientôt
            expiring_mask = (df_with_dates[best_date_col] >= today) & (df_with_dates[best_date_col] <= threshold_date)
            expiring_lots = df_with_dates[expiring_mask].copy()
            
            if len(expiring_lots) == 0:
                filters_desc = self._describe_filters(intention['filters'])
                response = f"✅ **Bonne nouvelle !**\n\n"
                if filters_desc:
                    response += f"**Filtres appliqués**: {filters_desc}\n\n"
                response += f"Aucun lot ne se termine dans les **{months_threshold:.0f} mois** à venir.\n\n"
                response += f"📊 **Statistiques :**\n"
                response += f"- Total de lots analysés: {len(df)}\n"
                response += f"- Lots avec dates valides: {len(df_with_dates)}\n"
                response += f"- Colonne utilisée: {best_date_col}\n"
                response += f"- Période d'alerte: {today.strftime('%d/%m/%Y')} → {threshold_date.strftime('%d/%m/%Y')}"
                return response
            
            # Ajouter les colonnes calculées
            expiring_lots['jours_restants'] = (expiring_lots[best_date_col] - today).dt.days
            expiring_lots['date_fin'] = expiring_lots[best_date_col]
            expiring_lots['type_fin'] = best_date_col.replace('fin_', '').replace('_', ' ').title()
            
            # Trier par jours restants
            expiring_lots = expiring_lots.sort_values('jours_restants')
            
            # Préparer le tableau pour affichage
            self._last_table_data = self._prepare_expiring_table_data(expiring_lots)
            
            # Préparer les données pour les graphiques
            self._last_graph_data = self._prepare_expiring_graph_data(expiring_lots)
            
            # Créer la réponse
            filters_desc = self._describe_filters(intention['filters'])
            
            response = f"⚠️ **Lots dont la fin de marché approche**\n\n"
            
            if filters_desc:
                response += f"**Filtres appliqués**: {filters_desc}\n"
            
            response += f"**Période d'alerte**: {months_threshold:.0f} mois ({int(months_threshold * 30)} jours)\n"
            response += f"**Colonne utilisée**: {best_date_col}\n"
            response += f"**Nombre de lots concernés**: {len(expiring_lots)}\n\n"
            
            # Catégoriser par urgence
            urgent = expiring_lots[expiring_lots['jours_restants'] <= 30]
            warning = expiring_lots[(expiring_lots['jours_restants'] > 30) & (expiring_lots['jours_restants'] <= 60)]
            normal = expiring_lots[expiring_lots['jours_restants'] > 60]
            
            if len(urgent) > 0:
                response += f"🔴 **Urgent** (≤ 30 jours): {len(urgent)} lots\n"
            if len(warning) > 0:
                response += f"🟠 **Attention** (31-60 jours): {len(warning)} lots\n"
            if len(normal) > 0:
                response += f"🟡 **À surveiller** (> 60 jours): {len(normal)} lots\n"
            
            response += "\n```TABLEAU_STREAMLIT```\n\n"
            
            # Ajouter un indicateur pour les graphiques
            response += "```GRAPHIQUES_STREAMLIT```\n\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur gestion lots expirants: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Erreur lors de la recherche des lots expirants: {str(e)}"
    
    def _prepare_expiring_table_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prépare les données des lots expirants pour l'affichage en tableau"""
        try:
            # Sélectionner les colonnes importantes
            important_cols = ['intitule_lot', 'groupement', 'univers', 'montant_global_estime', 
                            'statut', 'reference_procedure', 'date_fin', 'jours_restants', 'type_fin']
            
            cols_to_show = [col for col in important_cols if col in df.columns]
            display_df = df[cols_to_show].copy()
            
            # Renommer les colonnes pour l'affichage
            column_rename = {
                'intitule_lot': 'Intitulé Lot',
                'groupement': 'Groupement',
                'univers': 'Univers',
                'montant_global_estime': 'Montant Estimé',
                'statut': 'Statut',
                'reference_procedure': 'Référence',
                'date_fin': 'Date de Fin',
                'jours_restants': 'Jours Restants',
                'type_fin': 'Type de Fin'
            }
            
            display_df = display_df.rename(columns=column_rename)
            
            # Formater les montants
            if 'Montant Estimé' in display_df.columns:
                display_df['Montant Estimé'] = display_df['Montant Estimé'].apply(
                    lambda x: f"{x:,.2f} €" if pd.notna(x) and x != 0 else "N/A"
                )
            
            # Formater les dates
            if 'Date de Fin' in display_df.columns:
                display_df['Date de Fin'] = display_df['Date de Fin'].apply(
                    lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else "N/A"
                )
            
            # Ajouter un indicateur d'urgence
            if 'Jours Restants' in display_df.columns:
                display_df['Urgence'] = display_df['Jours Restants'].apply(
                    lambda x: "🔴 Urgent" if x <= 30 else "🟠 Attention" if x <= 60 else "🟡 À surveiller"
                )
                display_df['Jours Restants'] = display_df['Jours Restants'].apply(
                    lambda x: f"J-{int(x)}" if pd.notna(x) else "N/A"
                )
            
            return display_df
            
        except Exception as e:
            logger.error(f"❌ Erreur préparation tableau expirants: {e}")
            return df.head(10)
    
    def _handle_conversation(self, question: str) -> str:
        """Gère les questions conversationnelles"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['bonjour', 'salut', 'hello', 'hi']):
            return """👋 **Bonjour ! Je suis votre assistant IA avancé pour la veille concurrentielle.**

Je peux répondre à toutes vos questions sur la base de données :

🔢 **Statistiques**:
- "Combien de lots par univers ?"
- "Quelle est la somme totale des budgets ?"
- "Quel est le montant moyen pour le RESAH ?"

📋 **Listes et filtres**:
- "Montre-moi les lots du RESAH en informatique"
- "Liste les lots de plus de 100 000 €"
- "Affiche les appels d'offres en cours"

⏰ **Fins de marché**:
- "Quels lots se terminent bientôt ?"
- "Montre les marchés qui expirent dans 6 mois"
- "Lots dont la fin de marché approche"
- "Affiche les lots du RESAH qui se terminent bientôt"

📊 **Analyses**:
- "Analyse la répartition par groupement"
- "Compare les univers"
- "Donne-moi les statistiques complètes"

⚖️ **Comparaisons**:
- "Compare RESAH et UNIHA"
- "Quelle est la différence entre les univers ?"

🔗 **Conversations contextuelles**:
- Posez une première question, puis enchaînez !
- "Montre les lots du RESAH" → "Et pour l'UNIHA ?"
- "Combien de lots en informatique ?" → "Et en médical ?"

N'hésitez pas à poser n'importe quelle question ! 😊"""
        
        elif 'merci' in question_lower:
            return "😊 **Je vous en prie !** N'hésitez pas si vous avez d'autres questions sur la base de données."
        
        elif any(word in question_lower for word in ['au revoir', 'bye', 'adieu']):
            return "👋 **Au revoir !** À bientôt pour d'autres analyses !"
        
        elif any(phrase in question_lower for phrase in ['historique', 'histoire', 'conversation précédente', 'ce qu', 'on a dit']):
            return self.display_conversation_summary()
        
        elif any(phrase in question_lower for phrase in ['diagnostic', 'diagnostique', 'état des données', 'qualité des données', 'problème de données']):
            return self._handle_data_diagnostic(question)
        
        else:
            return self._handle_general(question, {})
    
    def _handle_general(self, question: str, intention: Dict[str, Any]) -> str:
        """Gère les questions générales ou non reconnues"""
        return f"""🤔 **Je ne suis pas certain de bien comprendre votre question.**

**Voici quelques exemples de questions que vous pouvez poser**:

📊 **Statistiques**:
- "Combien y a-t-il de lots au total ?"
- "Quelle est la somme des budgets ?"
- "Quel est le montant moyen par univers ?"

🔍 **Recherche et filtrage**:
- "Montre-moi les lots du RESAH"
- "Liste les lots en informatique"
- "Affiche les lots de plus de 100 000 €"

⏰ **Fins de marché**:
- "Quels lots se terminent bientôt ?"
- "Montre les marchés qui expirent dans 6 mois"
- "Affiche les lots du RESAH qui se terminent bientôt"

📈 **Analyses**:
- "Répartition par groupement"
- "Compare les univers"
- "Analyse complète des données"

💡 **Astuce**: Essayez d'être plus précis dans votre question !

*Votre question*: "{question}"
"""
    
    def _describe_filters(self, filters: Dict[str, Any]) -> str:
        """Décrit les filtres appliqués en langage naturel"""
        if not filters:
            return ""
        
        descriptions = []
        
        for key, value in filters.items():
            if key == 'groupement':
                descriptions.append(f"Groupement: {value}")
            elif key == 'univers':
                descriptions.append(f"Univers: {value}")
            elif key == 'statut':
                descriptions.append(f"Statut: {value}")
            elif key == 'year':
                descriptions.append(f"Année: {value}")
            elif key == 'montant_min':
                descriptions.append(f"Montant ≥ {value:,.0f} €")
            elif key == 'montant_max':
                descriptions.append(f"Montant ≤ {value:,.0f} €")
            elif key == 'montant_approx':
                descriptions.append(f"Montant ≈ {value:,.0f} €")
        
        return ", ".join(descriptions)
    
    def _update_average_response_time(self, elapsed_time: float):
        """Met à jour le temps de réponse moyen"""
        total = self.performance_metrics['total_questions']
        current_avg = self.performance_metrics['average_response_time']
        
        if total == 1:
            self.performance_metrics['average_response_time'] = elapsed_time
        else:
            self.performance_metrics['average_response_time'] = (
                (current_avg * (total - 1) + elapsed_time) / total
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de performance"""
        metrics = self.performance_metrics.copy()
        
        if metrics['total_questions'] > 0:
            metrics['success_rate'] = metrics['successful_answers'] / metrics['total_questions']
            metrics['cache_hit_rate'] = metrics['cache_hits'] / (metrics['cache_hits'] + metrics['cache_misses']) if (metrics['cache_hits'] + metrics['cache_misses']) > 0 else 0
        else:
            metrics['success_rate'] = 0
            metrics['cache_hit_rate'] = 0
        
        return metrics
    
    def clear_conversation_memory(self):
        """Efface l'historique de conversation et le cache"""
        self.conversation_history = []
        self.cache = {}
        logger.info("🗑️ Mémoire de conversation effacée")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Retourne l'historique de conversation"""
        return self.conversation_history
    
    def display_conversation_summary(self) -> str:
        """Affiche un résumé de l'historique de conversation"""
        if not self.conversation_history:
            return "📭 Aucune conversation enregistrée."
        
        response = f"📜 **Historique de conversation** ({len(self.conversation_history)} échanges)\n\n"
        
        for i, exchange in enumerate(self.conversation_history[-10:], 1):  # Derniers 10 échanges
            timestamp = exchange.get('timestamp', datetime.now()).strftime('%H:%M:%S')
            question = exchange.get('question', '')
            is_contextual = exchange.get('is_contextual', False)
            
            contextual_icon = "🔗" if is_contextual else "💬"
            response += f"{contextual_icon} **[{timestamp}]** {question}\n"
        
        if len(self.conversation_history) > 10:
            response += f"\n*... et {len(self.conversation_history) - 10} échanges plus anciens*"
        
        return response
    
    def _handle_data_diagnostic(self, question: str) -> str:
        """Gère les demandes de diagnostic des données"""
        try:
            if not self.initialized or self.data is None:
                return "❌ Aucune donnée chargée pour le diagnostic."
            
            response = "🔍 **Diagnostic des données**\n\n"
            
            # Informations générales
            response += f"**Total d'enregistrements**: {len(self.data)}\n"
            response += f"**Nombre de colonnes**: {len(self.data.columns)}\n\n"
            
            # Analyse des colonnes de dates
            date_columns = ['fin_avec_reconduction', 'fin_sans_reconduction', 'date_limite', 'date_attribution']
            available_date_cols = [col for col in date_columns if col in self.data.columns]
            
            response += "**📅 Analyse des colonnes de dates :**\n"
            for col in available_date_cols:
                non_null = self.data[col].notna().sum()
                null_percent = (1 - non_null / len(self.data)) * 100 if len(self.data) > 0 else 100
                response += f"- **{col}**: {non_null}/{len(self.data)} ({null_percent:.1f}% vides)\n"
            
            if not available_date_cols:
                response += "- ❌ Aucune colonne de date trouvée\n"
            
            response += "\n**📊 Exemples de données de dates :**\n"
            for col in available_date_cols[:2]:  # Limiter à 2 colonnes
                sample_data = self.data[col].dropna().head(5).tolist()
                response += f"- **{col}**: {sample_data}\n"
            
            # Analyse des colonnes importantes
            important_cols = ['groupement', 'univers', 'statut', 'montant_global_estime']
            response += "\n**📋 Analyse des colonnes importantes :**\n"
            for col in important_cols:
                if col in self.data.columns:
                    non_null = self.data[col].notna().sum()
                    null_percent = (1 - non_null / len(self.data)) * 100 if len(self.data) > 0 else 100
                    unique_vals = self.data[col].nunique()
                    response += f"- **{col}**: {non_null}/{len(self.data)} ({null_percent:.1f}% vides), {unique_vals} valeurs uniques\n"
                else:
                    response += f"- **{col}**: ❌ Colonne manquante\n"
            
            # Recommandations
            response += "\n**💡 Recommandations :**\n"
            
            if not available_date_cols:
                response += "- ❌ **CRITIQUE**: Aucune colonne de date trouvée. Ajoutez des colonnes de dates valides.\n"
            else:
                best_date_col = None
                max_valid = 0
                for col in available_date_cols:
                    valid_count = self.data[col].notna().sum()
                    if valid_count > max_valid:
                        max_valid = valid_count
                        best_date_col = col
                
                if best_date_col and max_valid > 0:
                    response += f"- ✅ Colonne de date recommandée: **{best_date_col}** ({max_valid} dates valides)\n"
                else:
                    response += "- ❌ Aucune colonne de date avec des données valides\n"
            
            # Vérifier les montants
            if 'montant_global_estime' in self.data.columns:
                montant_non_null = self.data['montant_global_estime'].notna().sum()
                if montant_non_null == 0:
                    response += "- ⚠️ Colonne 'montant_global_estime' vide - ajoutez des montants\n"
                else:
                    response += f"- ✅ Montants disponibles: {montant_non_null} enregistrements\n"
            
            # Vérifier les groupements
            if 'groupement' in self.data.columns:
                groupements = self.data['groupement'].value_counts()
                response += f"- ✅ Groupements trouvés: {', '.join(groupements.head(3).index.tolist())}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur diagnostic: {e}")
            return f"❌ Erreur lors du diagnostic: {str(e)}"
    
    def get_model_status(self) -> Dict[str, bool]:
        """Retourne le statut des modèles (pour compatibilité avec l'app)"""
        return {
            'bert_model': self.initialized,
            'embedding_model': self.initialized,
            'nlp_model': self.initialized,
            'classifier': self.initialized
        }
