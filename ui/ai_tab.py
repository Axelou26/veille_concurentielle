"""
Onglet IA
Gère l'interface et les interactions avec l'IA
"""

import streamlit as st
from ai_engine import VeilleAIEngine
import pandas as pd
import json


def render_ai_tab(data: pd.DataFrame, ai_engine: VeilleAIEngine):
    """
    Rend l'onglet IA
    
    Args:
        data (pd.DataFrame): Données de la base de données
        ai_engine (VeilleAIEngine): Moteur d'IA
    """
    st.header("🤖 Assistant IA")
    
    # Statut des modèles IA
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("🧠 **Moteur d'IA local** - Modèles français et multilingues")
    with col2:
        if st.button("🚀 Initialiser l'IA", type="primary"):
            with st.spinner("Initialisation des modèles IA..."):
                try:
                    ai_engine.initialize(data, load_heavy_models=True)
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
    
    # Métriques de performance de l'IA
    if hasattr(ai_engine, 'initialized') and ai_engine.initialized:
        st.success("✅ IA initialisée et prête à répondre")
    
    # Section conversation
    st.subheader("💬 Conversation avec l'IA")
    
    # Initialiser la conversation dans session_state
    if 'conversation_messages' not in st.session_state:
        st.session_state.conversation_messages = []
    
    # Afficher l'historique de la conversation
    if st.session_state.conversation_messages:
        st.markdown("### 📜 Historique de la conversation")
        
        for idx, message in enumerate(st.session_state.conversation_messages):
            if message['type'] == 'user':
                with st.chat_message("user"):
                    st.write(message['content'])
            elif message['type'] == 'assistant':
                with st.chat_message("assistant"):
                    # Afficher le contenu avant le tableau
                    st.markdown(message['content'])
                    
                    # Afficher le tableau si présent
                    if 'table_data' in message and message['table_data'] is not None:
                        table_data = message['table_data']
                        
                        # Afficher le tableau avec options
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            # Afficher seulement les 20 premières lignes par défaut
                            if not st.session_state.get(f"show_all_table_{idx}", False):
                                st.dataframe(table_data.head(20), width='stretch')
                                if len(table_data) > 20:
                                    st.info(f"Affichage des 20 premières lignes sur {len(table_data)}")
                            else:
                                st.dataframe(table_data, width='stretch')
                        
                        with col2:
                            # Bouton pour afficher tous les résultats
                            if len(table_data) > 20:
                                if st.button(f"📊 Afficher tous les {len(table_data)} résultats", key=f"show_all_{idx}"):
                                    st.session_state[f"show_all_table_{idx}"] = True
                                    st.rerun()
                            
                            # Bouton pour télécharger en CSV
                            if st.button("💾 Télécharger CSV", key=f"download_{idx}"):
                                csv_data = table_data.to_csv(index=False)
                                st.download_button(
                                    label="📥 Télécharger",
                                    data=csv_data,
                                    file_name=f"resultats_ia_{idx}.csv",
                                    mime="text/csv",
                                    key=f"dl_{idx}"
                                )
                        
                        # Afficher le tableau complet si demandé
                        if st.session_state.get(f"show_all_table_{idx}", False):
                            st.markdown("#### 📊 Tableau complet")
                            st.dataframe(
                                table_data,
                                width='stretch',
                                height=400
                            )
                    
                    # Afficher le contenu après le tableau
                    if 'after_table' in message and message['after_table']:
                        st.markdown(message['after_table'])
    
    # Formulaire de question
    st.markdown("### ❓ Posez une question")
    
    question = st.text_input(
        "Votre question",
        placeholder="Ex: Quels sont les marchés médicaux en cours ?",
        key="ai_question_input"
    )
    
    if st.button("🚀 Envoyer", type="primary"):
        if question:
            if not hasattr(ai_engine, 'initialized') or not ai_engine.initialized:
                st.error("❌ L'IA n'est pas encore initialisée. Cliquez sur 'Initialiser l'IA' d'abord.")
            else:
                with st.spinner("🤖 L'IA réfléchit..."):
                    try:
                        # Ajouter la question à la conversation
                        st.session_state.conversation_messages.append({
                            'type': 'user',
                            'content': question
                        })
                        
                        # Obtenir la réponse de l'IA
                        answer = ai_engine.query(question)
                        
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
                        st.error(f"❌ Erreur lors de la génération de la réponse: {e}")
        else:
            st.warning("⚠️ Veuillez entrer une question")

