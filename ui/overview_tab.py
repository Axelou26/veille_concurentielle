"""
Onglet Vue d'ensemble
Affiche une vue d'ensemble des données et des colonnes
"""

import streamlit as st
import pandas as pd
from config import COLUMNS_CONFIG


def render_overview_tab(data: pd.DataFrame):
    """
    Rend l'onglet Vue d'ensemble
    
    Args:
        data (pd.DataFrame): Données de la base de données
    """
    st.header("📊 Vue d'ensemble des données")
    
    # Utiliser les 44 colonnes standard depuis config
    colonnes_44 = COLUMNS_CONFIG['french_names']
    
    # Aperçu des données
    st.subheader("Aperçu des données")
    st.dataframe(data.head(20), width='stretch')
    
    # Informations sur les colonnes
    st.subheader("Structure des données")
    col_info = pd.DataFrame({
        'Colonne': data.columns,
        'Type': [str(data[col].dtype) for col in data.columns],
        'Valeurs uniques': [data[col].nunique() for col in data.columns],
        'Valeurs manquantes': [data[col].isna().sum() for col in data.columns]
    })
    st.dataframe(col_info, width='stretch')
    
    # Section des 44 colonnes standard
    st.subheader("📋 Les 44 colonnes standard de la base de données")
    
    # Créer un DataFrame pour afficher toutes les 44 colonnes
    colonnes_df = pd.DataFrame({
        'N°': range(1, 45),
        'Nom de la colonne': colonnes_44,
        'Présente dans les données': [col in data.columns for col in colonnes_44],
        'Type dans les données': [str(data[col].dtype) if col in data.columns else 'Non présente' for col in colonnes_44],
        'Valeurs uniques': [data[col].nunique() if col in data.columns else 0 for col in colonnes_44],
        'Valeurs manquantes': [data[col].isna().sum() if col in data.columns else 0 for col in colonnes_44]
    })
    
    # Afficher le tableau des 44 colonnes
    st.dataframe(colonnes_df, width='stretch', height=600)
    
    # Statistiques sur les colonnes
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        colonnes_presentes = sum(1 for col in colonnes_44 if col in data.columns)
        st.metric("📊 Colonnes présentes", f"{colonnes_presentes}/44")
    
    with col2:
        colonnes_manquantes = 44 - colonnes_presentes
        st.metric("❌ Colonnes manquantes", colonnes_manquantes)
    
    with col3:
        taux_completude = (colonnes_presentes / 44) * 100
        st.metric("✅ Taux de complétude", f"{taux_completude:.1f}%")
    
    with col4:
        if colonnes_manquantes > 0:
            st.metric("⚠️ Statut", "Incomplet")
        else:
            st.metric("✅ Statut", "Complet")
    
    # Afficher les colonnes manquantes si il y en a
    if colonnes_manquantes > 0:
        st.warning(f"⚠️ **{colonnes_manquantes} colonnes manquantes** dans votre base de données :")
        colonnes_manquantes_liste = [col for col in colonnes_44 if col not in data.columns]
        
        # Afficher par groupes de 5 colonnes
        for i in range(0, len(colonnes_manquantes_liste), 5):
            cols = st.columns(5)
            for j, col in enumerate(colonnes_manquantes_liste[i:i+5]):
                with cols[j]:
                    st.write(f"• {col}")
    
    # Afficher les colonnes supplémentaires (non standard)
    colonnes_supplementaires = [col for col in data.columns if col not in colonnes_44]
    if colonnes_supplementaires:
        st.info(f"ℹ️ **{len(colonnes_supplementaires)} colonnes supplémentaires** détectées :")
        for col in colonnes_supplementaires:
            st.write(f"• {col}")

