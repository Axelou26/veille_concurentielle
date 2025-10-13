"""
🗄️ Gestionnaire de Base de Données - Performance Optimisée
==========================================================

Remplace le fichier Excel par une base de données locale
- Performance élevée
- Sauvegarde automatique
- Requêtes SQL complexes
- Interface moderne
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestionnaire de base de données locale pour la veille concurrentielle"""
    
    def __init__(self, db_path: str = "database/veille_concurrentielle.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.connection = None
        
        # NOUVEAU: Système de backup et validation
        self.backup_enabled = True
        self.backup_interval = 24  # heures
        self.last_backup = None
        self.validation_enabled = True
        self.performance_metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'average_query_time': 0,
            'backup_count': 0
        }
        
        self._init_database()
    
    def _init_database(self):
        """Initialise la base de données et crée les tables"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
            
            # Créer la table principale des appels d'offres
            self._create_tables()
            logger.info(f"✅ Base de données initialisée: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation base de données: {e}")
            raise
    
    def _create_tables(self):
        """Crée les tables de la base de données"""
        try:
            cursor = self.connection.cursor()
            
            # Table principale des appels d'offres
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS appels_offres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mots_cles TEXT,
                univers TEXT,
                segment TEXT,
                famille TEXT,
                statut TEXT,
                groupement TEXT,
                reference_procedure TEXT UNIQUE,
                type_procedure TEXT,
                mono_multi TEXT,
                execution_marche TEXT,
                date_limite TEXT,
                date_attribution TEXT,
                duree_marche INTEGER,
                reconduction TEXT,
                fin_sans_reconduction TEXT,
                fin_avec_reconduction TEXT,
                nbr_lots INTEGER,
                intitule_procedure TEXT,
                lot_numero INTEGER,
                intitule_lot TEXT,
                montant_global_estime REAL,
                montant_global_maxi REAL,
                achat TEXT,
                credit_bail TEXT,
                credit_bail_duree INTEGER,
                location TEXT,
                location_duree INTEGER,
                mad TEXT,
                quantite_minimum INTEGER,
                quantites_estimees INTEGER,
                quantite_maximum INTEGER,
                criteres_economique TEXT,
                criteres_techniques TEXT,
                autres_criteres TEXT,
                rse TEXT,
                contribution_fournisseur TEXT,
                attributaire TEXT,
                produit_retenu TEXT,
                infos_complementaires TEXT,
                remarques TEXT,
                notes_acheteur_procedure TEXT,
                notes_acheteur_fournisseur TEXT,
                notes_acheteur_positionnement TEXT,
                note_veille TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_table_sql)
            
            # Table des métadonnées
            create_metadata_sql = """
            CREATE TABLE IF NOT EXISTS metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_metadata_sql)
            
            # Table des logs d'extraction
            create_logs_sql = """
            CREATE TABLE IF NOT EXISTS extraction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fichier_source TEXT,
                type_fichier TEXT,
                elements_extraits INTEGER,
                elements_generes INTEGER,
                taux_reussite REAL,
                erreurs TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_logs_sql)
            
            # Index pour améliorer les performances
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_reference ON appels_offres(reference_procedure)",
                "CREATE INDEX IF NOT EXISTS idx_univers ON appels_offres(univers)",
                "CREATE INDEX IF NOT EXISTS idx_statut ON appels_offres(statut)",
                "CREATE INDEX IF NOT EXISTS idx_groupement ON appels_offres(groupement)",
                "CREATE INDEX IF NOT EXISTS idx_date_limite ON appels_offres(date_limite)",
                "CREATE INDEX IF NOT EXISTS idx_montant ON appels_offres(montant_global_estime)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            self.connection.commit()
            logger.info("✅ Tables et index créés avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur création tables: {e}")
            raise
    
    def import_from_excel(self, excel_path: str) -> Dict[str, Any]:
        """Importe les données depuis un fichier Excel"""
        try:
            logger.info(f"📊 Import depuis Excel: {excel_path}")
            
            # Lire le fichier Excel
            df = pd.read_excel(excel_path)
            
            # Nettoyer les données
            df = self._clean_dataframe(df)
            
            # Insérer dans la base de données
            result = self.insert_dataframe(df)
            
            # Enregistrer les métadonnées
            self._save_metadata('last_excel_import', {
                'file_path': excel_path,
                'rows_imported': len(df),
                'columns': list(df.columns),
                'import_date': datetime.now().isoformat()
            })
            
            logger.info(f"✅ Import réussi: {result['rows_inserted']} lignes")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur import Excel: {e}")
            raise
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoie le DataFrame avant insertion"""
        try:
            # Supprimer les lignes vides
            df = df.dropna(how='all')
            
            # Nettoyer les noms de colonnes
            df.columns = df.columns.str.strip()
            
            # Convertir les types de données
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.strip()
                    # Remplacer 'nan' par None
                    df[col] = df[col].replace('nan', None)
            
            # Gérer les dates
            date_columns = [col for col in df.columns if 'date' in col.lower()]
            for col in date_columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Gérer les montants
            montant_columns = [col for col in df.columns if 'montant' in col.lower() or 'budget' in col.lower()]
            for col in montant_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage DataFrame: {e}")
            raise
    
    def insert_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Insère un DataFrame dans la base de données"""
        try:
            cursor = self.connection.cursor()
            
            # Mapping des colonnes Excel vers les colonnes de la base
            column_mapping = self._get_column_mapping(df.columns)
            
            rows_inserted = 0
            rows_updated = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    # Préparer les données pour l'insertion
                    data = self._prepare_row_data(row, column_mapping)
                    
                    # Vérifier si la référence existe déjà
                    if data.get('reference_procedure'):
                        cursor.execute(
                            "SELECT id FROM appels_offres WHERE reference_procedure = ?",
                            (data['reference_procedure'],)
                        )
                        existing = cursor.fetchone()
                        
                        if existing:
                            # Mettre à jour
                            self._update_row(cursor, existing['id'], data)
                            rows_updated += 1
                        else:
                            # Insérer
                            self._insert_row(cursor, data)
                            rows_inserted += 1
                    else:
                        # Insérer sans référence
                        self._insert_row(cursor, data)
                        rows_inserted += 1
                        
                except Exception as e:
                    errors.append(f"Ligne {_}: {str(e)}")
                    continue
            
            self.connection.commit()
            
            return {
                'rows_inserted': rows_inserted,
                'rows_updated': rows_updated,
                'total_processed': len(df),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur insertion DataFrame: {e}")
            raise
    
    def _get_column_mapping(self, excel_columns: List[str]) -> Dict[str, str]:
        """Mappe les colonnes Excel vers les colonnes de la base"""
        mapping = {}
        
        for col in excel_columns:
            col_lower = col.lower()
            
            # Mapping intelligent
            if 'mots' in col_lower and 'clés' in col_lower:
                mapping[col] = 'mots_cles'
            elif 'univers' in col_lower:
                mapping[col] = 'univers'
            elif 'segment' in col_lower:
                mapping[col] = 'segment'
            elif 'famille' in col_lower:
                mapping[col] = 'famille'
            elif 'statut' in col_lower:
                mapping[col] = 'statut'
            elif 'groupement' in col_lower:
                mapping[col] = 'groupement'
            elif 'référence' in col_lower or 'ref' in col_lower:
                mapping[col] = 'reference_procedure'
            elif 'type' in col_lower and 'procédure' in col_lower:
                mapping[col] = 'type_procedure'
            elif 'mono' in col_lower or 'multi' in col_lower:
                mapping[col] = 'mono_multi'
            elif 'exécution' in col_lower and 'marché' in col_lower:
                mapping[col] = 'execution_marche'
            elif 'date' in col_lower and 'limite' in col_lower:
                mapping[col] = 'date_limite'
            elif 'date' in col_lower and 'attribution' in col_lower:
                mapping[col] = 'date_attribution'
            elif 'durée' in col_lower and 'marché' in col_lower:
                mapping[col] = 'duree_marche'
            elif 'nbr' in col_lower and 'lots' in col_lower:
                mapping[col] = 'nbr_lots'
            elif 'intitulé' in col_lower and 'procédure' in col_lower:
                mapping[col] = 'intitule_procedure'
            elif 'lot' in col_lower and 'n°' in col_lower:
                mapping[col] = 'lot_numero'
            elif 'intitulé' in col_lower and 'lot' in col_lower:
                mapping[col] = 'intitule_lot'
            elif 'montant' in col_lower and 'estimé' in col_lower:
                mapping[col] = 'montant_global_estime'
            elif 'montant' in col_lower and 'maxi' in col_lower:
                mapping[col] = 'montant_global_maxi'
            elif 'quantité' in col_lower and 'minimum' in col_lower:
                mapping[col] = 'quantite_minimum'
            elif 'quantités' in col_lower and 'estimées' in col_lower:
                mapping[col] = 'quantites_estimees'
            elif 'quantité' in col_lower and 'maximum' in col_lower:
                mapping[col] = 'quantite_maximum'
            elif 'critères' in col_lower and 'économique' in col_lower:
                mapping[col] = 'criteres_economique'
            elif 'critères' in col_lower and 'technique' in col_lower:
                mapping[col] = 'criteres_techniques'
            elif 'autres' in col_lower and 'critères' in col_lower:
                mapping[col] = 'autres_criteres'
            elif 'attributaire' in col_lower:
                mapping[col] = 'attributaire'
            elif 'produit' in col_lower and 'retenu' in col_lower:
                mapping[col] = 'produit_retenu'
            elif 'infos' in col_lower and 'complémentaires' in col_lower:
                mapping[col] = 'infos_complementaires'
            elif 'remarques' in col_lower:
                mapping[col] = 'remarques'
            elif 'notes' in col_lower and 'acheteur' in col_lower:
                if 'procédure' in col_lower:
                    mapping[col] = 'notes_acheteur_procedure'
                elif 'fournisseur' in col_lower:
                    mapping[col] = 'notes_acheteur_fournisseur'
                elif 'positionnement' in col_lower:
                    mapping[col] = 'notes_acheteur_positionnement'
            elif 'note' in col_lower and 'veille' in col_lower:
                mapping[col] = 'note_veille'
            else:
                # Colonne non mappée
                mapping[col] = None
        
        return mapping
    
    def _prepare_row_data(self, row: pd.Series, column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Prépare les données d'une ligne pour l'insertion"""
        data = {}
        
        for excel_col, db_col in column_mapping.items():
            if db_col and excel_col in row:
                value = row[excel_col]
                
                # Conversion des types
                if pd.isna(value) or value == 'nan' or value == '':
                    data[db_col] = None
                elif db_col in ['duree_marche', 'nbr_lots', 'lot_numero', 'credit_bail_duree', 'location_duree']:
                    try:
                        data[db_col] = int(float(value)) if pd.notna(value) else None
                    except:
                        data[db_col] = None
                elif db_col in ['montant_global_estime', 'montant_global_maxi', 'quantite_minimum', 'quantites_estimees', 'quantite_maximum']:
                    try:
                        data[db_col] = float(value) if pd.notna(value) else None
                    except:
                        data[db_col] = None
                else:
                    data[db_col] = str(value) if pd.notna(value) else None
        
        return data
    
    def _insert_row(self, cursor, data: Dict[str, Any]):
        """Insère une ligne dans la base de données"""
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['?' for _ in columns])
        
        sql = f"INSERT INTO appels_offres ({', '.join(columns)}) VALUES ({placeholders})"
        cursor.execute(sql, values)
    
    def _update_row(self, cursor, row_id: int, data: Dict[str, Any]):
        """Met à jour une ligne dans la base de données"""
        columns = list(data.keys())
        values = list(data.values())
        set_clause = ', '.join([f"{col} = ?" for col in columns])
        
        sql = f"UPDATE appels_offres SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        cursor.execute(sql, values + [row_id])
    
    def get_all_data(self) -> pd.DataFrame:
        """Récupère toutes les données"""
        try:
            sql = "SELECT * FROM appels_offres ORDER BY created_at DESC"
            df = pd.read_sql_query(sql, self.connection)
            return df
        except Exception as e:
            logger.error(f"❌ Erreur récupération données: {e}")
            return pd.DataFrame()
    
    def search_data(self, query: str, columns: List[str] = None) -> pd.DataFrame:
        """Recherche dans les données"""
        try:
            if columns is None:
                columns = ['intitule_procedure', 'intitule_lot', 'infos_complementaires', 'remarques']
            
            where_conditions = []
            params = []
            
            for col in columns:
                where_conditions.append(f"{col} LIKE ?")
                params.append(f"%{query}%")
            
            where_clause = " OR ".join(where_conditions)
            sql = f"SELECT * FROM appels_offres WHERE {where_clause} ORDER BY created_at DESC"
            
            df = pd.read_sql_query(sql, self.connection, params=params)
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche: {e}")
            return pd.DataFrame()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calcule des statistiques sur les données"""
        try:
            cursor = self.connection.cursor()
            
            # Statistiques générales
            cursor.execute("SELECT COUNT(*) as total FROM appels_offres")
            total = cursor.fetchone()['total']
            
            # Répartition par univers
            cursor.execute("SELECT univers, COUNT(*) as count FROM appels_offres WHERE univers IS NOT NULL GROUP BY univers")
            univers_stats = dict(cursor.fetchall())
            
            # Répartition par statut
            cursor.execute("SELECT statut, COUNT(*) as count FROM appels_offres WHERE statut IS NOT NULL GROUP BY statut")
            statut_stats = dict(cursor.fetchall())
            
            # Répartition par groupement
            cursor.execute("SELECT groupement, COUNT(*) as count FROM appels_offres WHERE groupement IS NOT NULL GROUP BY groupement")
            groupement_stats = dict(cursor.fetchall())
            
            # Statistiques des montants
            cursor.execute("SELECT AVG(montant_global_estime) as avg_montant, MAX(montant_global_estime) as max_montant, MIN(montant_global_estime) as min_montant FROM appels_offres WHERE montant_global_estime IS NOT NULL")
            montant_stats = cursor.fetchone()
            
            return {
                'total_lots': total,
                'univers_stats': univers_stats,
                'statut_stats': statut_stats,
                'groupement_stats': groupement_stats,
                'montant_stats': {
                    'moyenne': montant_stats['avg_montant'],
                    'maximum': montant_stats['max_montant'],
                    'minimum': montant_stats['min_montant']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul statistiques: {e}")
            return {}
    
    def _save_metadata(self, key: str, value: Any):
        """Sauvegarde des métadonnées"""
        try:
            cursor = self.connection.cursor()
            value_json = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            
            cursor.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                (key, value_json)
            )
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde métadonnées: {e}")
    
    def get_metadata(self, key: str) -> Any:
        """Récupère des métadonnées"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT value FROM metadata WHERE key = ?", (key,))
            result = cursor.fetchone()
            
            if result:
                try:
                    return json.loads(result['value'])
                except:
                    return result['value']
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération métadonnées: {e}")
            return None
    
    def close(self):
        """Ferme la connexion à la base de données"""
        if self.connection:
            self.connection.close()
            logger.info("✅ Connexion base de données fermée")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # NOUVELLES MÉTHODES POUR BACKUP ET VALIDATION
    
    def create_backup(self) -> bool:
        """Crée une sauvegarde de la base de données"""
        try:
            if not self.backup_enabled:
                return False
                
            backup_dir = self.db_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"veille_concurrentielle_backup_{timestamp}.db"
            
            # Créer la sauvegarde
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            self.last_backup = datetime.now()
            self.performance_metrics['backup_count'] += 1
            
            logger.info(f"✅ Sauvegarde créée: {backup_path}")
            
            # Nettoyer les anciennes sauvegardes (garder seulement les 10 dernières)
            self._cleanup_old_backups(backup_dir)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur création sauvegarde: {e}")
            return False
    
    def _cleanup_old_backups(self, backup_dir: Path, keep_count: int = 10):
        """Nettoie les anciennes sauvegardes"""
        try:
            backup_files = list(backup_dir.glob("veille_concurrentielle_backup_*.db"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Supprimer les anciennes sauvegardes
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                logger.info(f"🗑️ Ancienne sauvegarde supprimée: {old_backup.name}")
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur nettoyage sauvegardes: {e}")
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Restaure la base de données depuis une sauvegarde"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"❌ Fichier de sauvegarde introuvable: {backup_path}")
                return False
            
            # Fermer la connexion actuelle
            if self.connection:
                self.connection.close()
            
            # Créer une sauvegarde de la base actuelle
            current_backup = self.db_path.with_suffix('.db.current_backup')
            import shutil
            shutil.copy2(self.db_path, current_backup)
            
            # Restaurer depuis la sauvegarde
            shutil.copy2(backup_file, self.db_path)
            
            # Rouvrir la connexion
            self._init_database()
            
            logger.info(f"✅ Base de données restaurée depuis: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur restauration: {e}")
            return False
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """Valide l'intégrité des données"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'statistics': {},
            'recommendations': []
        }
        
        try:
            cursor = self.connection.cursor()
            
            # Vérifier les contraintes d'intégrité
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result != "ok":
                validation_result['is_valid'] = False
                validation_result['issues'].append(f"Problème d'intégrité: {integrity_result}")
            
            # Vérifier les données orphelines
            cursor.execute("""
                SELECT COUNT(*) FROM appels_offres 
                WHERE reference_procedure IS NULL OR reference_procedure = ''
            """)
            null_refs = cursor.fetchone()[0]
            
            if null_refs > 0:
                validation_result['issues'].append(f"{null_refs} enregistrements sans référence")
                validation_result['recommendations'].append("Ajouter des références manquantes")
            
            # Vérifier les doublons
            cursor.execute("""
                SELECT reference_procedure, COUNT(*) 
                FROM appels_offres 
                WHERE reference_procedure IS NOT NULL 
                GROUP BY reference_procedure 
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            
            if duplicates:
                validation_result['issues'].append(f"{len(duplicates)} références en doublon")
                validation_result['recommendations'].append("Nettoyer les doublons")
            
            # Statistiques générales
            cursor.execute("SELECT COUNT(*) FROM appels_offres")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT reference_procedure) FROM appels_offres WHERE reference_procedure IS NOT NULL")
            unique_refs = cursor.fetchone()[0]
            
            validation_result['statistics'] = {
                'total_records': total_records,
                'unique_references': unique_refs,
                'duplicate_count': len(duplicates),
                'null_references': null_refs
            }
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['issues'].append(f"Erreur validation: {str(e)}")
            logger.error(f"❌ Erreur validation intégrité: {e}")
        
        return validation_result
    
    def optimize_database(self) -> bool:
        """Optimise la base de données"""
        try:
            cursor = self.connection.cursor()
            
            # Analyser les tables
            cursor.execute("ANALYZE")
            
            # Vérifier l'intégrité
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result != "ok":
                logger.warning(f"⚠️ Problème d'intégrité détecté: {integrity_result}")
                return False
            
            # Optimiser la base
            cursor.execute("VACUUM")
            
            logger.info("✅ Base de données optimisée")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur optimisation: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Retourne les informations sur la base de données"""
        try:
            cursor = self.connection.cursor()
            
            # Informations générales
            cursor.execute("SELECT COUNT(*) FROM appels_offres")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM metadata")
            metadata_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM extraction_logs")
            logs_count = cursor.fetchone()[0]
            
            # Taille de la base
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            # Dernière modification
            last_modified = datetime.fromtimestamp(self.db_path.stat().st_mtime) if self.db_path.exists() else None
            
            return {
                'total_records': total_records,
                'metadata_entries': metadata_count,
                'extraction_logs': logs_count,
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'last_modified': last_modified.isoformat() if last_modified else None,
                'last_backup': self.last_backup.isoformat() if self.last_backup else None,
                'backup_enabled': self.backup_enabled,
                'validation_enabled': self.validation_enabled,
                'performance_metrics': self.performance_metrics
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération infos base: {e}")
            return {}
    
    def enable_auto_backup(self, enabled: bool = True, interval_hours: int = 24):
        """Active/désactive la sauvegarde automatique"""
        self.backup_enabled = enabled
        self.backup_interval = interval_hours
        logger.info(f"🔧 Sauvegarde automatique: {'activée' if enabled else 'désactivée'} (intervalle: {interval_hours}h)")
    
    def enable_validation(self, enabled: bool = True):
        """Active/désactive la validation des données"""
        self.validation_enabled = enabled
        logger.info(f"🔧 Validation des données: {'activée' if enabled else 'désactivée'}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de performance"""
        metrics = self.performance_metrics.copy()
        
        if metrics['total_queries'] > 0:
            metrics['success_rate'] = metrics['successful_queries'] / metrics['total_queries']
        else:
            metrics['success_rate'] = 0
            
        return metrics
    
    def _update_query_metrics(self, success: bool, query_time: float):
        """Met à jour les métriques de requête"""
        self.performance_metrics['total_queries'] += 1
        if success:
            self.performance_metrics['successful_queries'] += 1
        
        # Mettre à jour le temps moyen
        current_avg = self.performance_metrics['average_query_time']
        total_queries = self.performance_metrics['total_queries']
        
        if total_queries == 1:
            self.performance_metrics['average_query_time'] = query_time
        else:
            self.performance_metrics['average_query_time'] = (
                (current_avg * (total_queries - 1) + query_time) / total_queries
            )
