"""
🚀 IA Veille Concurrentielle
============================

Application Streamlit avec :
- Modèles IA locaux
- Base de données locale
- Interface moderne
- Performance optimisée
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import json
import logging
from pathlib import Path

# Import des modules locaux
from database_manager import DatabaseManager
from ai_engine import VeilleAIEngine
from ao_extractor_v2 import AOExtractorV2
from extraction_improver import extraction_improver
from universal_criteria_extractor import UniversalCriteriaExtractor

# Import des modules UI
from ui import (
    render_overview_tab,
    render_ai_tab,
    render_stats_tab,
    render_insert_ao_tab,
    render_database_tab
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de la page
st.set_page_config(
    page_title="🚀 IA Conversationnelle - Veille Concurrentielle",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre et description
st.title("🚀 IA Conversationnelle - Veille Concurrentielle")
st.markdown("""
**🤖 Système d'IA ultra performant pour l'analyse d'appels d'offres**
- ✅ **Interface moderne** - Interface intuitive et performante
- 🧠 **IA Locale** - Modèles intégrés et privés
- 🗄️ **Base locale** - Données sécurisées localement
""")

# Initialisation des composants
@st.cache_resource
def init_components():
    """Initialise les composants de l'application"""
    try:
        # Base de données locale
        db_manager = DatabaseManager()
        
        # Moteur IA
        ai_engine = VeilleAIEngine()
        
        # Extracteur de critères universel
        criteria_extractor = UniversalCriteriaExtractor()
        
        return db_manager, ai_engine, criteria_extractor
    except Exception as e:
        st.error(f"❌ Erreur initialisation: {e}")
        return None, None, None

