"""
Onglet Base de données
Gère la gestion et la maintenance de la base de données
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import DatabaseManager
from ao_extractor_v2 import AOExtractorV2


def render_database_tab(
    db_manager: DatabaseManager,
    ao_extractor: AOExtractorV2 = None
):
    """
    Rend l'onglet Base de données
    
    Args:
        db_manager (DatabaseManager): Gestionnaire de base de données
        ao_extractor (AOExtractorV2, optional): Extracteur d'AO pour les métriques
    """
    st.header("🗄️ Gestion de la Base de Données")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Informations de la Base")
        
        # Statistiques de la base
        stats = db_manager.get_statistics()
        if stats:
            st.write(f"**Total des lots:** {stats.get('total_lots', 0)}")
            st.write(f"**Univers représentés:** {len(stats.get('univers_stats', {}))}")
            st.write(f"**Statuts différents:** {len(stats.get('statut_stats', {}))}")
            st.write(f"**Groupements:** {len(stats.get('groupement_stats', {}))}")
        
        # Métadonnées
        st.subheader("📋 Métadonnées")
        if hasattr(db_manager, 'get_metadata'):
            last_import = db_manager.get_metadata('last_excel_import')
            if last_import:
                st.write(f"**Dernier import:** {last_import.get('import_date', 'N/A')}")
                st.write(f"**Fichier:** {last_import.get('file_path', 'N/A')}")
                st.write(f"**Lignes importées:** {last_import.get('rows_imported', 'N/A')}")
    
    with col2:
        st.subheader("🔧 Actions")
        
        # Export des données
        if st.button("📥 Exporter toutes les données"):
            try:
                all_data = db_manager.get_all_data()
                csv_data = all_data.to_csv(index=False)
                
                st.download_button(
                    label="💾 Télécharger CSV",
                    data=csv_data,
                    file_name=f"export_veille_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                st.success("✅ Export prêt au téléchargement")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'export: {e}")
        
        # Recherche dans la base
        st.subheader("🔍 Recherche")
        search_term = st.text_input("Terme de recherche")
        if search_term:
            if hasattr(db_manager, 'search_data'):
                results = db_manager.search_data(search_term)
                if not results.empty:
                    st.write(f"**Résultats trouvés:** {len(results)}")
                    st.dataframe(results.head(10), width='stretch')
                else:
                    st.info("Aucun résultat trouvé")
        
        # Maintenance de la base
        st.subheader("🔧 Maintenance de la Base")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Créer sauvegarde"):
                if hasattr(db_manager, 'create_backup'):
                    if db_manager.create_backup():
                        st.success("✅ Sauvegarde créée!")
                    else:
                        st.error("❌ Erreur création sauvegarde")
                else:
                    st.warning("⚠️ Fonction de sauvegarde non disponible")
        
        with col2:
            if st.button("🔍 Valider intégrité"):
                if hasattr(db_manager, 'validate_data_integrity'):
                    validation = db_manager.validate_data_integrity()
                    if validation['is_valid']:
                        st.success("✅ Intégrité validée")
                    else:
                        st.warning("⚠️ Problèmes détectés")
                        for issue in validation['issues']:
                            st.write(f"• {issue}")
                else:
                    st.warning("⚠️ Fonction de validation non disponible")
        
        with col3:
            if st.button("⚡ Optimiser base"):
                if hasattr(db_manager, 'optimize_database'):
                    if db_manager.optimize_database():
                        st.success("✅ Base optimisée!")
                    else:
                        st.error("❌ Erreur optimisation")
                else:
                    st.warning("⚠️ Fonction d'optimisation non disponible")
        
        # Informations détaillées de la base
        if hasattr(db_manager, 'get_database_info'):
            with st.expander("📊 Informations détaillées de la base"):
                db_info = db_manager.get_database_info()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Taille de la base", f"{db_info.get('database_size_mb', 0):.2f} MB")
                    st.metric("Sauvegardes créées", db_info.get('performance_metrics', {}).get('backup_count', 0))
                
                with col2:
                    st.metric("Dernière modification", db_info.get('last_modified', 'N/A')[:10] if db_info.get('last_modified') else 'N/A')
                    st.metric("Dernière sauvegarde", db_info.get('last_backup', 'N/A')[:10] if db_info.get('last_backup') else 'N/A')
                
                # Métriques de performance
                perf_metrics = db_info.get('performance_metrics', {})
                if perf_metrics:
                    st.subheader("📈 Métriques de performance")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Requêtes totales", perf_metrics.get('total_queries', 0))
                    with col2:
                        success_rate = perf_metrics.get('success_rate', 0) * 100
                        st.metric("Taux de succès", f"{success_rate:.1f}%")
                    with col3:
                        avg_time = perf_metrics.get('average_query_time', 0)
                        st.metric("Temps moyen", f"{avg_time:.3f}s")
        
        # Métriques V2 de l'extracteur
        if ao_extractor and hasattr(ao_extractor, 'extraction_metrics'):
            with st.expander("🚀 Métriques Extracteur V2"):
                v2_metrics = ao_extractor.extraction_metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Extractions totales", v2_metrics.get('total_extractions', 0))
                with col2:
                    st.metric("Extractions réussies", v2_metrics.get('successful_extractions', 0))
                with col3:
                    st.metric("Erreurs validation", v2_metrics.get('validation_errors', 0))
                with col4:
                    st.metric("Patterns améliorés", v2_metrics.get('pattern_improvements', 0))
        
        # Nettoyage de la base
        if st.button("🗑️ Vider la base de données", type="secondary"):
            if st.checkbox("Confirmer la suppression de toutes les données"):
                try:
                    cursor = db_manager.connection.cursor()
                    cursor.execute("DELETE FROM appels_offres")
                    db_manager.connection.commit()
                    st.success("✅ Base de données vidée")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors du nettoyage: {e}")

