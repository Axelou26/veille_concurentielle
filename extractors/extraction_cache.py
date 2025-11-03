"""
💾 Cache Intelligent pour Extractions
=====================================

Cache basé sur hash pour éviter les extractions répétées de documents similaires.
"""

import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ExtractionCache:
    """
    Cache intelligent basé sur hash du document
    
    Utilise un hash du contenu pour identifier les documents similaires
    et éviter les extractions répétées.
    """
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        """
        Initialise le cache
        
        Args:
            max_size: Taille maximale du cache
            ttl_hours: Durée de vie des entrées en heures (Time To Live)
        """
        self.cache = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
    
    def get_cache_key(self, file_content: bytes, file_name: str = None) -> str:
        """
        Génère une clé de cache depuis le contenu du fichier
        
        Args:
            file_content: Contenu du fichier en bytes
            file_name: Nom du fichier (optionnel, pour debug)
            
        Returns:
            Clé de cache (hash)
        """
        try:
            # Utiliser le premier 2KB + dernier 2KB + taille pour un hash rapide
            # Cela permet d'identifier les fichiers similaires même avec de petites différences
            sample_size = min(2048, len(file_content))
            sample = file_content[:sample_size] + file_content[-sample_size:] if len(file_content) > sample_size * 2 else file_content
            size_bytes = len(file_content).to_bytes(8, 'big')
            
            hash_input = sample + size_bytes
            if file_name:
                hash_input += file_name.encode('utf-8')
            
            cache_key = hashlib.md5(hash_input).hexdigest()
            return cache_key
            
        except Exception as e:
            logger.error(f"Erreur génération clé cache: {e}")
            # Fallback: utiliser juste le hash complet (plus lent)
            return hashlib.md5(file_content[:10000]).hexdigest()  # Limiter à 10KB pour performance
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une extraction depuis le cache
        
        Args:
            cache_key: Clé de cache
            
        Returns:
            Données extraites ou None si non trouvé/expiré
        """
        self.stats['total_requests'] += 1
        
        if cache_key not in self.cache:
            self.stats['misses'] += 1
            return None
        
        entry = self.cache[cache_key]
        
        # Vérifier si l'entrée a expiré
        if datetime.now() - entry['timestamp'] > self.ttl:
            # Supprimer l'entrée expirée
            del self.cache[cache_key]
            self.stats['misses'] += 1
            logger.debug(f"Cache expiré pour la clé: {cache_key[:8]}...")
            return None
        
        self.stats['hits'] += 1
        logger.debug(f"Cache hit pour la clé: {cache_key[:8]}...")
        return entry['data']
    
    def set(self, cache_key: str, data: Dict[str, Any]):
        """
        Sauvegarde une extraction dans le cache
        
        Args:
            cache_key: Clé de cache
            data: Données extraites à sauvegarder
        """
        try:
            # Si le cache est plein, supprimer l'entrée la plus ancienne
            if len(self.cache) >= self.max_size and cache_key not in self.cache:
                # Trouver et supprimer l'entrée la plus ancienne
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k]['timestamp']
                )
                del self.cache[oldest_key]
                self.stats['evictions'] += 1
                logger.debug(f"Cache éviction pour la clé: {oldest_key[:8]}...")
            
            # Sauvegarder la nouvelle entrée
            self.cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now()
            }
            
            logger.debug(f"Cache set pour la clé: {cache_key[:8]}...")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache: {e}")
    
    def clear(self):
        """Vide complètement le cache"""
        self.cache.clear()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
        logger.info("Cache vidé")
    
    def cleanup_expired(self):
        """Nettoie les entrées expirées"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - entry['timestamp'] > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cache: {len(expired_keys)} entrées expirées supprimées")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache
        
        Returns:
            Dictionnaire des statistiques
        """
        hit_rate = (
            self.stats['hits'] / self.stats['total_requests'] * 100
            if self.stats['total_requests'] > 0 else 0
        )
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'total_requests': self.stats['total_requests'],
            'hit_rate': round(hit_rate, 2)
        }

