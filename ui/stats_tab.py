"""
Onglet Statistiques
Affiche les statistiques et visualisations des données
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import DatabaseManager


def render_stats_tab(data: pd.DataFrame, db_manager: DatabaseManager):
    """
    Rend l'onglet Statistiques
    
    Args:
        data (pd.DataFrame): Données de la base de données
        db_manager (DatabaseManager): Gestionnaire de base de données
    """
    st.header("📈 Statistiques et visualisations")
    
    # Statistiques de la base de données
    stats = db_manager.get_statistics()
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total Lots", stats.get('total_lots', 0))
        
        with col2:
            avg_montant = stats.get('montant_stats', {}).get('moyenne', 0)
            st.metric("💰 Budget Moyen", f"{avg_montant:,.0f}€" if avg_montant else "N/A")
        
        with col3:
            max_montant = stats.get('montant_stats', {}).get('maximum', 0)
            st.metric("💰 Budget Max", f"{max_montant:,.0f}€" if max_montant else "N/A")
        
        with col4:
            # Calculer le pourcentage de marchés exécutés
            total_lots = stats.get('total_lots', 0)
            executed_lots = len(data[data['statut'] == 'AO ATTRIBUÉ']) if 'statut' in data.columns else 0
            execution_rate = (executed_lots / total_lots * 100) if total_lots > 0 else 0
            st.metric("✅ Taux d'exécution", f"{execution_rate:.1f}%")
    
    # Statistiques par groupement
    if 'groupement' in data.columns:
        st.subheader("📊 Marchés par Groupement")
        
        # Calculer les statistiques par groupement
        groupement_stats = data.groupby('groupement').size().reset_index(name='total_lots')
        
        # Calculer les lots exécutés
        if 'statut' in data.columns:
            executed = data[data['statut'] == 'AO ATTRIBUÉ'].groupby('groupement').size().reset_index(name='executed_lots')
            groupement_stats = groupement_stats.merge(executed, on='groupement', how='left')
            groupement_stats['executed_lots'] = groupement_stats['executed_lots'].fillna(0)
            groupement_stats['execution_rate'] = (groupement_stats['executed_lots'] / groupement_stats['total_lots'] * 100).round(2)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 📋 Tableau des marchés actifs et exécutés par groupement")
            st.dataframe(groupement_stats, width='stretch', hide_index=True)
        
        with col2:
            st.markdown("#### 🥧 Répartition des marchés actifs selon leur groupement")
            fig_pie_groupement = px.pie(
                groupement_stats, 
                values='total_lots', 
                names='groupement',
                title="Répartition en pourcentage des marchés actifs selon leur groupement",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie_groupement.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie_groupement, width='stretch')
    
    # Statistiques par univers
    if 'univers' in data.columns:
        st.subheader("🌍 Marchés par Univers")
        
        # Calculer les statistiques par univers
        univers_stats = data.groupby('univers').size().reset_index(name='total_lots')
        
        # Calculer les lots exécutés
        if 'statut' in data.columns:
            executed = data[data['statut'] == 'AO ATTRIBUÉ'].groupby('univers').size().reset_index(name='executed_lots')
            univers_stats = univers_stats.merge(executed, on='univers', how='left')
            univers_stats['executed_lots'] = univers_stats['executed_lots'].fillna(0)
            univers_stats['execution_rate'] = (univers_stats['executed_lots'] / univers_stats['total_lots'] * 100).round(2)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 📋 Tableau des marchés actifs et exécutés par univers")
            st.dataframe(univers_stats, width='stretch', hide_index=True)
        
        with col2:
            st.markdown("#### 🥧 Répartition des marchés actifs selon l'univers")
            fig_pie_univers = px.pie(
                univers_stats, 
                values='total_lots', 
                names='univers',
                title="Répartition en pourcentage des marchés actifs selon l'univers",
                color_discrete_sequence=px.colors.qualitative.Set1
            )
            fig_pie_univers.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie_univers, width='stretch')
    
    # Graphiques existants
    if stats:
        col1, col2 = st.columns(2)
        
        with col1:
            if stats.get('univers_stats'):
                fig = px.pie(
                    values=list(stats['univers_stats'].values()),
                    names=list(stats['univers_stats'].keys()),
                    title="Répartition par Univers"
                )
                st.plotly_chart(fig, width='stretch')
        
        with col2:
            if stats.get('statut_stats'):
                fig = px.bar(
                    x=list(stats['statut_stats'].keys()),
                    y=list(stats['statut_stats'].values()),
                    title="Répartition par Statut"
                )
                st.plotly_chart(fig, width='stretch')

