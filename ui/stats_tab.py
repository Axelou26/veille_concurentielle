"""
Onglet Statistiques
Affiche les statistiques et visualisations des données
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
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
    
    # ===== MÉTRIQUES CLÉS =====
    st.subheader("📊 Métriques Clés")
    
    if stats:
        # Calculer le budget total
        budget_total = 0
        if 'montant_global_estime' in data.columns:
            budget_total = data['montant_global_estime'].fillna(0).sum()
        
        # Calculer les métriques
        total_lots = stats.get('total_lots', len(data))
        executed_lots = len(data[data['statut'] == 'AO ATTRIBUÉ']) if 'statut' in data.columns else 0
        execution_rate = (executed_lots / total_lots * 100) if total_lots > 0 else 0
        avg_montant = stats.get('montant_stats', {}).get('moyenne', 0)
        max_montant = stats.get('montant_stats', {}).get('maximum', 0)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📊 Total Lots", f"{total_lots:,}")
        
        with col2:
            st.metric("💰 Budget Total", f"{budget_total:,.0f}€" if budget_total > 0 else "N/A")
        
        with col3:
            st.metric("💰 Budget Moyen", f"{avg_montant:,.0f}€" if avg_montant else "N/A")
        
        with col4:
            st.metric("💰 Budget Max", f"{max_montant:,.0f}€" if max_montant else "N/A")
        
        with col5:
            st.metric("✅ Taux d'exécution", f"{execution_rate:.1f}%")
    
    # ===== ALERTES =====
    st.subheader("🔔 Alertes et Notifications")
    
    alert_cols = st.columns(3)
    
    with alert_cols[0]:
        # Marchés expirant dans les 30 prochains jours
        expiring_soon = 0
        if 'fin_sans_reconduction' in data.columns or 'fin_avec_reconduction' in data.columns:
            today = datetime.now().date()
            threshold = today + timedelta(days=30)
            
            for date_col in ['fin_sans_reconduction', 'fin_avec_reconduction']:
                if date_col in data.columns:
                    for date_str in data[date_col].dropna():
                        try:
                            # Essayer différents formats de date
                            date_obj = None
                            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                                try:
                                    date_obj = datetime.strptime(str(date_str), fmt).date()
                                    break
                                except:
                                    continue
                            
                            if date_obj and today <= date_obj <= threshold:
                                expiring_soon += 1
                        except:
                            continue
        
        if expiring_soon > 0:
            st.warning(f"⚠️ **{expiring_soon} marché(s) expirant dans les 30 jours**")
        else:
            st.success("✅ Aucun marché n'expire dans les 30 jours")
    
    with alert_cols[1]:
        # Marchés avec montants élevés
        high_value = 0
        if 'montant_global_estime' in data.columns:
            # Considérer comme montant élevé > 1M€
            high_value = len(data[data['montant_global_estime'] > 1_000_000])
        
        if high_value > 0:
            st.info(f"💎 **{high_value} marché(x) avec montant > 1M€**")
        else:
            st.info("💎 Aucun marché avec montant élevé")
    
    with alert_cols[2]:
        # Marchés en cours
        en_cours = len(data[data['statut'] == 'AO EN COURS']) if 'statut' in data.columns else 0
        if en_cours > 0:
            st.info(f"🔄 **{en_cours} marché(x) en cours**")
        else:
            st.info("🔄 Aucun marché en cours")
    
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
    
    # ===== TOP 5 UNIVERS =====
    if 'univers' in data.columns:
        st.subheader("🏆 Top 5 des Univers")
        top_univers = data['univers'].value_counts().head(5)
        
        if len(top_univers) > 0:
            fig_bar = px.bar(
                x=top_univers.values,
                y=top_univers.index,
                orientation='h',
                title="Top 5 des Univers par nombre de lots",
                labels={'x': 'Nombre de lots', 'y': 'Univers'},
                color=top_univers.values,
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, width='stretch')
    
    # ===== GRAPHIQUE PAR STATUT =====
    if 'statut' in data.columns:
        st.subheader("📊 Répartition par Statut")
        statut_counts = data['statut'].value_counts()
        
        if len(statut_counts) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pie_statut = px.pie(
                    values=statut_counts.values,
                    names=statut_counts.index,
                    title="Répartition en pourcentage par Statut",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_pie_statut.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie_statut, width='stretch')
            
            with col2:
                fig_bar_statut = px.bar(
                    x=statut_counts.index,
                    y=statut_counts.values,
                    title="Nombre de lots par Statut",
                    labels={'x': 'Statut', 'y': 'Nombre de lots'},
                    color=statut_counts.values,
                    color_continuous_scale='Greens'
                )
                fig_bar_statut.update_layout(showlegend=False)
                st.plotly_chart(fig_bar_statut, width='stretch')

