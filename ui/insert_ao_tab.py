"""
Onglet Insertion AO
Gère l'upload et l'extraction d'appels d'offres
"""

import streamlit as st
import pandas as pd
import logging
from pathlib import Path
from ao_extractor_v2 import AOExtractorV2
from universal_criteria_extractor import UniversalCriteriaExtractor
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)


def render_insert_ao_tab(
    data: pd.DataFrame,
    ao_extractor: AOExtractorV2,
    criteria_extractor: UniversalCriteriaExtractor,
    db_manager: DatabaseManager
):
    """
    Rend l'onglet Insertion AO
    
    Args:
        data (pd.DataFrame): Données de référence
        ao_extractor (AOExtractorV2): Extracteur d'AO
        criteria_extractor (UniversalCriteriaExtractor): Extracteur de critères
        db_manager (DatabaseManager): Gestionnaire de base de données
    """
    st.header("📥 Insertion d'Appels d'Offres")
    st.info("🚀 **Système d'extraction intelligent** - L'IA apprend depuis vos données et extrait BEAUCOUP PLUS d'éléments !")
    
    # Section upload du fichier AO
    st.subheader("📁 Upload du fichier d'appel d'offres")
    
    uploaded_file = st.file_uploader(
        "Choisissez un fichier (Excel, PDF, Word, TXT)",
        type=['xlsx', 'xls', 'pdf', 'docx', 'doc', 'txt'],
        help="Formats supportés: Excel, PDF, Word, TXT"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Fichier uploadé: {uploaded_file.name}")
        
        # Traitement du fichier uploadé
        with st.spinner("🔍 Analyse du fichier..."):
            try:
                extracted_entries = []
                
                # Extraction unifiée avec AOExtractorV2
                uploaded_file.seek(0)
                
                file_analysis = {
                    'nom': uploaded_file.name,
                    'type': uploaded_file.type,
                    'taille': uploaded_file.size,
                    'contenu_extraite': {'type': uploaded_file.type.split('/')[-1]},
                    'erreur': None
                }
                
                extracted_entries = ao_extractor.extract_from_file(
                    uploaded_file,
                    file_analysis,
                    data.columns.tolist() if not data.empty else []
                )
                
                # Extraction des critères pour les fichiers non-PDF
                if uploaded_file.type != "application/pdf" and extracted_entries:
                    if not any('erreur' in entry for entry in extracted_entries):
                        text_content = ""
                        if 'excel' in uploaded_file.type:
                            try:
                                df = pd.read_excel(uploaded_file)
                                text_content = df.to_string()
                            except:
                                text_content = str(extracted_entries)
                        else:
                            try:
                                text_content = uploaded_file.read().decode('utf-8')
                            except:
                                text_content = str(extracted_entries)
                        
                        if text_content:
                            criteria_result = criteria_extractor.extract_criteria(text_content, uploaded_file.type)
                            
                            if criteria_result.has_criteria:
                                for entry in extracted_entries:
                                    if 'valeurs_extraites' in entry:
                                        if criteria_result.global_criteria:
                                            for critere in criteria_result.global_criteria:
                                                if 'économique' in critere.type_critere.lower() or 'prix' in critere.type_critere.lower():
                                                    entry['valeurs_extraites']['criteres_economique'] = f"{critere.pourcentage}% - {critere.description}"
                                                elif 'technique' in critere.type_critere.lower():
                                                    entry['valeurs_extraites']['criteres_techniques'] = f"{critere.pourcentage}% - {critere.description}"
                                                elif 'rse' in critere.type_critere.lower() or 'durable' in critere.type_critere.lower():
                                                    entry['valeurs_extraites']['rse'] = f"{critere.pourcentage}% - {critere.description}"
                                                else:
                                                    entry['valeurs_extraites']['autres_criteres'] = f"{critere.pourcentage}% - {critere.description}"
                
                if extracted_entries and not any('erreur' in entry for entry in extracted_entries):
                    # Sauvegarder les données extraites dans session_state pour l'édition
                    st.session_state['last_extracted_entries'] = extracted_entries
                    
                    st.success("✅ Extraction réussie!")
                    
                    # Affichage des résultats
                    st.info(f"🎯 **{len(extracted_entries)} lot(s) détecté(s)**")
                    
                    # Afficher un message informatif
                    if uploaded_file.type == "application/pdf":
                        st.info("✅ Extraction effectuée avec **PDFExtractor**")
                    elif 'excel' in uploaded_file.type:
                        st.info("✅ Extraction effectuée avec **ExcelExtractor**")
                    else:
                        st.info("✅ Extraction effectuée avec **TextExtractor**")
                    
                    # Métriques
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        total_extracted = sum(len(entry.get('valeurs_extraites', {})) for entry in extracted_entries)
                        st.metric("📄 Valeurs extraites", total_extracted)
                    
                    with col2:
                        total_generated = sum(len(entry.get('valeurs_generees', {})) for entry in extracted_entries)
                        st.metric("🤖 Valeurs générées", total_generated)
                    
                    with col3:
                        total_elements = total_extracted + total_generated
                        st.metric("📊 Total éléments", total_elements)
                    
                    # Afficher un aperçu des données extraites
                    st.markdown("### 📋 Aperçu des données extraites")
                    
                    for i, entry in enumerate(extracted_entries):
                        with st.expander(f"📦 Lot {i+1}: {entry.get('valeurs_extraites', {}).get('intitule_lot', 'N/A')[:50]}...", expanded=(i == 0)):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**📄 Valeurs extraites:**")
                                valeurs_extraites = entry.get('valeurs_extraites', {})
                                if valeurs_extraites:
                                    for key, value in list(valeurs_extraites.items())[:10]:  # Afficher les 10 premiers
                                        if value:
                                            st.write(f"- **{key}**: {str(value)[:100]}")
                                
                                if len(valeurs_extraites) > 10:
                                    st.info(f"... et {len(valeurs_extraites) - 10} autres champs")
                            
                            with col2:
                                st.markdown("**🤖 Valeurs générées:**")
                                valeurs_generees = entry.get('valeurs_generees', {})
                                if valeurs_generees:
                                    for key, value in list(valeurs_generees.items())[:10]:  # Afficher les 10 premiers
                                        if value:
                                            st.write(f"- **{key}**: {str(value)[:100]}")
                                
                                if len(valeurs_generees) > 10:
                                    st.info(f"... et {len(valeurs_generees) - 10} autres champs")
                    
                    # Note: L'interface d'édition complète reste dans app.py pour l'instant
                    # car elle est très complexe et dépend de beaucoup de session_state
                    st.info("ℹ️ L'interface d'édition complète des lots est disponible dans la section dédiée ci-dessous.")
                    
                else:
                    st.error("❌ Erreur lors de l'extraction")
                    if extracted_entries:
                        for entry in extracted_entries:
                            if 'erreur' in entry:
                                st.error(f"Erreur: {entry['erreur']}")
                                
            except Exception as e:
                st.error(f"❌ Erreur lors du traitement: {e}")
                logger.exception("Erreur lors du traitement du fichier")