# Fonction pour recharger l'IA avec les nouvelles données
def reload_ai_with_data(ai_engine, data):
    """Recharge l'IA avec les nouvelles données"""
    try:
        ai_engine.initialize(data)
        return True
    except Exception as e:
        st.error(f"❌ Erreur rechargement IA: {e}")
        return False

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Bouton de debug pour vider le cache
    if st.button("🔄 Recharger l'application"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()
    
    # Bouton pour forcer la réinitialisation de l'IA
    if st.button("🧠 Recharger l'IA avec toutes les données"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()
    
    # Section informations système
    st.subheader("📊 Informations Système")
    st.info("""
    **🤖 IA:** Modèles locaux
    **🗄️ Base:** Base locale
    **🚀 Extracteur:** Version V2 (Modulaire)
    """)
    
    # Section nouvelles fonctionnalités V2
    st.subheader("🚀 Nouvelles Fonctionnalités V2")
    st.success("""
    **✅ Architecture modulaire**
    **✅ Détection intelligente des lots**
    **✅ Validation avancée**
    **✅ Patterns optimisés**
    **✅ Performance améliorée**
    """)
    
    # Section filtres
    st.subheader("🔍 Filtres")
    search_query = st.text_input("Recherche textuelle")
    
    # Bouton d'actualisation
    if st.button("🔄 Actualiser les données"):
        st.cache_data.clear()
        st.rerun()

# Initialisation
try:
    db_manager, ai_engine, criteria_extractor = init_components()
    
    if db_manager is None or ai_engine is None:
        st.error("❌ Erreur lors de l'initialisation des composants")
        st.stop()
    
    # Chargement des données
    with st.spinner("📊 Chargement des données depuis la base..."):
        data = db_manager.get_all_data()
        
        if data.empty:
            st.warning("⚠️ Aucune donnée trouvée dans la base. Importez d'abord un fichier Excel.")
            
            # Section d'import
            st.subheader("📥 Import de données")
            uploaded_file = st.file_uploader(
                "Choisissez un fichier Excel à importer",
                type=['xlsx', 'xls'],
                help="Importez votre fichier Excel pour commencer"
            )
            
            if uploaded_file is not None:
                with st.spinner("📊 Import en cours..."):
                    try:
                        # Sauvegarder temporairement le fichier
                        temp_path = f"temp_{uploaded_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Importer dans la base
                        result = db_manager.import_from_excel(temp_path)
                        
                        # Supprimer le fichier temporaire
                        Path(temp_path).unlink()
                        
                        st.success(f"✅ Import réussi: {result['rows_inserted']} lignes importées")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'import: {e}")
            
            st.stop()
        
        # Initialisation de l'extracteur d'AO V2 avec les données de référence ET la BDD
        ao_extractor = AOExtractorV2(reference_data=data, database_manager=db_manager)
        
        # NOUVEAU: Forcer la réinitialisation de l'IA avec toutes les données
        if not hasattr(ai_engine, 'initialized') or not ai_engine.initialized:
            with st.spinner("🧠 Initialisation de l'IA avec toutes les données..."):
                    try:
                        ai_engine.initialize(data, load_heavy_models=False)  # Mode rapide
                        st.success(f"✅ IA initialisée avec {len(data)} documents!")
                    except Exception as e:
                        st.error(f"❌ Erreur initialisation IA: {e}")
        else:
            # Vérifier si l'IA a le bon nombre de documents
            if hasattr(ai_engine, 'corpus') and len(ai_engine.corpus) != len(data):
                with st.spinner("🔄 Mise à jour de l'IA avec les nouvelles données..."):
                    try:
                        ai_engine.initialize(data, load_heavy_models=False)  # Mode rapide
                        st.success(f"✅ IA mise à jour avec {len(data)} documents!")
                    except Exception as e:
                        st.error(f"❌ Erreur mise à jour IA: {e}")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Lots", len(data))
    
    with col2:
        st.metric("📊 Colonnes", len(data.columns))
    
    with col3:
        st.metric("📅 Date", datetime.now().strftime("%d/%m/%Y"))
    
    with col4:
        st.metric("⏰ Heure", datetime.now().strftime("%H:%M"))
    
    # Onglets principaux
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Vue d'ensemble", 
        "🤖 IA", 
        "📈 Statistiques",
        "📥 Insertion AO",
        "🗄️ Base de données"
    ])
    
    # Onglet 1: Vue d'ensemble
    with tab1:
        render_overview_tab(data)
    
    # Onglet 2: IA
    with tab2:
        render_ai_tab(data, ai_engine)
    
    # Onglet 3: Statistiques
    with tab3:
        render_stats_tab(data, db_manager)
        
    
    # Onglet 4: Insertion AO
    with tab4:
        # Afficher l'interface d'upload et extraction (version simplifiée)
        render_insert_ao_tab(data, ao_extractor, criteria_extractor, db_manager)
        
        # Interface d'édition détaillée (reste dans app.py pour la complexité)
        st.markdown("---")
        st.subheader("✏️ Édition Détaillée des Données Extraites")
        
        # Vérifier s'il y a des données extraites en session_state
        extracted_entries_key = 'last_extracted_entries'
        if extracted_entries_key in st.session_state:
            try:
                extracted_entries = st.session_state[extracted_entries_key]
                
                if extracted_entries and not any('erreur' in entry for entry in extracted_entries):
                    # Interface d'édition unique (en dehors de la boucle)
                    if extracted_entries:
                        # Créer un identifiant unique pour cette extraction (basé sur le premier entry)
                        extraction_key = extracted_entries[0].get('lot_id', 'extraction_0')
                        
                        # Utiliser les données du premier lot pour l'édition générale
                        first_entry = extracted_entries[0]
                        all_data = {}
                        valeurs_extraites = first_entry.get('valeurs_extraites', {})
                        valeurs_generees = first_entry.get('valeurs_generees', {})
                        all_data.update(valeurs_extraites)
                        all_data.update(valeurs_generees)
                        
                        if all_data:
                            # Interface d'édition des colonnes
                            st.subheader("✏️ Édition des Données Extraites")
                            
                            # Initialiser les données éditées
                            edited_data = {}
                            
                            # Gestion des lots en dehors du formulaire
                            st.subheader("📦 Gestion des Lots")
                            
                            # Initialiser la liste des lots dans session_state si nécessaire
                            if f'lots_list_{extraction_key}' not in st.session_state:
                                # Créer les lots directement depuis extracted_entries
                                existing_lots = []
                                
                                for j, entry in enumerate(extracted_entries):
                                    valeurs_lot = entry.get('valeurs_extraites', {})
                                    lot_info = entry.get('lot_info', {})
                                    
                                    # Créer le lot depuis les données extraites ou lot_info
                                    lot = {
                                        'numero': valeurs_lot.get('lot_numero') or lot_info.get('numero', j + 1) if lot_info else j + 1,
                                        'intitule': valeurs_lot.get('intitule_lot', '') or (lot_info.get('intitule', '') if lot_info else ''),
                                        'attributaire': valeurs_lot.get('attributaire', '') or (lot_info.get('attributaire', '') if lot_info else ''),
                                        'produit_retenu': valeurs_lot.get('produit_retenu', '') or (lot_info.get('produit_retenu', '') if lot_info else ''),
                                        'infos_complementaires': valeurs_lot.get('infos_complementaires', '') or (lot_info.get('infos_complementaires', '') if lot_info else ''),
                                        'montant_estime': valeurs_lot.get('montant_global_estime', 0) or (lot_info.get('montant_estime', 0) if lot_info else 0),
                                        'montant_maximum': valeurs_lot.get('montant_global_maxi', 0) or (lot_info.get('montant_maximum', 0) if lot_info else 0),
                                        'quantite_minimum': valeurs_lot.get('quantite_minimum', 0) or (lot_info.get('quantite_minimum', 0) if lot_info else 0),
                                        'quantites_estimees': valeurs_lot.get('quantites_estimees', '') or (lot_info.get('quantites_estimees', '') if lot_info else ''),
                                        'quantite_maximum': valeurs_lot.get('quantite_maximum', 0) or (lot_info.get('quantite_maximum', 0) if lot_info else 0),
                                        'criteres_economique': valeurs_lot.get('criteres_economique', '') or (lot_info.get('criteres_economique', '') if lot_info else ''),
                                        'criteres_techniques': valeurs_lot.get('criteres_techniques', '') or (lot_info.get('criteres_techniques', '') if lot_info else ''),
                                        'autres_criteres': valeurs_lot.get('autres_criteres', '') or (lot_info.get('autres_criteres', '') if lot_info else ''),
                                        'rse': valeurs_lot.get('rse', '') or (lot_info.get('rse', '') if lot_info else ''),
                                        'contribution_fournisseur': valeurs_lot.get('contribution_fournisseur', '') or (lot_info.get('contribution_fournisseur', '') if lot_info else '')
                                    }
                                    existing_lots.append(lot)
                                
                                # S'assurer qu'on a au moins un lot (fallback si aucune entrée)
                                if not existing_lots:
                                    default_lot = {
                                        'numero': int(all_data.get('lot_numero', 1)) if all_data.get('lot_numero') else 1,
                                        'intitule': all_data.get('intitule_lot', ''),
                                        'attributaire': all_data.get('attributaire', ''),
                                        'produit_retenu': all_data.get('produit_retenu', ''),
                                        'infos_complementaires': all_data.get('infos_complementaires', ''),
                                        'montant_estime': all_data.get('montant_global_estime', 0),
                                        'montant_maximum': all_data.get('montant_global_maxi', 0),
                                        'quantite_minimum': all_data.get('quantite_minimum', 0),
                                        'quantites_estimees': all_data.get('quantites_estimees', ''),
                                        'quantite_maximum': all_data.get('quantite_maximum', 0),
                                        'criteres_economique': all_data.get('criteres_economique', ''),
                                        'criteres_techniques': all_data.get('criteres_techniques', ''),
                                        'autres_criteres': all_data.get('autres_criteres', ''),
                                        'rse': all_data.get('rse', ''),
                                        'contribution_fournisseur': all_data.get('contribution_fournisseur', '')
                                    }
                                    existing_lots = [default_lot]
                                
                                st.session_state[f'lots_list_{extraction_key}'] = existing_lots
                                logger.info(f"✅ {len(existing_lots)} lots initialisés depuis extracted_entries")
                            
                            # Utiliser extraction_key au lieu de i partout
                            lots_key = f'lots_list_{extraction_key}'
                            
                            # Afficher le nombre total de lots
                            total_lots = len(st.session_state[lots_key])
                            
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.metric("📊 Nombre total de lots", total_lots)
                            with col2:
                                if st.button("➕ Ajouter un lot", key=f"add_lot_{extraction_key}"):
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
                                    st.session_state[lots_key].append(new_lot)
                                    st.rerun()
                            with col3:
                                if st.button("🗑️ Supprimer dernier", key=f"del_lot_{extraction_key}"):
                                    if total_lots > 1:
                                        st.session_state[lots_key].pop()
                                        st.rerun()
                            
                            # Afficher chaque lot
                            for lot_idx, lot in enumerate(st.session_state[lots_key]):
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
                                        key=f"lot_numero_{extraction_key}_{lot_idx}"
                                    )
                                    st.session_state[lots_key][lot_idx]['numero'] = new_numero
                                    
                                    # Intitulé du lot
                                    new_intitule = st.text_area(
                                        f"Intitulé du lot", 
                                        value=lot['intitule'],
                                        key=f"lot_intitule_{extraction_key}_{lot_idx}",
                                        height=100
                                    )
                                    st.session_state[lots_key][lot_idx]['intitule'] = new_intitule
                                    
                                    # Attributaire
                                    new_attributaire = st.text_input(
                                        f"Attributaire", 
                                        value=lot['attributaire'],
                                        key=f"lot_attributaire_{extraction_key}_{lot_idx}"
                                    )
                                    st.session_state[lots_key][lot_idx]['attributaire'] = new_attributaire
                                
                                with col2:
                                                    st.markdown("#### 📝 Détails du lot")
                                                    
                                                    # Produit retenu
                                                    new_produit = st.text_input(
                                                        f"Produit retenu", 
                                                        value=lot['produit_retenu'],
                                                        key=f"lot_produit_{extraction_key}_{lot_idx}"
                                                    )
                                                    st.session_state[lots_key][lot_idx]['produit_retenu'] = new_produit
                                                    
                                                    # Infos complémentaires
                                                    new_infos = st.text_area(
                                                        f"Infos complémentaires", 
                                                        value=lot['infos_complementaires'],
                                                        key=f"lot_infos_{extraction_key}_{lot_idx}",
                                                        height=100
                                                    )
                                                    st.session_state[lots_key][lot_idx]['infos_complementaires'] = new_infos
                                                    
                                                    # Montants du lot
                                                    st.markdown("#### 💰 Montants du lot")
                                                    
                                                    col_montant1, col_montant2 = st.columns(2)
                                                    
                                                    with col_montant1:
                                                        montant_estime = st.number_input(
                                                            f"Montant estimé (€)", 
                                                            value=float(lot.get('montant_estime', 0)),
                                                            min_value=0.0,
                                                            step=1000.0,
                                                            key=f"lot_montant_estime_{extraction_key}_{lot_idx}"
                                                        )
                                                        st.session_state[lots_key][lot_idx]['montant_estime'] = montant_estime
                                                    
                                                    with col_montant2:
                                                        montant_maximum = st.number_input(
                                                            f"Montant maximum (€)", 
                                                            value=float(lot.get('montant_maximum', 0)),
                                                            min_value=0.0,
                                                            step=1000.0,
                                                            key=f"lot_montant_maximum_{extraction_key}_{lot_idx}"
                                                        )
                                                        st.session_state[lots_key][lot_idx]['montant_maximum'] = montant_maximum
                                                    
                                                    # Quantités du lot
                                                    st.markdown("#### 📊 Quantités du lot")
                                                    
                                                    col_qte1, col_qte2, col_qte3 = st.columns(3)
                                                    
                                                    with col_qte1:
                                                        quantite_minimum = st.number_input(
                                                            f"Quantité minimum", 
                                                            value=int(lot.get('quantite_minimum', 0)) if lot.get('quantite_minimum') else 0,
                                                            min_value=0,
                                                            key=f"lot_quantite_minimum_{extraction_key}_{lot_idx}"
                                                        )
                                                        st.session_state[lots_key][lot_idx]['quantite_minimum'] = quantite_minimum
                                                    
                                                    with col_qte2:
                                                        quantites_estimees = st.text_input(
                                                            f"Quantités estimées", 
                                                            value=str(lot.get('quantites_estimees', '')),
                                                            key=f"lot_quantites_estimees_{extraction_key}_{lot_idx}"
                                                        )
                                                        st.session_state[lots_key][lot_idx]['quantites_estimees'] = quantites_estimees
                                                    
                                                    with col_qte3:
                                                        quantite_maximum = st.number_input(
                                                            f"Quantité maximum", 
                                                            value=int(lot.get('quantite_maximum', 0)) if lot.get('quantite_maximum') else 0,
                                                            min_value=0,
                                                            key=f"lot_quantite_maximum_{extraction_key}_{lot_idx}"
                                                        )
                                                        st.session_state[lots_key][lot_idx]['quantite_maximum'] = quantite_maximum
                                                    
                                                    # Critères d'attribution du lot
                                                    st.markdown("#### ⚖️ Critères d'attribution du lot")
                                                    
                                                    col_crit1, col_crit2, col_crit3 = st.columns(3)
                                                    
                                                    with col_crit1:
                                                        criteres_economique = st.text_input(
                                                            f"Critères économiques", 
                                                            value=str(lot.get('criteres_economique', '')),
                                                            key=f"lot_criteres_economique_{extraction_key}_{lot_idx}"
                                                        )
                                                        st.session_state[lots_key][lot_idx]['criteres_economique'] = criteres_economique
                                                    
                                                    with col_crit2:
                                                        criteres_techniques = st.text_input(
                                                            f"Critères techniques", 
                                                            value=str(lot.get('criteres_techniques', '')),
                                                            key=f"lot_criteres_techniques_{extraction_key}_{lot_idx}"
                                                        )
                                                        st.session_state[lots_key][lot_idx]['criteres_techniques'] = criteres_techniques
                                                    
                                                    with col_crit3:
                                                        autres_criteres = st.text_input(
                                                            f"Autres critères", 
                                                            value=str(lot.get('autres_criteres', '')),
                                                            key=f"lot_autres_criteres_{extraction_key}_{lot_idx}"
                                                        )
                                                        st.session_state[lots_key][lot_idx]['autres_criteres'] = autres_criteres
                                                    
                                                    # RSE et contribution fournisseur du lot
                                                    st.markdown("#### 🌱 RSE et contribution fournisseur du lot")
                                                    
                                                    col_rse1, col_rse2 = st.columns(2)
                                                    
                                                    with col_rse1:
                                                        rse = st.text_input(
                                                            f"RSE", 
                                                            value=str(lot.get('rse', '')),
                                                            key=f"lot_rse_{extraction_key}_{lot_idx}"
                                                        )
                                                        st.session_state[lots_key][lot_idx]['rse'] = rse
                                                    
                                                    with col_rse2:
                                                        contribution_fournisseur = st.text_input(
                                                            f"Contribution fournisseur", 
                                                            value=str(lot.get('contribution_fournisseur', '')),
                                                            key=f"lot_contribution_fournisseur_{extraction_key}_{lot_idx}"
                                                        )
                                                        st.session_state[lots_key][lot_idx]['contribution_fournisseur'] = contribution_fournisseur
                                                    
                                                    # Bouton pour supprimer ce lot (si plus d'un lot)
                                                    if total_lots > 1:
                                                        if st.button(f"🗑️ Supprimer ce lot", key=f"del_specific_lot_{extraction_key}_{lot_idx}"):
                                                            st.session_state[lots_key].pop(lot_idx)
                                                            st.rerun()
                            
                            # Créer un formulaire d'édition complet avec toutes les 44 colonnes
                            with st.form(f"edit_extracted_data_{extraction_key}"):
                                st.write("**Modifiez les valeurs extraites ci-dessous :**")
                                
                                # Créer des onglets pour organiser les 44 colonnes
                                tab_gen, tab_dates, tab_autres = st.tabs([
                                    "📋 Général", "📅 Dates", "📝 Autres"
                                ])
                                
                                # Onglet 1: Informations générales
                                with tab_gen:
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("#### 📋 Informations de base")
                                        
                                        # Mots clés
                                        edited_data['mots_cles'] = st.text_input(
                                            "Mots clés", 
                                            value=all_data.get('mots_cles', ''),
                                            key=f"edit_mots_cles_{extraction_key}"
                                        )
                                        
                                        # Univers
                                        edited_data['univers'] = st.selectbox(
                                            "Univers",
                                            options=['MÉDICAL', 'TECHNIQUE', 'GÉNÉRAL', 'INFORMATIQUE', 'LOGISTIQUE', 'MAINTENANCE', 'AUTRE'],
                                            index=['MÉDICAL', 'TECHNIQUE', 'GÉNÉRAL', 'INFORMATIQUE', 'LOGISTIQUE', 'MAINTENANCE', 'AUTRE'].index(all_data.get('univers', 'MÉDICAL')) if all_data.get('univers') in ['MÉDICAL', 'TECHNIQUE', 'GÉNÉRAL', 'INFORMATIQUE', 'LOGISTIQUE', 'MAINTENANCE', 'AUTRE'] else 0,
                                            key=f"edit_univers_{extraction_key}"
                                        )
                                        
                                        # Segment
                                        edited_data['segment'] = st.text_input(
                                            "Segment", 
                                            value=all_data.get('segment', ''),
                                            key=f"edit_segment_{extraction_key}"
                                        )
                                        
                                        # Famille
                                        edited_data['famille'] = st.text_input(
                                            "Famille", 
                                            value=all_data.get('famille', ''),
                                            key=f"edit_famille_{extraction_key}"
                                        )
                                        
                                        # Statut
                                        edited_data['statut'] = st.selectbox(
                                            "Statut",
                                            options=['AO EN COURS', 'AO ATTRIBUÉ', 'AO ANNULÉ', 'AO REPORTÉ', 'AO SUSPENDU', 'AO CLÔTURÉ'],
                                            index=['AO EN COURS', 'AO ATTRIBUÉ', 'AO ANNULÉ', 'AO REPORTÉ', 'AO SUSPENDU', 'AO CLÔTURÉ'].index(all_data.get('statut', 'AO EN COURS')) if all_data.get('statut') in ['AO EN COURS', 'AO ATTRIBUÉ', 'AO ANNULÉ', 'AO REPORTÉ', 'AO SUSPENDU', 'AO CLÔTURÉ'] else 0,
                                            key=f"edit_statut_{extraction_key}"
                                        )
                                        
                                        # Groupement
                                        edited_data['groupement'] = st.selectbox(
                                            "Groupement",
                                            options=['RESAH', 'UNIHA', 'UGAP', 'CAIH', 'AUTRE'],
                                            index=['RESAH', 'UNIHA', 'UGAP', 'CAIH', 'AUTRE'].index(all_data.get('groupement', 'RESAH')) if all_data.get('groupement') in ['RESAH', 'UNIHA', 'UGAP', 'CAIH', 'AUTRE'] else 0,
                                            key=f"edit_groupement_{extraction_key}"
                                        )
                                        
                                        with col2:
                                            st.markdown("#### 📄 Procédure")
                                            
                                            # Référence de procédure
                                            edited_data['reference_procedure'] = st.text_input(
                                                "Référence de procédure", 
                                                value=all_data.get('reference_procedure', ''),
                                                key=f"edit_ref_proc_{extraction_key}"
                                            )
                                            
                                            # Type de procédure
                                            edited_data['type_procedure'] = st.selectbox(
                                                "Type de procédure",
                                                options=['Appel d\'offres ouvert', 'Appel d\'offres restreint', 'Procédure adaptée', 'Marché de gré à gré', 'Accord-cadre'],
                                                index=['Appel d\'offres ouvert', 'Appel d\'offres restreint', 'Procédure adaptée', 'Marché de gré à gré', 'Accord-cadre'].index(all_data.get('type_procedure', 'Appel d\'offres ouvert')) if all_data.get('type_procedure') in ['Appel d\'offres ouvert', 'Appel d\'offres restreint', 'Procédure adaptée', 'Marché de gré à gré', 'Accord-cadre'] else 0,
                                                key=f"edit_type_proc_{extraction_key}"
                                            )
                                            
                                            # Mono ou multi-attributif
                                            edited_data['mono_multi'] = st.selectbox(
                                                "Mono ou multi-attributif",
                                                options=['Mono-attributif', 'Multi-attributif'],
                                                index=['Mono-attributif', 'Multi-attributif'].index(all_data.get('mono_multi', 'Multi-attributif')) if all_data.get('mono_multi') in ['Mono-attributif', 'Multi-attributif'] else 1,
                                                key=f"edit_mono_multi_{extraction_key}"
                                            )
                                            
                                            # Exécution du marché
                                            edited_data['execution_marche'] = st.text_input(
                                                "Exécution du marché", 
                                                value=all_data.get('execution_marche', ''),
                                                key=f"edit_execution_marche_{extraction_key}"
                                            )
                                            
                                            # Intitulé de procédure
                                            edited_data['intitule_procedure'] = st.text_area(
                                                "Intitulé de procédure", 
                                                value=all_data.get('intitule_procedure', ''),
                                                key=f"edit_int_proc_{extraction_key}",
                                                height=100
                                            )
                                    
                                    # Onglet 2: Dates
                                    with tab_dates:
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown("#### 📅 Dates importantes")
                                            
                                            # Date limite
                                            edited_data['date_limite'] = st.date_input(
                                                "Date limite de remise des offres",
                                                value=pd.to_datetime(all_data.get('date_limite', '2024-12-31')).date() if all_data.get('date_limite') else pd.to_datetime('2024-12-31').date(),
                                                key=f"edit_date_limite_{extraction_key}"
                                            )
                                            
                                            # Date d'attribution
                                            edited_data['date_attribution'] = st.date_input(
                                                "Date d'attribution du marché",
                                                value=pd.to_datetime(all_data.get('date_attribution', '2024-12-31')).date() if all_data.get('date_attribution') else None,
                                                key=f"edit_date_attribution_{extraction_key}"
                                            )
                                            
                                            # Durée du marché
                                            edited_data['duree_marche'] = st.number_input(
                                                "Durée du marché (mois)",
                                                value=int(all_data.get('duree_marche', 0)) if all_data.get('duree_marche') else 0,
                                                min_value=0,
                                                max_value=120,
                                                key=f"edit_duree_marche_{extraction_key}"
                                            )
                                        
                                        with col2:
                                            st.markdown("#### 🔄 Reconduction")
                                            
                                            # Reconduction
                                            edited_data['reconduction'] = st.selectbox(
                                                "Reconduction",
                                                options=['Oui', 'Non', 'Non spécifié'],
                                                index=['Oui', 'Non', 'Non spécifié'].index(all_data.get('reconduction', 'Non spécifié')) if all_data.get('reconduction') in ['Oui', 'Non', 'Non spécifié'] else 2,
                                                key=f"edit_reconduction_{extraction_key}"
                                            )
                                            
                                            # Fin sans reconduction
                                            edited_data['fin_sans_reconduction'] = st.date_input(
                                                "Fin (sans reconduction)",
                                                value=pd.to_datetime(all_data.get('fin_sans_reconduction')).date() if all_data.get('fin_sans_reconduction') else None,
                                                key=f"edit_fin_sans_reconduction_{extraction_key}"
                                            )
                                            
                                            # Fin avec reconduction
                                            edited_data['fin_avec_reconduction'] = st.date_input(
                                                "Fin (avec reconduction)",
                                                value=pd.to_datetime(all_data.get('fin_avec_reconduction')).date() if all_data.get('fin_avec_reconduction') else None,
                                                key=f"edit_fin_avec_reconduction_{extraction_key}"
                                            )
                                    
                                    # Onglet 3: Autres informations
                                    with tab_autres:
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown("#### 📝 Notes et remarques")
                                            
                                            # Remarques
                                            edited_data['remarques'] = st.text_area(
                                                "Remarques", 
                                                value=all_data.get('remarques', ''),
                                                key=f"edit_remarques_{extraction_key}",
                                                height=100
                                            )
                                            
                                            # Notes de l'acheteur sur la procédure
                                            edited_data['notes_acheteur_procedure'] = st.text_area(
                                                "Notes de l'acheteur sur la procédure", 
                                                value=all_data.get('notes_acheteur_procedure', ''),
                                                key=f"edit_notes_acheteur_procedure_{extraction_key}",
                                                height=100
                                            )
                                            
                                            # Notes de l'acheteur sur le fournisseur
                                            edited_data['notes_acheteur_fournisseur'] = st.text_area(
                                                "Notes de l'acheteur sur le fournisseur", 
                                                value=all_data.get('notes_acheteur_fournisseur', ''),
                                                key=f"edit_notes_acheteur_fournisseur_{extraction_key}",
                                                height=100
                                            )
                                        
                                        with col2:
                                            st.markdown("#### 📊 Autres informations")
                                            
                                            # Notes de l'acheteur sur le positionnement
                                            edited_data['notes_acheteur_positionnement'] = st.text_area(
                                                "Notes de l'acheteur sur le positionnement", 
                                                value=all_data.get('notes_acheteur_positionnement', ''),
                                                key=f"edit_notes_acheteur_positionnement_{extraction_key}",
                                                height=100
                                            )
                                            
                                            # Note Veille concurrentielle
                                            edited_data['note_veille'] = st.text_input(
                                                "Note Veille concurrentielle disponible", 
                                                value=all_data.get('note_veille', ''),
                                                key=f"edit_note_veille_{extraction_key}"
                                            )
                                            
                                            # Achat
                                            edited_data['achat'] = st.selectbox(
                                                "Achat",
                                                options=['Oui', 'Non', 'Non spécifié'],
                                                index=['Oui', 'Non', 'Non spécifié'].index(all_data.get('achat', 'Non spécifié')) if all_data.get('achat') in ['Oui', 'Non', 'Non spécifié'] else 2,
                                                key=f"edit_achat_{extraction_key}"
                                            )
                                            
                                            # Crédit bail
                                            edited_data['credit_bail'] = st.selectbox(
                                                "Crédit bail",
                                                options=['Oui', 'Non', 'Non spécifié'],
                                                index=['Oui', 'Non', 'Non spécifié'].index(all_data.get('credit_bail', 'Non spécifié')) if all_data.get('credit_bail') in ['Oui', 'Non', 'Non spécifié'] else 2,
                                                key=f"edit_credit_bail_{extraction_key}"
                                            )
                                            
                                            # Crédit bail durée
                                            edited_data['credit_bail_duree'] = st.number_input(
                                                "Crédit bail (durée année)",
                                                value=int(all_data.get('credit_bail_duree', 0)) if all_data.get('credit_bail_duree') else 0,
                                                min_value=0,
                                                max_value=20,
                                                key=f"edit_credit_bail_duree_{extraction_key}"
                                            )
                                            
                                            # Location
                                            edited_data['location'] = st.selectbox(
                                                "Location",
                                                options=['Oui', 'Non', 'Non spécifié'],
                                                index=['Oui', 'Non', 'Non spécifié'].index(all_data.get('location', 'Non spécifié')) if all_data.get('location') in ['Oui', 'Non', 'Non spécifié'] else 2,
                                                key=f"edit_location_{extraction_key}"
                                            )
                                            
                                            # Location durée
                                            edited_data['location_duree'] = st.number_input(
                                                "Location (durée années)",
                                                value=int(all_data.get('location_duree', 0)) if all_data.get('location_duree') else 0,
                                                min_value=0,
                                                max_value=20,
                                                key=f"edit_location_duree_{extraction_key}"
                                            )
                                            
                                            # MAD
                                            edited_data['mad'] = st.selectbox(
                                                "MAD",
                                                options=['Oui', 'Non', 'Non spécifié'],
                                                index=['Oui', 'Non', 'Non spécifié'].index(all_data.get('mad', 'Non spécifié')) if all_data.get('mad') in ['Oui', 'Non', 'Non spécifié'] else 2,
                                                key=f"edit_mad_{extraction_key}"
                                            )
                                    
                                    # Mettre à jour les données des lots depuis session_state
                                    if lots_key in st.session_state:
                                        edited_data['lots'] = st.session_state[lots_key]
                                        edited_data['nbr_lots'] = len(st.session_state[lots_key])
                                        
                                        # Pour la compatibilité avec l'ancien système, garder les champs principaux
                                        if st.session_state[lots_key]:
                                            premier_lot = st.session_state[lots_key][0]
                                            edited_data['lot_numero'] = premier_lot['numero']
                                            edited_data['intitule_lot'] = premier_lot['intitule']
                                            edited_data['attributaire'] = premier_lot['attributaire']
                                            edited_data['produit_retenu'] = premier_lot['produit_retenu']
                                            edited_data['infos_complementaires'] = premier_lot['infos_complementaires']
                                            
                                            # NOUVEAU: Ajouter les montants du premier lot
                                            edited_data['montant_global_estime'] = premier_lot.get('montant_estime', 0)
                                            edited_data['montant_global_maxi'] = premier_lot.get('montant_maximum', 0)
                                            
                                            # NOUVEAU: Ajouter les quantités du premier lot
                                            edited_data['quantite_minimum'] = premier_lot.get('quantite_minimum', 0)
                                            edited_data['quantites_estimees'] = premier_lot.get('quantites_estimees', '')
                                            edited_data['quantite_maximum'] = premier_lot.get('quantite_maximum', 0)
                                            
                                            # NOUVEAU: Ajouter les critères du premier lot
                                            edited_data['criteres_economique'] = premier_lot.get('criteres_economique', '')
                                            edited_data['criteres_techniques'] = premier_lot.get('criteres_techniques', '')
                                            edited_data['autres_criteres'] = premier_lot.get('autres_criteres', '')
                                            
                                            # NOUVEAU: Ajouter RSE et contribution du premier lot
                                            edited_data['rse'] = premier_lot.get('rse', '')
                                            edited_data['contribution_fournisseur'] = premier_lot.get('contribution_fournisseur', '')
                                            
                                            # Calculer le total des montants de tous les lots
                                            total_estime = sum(lot.get('montant_estime', 0) for lot in st.session_state[lots_key])
                                            total_maximum = sum(lot.get('montant_maximum', 0) for lot in st.session_state[lots_key])
                                            edited_data['montant_total_estime'] = total_estime
                                            edited_data['montant_total_maximum'] = total_maximum
                                    
                                    # Boutons d'action
                                    col_save, col_reset, col_export = st.columns(3)
                                    
                                    with col_save:
                                        save_button = st.form_submit_button("💾 Sauvegarder les modifications", type="primary")
                                    
                                    with col_reset:
                                        reset_button = st.form_submit_button("🔄 Réinitialiser")
                                    
                                    with col_export:
                                        export_button = st.form_submit_button("📤 Exporter CSV")
                                    
                                    # Actions
                                    if save_button:
                                        # Mettre à jour all_data avec les modifications
                                        all_data.update(edited_data)
                                        
                                        # Sauvegarder dans la base de données
                                        try:
                                            # Convertir les dates en format string pour la base
                                            for date_field in ['date_limite', 'date_attribution']:
                                                if all_data.get(date_field):
                                                    if hasattr(all_data[date_field], 'strftime'):
                                                        all_data[date_field] = all_data[date_field].strftime('%Y-%m-%d')
                                            
                                            # Insérer dans la base de données
                                            db_manager = DatabaseManager()
                                            success = db_manager.insert_appel_offre(all_data)
                                            
                                            if success:
                                                st.success("✅ Données sauvegardées dans la base de données avec succès !")
                                            else:
                                                st.warning("⚠️ Données mises à jour localement mais erreur lors de la sauvegarde en base")
                                        except Exception as e:
                                            st.error(f"❌ Erreur lors de la sauvegarde en base : {str(e)}")
                                            st.info("💡 Les données sont mises à jour localement")
                                        
                                        st.rerun()
                                    
                                    if reset_button:
                                        st.rerun()
                                    
                                    if export_button:
                                        # Exporter en CSV
                                        df_export = pd.DataFrame([all_data])
                                        csv = df_export.to_csv(index=False)
                                        st.download_button(
                                            label="📥 Télécharger CSV",
                                            data=csv,
                                            file_name=f"extraction_{all_data.get('reference_procedure', 'unknown')}.csv",
                                            mime="text/csv"
                                        )
                        
                        # Afficher les données finales
                        st.subheader("📊 Données Finales")
                        
                        # NOUVEAU: Créer un DataFrame avec toutes les lignes des lots
                        lots_list = st.session_state.get(lots_key, [])
                        first_entry = extracted_entries[0] if extracted_entries else None
                        extracted_info = first_entry if first_entry else {}
                        
                        if lots_list:
                            # Créer une ligne par lot
                            all_lots_data = []
                            
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
                            
                            # Créer le DataFrame avec toutes les lignes
                            df_all_lots = pd.DataFrame(all_lots_data)
                            
                            st.info(f"📋 **{len(lots_list)} lots détectés** - Chaque ligne représente un lot")
                            
                        else:
                            # Fallback: utiliser les données existantes si pas de lots détectés
                            df_all_lots = pd.DataFrame([all_data])
                            st.info("📋 **1 lot unique** détecté")
                        
                        # Option pour afficher toutes les colonnes
                        show_all_columns = st.checkbox("🔍 Afficher toutes les 44 colonnes", value=False)
                        
                        # Initialiser la clé pour le DataFrame éditable dans session_state
                        df_editable_key = f'df_editable_{extraction_key}'
                        # Mettre à jour le DataFrame si les données ont changé (basé sur le nombre de lots)
                        current_lots_count = len(lots_list) if lots_list else 1
                        if (df_editable_key not in st.session_state or 
                            len(st.session_state[df_editable_key]) != current_lots_count):
                            st.session_state[df_editable_key] = df_all_lots.copy()
                        
                        if show_all_columns:
                            # Créer un DataFrame avec toutes les colonnes de la base de données
                            all_columns = [
                                'mots_cles', 'univers', 'segment', 'famille', 'statut', 'groupement',
                                'reference_procedure', 'type_procedure', 'mono_multi', 'execution_marche',
                                'date_limite', 'date_attribution', 'duree_marche', 'reconduction',
                                'fin_sans_reconduction', 'fin_avec_reconduction', 'nbr_lots',
                                'intitule_procedure', 'lot_numero', 'intitule_lot',
                                'montant_global_estime', 'montant_global_maxi', 'achat', 'credit_bail',
                                'credit_bail_duree', 'location', 'location_duree', 'mad',
                                'quantite_minimum', 'quantites_estimees', 'quantite_maximum',
                                'criteres_economique', 'criteres_techniques', 'autres_criteres',
                                'rse', 'contribution_fournisseur', 'attributaire', 'produit_retenu',
                                'infos_complementaires', 'remarques', 'notes_acheteur_procedure',
                                'notes_acheteur_fournisseur', 'notes_acheteur_positionnement', 'note_veille'
                            ]
                            
                            # Ajouter les colonnes manquantes avec des valeurs vides
                            for col in all_columns:
                                if col not in st.session_state[df_editable_key].columns:
                                    st.session_state[df_editable_key][col] = ''
                            
                            # Réorganiser les colonnes
                            st.session_state[df_editable_key] = st.session_state[df_editable_key][all_columns]
                            
                            # Afficher le tableau éditable complet
                            st.markdown("**✏️ Éditez directement les valeurs dans le tableau ci-dessous :**")
                            edited_df = st.data_editor(
                                st.session_state[df_editable_key],
                                width='stretch',
                                height=400,
                                num_rows="fixed",
                                key=f"data_editor_all_{extraction_key}"
                            )
                            
                            # Mettre à jour le DataFrame dans session_state
                            st.session_state[df_editable_key] = edited_df.copy()
                            
                            # Bouton pour appliquer les modifications du tableau aux lots
                            col_apply1, col_refresh1 = st.columns([1, 1])
                            with col_apply1:
                                if st.button("💾 Appliquer les modifications du tableau", key=f"apply_table_edit_all_{extraction_key}", type="primary"):
                                    try:
                                        # Synchroniser les modifications du tableau avec les lots
                                        for idx, row in edited_df.iterrows():
                                            if idx < len(lots_list):
                                                # Mettre à jour le lot correspondant
                                                lots_list[idx]['numero'] = int(row.get('lot_numero', idx + 1)) if pd.notna(row.get('lot_numero')) else idx + 1
                                                lots_list[idx]['intitule'] = str(row.get('intitule_lot', '')) if pd.notna(row.get('intitule_lot')) else ''
                                                lots_list[idx]['attributaire'] = str(row.get('attributaire', '')) if pd.notna(row.get('attributaire')) else ''
                                                lots_list[idx]['produit_retenu'] = str(row.get('produit_retenu', '')) if pd.notna(row.get('produit_retenu')) else ''
                                                lots_list[idx]['infos_complementaires'] = str(row.get('infos_complementaires', '')) if pd.notna(row.get('infos_complementaires')) else ''
                                                lots_list[idx]['montant_estime'] = float(row.get('montant_global_estime', 0)) if pd.notna(row.get('montant_global_estime')) else 0
                                                lots_list[idx]['montant_maximum'] = float(row.get('montant_global_maxi', 0)) if pd.notna(row.get('montant_global_maxi')) else 0
                                                lots_list[idx]['quantite_minimum'] = int(row.get('quantite_minimum', 0)) if pd.notna(row.get('quantite_minimum')) else 0
                                                lots_list[idx]['quantites_estimees'] = str(row.get('quantites_estimees', '')) if pd.notna(row.get('quantites_estimees')) else ''
                                                lots_list[idx]['quantite_maximum'] = int(row.get('quantite_maximum', 0)) if pd.notna(row.get('quantite_maximum')) else 0
                                                lots_list[idx]['criteres_economique'] = str(row.get('criteres_economique', '')) if pd.notna(row.get('criteres_economique')) else ''
                                                lots_list[idx]['criteres_techniques'] = str(row.get('criteres_techniques', '')) if pd.notna(row.get('criteres_techniques')) else ''
                                                lots_list[idx]['autres_criteres'] = str(row.get('autres_criteres', '')) if pd.notna(row.get('autres_criteres')) else ''
                                                lots_list[idx]['rse'] = str(row.get('rse', '')) if pd.notna(row.get('rse')) else ''
                                                lots_list[idx]['contribution_fournisseur'] = str(row.get('contribution_fournisseur', '')) if pd.notna(row.get('contribution_fournisseur')) else ''
                                        
                                        # Mettre à jour les données générales également
                                        try:
                                            if len(edited_df) > 0:
                                                first_row = edited_df.iloc[0]
                                                for col in all_columns:
                                                    if col not in ['lot_numero', 'intitule_lot', 'attributaire', 'produit_retenu', 'infos_complementaires',
                                                                   'montant_global_estime', 'montant_global_maxi', 'quantite_minimum', 'quantites_estimees',
                                                                   'quantite_maximum', 'criteres_economique', 'criteres_techniques', 'autres_criteres',
                                                                   'rse', 'contribution_fournisseur']:
                                                        if pd.notna(first_row.get(col)):
                                                            all_data[col] = first_row[col]
                                        except NameError:
                                            # all_data n'est pas défini, ce n'est pas grave
                                            pass
                                        
                                        st.session_state[lots_key] = lots_list
                                        st.success("✅ Modifications du tableau appliquées avec succès !")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Erreur lors de l'application des modifications : {e}")
                            with col_refresh1:
                                if st.button("🔄 Rafraîchir depuis les lots", key=f"refresh_from_lots_all_{extraction_key}"):
                                    # Reconstruire le DataFrame depuis les lots
                                    lots_list = st.session_state.get(lots_key, [])
                                    if lots_list:
                                        all_lots_data_refresh = []
                                        for lot_idx, lot in enumerate(lots_list):
                                            lot_data_refresh = {}
                                            lot_data_refresh.update(extracted_info.get('valeurs_extraites', {}))
                                            lot_data_refresh.update(extracted_info.get('valeurs_generees', {}))
                                            lot_data_refresh['lot_numero'] = lot.get('numero', lot_idx + 1)
                                            lot_data_refresh['intitule_lot'] = lot.get('intitule', '')
                                            lot_data_refresh['attributaire'] = lot.get('attributaire', '')
                                            lot_data_refresh['produit_retenu'] = lot.get('produit_retenu', '')
                                            lot_data_refresh['infos_complementaires'] = lot.get('infos_complementaires', '')
                                            lot_data_refresh['montant_global_estime'] = lot.get('montant_estime', 0)
                                            lot_data_refresh['montant_global_maxi'] = lot.get('montant_maximum', 0)
                                            lot_data_refresh['quantite_minimum'] = lot.get('quantite_minimum', 0)
                                            lot_data_refresh['quantites_estimees'] = lot.get('quantites_estimees', '')
                                            lot_data_refresh['quantite_maximum'] = lot.get('quantite_maximum', 0)
                                            lot_data_refresh['criteres_economique'] = lot.get('criteres_economique', '')
                                            lot_data_refresh['criteres_techniques'] = lot.get('criteres_techniques', '')
                                            lot_data_refresh['autres_criteres'] = lot.get('autres_criteres', '')
                                            lot_data_refresh['rse'] = lot.get('rse', '')
                                            lot_data_refresh['contribution_fournisseur'] = lot.get('contribution_fournisseur', '')
                                            all_lots_data_refresh.append(lot_data_refresh)
                                        # Ajouter les colonnes manquantes
                                        df_refresh = pd.DataFrame(all_lots_data_refresh)
                                        for col in all_columns:
                                            if col not in df_refresh.columns:
                                                df_refresh[col] = ''
                                        df_refresh = df_refresh[all_columns]
                                        st.session_state[df_editable_key] = df_refresh.copy()
                                    st.rerun()
                        else:
                            # Afficher seulement les colonnes principales (éditables)
                            main_columns = [
                                'reference_procedure', 'intitule_procedure', 'lot_numero', 'intitule_lot',
                                'attributaire', 'produit_retenu', 'montant_global_estime', 'montant_global_maxi',
                                'quantite_minimum', 'quantites_estimees', 'quantite_maximum',
                                'criteres_economique', 'criteres_techniques', 'autres_criteres',
                                'rse', 'contribution_fournisseur', 'statut', 'type_procedure'
                            ]
                            
                            # Créer un DataFrame avec seulement les colonnes principales
                            df_main = st.session_state[df_editable_key].copy()
                            for col in main_columns:
                                if col not in df_main.columns:
                                    df_main[col] = ''
                            
                            # Garder seulement les colonnes qui existent dans main_columns
                            existing_main_cols = [col for col in main_columns if col in df_main.columns]
                            df_main = df_main[existing_main_cols]
                            
                            st.markdown("**✏️ Éditez directement les valeurs dans le tableau ci-dessous :**")
                            edited_df = st.data_editor(
                                df_main,
                                width='stretch',
                                num_rows="fixed",
                                key=f"data_editor_main_{extraction_key}"
                            )
                            
                            # Mettre à jour le DataFrame principal avec les modifications
                            for col in edited_df.columns:
                                if col in st.session_state[df_editable_key].columns:
                                    st.session_state[df_editable_key][col] = edited_df[col]
                            for idx in range(len(edited_df)):
                                for col in edited_df.columns:
                                    if col in st.session_state[df_editable_key].columns and idx < len(st.session_state[df_editable_key]):
                                        st.session_state[df_editable_key].iloc[idx, st.session_state[df_editable_key].columns.get_loc(col)] = edited_df.iloc[idx][col]
                            
                            # Bouton pour appliquer les modifications du tableau aux lots
                            col_apply2, col_refresh2 = st.columns([1, 1])
                            with col_apply2:
                                if st.button("💾 Appliquer les modifications du tableau", key=f"apply_table_edit_main_{extraction_key}", type="primary"):
                                    try:
                                        # Synchroniser les modifications du tableau avec les lots
                                        for idx, row in edited_df.iterrows():
                                            if idx < len(lots_list):
                                                # Mettre à jour le lot correspondant
                                                if pd.notna(row.get('lot_numero')):
                                                    lots_list[idx]['numero'] = int(row.get('lot_numero', idx + 1))
                                                if pd.notna(row.get('intitule_lot')):
                                                    lots_list[idx]['intitule'] = str(row.get('intitule_lot', ''))
                                                if pd.notna(row.get('attributaire')):
                                                    lots_list[idx]['attributaire'] = str(row.get('attributaire', ''))
                                                if pd.notna(row.get('produit_retenu')):
                                                    lots_list[idx]['produit_retenu'] = str(row.get('produit_retenu', ''))
                                                if pd.notna(row.get('montant_global_estime')):
                                                    lots_list[idx]['montant_estime'] = float(row.get('montant_global_estime', 0))
                                                if pd.notna(row.get('montant_global_maxi')):
                                                    lots_list[idx]['montant_maximum'] = float(row.get('montant_global_maxi', 0))
                                                if pd.notna(row.get('quantite_minimum')):
                                                    lots_list[idx]['quantite_minimum'] = int(row.get('quantite_minimum', 0))
                                                if pd.notna(row.get('quantites_estimees')):
                                                    lots_list[idx]['quantites_estimees'] = str(row.get('quantites_estimees', ''))
                                                if pd.notna(row.get('quantite_maximum')):
                                                    lots_list[idx]['quantite_maximum'] = int(row.get('quantite_maximum', 0))
                                                if pd.notna(row.get('criteres_economique')):
                                                    lots_list[idx]['criteres_economique'] = str(row.get('criteres_economique', ''))
                                                if pd.notna(row.get('criteres_techniques')):
                                                    lots_list[idx]['criteres_techniques'] = str(row.get('criteres_techniques', ''))
                                                if pd.notna(row.get('autres_criteres')):
                                                    lots_list[idx]['autres_criteres'] = str(row.get('autres_criteres', ''))
                                                if pd.notna(row.get('rse')):
                                                    lots_list[idx]['rse'] = str(row.get('rse', ''))
                                                if pd.notna(row.get('contribution_fournisseur')):
                                                    lots_list[idx]['contribution_fournisseur'] = str(row.get('contribution_fournisseur', ''))
                                        
                                        # Mettre à jour les données générales également
                                        try:
                                            if len(edited_df) > 0:
                                                first_row = edited_df.iloc[0]
                                                for col in existing_main_cols:
                                                    if col not in ['lot_numero', 'intitule_lot', 'attributaire', 'produit_retenu',
                                                                   'montant_global_estime', 'montant_global_maxi', 'quantite_minimum',
                                                                   'quantites_estimees', 'quantite_maximum', 'criteres_economique',
                                                                   'criteres_techniques', 'autres_criteres', 'rse', 'contribution_fournisseur']:
                                                        if pd.notna(first_row.get(col)) and col in all_data:
                                                            all_data[col] = first_row[col]
                                        except NameError:
                                            # all_data n'est pas défini, ce n'est pas grave
                                            pass
                                        
                                        st.session_state[lots_key] = lots_list
                                        st.success("✅ Modifications du tableau appliquées avec succès !")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Erreur lors de l'application des modifications : {e}")
                            with col_refresh2:
                                if st.button("🔄 Rafraîchir depuis les lots", key=f"refresh_from_lots_main_{extraction_key}"):
                                    # Reconstruire le DataFrame depuis les lots
                                    lots_list = st.session_state.get(lots_key, [])
                                    if lots_list:
                                        all_lots_data_refresh = []
                                        for lot_idx, lot in enumerate(lots_list):
                                            lot_data_refresh = {}
                                            lot_data_refresh.update(extracted_info.get('valeurs_extraites', {}))
                                            lot_data_refresh.update(extracted_info.get('valeurs_generees', {}))
                                            lot_data_refresh['lot_numero'] = lot.get('numero', lot_idx + 1)
                                            lot_data_refresh['intitule_lot'] = lot.get('intitule', '')
                                            lot_data_refresh['attributaire'] = lot.get('attributaire', '')
                                            lot_data_refresh['produit_retenu'] = lot.get('produit_retenu', '')
                                            lot_data_refresh['montant_global_estime'] = lot.get('montant_estime', 0)
                                            lot_data_refresh['montant_global_maxi'] = lot.get('montant_maximum', 0)
                                            lot_data_refresh['quantite_minimum'] = lot.get('quantite_minimum', 0)
                                            lot_data_refresh['quantites_estimees'] = lot.get('quantites_estimees', '')
                                            lot_data_refresh['quantite_maximum'] = lot.get('quantite_maximum', 0)
                                            lot_data_refresh['criteres_economique'] = lot.get('criteres_economique', '')
                                            lot_data_refresh['criteres_techniques'] = lot.get('criteres_techniques', '')
                                            lot_data_refresh['autres_criteres'] = lot.get('autres_criteres', '')
                                            lot_data_refresh['rse'] = lot.get('rse', '')
                                            lot_data_refresh['contribution_fournisseur'] = lot.get('contribution_fournisseur', '')
                                            all_lots_data_refresh.append(lot_data_refresh)
                                        df_refresh = pd.DataFrame(all_lots_data_refresh)
                                        # Ajouter les colonnes manquantes
                                        for col in main_columns:
                                            if col not in df_refresh.columns:
                                                df_refresh[col] = ''
                                        existing_refresh_cols = [col for col in main_columns if col in df_refresh.columns]
                                        df_refresh = df_refresh[existing_refresh_cols]
                                        # Mettre à jour le DataFrame éditable
                                        for col in df_refresh.columns:
                                            if col in st.session_state[df_editable_key].columns:
                                                for idx in range(min(len(df_refresh), len(st.session_state[df_editable_key]))):
                                                    st.session_state[df_editable_key].iloc[idx, st.session_state[df_editable_key].columns.get_loc(col)] = df_refresh.iloc[idx][col]
                                    st.rerun()
                        
                        # Statistiques
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("📄 Extraites", len(valeurs_extraites))
                        with col2:
                            st.metric("🤖 Générées", len(valeurs_generees))
                        with col3:
                            st.metric("📊 Total champs", len(all_data))
                        with col4:
                            st.metric("📋 Lots détectés", len(lots_list) if lots_list else 1)
                        
                        # Afficher le JSON complet si demandé
                        if st.checkbox("Afficher toutes les données en JSON", key="json_all_data"):
                            st.json(all_data)
                        else:
                            st.warning("⚠️ Aucune donnée disponible")
                        
                        # NOUVEAU: Fonction pour synchroniser les modifications des lots dans extracted_entries
                        def sync_lots_modifications():
                            """Synchronise les modifications des lots depuis st.session_state vers extracted_entries"""
                            try:
                                for i, extracted_info in enumerate(extracted_entries):
                                    lots_list = st.session_state.get(f'lots_list_{i}', [])
                                    
                                    if lots_list:
                                        # Mettre à jour les valeurs extraites avec les données modifiées des lots
                                        valeurs_extraites = extracted_info.get('valeurs_extraites', {})
                                        
                                        # Si plusieurs lots, créer une entrée par lot
                                        if len(lots_list) > 1:
                                            # Pour chaque lot, mettre à jour les données correspondantes
                                            for lot_idx, lot in enumerate(lots_list):
                                                if lot_idx < len(extracted_entries):
                                                    # Mettre à jour l'entrée correspondante
                                                    entry = extracted_entries[lot_idx]
                                                    entry['valeurs_extraites'].update({
                                                        'lot_numero': lot.get('numero', lot_idx + 1),
                                                        'intitule_lot': lot.get('intitule', ''),
                                                        'montant_global_estime': lot.get('montant_estime', 0),
                                                        'montant_global_maxi': lot.get('montant_maximum', 0),
                                                        'quantite_minimum': lot.get('quantite_minimum', 0),
                                                        'quantites_estimees': lot.get('quantites_estimees', ''),
                                                        'quantite_maximum': lot.get('quantite_maximum', 0),
                                                        'criteres_economique': lot.get('criteres_economique', ''),
                                                        'criteres_techniques': lot.get('criteres_techniques', ''),
                                                        'autres_criteres': lot.get('autres_criteres', ''),
                                                        'rse': lot.get('rse', ''),
                                                        'contribution_fournisseur': lot.get('contribution_fournisseur', ''),
                                                        'attributaire': lot.get('attributaire', ''),
                                                        'produit_retenu': lot.get('produit_retenu', ''),
                                                        'infos_complementaires': lot.get('infos_complementaires', '')
                                                    })
                                        else:
                                            # Un seul lot ou premier lot
                                            if lots_list:
                                                lot = lots_list[0]
                                                valeurs_extraites.update({
                                                    'lot_numero': lot.get('numero', 1),
                                                    'intitule_lot': lot.get('intitule', ''),
                                                    'montant_global_estime': lot.get('montant_estime', 0),
                                                    'montant_global_maxi': lot.get('montant_maximum', 0),
                                                    'quantite_minimum': lot.get('quantite_minimum', 0),
                                                    'quantites_estimees': lot.get('quantites_estimees', ''),
                                                    'quantite_maximum': lot.get('quantite_maximum', 0),
                                                    'criteres_economique': lot.get('criteres_economique', ''),
                                                    'criteres_techniques': lot.get('criteres_techniques', ''),
                                                    'autres_criteres': lot.get('autres_criteres', ''),
                                                    'rse': lot.get('rse', ''),
                                                    'contribution_fournisseur': lot.get('contribution_fournisseur', ''),
                                                    'attributaire': lot.get('attributaire', ''),
                                                    'produit_retenu': lot.get('produit_retenu', ''),
                                                    'infos_complementaires': lot.get('infos_complementaires', '')
                                                })
                                
                                return True
                            except Exception as e:
                                st.error(f"❌ Erreur lors de la synchronisation: {e}")
                                return False
                        
                        # Bouton pour synchroniser les modifications
                        col_sync, col_insert = st.columns([1, 2])
                        with col_sync:
                            if st.button("🔄 Synchroniser les modifications", help="Met à jour les données finales avec vos modifications"):
                                if sync_lots_modifications():
                                    st.success("✅ Modifications synchronisées avec succès !")
                                    st.rerun()
                        
                        # Bouton pour insérer dans la base
                        with col_insert:
                            if st.button("💾 Insérer dans la base de données", type="primary"):
                                try:
                                    # NOUVEAU: Synchroniser automatiquement les modifications avant l'insertion
                                    sync_lots_modifications()
                                    
                                    # Insérer chaque lot dans la base de données
                                    total_inserted = 0
                                    extraction_key_insert = extracted_entries[0].get('lot_id', 'extraction_0') if extracted_entries else 'extraction_0'
                                    lots_key_insert = f'lots_list_{extraction_key_insert}'
                                    for i, extracted_info in enumerate(extracted_entries):
                                        # NOUVEAU: Créer une ligne par lot détecté
                                        lots_list = st.session_state.get(lots_key_insert, [])
                                        
                                        if lots_list:
                                            # Insérer chaque lot individuellement
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
                                                
                                                if lot_data:
                                                    df_new = pd.DataFrame([lot_data])
                                                    result = db_manager.insert_dataframe(df_new)
                                                    
                                                    if result.get('rows_inserted', 0) > 0 or result.get('rows_updated', 0) > 0:
                                                        total_inserted += result.get('rows_inserted', 0) + result.get('rows_updated', 0)
                                                        st.info(f"✅ Lot {lot.get('numero', lot_idx + 1)} inséré: {lot.get('intitule', '')[:50]}...")
                                                    else:
                                                        error_msg = result.get('errors', ['Erreur inconnue'])
                                                        st.error(f"❌ Erreur insertion lot {lot.get('numero', lot_idx + 1)}: {error_msg[0] if error_msg else 'Erreur inconnue'}")
                                        else:
                                            # Fallback: insérer comme avant si pas de lots détectés
                                            all_values = {}
                                            all_values.update(extracted_info.get('valeurs_extraites', {}))
                                            all_values.update(extracted_info.get('valeurs_generees', {}))
                                            
                                            if all_values:
                                                df_new = pd.DataFrame([all_values])
                                                result = db_manager.insert_dataframe(df_new)
                                                
                                                if result.get('rows_inserted', 0) > 0 or result.get('rows_updated', 0) > 0:
                                                    total_inserted += result.get('rows_inserted', 0) + result.get('rows_updated', 0)
                                                else:
                                                    error_msg = result.get('errors', ['Erreur inconnue'])
                                                    st.error(f"❌ Erreur insertion lot {i+1}: {error_msg[0] if error_msg else 'Erreur inconnue'}")
                                    
                                    if total_inserted > 0:
                                        st.success(f"✅ {total_inserted} ligne(s) insérée(s) dans la base de données (une ligne par lot)")
                                        
                                        # NOUVEAU: Créer une sauvegarde après insertion
                                        if hasattr(db_manager, 'create_backup'):
                                            if db_manager.create_backup():
                                                st.info("💾 Sauvegarde automatique créée")
                                        
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ Aucune donnée à insérer")
                                        
                                except Exception as e:
                                    st.error(f"❌ Erreur lors de l'insertion: {e}")
                else:
                    st.warning("⚠️ Extraction partielle - Vérifiez et complétez manuellement")
                    for i, entry in enumerate(extracted_entries):
                        if 'erreur' in entry:
                            st.error(f"Erreur lot {i+1}: {entry['erreur']}")
            except Exception as e:
                st.error(f"❌ Erreur lors de l'analyse: {e}")
    
    # Onglet 5: Base de données
    with tab5:
        render_database_tab(db_manager, ao_extractor)
    
    # Footer
    st.markdown("---")
    st.markdown("🚀 **IA Conversationnelle - Veille Concurrentielle** - Système ultra performant pour l'analyse d'appels d'offres")
    st.markdown("🤖 **IA Locale** | 🗄️ **Base locale**")
    
except Exception as e:
    st.error(f"❌ Erreur lors du chargement de l'application: {e}")
    st.info("Vérifiez que l'application est correctement configurée")
