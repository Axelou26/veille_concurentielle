"""
Fonctions utilitaires pour l'application de veille concurrentielle
Contient les fonctions réutilisables pour éviter la duplication de code
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config import COLUMNS_CONFIG, LOT_FIELDS_MAPPING, SELECTBOX_OPTIONS, UI_MESSAGES

def create_lot_data(lot_info, base_data):
    """
    Crée les données d'un lot à partir des informations de base
    
    Args:
        lot_info (dict): Informations spécifiques du lot
        base_data (dict): Données de base extraites
    
    Returns:
        dict: Données complètes du lot
    """
    lot_data = base_data.copy()
    
    # Ajouter les informations spécifiques au lot
    lot_data['nbr_lots'] = 1  # Sera mis à jour par la fonction appelante
    lot_data['lot_numero'] = lot_info.get('numero', 1)
    lot_data['intitule_lot'] = lot_info.get('intitule', '')
    
    # Mapper tous les champs de lot
    for field, mapping in LOT_FIELDS_MAPPING.items():
        lot_data[mapping] = lot_info.get(field, '')
    
    return lot_data

def process_detected_lots(lots_detected, extracted_data, uploaded_file_name, uploaded_file_size):
    """
    Traite les lots détectés par l'IA de manière centralisée
    
    Args:
        lots_detected (list): Liste des lots détectés
        extracted_data (dict): Données extraites de base
        uploaded_file_name (str): Nom du fichier uploadé
        uploaded_file_size (int): Taille du fichier uploadé
    
    Returns:
        list: Liste des entrées extraites
    """
    extracted_entries = []
    
    for i, lot in enumerate(lots_detected):
        # Créer les données du lot
        lot_data = create_lot_data(lot, extracted_data)
        lot_data['nbr_lots'] = len(lots_detected)
        
        # Créer l'entrée pour ce lot
        extracted_info = {
            'valeurs_extraites': lot_data,
            'valeurs_generees': {},
            'lot_id': f"LOT_{lot.get('numero', i + 1)}",
            'lot_info': lot,
            'extraction_source': lot.get('source', 'ai_extraction'),
            'metadata': {
                'nom_fichier': uploaded_file_name,
                'taille': uploaded_file_size,
                'contenu_extraite': {'type': 'pdf_avance'},
                'erreur': None
            }
        }
        extracted_entries.append(extracted_info)
    
    return extracted_entries

def create_default_lot(extracted_data, uploaded_file_name, uploaded_file_size):
    """
    Crée un lot par défaut quand aucun lot n'est détecté
    
    Args:
        extracted_data (dict): Données extraites de base
        uploaded_file_name (str): Nom du fichier uploadé
        uploaded_file_size (int): Taille du fichier uploadé
    
    Returns:
        list: Liste avec un lot par défaut
    """
    # Créer un lot par défaut avec les données extraites
    default_lot_data = extracted_data.copy()
    default_lot_data['nbr_lots'] = 1
    default_lot_data['lot_numero'] = 1
    default_lot_data['intitule_lot'] = extracted_data.get('intitule_procedure', 'Lot unique')
    
    # Ajouter les critères par défaut si pas trouvés
    for field in ['criteres_economique', 'criteres_techniques', 'autres_criteres']:
        if field not in default_lot_data:
            default_lot_data[field] = ''
    
    lot_info = {
        'numero': 1,
        'intitule': default_lot_data.get('intitule_procedure', 'Lot unique'),
        'montant_estime': default_lot_data.get('montant_global_estime', 0),
        'montant_maximum': default_lot_data.get('montant_global_maxi', 0),
        'criteres_economique': default_lot_data.get('criteres_economique', ''),
        'criteres_techniques': default_lot_data.get('criteres_techniques', ''),
        'autres_criteres': default_lot_data.get('autres_criteres', ''),
        'source': 'default_lot'
    }
    
    extracted_info = {
        'valeurs_extraites': default_lot_data,
        'valeurs_generees': {},
        'lot_id': 'LOT_1',
        'lot_info': lot_info,
        'extraction_source': 'default_lot',
        'metadata': {
            'nom_fichier': uploaded_file_name,
            'taille': uploaded_file_size,
            'contenu_extraite': {'type': 'pdf_avance'},
            'erreur': None
        }
    }
    
    return [extracted_info]

def create_metric_columns(metrics_data):
    """
    Crée des colonnes de métriques de manière réutilisable
    
    Args:
        metrics_data (list): Liste des métriques à afficher
    """
    if len(metrics_data) == 4:
        col1, col2, col3, col4 = st.columns(4)
        columns = [col1, col2, col3, col4]
    elif len(metrics_data) == 3:
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]
    else:
        columns = st.columns(len(metrics_data))
    
    for i, metric in enumerate(metrics_data):
        with columns[i]:
            st.metric(metric['label'], metric['value'])

def create_lot_editor(lot, lot_idx, i, total_lots):
    """
    Composant réutilisable pour l'édition des lots
    
    Args:
        lot (dict): Données du lot
        lot_idx (int): Index du lot
        i (int): Index de l'entrée
        total_lots (int): Nombre total de lots
    """
    with st.expander(f"📦 Lot {lot['numero']}: {lot['intitule'][:50]}{'...' if len(lot['intitule']) > 50 else ''}", expanded=lot_idx == 0):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📋 Informations du lot")
            
            # Numéro de lot
            new_numero = st.number_input(
                f"Numéro du lot",
                value=lot['numero'],
                min_value=1,
                max_value=100,
                key=f"lot_numero_{i}_{lot_idx}"
            )
            st.session_state[f'lots_list_{i}'][lot_idx]['numero'] = new_numero
            
            # Intitulé du lot
            new_intitule = st.text_area(
                f"Intitulé du lot", 
                value=lot['intitule'],
                key=f"lot_intitule_{i}_{lot_idx}",
                height=100
            )
            st.session_state[f'lots_list_{i}'][lot_idx]['intitule'] = new_intitule
            
            # Attributaire
            new_attributaire = st.text_input(
                f"Attributaire", 
                value=lot['attributaire'],
                key=f"lot_attributaire_{i}_{lot_idx}"
            )
            st.session_state[f'lots_list_{i}'][lot_idx]['attributaire'] = new_attributaire
        
        with col2:
            st.markdown("#### 📝 Détails du lot")
            
            # Produit retenu
            new_produit = st.text_input(
                f"Produit retenu", 
                value=lot['produit_retenu'],
                key=f"lot_produit_{i}_{lot_idx}"
            )
            st.session_state[f'lots_list_{i}'][lot_idx]['produit_retenu'] = new_produit
            
            # Infos complémentaires
            new_infos = st.text_area(
                f"Infos complémentaires", 
                value=lot['infos_complementaires'],
                key=f"lot_infos_{i}_{lot_idx}",
                height=100
            )
            st.session_state[f'lots_list_{i}'][lot_idx]['infos_complementaires'] = new_infos
            
            # Montants du lot
            st.markdown("#### 💰 Montants du lot")
            
            col_montant1, col_montant2 = st.columns(2)
            
            with col_montant1:
                montant_estime = st.number_input(
                    f"Montant estimé (€)", 
                    value=float(lot.get('montant_estime', 0)),
                    min_value=0.0,
                    step=1000.0,
                    key=f"lot_montant_estime_{i}_{lot_idx}"
                )
                st.session_state[f'lots_list_{i}'][lot_idx]['montant_estime'] = montant_estime
            
            with col_montant2:
                montant_maximum = st.number_input(
                    f"Montant maximum (€)", 
                    value=float(lot.get('montant_maximum', 0)),
                    min_value=0.0,
                    step=1000.0,
                    key=f"lot_montant_maximum_{i}_{lot_idx}"
                )
                st.session_state[f'lots_list_{i}'][lot_idx]['montant_maximum'] = montant_maximum
            
            # Quantités du lot
            st.markdown("#### 📊 Quantités du lot")
            
            col_qte1, col_qte2, col_qte3 = st.columns(3)
            
            with col_qte1:
                quantite_minimum = st.number_input(
                    f"Quantité minimum", 
                    value=int(lot.get('quantite_minimum', 0)) if lot.get('quantite_minimum') else 0,
                    min_value=0,
                    key=f"lot_quantite_minimum_{i}_{lot_idx}"
                )
                st.session_state[f'lots_list_{i}'][lot_idx]['quantite_minimum'] = quantite_minimum
            
            with col_qte2:
                quantites_estimees = st.text_input(
                    f"Quantités estimées", 
                    value=str(lot.get('quantites_estimees', '')),
                    key=f"lot_quantites_estimees_{i}_{lot_idx}"
                )
                st.session_state[f'lots_list_{i}'][lot_idx]['quantites_estimees'] = quantites_estimees
            
            with col_qte3:
                quantite_maximum = st.number_input(
                    f"Quantité maximum", 
                    value=int(lot.get('quantite_maximum', 0)) if lot.get('quantite_maximum') else 0,
                    min_value=0,
                    key=f"lot_quantite_maximum_{i}_{lot_idx}"
                )
                st.session_state[f'lots_list_{i}'][lot_idx]['quantite_maximum'] = quantite_maximum
            
            # Critères d'attribution du lot
            st.markdown("#### ⚖️ Critères d'attribution du lot")
            
            col_crit1, col_crit2, col_crit3 = st.columns(3)
            
            with col_crit1:
                criteres_economique = st.text_input(
                    f"Critères économiques", 
                    value=str(lot.get('criteres_economique', '')),
                    key=f"lot_criteres_economique_{i}_{lot_idx}"
                )
                st.session_state[f'lots_list_{i}'][lot_idx]['criteres_economique'] = criteres_economique
            
            with col_crit2:
                criteres_techniques = st.text_input(
                    f"Critères techniques", 
                    value=str(lot.get('criteres_techniques', '')),
                    key=f"lot_criteres_techniques_{i}_{lot_idx}"
                )
                st.session_state[f'lots_list_{i}'][lot_idx]['criteres_techniques'] = criteres_techniques
            
            with col_crit3:
                autres_criteres = st.text_input(
                    f"Autres critères", 
                    value=str(lot.get('autres_criteres', '')),
                    key=f"lot_autres_criteres_{i}_{lot_idx}"
                )
                st.session_state[f'lots_list_{i}'][lot_idx]['autres_criteres'] = autres_criteres
            
            # RSE et contribution fournisseur du lot
            st.markdown("#### 🌱 RSE et contribution fournisseur du lot")
            
            col_rse1, col_rse2 = st.columns(2)
            
            with col_rse1:
                rse = st.text_input(
                    f"RSE", 
                    value=str(lot.get('rse', '')),
                    key=f"lot_rse_{i}_{lot_idx}"
                )
                st.session_state[f'lots_list_{i}'][lot_idx]['rse'] = rse
            
            with col_rse2:
                contribution_fournisseur = st.text_input(
                    f"Contribution fournisseur", 
                    value=str(lot.get('contribution_fournisseur', '')),
                    key=f"lot_contribution_fournisseur_{i}_{lot_idx}"
                )
                st.session_state[f'lots_list_{i}'][lot_idx]['contribution_fournisseur'] = contribution_fournisseur
            
            # Bouton pour supprimer ce lot (si plus d'un lot)
            if total_lots > 1:
                if st.button(f"🗑️ Supprimer ce lot", key=f"del_specific_lot_{i}_{lot_idx}"):
                    st.session_state[f'lots_list_{i}'].pop(lot_idx)
                    st.rerun()

def create_form_field(field_name, field_type, value, key, **kwargs):
    """
    Crée un champ de formulaire de manière réutilisable
    
    Args:
        field_name (str): Nom du champ
        field_type (str): Type du champ (text_input, text_area, selectbox, etc.)
        value: Valeur par défaut
        key (str): Clé unique
        **kwargs: Arguments supplémentaires
    """
    if field_type == 'text_input':
        return st.text_input(field_name, value=value, key=key, **kwargs)
    elif field_type == 'text_area':
        return st.text_area(field_name, value=value, key=key, **kwargs)
    elif field_type == 'selectbox':
        options = kwargs.get('options', [])
        index = kwargs.get('index', 0)
        return st.selectbox(field_name, options=options, index=index, key=key)
    elif field_type == 'number_input':
        return st.number_input(field_name, value=value, key=key, **kwargs)
    elif field_type == 'date_input':
        return st.date_input(field_name, value=value, key=key, **kwargs)
    else:
        return st.text_input(field_name, value=value, key=key, **kwargs)

def collect_all_lots_data(extracted_entries):
    """
    Collecte toutes les données de lots de manière centralisée
    
    Args:
        extracted_entries (list): Liste des entrées extraites
    
    Returns:
        list: Liste de toutes les données de lots
    """
    all_lots_data = []
    
    for i, extracted_info in enumerate(extracted_entries):
        lots_list = st.session_state.get(f'lots_list_{i}', [])
        
        if lots_list:
            # Utiliser les lots spécifiques de cette entrée
            for lot_idx, lot in enumerate(lots_list):
                # Créer les données pour ce lot spécifique
                lot_data = {}
                lot_data.update(extracted_info.get('valeurs_extraites', {}))
                lot_data.update(extracted_info.get('valeurs_generees', {}))
                
                # Remplacer les données générales par les données spécifiques du lot
                lot_data['lot_numero'] = lot.get('numero', lot_idx + 1)
                lot_data['intitule_lot'] = lot.get('intitule', '')
                lot_data['attributaire'] = lot.get('attributaire', '')
                lot_data['produit_retenu'] = lot.get('produit_retenu', '')
                lot_data['infos_complementaires'] = lot.get('infos_complementaires', '')
                lot_data['montant_global_estime'] = lot.get('montant_estime', 0)
                lot_data['montant_global_maxi'] = lot.get('montant_maximum', 0)
                lot_data['quantite_minimum'] = lot.get('quantite_minimum', 0)
                lot_data['quantites_estimees'] = lot.get('quantites_estimees', '')
                lot_data['quantite_maximum'] = lot.get('quantite_maximum', 0)
                lot_data['criteres_economique'] = lot.get('criteres_economique', '')
                lot_data['criteres_techniques'] = lot.get('criteres_techniques', '')
                lot_data['autres_criteres'] = lot.get('autres_criteres', '')
                lot_data['rse'] = lot.get('rse', '')
                lot_data['contribution_fournisseur'] = lot.get('contribution_fournisseur', '')
                
                # Ajouter un identifiant unique pour ce lot
                lot_data['lot_id'] = f"LOT_{lot.get('numero', lot_idx + 1)}"
                lot_data['reference_lot'] = f"{lot_data.get('reference_procedure', 'UNKNOWN')}_LOT_{lot.get('numero', lot_idx + 1)}"
                
                all_lots_data.append(lot_data)
        else:
            # Fallback: utiliser les données existantes si pas de lots détectés
            lot_data = {}
            lot_data.update(extracted_info.get('valeurs_extraites', {}))
            lot_data.update(extracted_info.get('valeurs_generees', {}))
            all_lots_data.append(lot_data)
    
    return all_lots_data

def get_column_mapping():
    """
    Retourne le mapping entre les noms français et techniques des colonnes
    
    Returns:
        dict: Mapping des colonnes
    """
    french_names = COLUMNS_CONFIG['french_names']
    technical_names = COLUMNS_CONFIG['technical_names']
    
    return dict(zip(french_names, technical_names))

def display_ui_message(message_type, message_key, **kwargs):
    """
    Affiche un message d'interface de manière centralisée
    
    Args:
        message_type (str): Type de message (success, warning, error, info)
        message_key (str): Clé du message
        **kwargs: Variables à formater dans le message
    """
    message = UI_MESSAGES[message_type][message_key].format(**kwargs)
    
    if message_type == 'success':
        st.success(message)
    elif message_type == 'warning':
        st.warning(message)
    elif message_type == 'error':
        st.error(message)
    elif message_type == 'info':
        st.info(message)
