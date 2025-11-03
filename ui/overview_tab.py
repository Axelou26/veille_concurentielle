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
    
    # Section des 44 colonnes standard
    st.subheader("📋 Les 44 colonnes standard de la base de données")
    
    # Utiliser les noms techniques pour la comparaison avec la base de données
    colonnes_techniques = COLUMNS_CONFIG['technical_names']
    
    # Vérifier que les deux listes ont le même nombre d'éléments
    if len(colonnes_44) != len(colonnes_techniques):
        st.error(f"⚠️ Erreur de configuration : {len(colonnes_44)} noms français mais {len(colonnes_techniques)} noms techniques")
        return
    
    # Créer un mapping entre noms français et noms techniques
    mapping_colonnes = dict(zip(colonnes_44, colonnes_techniques))
    
    # Créer un DataFrame pour afficher toutes les 44 colonnes
    colonnes_df = pd.DataFrame({
        'N°': range(1, 45),
        'Nom de la colonne': colonnes_44,
        'Présente dans les données': [
            mapping_colonnes[col] in data.columns for col in colonnes_44
        ],
        'Type dans les données': [
            str(data[mapping_colonnes[col]].dtype) if mapping_colonnes[col] in data.columns else 'Non présente' 
            for col in colonnes_44
        ],
        'Valeurs uniques': [
            data[mapping_colonnes[col]].nunique() if mapping_colonnes[col] in data.columns else 0 
            for col in colonnes_44
        ],
        'Valeurs manquantes': [
            data[mapping_colonnes[col]].isna().sum() if mapping_colonnes[col] in data.columns else 0 
            for col in colonnes_44
        ]
    })
    
    # Afficher le tableau des 44 colonnes
    st.dataframe(colonnes_df, width='stretch', height=600)



