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
from ao_extractor import AOExtractor
from pdf_extractor import AdvancedPDFExtractor
from extraction_improver import extraction_improver
from universal_criteria_extractor import UniversalCriteriaExtractor

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
        
        # Initialisation de l'extracteur d'AO avec les données de référence
        ao_extractor = AOExtractor(reference_data=data)
        
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
        st.header("📊 Vue d'ensemble des données")
        
        # Définir les 44 colonnes standard
        colonnes_44 = [
            "Mots clés", "Univers", "Segment", "Famille", "Statut", "Groupement",
            "Référence de la procédure", "Type de procédure", "Mono ou multi-attributif",
            "Exécution du marché", "Date limite de remise des offres", "Date d'attribution du marché",
            "Durée du marché (mois)", "Reconduction", "Fin (sans reconduction)", "Fin (avec reconduction)",
            "Nbr lots", "Intitulé de la procédure", "Lot N°", "Intitulé du Lot",
            "Infos complémentaires", "Attributaire", "Produit retenu", "Remarques",
            "Notes de l'acheteur sur la procédure", "Notes de l'acheteur sur le fournisseur",
            "Notes de l'acheteur sur le positionnement", "Note Veille concurrentielle disponible",
            "Achat", "Crédit bail", "Crédit bail (durée année)", "Location", "Location (durée années)",
            "MAD", "Montant global estimé (€ HT) du marché", "Montant global maxi (€ HT)",
            "Quantité minimum", "Quantités estimées", "Quantité maximum",
            "Critères d'attribution : économique", "Critères d'attribution : techniques",
            "Autres critères d'attribution", "RSE", "Contribution fournisseur"
        ]
        
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
    
    # Onglet 2: IA
    with tab2:
        st.header("🤖 Assistant IA")
        
        # Statut des modèles IA
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("🧠 **Moteur d'IA local** - Modèles français et multilingues")
        with col2:
            if st.button("🚀 Initialiser l'IA", type="primary"):
                with st.spinner("Initialisation des modèles IA..."):
                    try:
                        ai_engine.initialize(data, load_heavy_models=True)  # Mode complet pour le bouton
                        st.success("✅ Moteur d'IA initialisé!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'initialisation: {e}")
        
        # Statut des modèles
        if hasattr(ai_engine, 'get_model_status'):
            model_status = ai_engine.get_model_status()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                status = "✅" if model_status.get('bert_model', False) else "❌"
                st.metric("BERT Français", status)
            with col2:
                status = "✅" if model_status.get('embedding_model', False) else "❌"
                st.metric("Embeddings", status)
            with col3:
                status = "✅" if model_status.get('nlp_model', False) else "❌"
                st.metric("NLP spaCy", status)
            with col4:
                status = "✅" if model_status.get('classifier', False) else "❌"
                st.metric("Classification", status)
        
        # NOUVEAU: Métriques de performance de l'IA
        if hasattr(ai_engine, 'get_performance_metrics'):
            with st.expander("📊 Métriques de performance de l'IA"):
                metrics = ai_engine.get_performance_metrics()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Questions traitées", metrics.get('total_questions', 0))
                with col2:
                    success_rate = metrics.get('success_rate', 0) * 100
                    st.metric("Taux de succès", f"{success_rate:.1f}%")
                with col3:
                    cache_rate = metrics.get('cache_hit_rate', 0) * 100
                    st.metric("Taux de cache", f"{cache_rate:.1f}%")
                with col4:
                    avg_time = metrics.get('average_response_time', 0)
                    st.metric("Temps moyen", f"{avg_time:.2f}s")
                
                # Boutons de gestion
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🗑️ Effacer mémoire"):
                        ai_engine.clear_conversation_memory()
                        st.success("Mémoire effacée!")
                        st.rerun()
                with col2:
                    if st.button("🔧 Toggle validation"):
                        current_state = getattr(ai_engine, 'response_validation', True)
                        ai_engine.set_response_validation(not current_state)
                        st.success(f"Validation {'activée' if not current_state else 'désactivée'}!")
                        st.rerun()
                with col3:
                    if st.button("📊 Afficher détails"):
                        st.json(metrics)
        
        # Interface de questions
        if hasattr(ai_engine, 'initialized') and ai_engine.initialized:
            st.subheader("💬 Conversation avec l'IA")
            
            # Initialiser la session pour la conversation
            if 'conversation_messages' not in st.session_state:
                st.session_state.conversation_messages = []
            
            # Afficher l'historique de la conversation
            if st.session_state.conversation_messages:
                st.markdown("#### 📜 Historique de la conversation")
                for idx, message in enumerate(st.session_state.conversation_messages):
                    if message['type'] == 'user':
                        with st.chat_message("user"):
                            st.write(message['content'])
                    else:
                        with st.chat_message("assistant"):
                            # Afficher le contenu avant le tableau
                            st.markdown(message['content'])
                            
                            # Afficher le tableau si présent
                            if 'table_data' in message and message['table_data'] is not None:
                                table_data = message['table_data']
                                
                                # Afficher le tableau avec options
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.dataframe(
                                        table_data, 
                                        width='stretch', 
                                        height=400,
                                        hide_index=True
                                    )
                                
                                with col2:
                                    # Bouton pour afficher tous les résultats
                                    if len(table_data) > 20:
                                        if st.button(f"📊 Afficher tous les {len(table_data)} résultats", key=f"show_all_{idx}"):
                                            st.session_state[f"show_all_table_{idx}"] = True
                                    
                                    # Bouton pour télécharger en CSV
                                    if st.button("💾 Télécharger CSV", key=f"download_{idx}"):
                                        csv_data = table_data.to_csv(index=False)
                                        st.download_button(
                                            label="📥 Télécharger",
                                            data=csv_data,
                                            file_name=f"lots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                            mime="text/csv",
                                            key=f"download_btn_{idx}"
                                        )
                                
                                # Afficher le tableau complet si demandé
                                if st.session_state.get(f"show_all_table_{idx}", False):
                                    st.markdown("#### 📊 Tableau complet")
                                    st.dataframe(
                                        table_data, 
                                        width='stretch', 
                                        height=600,
                                        hide_index=True
                                    )
                                    
                                    if st.button("🔼 Réduire", key=f"hide_all_{idx}"):
                                        st.session_state[f"show_all_table_{idx}"] = False
                                        st.rerun()
                            
                            # Afficher le contenu après le tableau
                            if 'after_table' in message and message['after_table']:
                                st.markdown(message['after_table'])
            else:
                st.info("💬 Commencez une conversation en posant votre première question ci-dessous !")
            
            # Interface de question générale avec recherche intégrée
            st.subheader("💬 Questions et Recherche")
            
            # Aide pour les recherches
            with st.expander("🔍 Aide pour les recherches"):
                st.markdown("""
                **Vous pouvez rechercher de plusieurs façons :**
                
                🔍 **Par référence de procédure :**
                - "Cherche 2024-R075"
                - "Trouve 2024-R072"
                
                📋 **Par intitulé de lot :**
                - "Cherche congélateurs"
                - "Trouve informatique"
                
                📄 **Par intitulé de procédure :**
                - "Cherche fourniture"
                - "Trouve maintenance"
                
                💬 **Questions générales :**
                - "Montre les lots du RESAH"
                - "Combien de lots en médical ?"
                - "Compare RESAH et UNIHA"
                """)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                question = st.text_area(
                    "Votre question ou recherche:",
                    placeholder="Ex: Cherche 2024-R075, Montre les lots du RESAH, Combien de lots en médical...",
                    height=100,
                    help="Tapez votre question ou utilisez 'Cherche' pour rechercher par référence, intitulé de lot ou procédure"
                )
            with col2:
                ask_button = st.button("❓ Demander", type="primary")
            with col3:
                if st.button("🗑️ Effacer tout"):
                    st.session_state.conversation_messages = []
                    st.rerun()
            
            if question and ask_button:
                try:
                    # Ajouter la question de l'utilisateur à la conversation
                    st.session_state.conversation_messages.append({
                        'type': 'user',
                        'content': question
                    })
                    
                    with st.spinner("🧠 L'IA locale analyse votre question..."):
                        answer = ai_engine.ask_question(question)
                        
                        # Vérifier si la réponse contient un tableau
                        if "```TABLEAU_STREAMLIT```" in answer:
                            # Remplacer l'indicateur par un tableau Streamlit
                            table_data = ai_engine.get_last_table_data()
                            if table_data is not None:
                                # Diviser la réponse en deux parties
                                parts = answer.split("```TABLEAU_STREAMLIT```")
                                before_table = parts[0]
                                after_table = parts[1] if len(parts) > 1 else ""
                                
                                # Ajouter la réponse avec tableau à la conversation
                                st.session_state.conversation_messages.append({
                                    'type': 'assistant',
                                    'content': before_table,
                                    'table_data': table_data,
                                    'after_table': after_table
                                })
                            else:
                                # Fallback si pas de données de tableau
                                st.session_state.conversation_messages.append({
                                    'type': 'assistant',
                                    'content': answer
                                })
                        else:
                            # Réponse normale sans tableau
                            st.session_state.conversation_messages.append({
                                'type': 'assistant',
                                'content': answer
                            })
                        
                        # Afficher un message de succès
                        st.success("✅ Réponse générée avec succès !")
                        
                        # Recharger pour afficher la nouvelle conversation
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors du traitement de votre question : {str(e)}")
                    st.info("💡 Essayez de reformuler votre question ou contactez le support.")
        else:
            st.warning("⚠️ Veuillez d'abord initialiser le moteur d'IA pour accéder aux fonctionnalités avancées.")
    
    # Onglet 3: Statistiques
    with tab3:
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
        
        # NOUVEAU: Statistiques par groupement (comme dans l'image)
        st.subheader("📊 Marchés par Groupement")
        
        if 'groupement' in data.columns:
            # Calculer les statistiques par groupement
            groupement_stats = data.groupby('groupement').agg({
                'statut': 'count',  # Total des lots
                'statut': lambda x: (x == 'AO ATTRIBUÉ').sum()  # Lots exécutés
            }).rename(columns={'statut': 'total_lots'})
            
            # Calculer le pourcentage d'exécution
            groupement_stats['executed_lots'] = data[data['statut'] == 'AO ATTRIBUÉ'].groupby('groupement').size()
            groupement_stats['executed_lots'] = groupement_stats['executed_lots'].fillna(0)
            groupement_stats['execution_rate'] = (groupement_stats['executed_lots'] / groupement_stats['total_lots'] * 100).round(2)
            
            # Créer le tableau des groupements
            groupement_table = groupement_stats.reset_index()
            groupement_table.columns = ['Groupement', 'Nb de Marchés actifs', 'Nb de marchés exécutés', 'Pourcentage de marchés exécutés']
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### 📋 Tableau des marchés actifs et exécutés par groupement")
                st.dataframe(groupement_table, width='stretch', hide_index=True)
            
            with col2:
                st.markdown("#### 🥧 Répartition des marchés actifs selon leur groupement")
                fig_pie_groupement = px.pie(
                    groupement_table, 
                    values='Nb de Marchés actifs', 
                    names='Groupement',
                    title="Répartition en pourcentage des marchés actifs selon leur groupement",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie_groupement.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie_groupement, width='stretch')
        
        # NOUVEAU: Statistiques par univers (comme dans l'image)
        st.subheader("🌍 Marchés par Univers")
        
        if 'univers' in data.columns:
            # Calculer les statistiques par univers
            univers_stats = data.groupby('univers').agg({
                'statut': 'count',  # Total des lots
                'statut': lambda x: (x == 'AO ATTRIBUÉ').sum()  # Lots exécutés
            }).rename(columns={'statut': 'total_lots'})
            
            # Calculer le pourcentage d'exécution
            univers_stats['executed_lots'] = data[data['statut'] == 'AO ATTRIBUÉ'].groupby('univers').size()
            univers_stats['executed_lots'] = univers_stats['executed_lots'].fillna(0)
            univers_stats['execution_rate'] = (univers_stats['executed_lots'] / univers_stats['total_lots'] * 100).round(2)
            
            # Créer le tableau des univers
            univers_table = univers_stats.reset_index()
            univers_table.columns = ['Univers', 'Nb de Marchés actifs', 'Nb de marchés exécutés', 'Pourcentage de marchés exécutés']
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### 📋 Tableau des marchés actifs et exécutés par univers")
                st.dataframe(univers_table, width='stretch', hide_index=True)
            
            with col2:
                st.markdown("#### 🥧 Répartition des marchés actifs selon l'univers")
                fig_pie_univers = px.pie(
                    univers_table, 
                    values='Nb de Marchés actifs', 
                    names='Univers',
                    title="Répartition en pourcentage des marchés actifs selon l'univers",
                    color_discrete_sequence=px.colors.qualitative.Set1
                )
                fig_pie_univers.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie_univers, width='stretch')
        
        # NOUVEAU: Graphique combiné Univers/Groupement
        st.subheader("🔗 Analyse croisée Univers/Groupement")
        
        if 'univers' in data.columns and 'groupement' in data.columns:
            # Créer un tableau croisé
            cross_table = data.groupby(['univers', 'groupement']).size().reset_index(name='nb_marchés')
            
            # Graphique en barres empilées
            fig_cross = px.bar(
                cross_table, 
                x='univers', 
                y='nb_marchés', 
                color='groupement',
                title="Nombre de marchés actifs selon l'univers et leur groupement",
                labels={'nb_marchés': 'Nombre de marchés', 'univers': 'Univers', 'groupement': 'Groupement'},
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_cross.update_layout(
                xaxis_tickangle=-45,
                height=500
            )
            st.plotly_chart(fig_cross, width='stretch')
            
            # Tableau croisé détaillé
            st.markdown("#### 📊 Tableau croisé détaillé")
            pivot_table = cross_table.pivot(index='univers', columns='groupement', values='nb_marchés').fillna(0)
            st.dataframe(pivot_table, width='stretch')
        
        # NOUVEAU: Graphiques de performance par groupement
        st.subheader("📈 Performance des Groupements")
        
        if 'groupement' in data.columns and 'statut' in data.columns:
            # Calculer les métriques de performance
            performance_data = []
            for groupement in data['groupement'].unique():
                group_data = data[data['groupement'] == groupement]
                total = len(group_data)
                executed = len(group_data[group_data['statut'] == 'AO ATTRIBUÉ'])
                execution_rate = (executed / total * 100) if total > 0 else 0
                
                performance_data.append({
                    'Groupement': groupement,
                    'Total': total,
                    'Exécutés': executed,
                    'Taux d\'exécution (%)': round(execution_rate, 2)
                })
            
            performance_df = pd.DataFrame(performance_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique en barres du taux d'exécution
                fig_perf = px.bar(
                    performance_df, 
                    x='Groupement', 
                    y='Taux d\'exécution (%)',
                    title="Taux d'exécution par groupement",
                    color='Taux d\'exécution (%)',
                    color_continuous_scale='RdYlGn'
                )
                fig_perf.update_layout(height=400)
                st.plotly_chart(fig_perf, width='stretch')
            
            with col2:
                # Graphique en barres du nombre total de marchés
                fig_total = px.bar(
                    performance_df, 
                    x='Groupement', 
                    y='Total',
                    title="Nombre total de marchés par groupement",
                    color='Total',
                    color_continuous_scale='Blues'
                )
                fig_total.update_layout(height=400)
                st.plotly_chart(fig_total, width='stretch')
        
        # NOUVEAU: Analyse temporelle
        st.subheader("📅 Analyse Temporelle")
        
        if 'date_limite' in data.columns:
            # Convertir les dates et filtrer les données valides
            data['date_limite'] = pd.to_datetime(data['date_limite'], errors='coerce')
            data_with_dates = data.dropna(subset=['date_limite'])
            
            if not data_with_dates.empty:
                # Grouper par mois
                data_with_dates['mois'] = data_with_dates['date_limite'].dt.to_period('M')
                monthly_stats = data_with_dates.groupby('mois').size().reset_index(name='nb_marchés')
                monthly_stats['mois_str'] = monthly_stats['mois'].astype(str)
                
                # Graphique temporel
                fig_temp = px.line(
                    monthly_stats, 
                    x='mois_str', 
                    y='nb_marchés',
                    title="Évolution du nombre de marchés par mois",
                    markers=True
                )
                fig_temp.update_layout(
                    xaxis_tickangle=-45,
                    height=400
                )
                st.plotly_chart(fig_temp, width='stretch')
        
        # Graphiques existants améliorés
        st.subheader("📊 Graphiques Généraux")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if stats.get('univers_stats'):
                fig = px.pie(
                    values=list(stats['univers_stats'].values()),
                    names=list(stats['univers_stats'].keys()),
                    title="Répartition par Univers (Graphique existant)"
                )
                st.plotly_chart(fig, width='stretch')
        
        with col2:
            if stats.get('statut_stats'):
                fig = px.bar(
                    x=list(stats['statut_stats'].keys()),
                    y=list(stats['statut_stats'].values()),
                    title="Répartition par Statut (Graphique existant)"
                )
                st.plotly_chart(fig, width='stretch')
        
    
    # Onglet 4: Insertion AO
    with tab4:
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
                    # Initialiser extracted_entries par défaut
                    extracted_entries = []
                    
                    # Extraction des informations avec le système universel amélioré
                    if uploaded_file.type == "application/pdf":
                        # Utiliser directement pdfplumber pour un meilleur résultat
                        import pdfplumber
                        with pdfplumber.open(uploaded_file) as pdf:
                            text_complet = ''
                            for page in pdf.pages:
                                text_complet += page.extract_text() + '\n'
                        
                        if text_complet:
                            # Utiliser l'extracteur amélioré
                            extracted_data = extraction_improver.extract_improved_data(text_complet)
                            
                            # NOUVEAU: Extraction des critères avec l'extracteur universel
                            criteria_result = criteria_extractor.extract_criteria(text_complet, "pdf")
                            
                            # Ajouter les critères extraits aux données
                            if criteria_result.has_criteria:
                                # Ajouter les critères aux données extraites
                                if criteria_result.global_criteria:
                                    for critere in criteria_result.global_criteria:
                                        if 'économique' in critere.type_critere.lower() or 'prix' in critere.type_critere.lower():
                                            extracted_data['criteres_economique'] = f"{critere.pourcentage}% - {critere.description}"
                                        elif 'technique' in critere.type_critere.lower():
                                            extracted_data['criteres_techniques'] = f"{critere.pourcentage}% - {critere.description}"
                                        elif 'rse' in critere.type_critere.lower() or 'durable' in critere.type_critere.lower():
                                            extracted_data['rse'] = f"{critere.pourcentage}% - {critere.description}"
                                        else:
                                            extracted_data['autres_criteres'] = f"{critere.pourcentage}% - {critere.description}"
                            
                            # NOUVEAU: Utiliser le système universel de détection des lots amélioré
                            lots_detected = ao_extractor._extract_structured_lots_from_pdf(text_complet)
                            
                            if lots_detected:
                                # Créer une entrée pour chaque lot détecté
                                extracted_entries = []
                                for i, lot in enumerate(lots_detected):
                                    # Créer une copie des données extraites pour chaque lot
                                    lot_data = extracted_data.copy()
                                    
                                    # Ajouter les informations spécifiques au lot
                                    lot_data['nbr_lots'] = len(lots_detected)
                                    lot_data['lot_numero'] = lot.get('numero', i + 1)
                                    lot_data['intitule_lot'] = lot.get('intitule', '')
                                    lot_data['montant_global_estime'] = lot.get('montant_estime', 0)
                                    lot_data['montant_global_maxi'] = lot.get('montant_maximum', 0)
                                    
                                    # NOUVEAU: Ajouter les critères spécifiques au lot
                                    # D'abord essayer les critères du lot spécifique
                                    lot_data['criteres_economique'] = lot.get('criteres_economique', '')
                                    lot_data['criteres_techniques'] = lot.get('criteres_techniques', '')
                                    lot_data['autres_criteres'] = lot.get('autres_criteres', '')
                                    
                                    # Si pas de critères spécifiques au lot, utiliser les critères globaux extraits
                                    if not lot_data['criteres_economique']:
                                        lot_data['criteres_economique'] = extracted_data.get('criteres_economique', '')
                                    if not lot_data['criteres_techniques']:
                                        lot_data['criteres_techniques'] = extracted_data.get('criteres_techniques', '')
                                    if not lot_data['autres_criteres']:
                                        lot_data['autres_criteres'] = extracted_data.get('autres_criteres', '')
                                    
                                    # Ajouter les critères RSE
                                    lot_data['rse'] = lot.get('rse', extracted_data.get('rse', ''))
                                    
                                    # Créer l'entrée pour ce lot
                                    extracted_info = {
                                        'valeurs_extraites': lot_data,
                                        'valeurs_generees': {},
                                        'lot_id': f"LOT_{lot.get('numero', i + 1)}",
                                        'lot_info': lot,
                                        'extraction_source': lot.get('source', 'ai_extraction'),
                                        'metadata': {
                                            'nom_fichier': uploaded_file.name,
                                            'taille': uploaded_file.size,
                                            'contenu_extraite': {'type': 'pdf_avance'},
                                            'erreur': None
                                        }
                                    }
                                    extracted_entries.append(extracted_info)
                                
                                st.info(f"🎯 **{len(lots_detected)} lots détectés par l'IA !**")
                            else:
                                # Aucun lot détecté, créer un lot par défaut
                                logger.info("Aucun lot détecté, création d'un lot par défaut")
                                
                                # Créer un lot par défaut avec les données extraites
                                default_lot_data = extracted_data.copy()
                                default_lot_data['nbr_lots'] = 1
                                default_lot_data['lot_numero'] = 1
                                default_lot_data['intitule_lot'] = extracted_data.get('intitule_procedure', 'Lot unique')
                                
                                # Ajouter les critères par défaut si pas trouvés
                                if 'criteres_economique' not in default_lot_data:
                                    default_lot_data['criteres_economique'] = ''
                                if 'criteres_techniques' not in default_lot_data:
                                    default_lot_data['criteres_techniques'] = ''
                                if 'autres_criteres' not in default_lot_data:
                                    default_lot_data['autres_criteres'] = ''
                                
                                extracted_info = {
                                    'valeurs_extraites': default_lot_data,
                                    'valeurs_generees': {},
                                    'lot_id': 'LOT_1',
                                    'lot_info': {
                                        'numero': 1,
                                        'intitule': default_lot_data.get('intitule_procedure', 'Lot unique'),
                                        'montant_estime': default_lot_data.get('montant_global_estime', 0),
                                        'montant_maximum': default_lot_data.get('montant_global_maxi', 0),
                                        'criteres_economique': default_lot_data.get('criteres_economique', ''),
                                        'criteres_techniques': default_lot_data.get('criteres_techniques', ''),
                                        'autres_criteres': default_lot_data.get('autres_criteres', ''),
                                        'source': 'default_lot'
                                    },
                                    'extraction_source': 'default_lot',
                                    'metadata': {
                                        'nom_fichier': uploaded_file.name,
                                        'taille': uploaded_file.size,
                                        'contenu_extraite': {'type': 'pdf_avance'},
                                        'erreur': None
                                    }
                                }
                                extracted_entries = [extracted_info]
                        else:
                            extracted_entries = [{'erreur': 'Aucun texte extrait du PDF'}]
                    else:
                        # Utiliser l'ancien système pour les autres fichiers
                        file_analysis = {
                            'nom': uploaded_file.name,
                            'type': uploaded_file.type,
                            'taille': uploaded_file.size,
                            'contenu_extraite': {'type': 'excel' if 'excel' in uploaded_file.type else 'texte'},
                            'erreur': None
                        }
                        extracted_entries = ao_extractor.extract_from_file(uploaded_file, file_analysis, data.columns.tolist())
                        
                        # NOUVEAU: Extraction des critères pour les autres types de fichiers
                        if extracted_entries and not any('erreur' in entry for entry in extracted_entries):
                            # Extraire le texte pour l'analyse des critères
                            text_content = ""
                            if 'excel' in uploaded_file.type:
                                # Pour Excel, essayer d'extraire le texte
                                try:
                                    import pandas as pd
                                    df = pd.read_excel(uploaded_file)
                                    text_content = df.to_string()
                                except:
                                    text_content = str(extracted_entries)
                            else:
                                # Pour Word et TXT, lire le contenu
                                try:
                                    text_content = uploaded_file.read().decode('utf-8')
                                except:
                                    text_content = str(extracted_entries)
                            
                            if text_content:
                                # Extraire les critères
                                criteria_result = criteria_extractor.extract_criteria(text_content, uploaded_file.type)
                                
                                if criteria_result.has_criteria:
                                    # Ajouter les critères aux entrées extraites
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
                        st.success("✅ Extraction réussie!")
                        
                        # Affichage des résultats
                        st.info(f"🎯 **{len(extracted_entries)} lot(s) détecté(s)**")
                        
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
                        
                        # NOUVEAU: Validation croisée avant insertion
                        if hasattr(ao_extractor, 'validate_extraction'):
                            # Validation pour chaque lot
                            for i, extracted_info in enumerate(extracted_entries):
                                # Fusion des valeurs extraites et générées pour la validation
                                all_values = {}
                                all_values.update(extracted_info.get('valeurs_extraites', {}))
                                all_values.update(extracted_info.get('valeurs_generees', {}))
                            
                            with st.expander("🔍 Validation croisée des données"):
                                for i, extracted_info in enumerate(extracted_entries):
                                    lot_id = extracted_info.get('lot_id', f'LOT_{i+1}')
                                    lot_numero = extracted_info.get('valeurs_extraites', {}).get('lot_numero', i+1)
                                    lot_intitule = extracted_info.get('valeurs_extraites', {}).get('intitule_lot', 'N/A')
                                    
                                    st.subheader(f"📋 Lot {lot_numero}: {lot_intitule[:50]}...")
                                    
                                    # Fusion des valeurs extraites et générées pour la validation
                                    all_values = {}
                                    all_values.update(extracted_info.get('valeurs_extraites', {}))
                                    all_values.update(extracted_info.get('valeurs_generees', {}))
                                    
                                    validation_result = ao_extractor.validate_extraction(all_values)
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if validation_result['overall_valid']:
                                            st.success("✅ Validation réussie")
                                        else:
                                            st.warning("⚠️ Problèmes de validation détectés")
                                    
                                    with col2:
                                        confidence = validation_result['overall_confidence'] * 100
                                        st.metric("Confiance", f"{confidence:.1f}%")
                                    
                                    # Afficher les recommandations
                                    if validation_result.get('recommendations'):
                                        st.info("💡 **Recommandations:**")
                                        for rec in validation_result['recommendations']:
                                            st.write(f"• {rec}")
                                    
                                    # Afficher les détails de validation
                                    if st.checkbox(f"Afficher les détails de validation - Lot {lot_numero}", key=f"validation_details_{i}"):
                                        st.json(validation_result)
                                    
                                    if i < len(extracted_entries) - 1:
                                        st.markdown("---")
                        
                        # NOUVEAU: Affichage détaillé des valeurs extraites et générées
                        st.markdown("---")
                        st.subheader("📊 Détail des Données")
                        
                        # Afficher la liste des lots détectés
                        for i, extracted_info in enumerate(extracted_entries):
                            lot_id = extracted_info.get('lot_id', f'LOT_{i+1}')
                            lot_numero = extracted_info.get('valeurs_extraites', {}).get('lot_numero', i+1)
                            lot_intitule = extracted_info.get('valeurs_extraites', {}).get('intitule_lot', 'N/A')
                            
                            st.markdown(f"**Lot {lot_numero}: {lot_intitule}**")
                        
                        # Interface d'édition unique (en dehors de la boucle)
                        if extracted_entries:
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
                                if f'lots_list_{i}' not in st.session_state:
                                        # NOUVEAU: Récupérer les lots depuis extracted_entries
                                        existing_lots = []
                                        
                                        # Essayer de récupérer les lots depuis all_data d'abord
                                        if all_data.get('lots'):
                                            existing_lots = all_data.get('lots', [])
                                        else:
                                            # Si pas de lots dans all_data, créer les lots depuis extracted_entries
                                            for j, entry in enumerate(extracted_entries):
                                                lot_info = entry.get('lot_info', {})
                                                if lot_info:
                                                    # Utiliser les informations du lot détecté par l'IA
                                                    lot = {
                                                        'numero': lot_info.get('numero', j + 1),
                                                        'intitule': lot_info.get('intitule', ''),
                                                        'attributaire': lot_info.get('attributaire', ''),
                                                        'produit_retenu': lot_info.get('produit_retenu', ''),
                                                        'infos_complementaires': lot_info.get('infos_complementaires', ''),
                                                        'montant_estime': lot_info.get('montant_estime', 0),
                                                        'montant_maximum': lot_info.get('montant_maximum', 0)
                                                    }
                                                    existing_lots.append(lot)
                                        
                                        if existing_lots:
                                            st.session_state[f'lots_list_{i}'] = existing_lots
                                        else:
                                            # Créer un lot par défaut avec les données existantes
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
                                            st.session_state[f'lots_list_{i}'] = [default_lot]
                                        
                                        # Afficher le nombre total de lots
                                        total_lots = len(st.session_state[f'lots_list_{i}'])
                                        
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
                                        
                                        # Afficher chaque lot
                                        for lot_idx, lot in enumerate(st.session_state[f'lots_list_{i}']):
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
                                        
                                        # Créer un formulaire d'édition complet avec toutes les 44 colonnes
                                        with st.form(f"edit_extracted_data_{i}"):
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
                                                        key=f"edit_mots_cles_{i}"
                                                    )
                                                    
                                                    # Univers
                                                edited_data['univers'] = st.selectbox(
                                                    "Univers",
                                                    options=['MÉDICAL', 'TECHNIQUE', 'GÉNÉRAL', 'INFORMATIQUE', 'LOGISTIQUE', 'MAINTENANCE', 'AUTRE'],
                                                    index=['MÉDICAL', 'TECHNIQUE', 'GÉNÉRAL', 'INFORMATIQUE', 'LOGISTIQUE', 'MAINTENANCE', 'AUTRE'].index(all_data.get('univers', 'MÉDICAL')) if all_data.get('univers') in ['MÉDICAL', 'TECHNIQUE', 'GÉNÉRAL', 'INFORMATIQUE', 'LOGISTIQUE', 'MAINTENANCE', 'AUTRE'] else 0,
                                                    key=f"edit_univers_{i}"
                                                )
                                        
                                                # Segment
                                                edited_data['segment'] = st.text_input(
                                                    "Segment", 
                                                    value=all_data.get('segment', ''),
                                                    key=f"edit_segment_{i}"
                                                )
                                                
                                                # Famille
                                                edited_data['famille'] = st.text_input(
                                                    "Famille", 
                                                    value=all_data.get('famille', ''),
                                                    key=f"edit_famille_{i}"
                                                )
                                        
                                                # Statut
                                                edited_data['statut'] = st.selectbox(
                                                    "Statut",
                                                    options=['AO EN COURS', 'AO ATTRIBUÉ', 'AO ANNULÉ', 'AO REPORTÉ', 'AO SUSPENDU', 'AO CLÔTURÉ'],
                                                    index=['AO EN COURS', 'AO ATTRIBUÉ', 'AO ANNULÉ', 'AO REPORTÉ', 'AO SUSPENDU', 'AO CLÔTURÉ'].index(all_data.get('statut', 'AO EN COURS')) if all_data.get('statut') in ['AO EN COURS', 'AO ATTRIBUÉ', 'AO ANNULÉ', 'AO REPORTÉ', 'AO SUSPENDU', 'AO CLÔTURÉ'] else 0,
                                                    key=f"edit_statut_{i}"
                                                )
                                    
                                                # Groupement
                                                edited_data['groupement'] = st.selectbox(
                                                    "Groupement",
                                                    options=['RESAH', 'UNIHA', 'UGAP', 'CAIH', 'AUTRE'],
                                                    index=['RESAH', 'UNIHA', 'UGAP', 'CAIH', 'AUTRE'].index(all_data.get('groupement', 'RESAH')) if all_data.get('groupement') in ['RESAH', 'UNIHA', 'UGAP', 'CAIH', 'AUTRE'] else 0,
                                                    key=f"edit_groupement_{i}"
                                                )
                                                
                                            with col2:
                                                st.markdown("#### 📄 Procédure")
                                                
                                                # Référence de procédure
                                                edited_data['reference_procedure'] = st.text_input(
                                                    "Référence de procédure", 
                                                    value=all_data.get('reference_procedure', ''),
                                                    key=f"edit_ref_proc_{i}"
                                                )
                                                
                                                # Type de procédure
                                                edited_data['type_procedure'] = st.selectbox(
                                                    "Type de procédure",
                                                    options=['Appel d\'offres ouvert', 'Appel d\'offres restreint', 'Procédure adaptée', 'Marché de gré à gré', 'Accord-cadre'],
                                                    index=['Appel d\'offres ouvert', 'Appel d\'offres restreint', 'Procédure adaptée', 'Marché de gré à gré', 'Accord-cadre'].index(all_data.get('type_procedure', 'Appel d\'offres ouvert')) if all_data.get('type_procedure') in ['Appel d\'offres ouvert', 'Appel d\'offres restreint', 'Procédure adaptée', 'Marché de gré à gré', 'Accord-cadre'] else 0,
                                                    key=f"edit_type_proc_{i}"
                                                )
                                                
                                                # Mono ou multi-attributif
                                                edited_data['mono_multi'] = st.selectbox(
                                                    "Mono ou multi-attributif",
                                                    options=['Mono-attributif', 'Multi-attributif'],
                                                    index=['Mono-attributif', 'Multi-attributif'].index(all_data.get('mono_multi', 'Multi-attributif')) if all_data.get('mono_multi') in ['Mono-attributif', 'Multi-attributif'] else 1,
                                                    key=f"edit_mono_multi_{i}"
                                                )
                                                
                                                # Exécution du marché
                                                edited_data['execution_marche'] = st.text_input(
                                                    "Exécution du marché", 
                                                    value=all_data.get('execution_marche', ''),
                                                    key=f"edit_execution_marche_{i}"
                                                )
                                                
                                                # Intitulé de procédure
                                                edited_data['intitule_procedure'] = st.text_area(
                                                    "Intitulé de procédure", 
                                                    value=all_data.get('intitule_procedure', ''),
                                                    key=f"edit_int_proc_{i}",
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
                                                    key=f"edit_date_limite_{i}"
                                                )
                                                    
                                                    # Date d'attribution
                                                edited_data['date_attribution'] = st.date_input(
                                                        "Date d'attribution du marché",
                                                    value=pd.to_datetime(all_data.get('date_attribution', '2024-12-31')).date() if all_data.get('date_attribution') else None,
                                                    key=f"edit_date_attribution_{i}"
                                                )
                                                
                                                # Durée du marché
                                                edited_data['duree_marche'] = st.number_input(
                                                    "Durée du marché (mois)",
                                                    value=int(all_data.get('duree_marche', 0)) if all_data.get('duree_marche') else 0,
                                                    min_value=0,
                                                    max_value=120,
                                                    key=f"edit_duree_marche_{i}"
                                                )
                                                
                                                with col2:
                                                    st.markdown("#### 🔄 Reconduction")
                                                    
                                                    # Reconduction
                                                    edited_data['reconduction'] = st.selectbox(
                                                        "Reconduction",
                                                        options=['Oui', 'Non', 'Non spécifié'],
                                                        index=['Oui', 'Non', 'Non spécifié'].index(all_data.get('reconduction', 'Non spécifié')) if all_data.get('reconduction') in ['Oui', 'Non', 'Non spécifié'] else 2,
                                                        key=f"edit_reconduction_{i}"
                                                    )
                                                    
                                                    # Fin sans reconduction
                                                    edited_data['fin_sans_reconduction'] = st.date_input(
                                                        "Fin (sans reconduction)",
                                                        value=pd.to_datetime(all_data.get('fin_sans_reconduction')).date() if all_data.get('fin_sans_reconduction') else None,
                                                        key=f"edit_fin_sans_reconduction_{i}"
                                                    )
                                                    
                                                    # Fin avec reconduction
                                                    edited_data['fin_avec_reconduction'] = st.date_input(
                                                        "Fin (avec reconduction)",
                                                        value=pd.to_datetime(all_data.get('fin_avec_reconduction')).date() if all_data.get('fin_avec_reconduction') else None,
                                                        key=f"edit_fin_avec_reconduction_{i}"
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
                                                        key=f"edit_remarques_{i}",
                                                        height=100
                                                    )
                                                    
                                                    # Notes de l'acheteur sur la procédure
                                                    edited_data['notes_acheteur_procedure'] = st.text_area(
                                                        "Notes de l'acheteur sur la procédure", 
                                                        value=all_data.get('notes_acheteur_procedure', ''),
                                                        key=f"edit_notes_acheteur_procedure_{i}",
                                                        height=100
                                                    )
                                                    
                                                    # Notes de l'acheteur sur le fournisseur
                                                    edited_data['notes_acheteur_fournisseur'] = st.text_area(
                                                        "Notes de l'acheteur sur le fournisseur", 
                                                        value=all_data.get('notes_acheteur_fournisseur', ''),
                                                        key=f"edit_notes_acheteur_fournisseur_{i}",
                                                        height=100
                                                    )
                                                
                                                with col2:
                                                    st.markdown("#### 📊 Autres informations")
                                                    
                                                    # Notes de l'acheteur sur le positionnement
                                                    edited_data['notes_acheteur_positionnement'] = st.text_area(
                                                        "Notes de l'acheteur sur le positionnement", 
                                                        value=all_data.get('notes_acheteur_positionnement', ''),
                                                        key=f"edit_notes_acheteur_positionnement_{i}",
                                                        height=100
                                                    )
                                                    
                                                    # Note Veille concurrentielle
                                                    edited_data['note_veille'] = st.text_input(
                                                        "Note Veille concurrentielle disponible", 
                                                        value=all_data.get('note_veille', ''),
                                                        key=f"edit_note_veille_{i}"
                                                    )
                                                    
                                                    # Achat
                                                    edited_data['achat'] = st.selectbox(
                                                        "Achat",
                                                        options=['Oui', 'Non', 'Non spécifié'],
                                                        index=['Oui', 'Non', 'Non spécifié'].index(all_data.get('achat', 'Non spécifié')) if all_data.get('achat') in ['Oui', 'Non', 'Non spécifié'] else 2,
                                                        key=f"edit_achat_{i}"
                                                    )
                                                    
                                                    # Crédit bail
                                                    edited_data['credit_bail'] = st.selectbox(
                                                        "Crédit bail",
                                                        options=['Oui', 'Non', 'Non spécifié'],
                                                        index=['Oui', 'Non', 'Non spécifié'].index(all_data.get('credit_bail', 'Non spécifié')) if all_data.get('credit_bail') in ['Oui', 'Non', 'Non spécifié'] else 2,
                                                        key=f"edit_credit_bail_{i}"
                                                    )
                                                    
                                                    # Crédit bail durée
                                                    edited_data['credit_bail_duree'] = st.number_input(
                                                        "Crédit bail (durée année)",
                                                        value=int(all_data.get('credit_bail_duree', 0)) if all_data.get('credit_bail_duree') else 0,
                                                        min_value=0,
                                                        max_value=20,
                                                        key=f"edit_credit_bail_duree_{i}"
                                                    )
                                                    
                                                    # Location
                                                    edited_data['location'] = st.selectbox(
                                                        "Location",
                                                        options=['Oui', 'Non', 'Non spécifié'],
                                                        index=['Oui', 'Non', 'Non spécifié'].index(all_data.get('location', 'Non spécifié')) if all_data.get('location') in ['Oui', 'Non', 'Non spécifié'] else 2,
                                                        key=f"edit_location_{i}"
                                                    )
                                                    
                                                    # Location durée
                                                    edited_data['location_duree'] = st.number_input(
                                                        "Location (durée années)",
                                                        value=int(all_data.get('location_duree', 0)) if all_data.get('location_duree') else 0,
                                                        min_value=0,
                                                        max_value=20,
                                                        key=f"edit_location_duree_{i}"
                                                    )
                                                    
                                                    # MAD
                                                    edited_data['mad'] = st.selectbox(
                                                        "MAD",
                                                        options=['Oui', 'Non', 'Non spécifié'],
                                                        index=['Oui', 'Non', 'Non spécifié'].index(all_data.get('mad', 'Non spécifié')) if all_data.get('mad') in ['Oui', 'Non', 'Non spécifié'] else 2,
                                                        key=f"edit_mad_{i}"
                                                )
                                            
                                            # Mettre à jour les données des lots depuis session_state
                                            if f'lots_list_{i}' in st.session_state:
                                                edited_data['lots'] = st.session_state[f'lots_list_{i}']
                                                edited_data['nbr_lots'] = len(st.session_state[f'lots_list_{i}'])
                                                
                                                # Pour la compatibilité avec l'ancien système, garder les champs principaux
                                                if st.session_state[f'lots_list_{i}']:
                                                    premier_lot = st.session_state[f'lots_list_{i}'][0]
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
                                                    total_estime = sum(lot.get('montant_estime', 0) for lot in st.session_state[f'lots_list_{i}'])
                                                    total_maximum = sum(lot.get('montant_maximum', 0) for lot in st.session_state[f'lots_list_{i}'])
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
                                lots_list = st.session_state.get(f'lots_list_{i}', [])
                                
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
                                        if col not in df_all_lots.columns:
                                            df_all_lots[col] = ''
                                    
                                    # Réorganiser les colonnes
                                    df_all_lots = df_all_lots[all_columns]
                                    
                                    # Afficher le tableau complet
                                    st.dataframe(df_all_lots, width='stretch', height=400)
                                    
                                    # Bouton pour éditer le tableau complet
                                    if st.button("✏️ Éditer le tableau complet"):
                                        st.info("💡 Utilisez le formulaire ci-dessus pour modifier les valeurs, puis cliquez sur 'Sauvegarder'")
                                else:
                                    # Afficher seulement les colonnes principales
                                    st.dataframe(df_all_lots, width='stretch')
                                
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
                        
                        # Bouton pour insérer dans la base
                        if st.button("💾 Insérer dans la base de données", type="primary"):
                            try:
                                # Insérer chaque lot dans la base de données
                                total_inserted = 0
                                for i, extracted_info in enumerate(extracted_entries):
                                    # NOUVEAU: Créer une ligne par lot détecté
                                    lots_list = st.session_state.get(f'lots_list_{i}', [])
                                    
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
                                                
                                                if result['success']:
                                                    total_inserted += result['rows_inserted']
                                                    st.info(f"✅ Lot {lot.get('numero', lot_idx + 1)} inséré: {lot.get('intitule', '')[:50]}...")
                                                else:
                                                    st.error(f"❌ Erreur insertion lot {lot.get('numero', lot_idx + 1)}: {result.get('error', 'Erreur inconnue')}")
                                    else:
                                        # Fallback: insérer comme avant si pas de lots détectés
                                        all_values = {}
                                        all_values.update(extracted_info.get('valeurs_extraites', {}))
                                        all_values.update(extracted_info.get('valeurs_generees', {}))
                                        
                                        if all_values:
                                            df_new = pd.DataFrame([all_values])
                                            result = db_manager.insert_dataframe(df_new)
                                            
                                            if result['success']:
                                                total_inserted += result['rows_inserted']
                                            else:
                                                st.error(f"❌ Erreur insertion lot {i+1}: {result.get('error', 'Erreur inconnue')}")
                                
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
                results = db_manager.search_data(search_term)
                if not results.empty:
                    st.write(f"**Résultats trouvés:** {len(results)}")
                    st.dataframe(results.head(10), width='stretch')
                else:
                    st.info("Aucun résultat trouvé")
            
            # NOUVEAU: Monitoring et maintenance de la base
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
            
            # NOUVEAU: Informations détaillées de la base
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
    
    # Footer
    st.markdown("---")
    st.markdown("🚀 **IA Conversationnelle - Veille Concurrentielle** - Système ultra performant pour l'analyse d'appels d'offres")
    st.markdown("🤖 **IA Locale** | 🗄️ **Base locale**")
    
except Exception as e:
    st.error(f"❌ Erreur lors du chargement de l'application: {e}")
    st.info("Vérifiez que l'application est correctement configurée")
