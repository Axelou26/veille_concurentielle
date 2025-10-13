"""
Composants UI réutilisables pour l'application de veille concurrentielle
Contient les composants Streamlit réutilisables pour éviter la duplication
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config import COLUMNS_CONFIG, SELECTBOX_OPTIONS, UI_MESSAGES
from utils import create_metric_columns, create_form_field

def create_main_metrics(data):
    """
    Crée les métriques principales de l'application
    
    Args:
        data (DataFrame): Données de la base
    """
    metrics_data = [
        {'label': "📋 Total Lots", 'value': len(data)},
        {'label': "📊 Colonnes", 'value': len(data.columns)},
        {'label': "📅 Date", 'value': datetime.now().strftime("%d/%m/%Y")},
        {'label': "⏰ Heure", 'value': datetime.now().strftime("%H:%M")}
    ]
    create_metric_columns(metrics_data)

def create_columns_metrics(data):
    """
    Crée les métriques des colonnes
    
    Args:
        data (DataFrame): Données de la base
    """
    colonnes_44 = COLUMNS_CONFIG['french_names']
    colonnes_presentes = sum(1 for col in colonnes_44 if col in data.columns)
    colonnes_manquantes = 44 - colonnes_presentes
    taux_completude = (colonnes_presentes / 44) * 100
    
    metrics_data = [
        {'label': "📊 Colonnes présentes", 'value': f"{colonnes_presentes}/44"},
        {'label': "❌ Colonnes manquantes", 'value': colonnes_manquantes},
        {'label': "✅ Taux de complétude", 'value': f"{taux_completude:.1f}%"},
        {'label': "⚠️ Statut" if colonnes_manquantes > 0 else "✅ Statut", 
         'value': "Incomplet" if colonnes_manquantes > 0 else "Complet"}
    ]
    create_metric_columns(metrics_data)

def create_lots_management_ui(i, lots_list):
    """
    Crée l'interface de gestion des lots
    
    Args:
        i (int): Index de l'entrée
        lots_list (list): Liste des lots
    """
    # Afficher le nombre total de lots
    total_lots = len(lots_list)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.metric("📊 Nombre total de lots", total_lots)
    with col2:
        if st.button("➕ Ajouter un lot", key=f"add_lot_{i}"):
            new_lot = {
                'numero': total_lots + 1,
                'intitule': '',
                'attributaire': '',
                'produit_retenu': '',
                'infos_complementaires': '',
                'montant_estime': 0,
                'montant_maximum': 0,
                'quantite_minimum': 0,
                'quantites_estimees': '',
                'quantite_maximum': 0,
                'criteres_economique': '',
                'criteres_techniques': '',
                'autres_criteres': '',
                'rse': '',
                'contribution_fournisseur': ''
            }
            st.session_state[f'lots_list_{i}'].append(new_lot)
            st.rerun()
    with col3:
        if st.button("🗑️ Supprimer dernier", key=f"del_lot_{i}"):
            if total_lots > 1:
                st.session_state[f'lots_list_{i}'].pop()
                st.rerun()

def create_form_tabs():
    """
    Crée les onglets du formulaire d'édition
    
    Returns:
        tuple: Onglets du formulaire
    """
    return st.tabs(["📋 Général", "📅 Dates", "📝 Autres"])

def create_general_tab_fields(all_data, i):
    """
    Crée les champs de l'onglet général
    
    Args:
        all_data (dict): Données à éditer
        i (int): Index de l'entrée
    
    Returns:
        dict: Données éditées
    """
    edited_data = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Informations de base")
        
        edited_data['mots_cles'] = create_form_field(
            "Mots clés", "text_input", 
            all_data.get('mots_cles', ''), f"edit_mots_cles_{i}"
        )
        
        edited_data['univers'] = create_form_field(
            "Univers", "selectbox", 
            all_data.get('univers', 'MÉDICAL'), f"edit_univers_{i}",
            options=SELECTBOX_OPTIONS['univers'],
            index=SELECTBOX_OPTIONS['univers'].index(all_data.get('univers', 'MÉDICAL')) if all_data.get('univers') in SELECTBOX_OPTIONS['univers'] else 0
        )
        
        edited_data['segment'] = create_form_field(
            "Segment", "text_input", 
            all_data.get('segment', ''), f"edit_segment_{i}"
        )
        
        edited_data['famille'] = create_form_field(
            "Famille", "text_input", 
            all_data.get('famille', ''), f"edit_famille_{i}"
        )
        
        edited_data['statut'] = create_form_field(
            "Statut", "selectbox", 
            all_data.get('statut', 'AO EN COURS'), f"edit_statut_{i}",
            options=SELECTBOX_OPTIONS['statut'],
            index=SELECTBOX_OPTIONS['statut'].index(all_data.get('statut', 'AO EN COURS')) if all_data.get('statut') in SELECTBOX_OPTIONS['statut'] else 0
        )
        
        edited_data['groupement'] = create_form_field(
            "Groupement", "selectbox", 
            all_data.get('groupement', 'RESAH'), f"edit_groupement_{i}",
            options=SELECTBOX_OPTIONS['groupement'],
            index=SELECTBOX_OPTIONS['groupement'].index(all_data.get('groupement', 'RESAH')) if all_data.get('groupement') in SELECTBOX_OPTIONS['groupement'] else 0
        )
    
    with col2:
        st.markdown("#### 📄 Procédure")
        
        edited_data['reference_procedure'] = create_form_field(
            "Référence de procédure", "text_input", 
            all_data.get('reference_procedure', ''), f"edit_ref_proc_{i}"
        )
        
        edited_data['type_procedure'] = create_form_field(
            "Type de procédure", "selectbox", 
            all_data.get('type_procedure', 'Appel d\'offres ouvert'), f"edit_type_proc_{i}",
            options=SELECTBOX_OPTIONS['type_procedure'],
            index=SELECTBOX_OPTIONS['type_procedure'].index(all_data.get('type_procedure', 'Appel d\'offres ouvert')) if all_data.get('type_procedure') in SELECTBOX_OPTIONS['type_procedure'] else 0
        )
        
        edited_data['mono_multi'] = create_form_field(
            "Mono ou multi-attributif", "selectbox", 
            all_data.get('mono_multi', 'Multi-attributif'), f"edit_mono_multi_{i}",
            options=SELECTBOX_OPTIONS['mono_multi'],
            index=SELECTBOX_OPTIONS['mono_multi'].index(all_data.get('mono_multi', 'Multi-attributif')) if all_data.get('mono_multi') in SELECTBOX_OPTIONS['mono_multi'] else 1
        )
        
        edited_data['execution_marche'] = create_form_field(
            "Exécution du marché", "text_input", 
            all_data.get('execution_marche', ''), f"edit_execution_marche_{i}"
        )
        
        edited_data['intitule_procedure'] = create_form_field(
            "Intitulé de procédure", "text_area", 
            all_data.get('intitule_procedure', ''), f"edit_int_proc_{i}",
            height=100
        )
    
    return edited_data

def create_dates_tab_fields(all_data, i):
    """
    Crée les champs de l'onglet dates
    
    Args:
        all_data (dict): Données à éditer
        i (int): Index de l'entrée
    
    Returns:
        dict: Données éditées
    """
    edited_data = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📅 Dates importantes")
        
        edited_data['date_limite'] = create_form_field(
            "Date limite de remise des offres", "date_input", 
            pd.to_datetime(all_data.get('date_limite', '2024-12-31')).date() if all_data.get('date_limite') else pd.to_datetime('2024-12-31').date(), 
            f"edit_date_limite_{i}"
        )
        
        edited_data['date_attribution'] = create_form_field(
            "Date d'attribution du marché", "date_input", 
            pd.to_datetime(all_data.get('date_attribution', '2024-12-31')).date() if all_data.get('date_attribution') else None, 
            f"edit_date_attribution_{i}"
        )
        
        edited_data['duree_marche'] = create_form_field(
            "Durée du marché (mois)", "number_input", 
            int(all_data.get('duree_marche', 0)) if all_data.get('duree_marche') else 0, 
            f"edit_duree_marche_{i}",
            min_value=0, max_value=120
        )
    
    with col2:
        st.markdown("#### 🔄 Reconduction")
        
        edited_data['reconduction'] = create_form_field(
            "Reconduction", "selectbox", 
            all_data.get('reconduction', 'Non spécifié'), f"edit_reconduction_{i}",
            options=SELECTBOX_OPTIONS['reconduction'],
            index=SELECTBOX_OPTIONS['reconduction'].index(all_data.get('reconduction', 'Non spécifié')) if all_data.get('reconduction') in SELECTBOX_OPTIONS['reconduction'] else 2
        )
        
        edited_data['fin_sans_reconduction'] = create_form_field(
            "Fin (sans reconduction)", "date_input", 
            pd.to_datetime(all_data.get('fin_sans_reconduction')).date() if all_data.get('fin_sans_reconduction') else None, 
            f"edit_fin_sans_reconduction_{i}"
        )
        
        edited_data['fin_avec_reconduction'] = create_form_field(
            "Fin (avec reconduction)", "date_input", 
            pd.to_datetime(all_data.get('fin_avec_reconduction')).date() if all_data.get('fin_avec_reconduction') else None, 
            f"edit_fin_avec_reconduction_{i}"
        )
    
    return edited_data

def create_autres_tab_fields(all_data, i):
    """
    Crée les champs de l'onglet autres
    
    Args:
        all_data (dict): Données à éditer
        i (int): Index de l'entrée
    
    Returns:
        dict: Données éditées
    """
    edited_data = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📝 Notes et remarques")
        
        edited_data['remarques'] = create_form_field(
            "Remarques", "text_area", 
            all_data.get('remarques', ''), f"edit_remarques_{i}",
            height=100
        )
        
        edited_data['notes_acheteur_procedure'] = create_form_field(
            "Notes de l'acheteur sur la procédure", "text_area", 
            all_data.get('notes_acheteur_procedure', ''), f"edit_notes_acheteur_procedure_{i}",
            height=100
        )
        
        edited_data['notes_acheteur_fournisseur'] = create_form_field(
            "Notes de l'acheteur sur le fournisseur", "text_area", 
            all_data.get('notes_acheteur_fournisseur', ''), f"edit_notes_acheteur_fournisseur_{i}",
            height=100
        )
    
    with col2:
        st.markdown("#### 📊 Autres informations")
        
        edited_data['notes_acheteur_positionnement'] = create_form_field(
            "Notes de l'acheteur sur le positionnement", "text_area", 
            all_data.get('notes_acheteur_positionnement', ''), f"edit_notes_acheteur_positionnement_{i}",
            height=100
        )
        
        edited_data['note_veille'] = create_form_field(
            "Note Veille concurrentielle disponible", "text_input", 
            all_data.get('note_veille', ''), f"edit_note_veille_{i}"
        )
        
        edited_data['achat'] = create_form_field(
            "Achat", "selectbox", 
            all_data.get('achat', 'Non spécifié'), f"edit_achat_{i}",
            options=SELECTBOX_OPTIONS['achat'],
            index=SELECTBOX_OPTIONS['achat'].index(all_data.get('achat', 'Non spécifié')) if all_data.get('achat') in SELECTBOX_OPTIONS['achat'] else 2
        )
        
        edited_data['credit_bail'] = create_form_field(
            "Crédit bail", "selectbox", 
            all_data.get('credit_bail', 'Non spécifié'), f"edit_credit_bail_{i}",
            options=SELECTBOX_OPTIONS['credit_bail'],
            index=SELECTBOX_OPTIONS['credit_bail'].index(all_data.get('credit_bail', 'Non spécifié')) if all_data.get('credit_bail') in SELECTBOX_OPTIONS['credit_bail'] else 2
        )
        
        edited_data['credit_bail_duree'] = create_form_field(
            "Crédit bail (durée année)", "number_input", 
            int(all_data.get('credit_bail_duree', 0)) if all_data.get('credit_bail_duree') else 0, 
            f"edit_credit_bail_duree_{i}",
            min_value=0, max_value=20
        )
        
        edited_data['location'] = create_form_field(
            "Location", "selectbox", 
            all_data.get('location', 'Non spécifié'), f"edit_location_{i}",
            options=SELECTBOX_OPTIONS['location'],
            index=SELECTBOX_OPTIONS['location'].index(all_data.get('location', 'Non spécifié')) if all_data.get('location') in SELECTBOX_OPTIONS['location'] else 2
        )
        
        edited_data['location_duree'] = create_form_field(
            "Location (durée années)", "number_input", 
            int(all_data.get('location_duree', 0)) if all_data.get('location_duree') else 0, 
            f"edit_location_duree_{i}",
            min_value=0, max_value=20
        )
        
        edited_data['mad'] = create_form_field(
            "MAD", "selectbox", 
            all_data.get('mad', 'Non spécifié'), f"edit_mad_{i}",
            options=SELECTBOX_OPTIONS['mad'],
            index=SELECTBOX_OPTIONS['mad'].index(all_data.get('mad', 'Non spécifié')) if all_data.get('mad') in SELECTBOX_OPTIONS['mad'] else 2
        )
    
    return edited_data

def create_form_buttons():
    """
    Crée les boutons du formulaire
    
    Returns:
        tuple: Boutons du formulaire
    """
    col_save, col_reset, col_export = st.columns(3)
    
    with col_save:
        save_button = st.form_submit_button("💾 Sauvegarder les modifications", type="primary")
    
    with col_reset:
        reset_button = st.form_submit_button("🔄 Réinitialiser")
    
    with col_export:
        export_button = st.form_submit_button("📤 Exporter CSV")
    
    return save_button, reset_button, export_button

def create_sidebar_buttons():
    """
    Crée les boutons de la sidebar
    
    Returns:
        tuple: Boutons de la sidebar
    """
    if st.button("🔄 Recharger l'application"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()
    
    if st.button("🧠 Recharger l'IA avec toutes les données"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()
    
    if st.button("🔄 Actualiser les données"):
        st.cache_data.clear()
        st.rerun()
