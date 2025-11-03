"""
Onglet IA
Gère l'interface et les interactions avec l'IA
"""

import streamlit as st
from ai_engine import VeilleAIEngine
import pandas as pd
import json
import re
import plotly.express as px
import plotly.graph_objects as go


def render_graphs(graph_data: dict, key_prefix: str = "graph"):
    """
    Affiche les graphiques selon les données fournies
    
    Args:
        graph_data (dict): Dictionnaire contenant les données des graphiques
        key_prefix (str): Préfixe pour les clés uniques des graphiques
    """
    if not graph_data:
        st.warning("⚠️ Aucune donnée de graphique disponible")
        return
    
    if 'data' not in graph_data or not graph_data['data']:
        st.warning("⚠️ Les données de graphique sont vides")
        return
    
    graph_type = graph_data.get('type', 'distribution')
    data = graph_data.get('data', {})
    
    graphs_created = 0
    
    # Graphiques de répartition (camembert ou barres)
    for key in ['univers', 'groupement', 'statut', 'urgence']:
        if key in data:
            chart_data = data[key]
            labels = chart_data.get('labels', [])
            values = chart_data.get('values', [])
            title = chart_data.get('title', f'Répartition par {key}')
            
            # Filtrer les labels et values vides
            if labels and values and len(labels) > 0 and len(values) > 0:
                # Filtrer les valeurs None ou vides
                filtered_pairs = [(l, v) for l, v in zip(labels, values) if l and str(l).strip() and (v is not None and v > 0)]
                
                if filtered_pairs:
                    labels_filtered = [l for l, v in filtered_pairs]
                    values_filtered = [v for l, v in filtered_pairs]
                    
                    # Créer un graphique en barres
                    try:
                        fig = px.bar(
                            x=labels_filtered,
                            y=values_filtered,
                            title=title,
                            labels={'x': '', 'y': 'Nombre de lots'},
                            color=values_filtered,
                            color_continuous_scale='Blues'
                        )
                        fig.update_layout(
                            showlegend=False,
                            height=400,
                            xaxis_tickangle=-45
                        )
                        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_{key}_bar")
                        graphs_created += 1
                    except Exception as e:
                        st.warning(f"⚠️ Erreur création graphique barres {key}: {e}")
                    
                    # Créer aussi un camembert si moins de 10 catégories
                    if len(labels_filtered) <= 10 and len(labels_filtered) > 0:
                        try:
                            fig_pie = px.pie(
                                values=values_filtered,
                                names=labels_filtered,
                                title=title,
                                hole=0.4
                            )
                            fig_pie.update_layout(height=400)
                            st.plotly_chart(fig_pie, use_container_width=True, key=f"{key_prefix}_{key}_pie")
                            graphs_created += 1
                        except Exception as e:
                            st.warning(f"⚠️ Erreur création graphique camembert {key}: {e}")
    
    # Graphique de distribution des montants (histogramme)
    if 'montants' in data:
        montants_data = data['montants']
        values = montants_data.get('values', [])
        title = montants_data.get('title', 'Distribution des Montants')
        
        if values and len(values) > 0:
            # Filtrer les valeurs valides
            valid_values = [v for v in values if v is not None and v > 0]
            
            if valid_values:
                fig = px.histogram(
                    x=valid_values,
                    nbins=montants_data.get('bins', 20),
                    title=title,
                    labels={'x': montants_data.get('xlabel', 'Montant (€)'), 
                           'y': montants_data.get('ylabel', 'Nombre de lots')}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_montants")
                graphs_created += 1
    
    # Graphique timeline pour les lots expirants
    if 'timeline' in data:
        timeline_data = data['timeline']
        dates = timeline_data.get('dates', [])
        jours_restants = timeline_data.get('jours_restants', [])
        montants = timeline_data.get('montants', [])
        title = timeline_data.get('title', 'Timeline des Expirations')
        
        if dates and jours_restants and len(dates) > 0:
            # Créer un DataFrame pour le graphique
            df_timeline = pd.DataFrame({
                'Date': pd.to_datetime(dates),
                'Jours restants': jours_restants,
                'Montant': montants if montants else [0] * len(dates)
            })
            
            # Graphique en ligne avec les jours restants
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_timeline['Date'],
                y=df_timeline['Jours restants'],
                mode='lines+markers',
                name='Jours restants',
                line=dict(color='red', width=2),
                marker=dict(size=8)
            ))
            
            # Si on a des montants, créer un graphique secondaire
            if montants and any(m > 0 for m in montants):
                fig.add_trace(go.Bar(
                    x=df_timeline['Date'],
                    y=df_timeline['Montant'],
                    name='Montant',
                    yaxis='y2',
                    opacity=0.5
                ))
                fig.update_layout(
                    yaxis2=dict(
                        title='Montant (€)',
                        overlaying='y',
                        side='right'
                    )
                )
            
            fig.update_layout(
                title=title,
                xaxis_title=timeline_data.get('xlabel', 'Date de fin'),
                yaxis_title=timeline_data.get('ylabel', 'Jours restants'),
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_timeline")
            graphs_created += 1
    
    # Message si aucun graphique n'a été créé
    if graphs_created == 0:
        st.info("ℹ️ Aucun graphique disponible pour ces données")


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
                    # Afficher le contenu avant le tableau (nettoyé des sections non désirées)
                    content = message.get('content', '')
                    if content:
                        # Supprimer les sections d'aperçu des résultats du contenu principal
                        # Pattern 1: Supprimer tout entre "Aperçu" et "... et X autres résultats"
                        # Pattern pour supprimer toute la section d'aperçu
                        pattern1 = r'Aperçu des (premiers )?résultats.*?\.\.\. et \d+ autres résultats'
                        content = re.sub(pattern1, '', content, flags=re.DOTALL | re.IGNORECASE)
                        
                        # Pattern 2: Supprimer toutes les sections avec "Lot #" et leurs détails
                        # Supprimer toute section qui commence par "Lot #" jusqu'à ce qu'on trouve "autres résultats" ou un autre "Lot #"
                        lines = content.split('\n')
                        filtered_lines = []
                        in_lot_section = False
                        
                        for i, line in enumerate(lines):
                            line_lower = line.lower()
                            line_stripped = line.strip()
                            
                            # Détecter le début de la section "Aperçu"
                            if 'aperçu' in line_lower and 'résultats' in line_lower:
                                in_lot_section = True
                                continue
                            
                            # Détecter les lignes avec "Lot #"
                            if 'lot #' in line_lower or line_stripped.startswith('**Lot #'):
                                in_lot_section = True
                                continue
                            
                            # Si on est dans la section des lots, ignorer toutes les lignes jusqu'à la fin
                            if in_lot_section:
                                # Détecter la fin de la section
                                if 'autres résultats' in line_lower or 'et' in line_lower and 'autres' in line_lower:
                                    in_lot_section = False
                                # Ignorer toutes les lignes qui contiennent des détails de lot
                                elif any(keyword.lower() in line_lower for keyword in ['intitule lot', 'groupement', 'univers:', 'statut:', 'reference procedure', 'date limite', 'intitule procedure']):
                                    continue
                                # Ignorer les lignes vides dans la section
                                elif line_stripped == '':
                                    continue
                                else:
                                    continue
                            
                            # Ajouter la ligne seulement si on n'est pas dans la section des lots
                            if not in_lot_section:
                                filtered_lines.append(line)
                        
                        cleaned_content = '\n'.join(filtered_lines).strip()
                        # Nettoyer les lignes vides multiples
                        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
                        # Supprimer tout ce qui reste entre "Aperçu" et "autres résultats" au cas où
                        cleaned_content = re.sub(r'aperçu.*?autres résultats', '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)
                        
                        if cleaned_content:
                            st.markdown(cleaned_content)
                    
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
                    
                    # Afficher les graphiques si présents
                    if 'graph_data' in message and message['graph_data'] is not None:
                        graph_data = message['graph_data']
                        st.markdown("#### 📊 Visualisations")
                        try:
                            # Debug: afficher le nombre de graphiques disponibles
                            if graph_data and 'data' in graph_data:
                                num_graphs = len([k for k in graph_data['data'].keys() if graph_data['data'][k]])
                                if num_graphs > 0:
                                    render_graphs(graph_data, key_prefix=f"graphs_{idx}")
                                else:
                                    st.info("ℹ️ Aucune donnée de graphique disponible dans les données filtrées")
                            else:
                                st.warning("⚠️ Format de données de graphique invalide")
                                st.json(graph_data)  # Afficher pour debug
                        except Exception as e:
                            st.error(f"❌ Erreur lors de l'affichage des graphiques: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                            st.json(graph_data)  # Afficher les données brutes pour debug
                    
                    # Afficher le contenu après le tableau (nettoyé des sections non désirées)
                    if 'after_table' in message and message['after_table']:
                        after_content = message['after_table']
                        # Utiliser le même nettoyage agressif
                        # Pattern pour supprimer toute la section d'aperçu
                        pattern1 = r'Aperçu des (premiers )?résultats.*?\.\.\. et \d+ autres résultats'
                        after_content = re.sub(pattern1, '', after_content, flags=re.DOTALL | re.IGNORECASE)
                        
                        # Supprimer toutes les sections avec "Lot #"
                        lines = after_content.split('\n')
                        filtered_lines = []
                        in_lot_section = False
                        
                        for line in lines:
                            line_lower = line.lower()
                            line_stripped = line.strip()
                            
                            # Détecter le début de la section "Aperçu"
                            if 'aperçu' in line_lower and 'résultats' in line_lower:
                                in_lot_section = True
                                continue
                            
                            # Détecter les lignes avec "Lot #"
                            if 'lot #' in line_lower or line_stripped.startswith('**Lot #'):
                                in_lot_section = True
                                continue
                            
                            # Si on est dans la section des lots, ignorer toutes les lignes
                            if in_lot_section:
                                # Détecter la fin de la section
                                if 'autres résultats' in line_lower:
                                    in_lot_section = False
                                    continue
                                # Ignorer toutes les lignes qui contiennent des détails de lot
                                elif any(keyword.lower() in line_lower for keyword in ['intitule lot', 'groupement', 'univers:', 'statut:', 'reference procedure', 'date limite', 'intitule procedure']):
                                    continue
                                # Ignorer les lignes vides
                                elif line_stripped == '':
                                    continue
                                else:
                                    continue
                            
                            # Ajouter la ligne seulement si on n'est pas dans la section des lots
                            if not in_lot_section:
                                filtered_lines.append(line)
                        
                        cleaned_content = '\n'.join(filtered_lines).strip()
                        # Nettoyer les lignes vides multiples
                        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
                        # Supprimer tout ce qui reste entre "Aperçu" et "autres résultats"
                        cleaned_content = re.sub(r'aperçu.*?autres résultats', '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)
                        
                        if cleaned_content:
                            st.markdown(cleaned_content)
    
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
                        answer = ai_engine.ask_question(question)
                        
                        # Vérifier si la réponse contient un tableau et/ou des graphiques
                        has_table = "```TABLEAU_STREAMLIT```" in answer
                        has_graphs = "```GRAPHIQUES_STREAMLIT```" in answer
                        
                        table_data = None
                        graph_data = None
                        before_table = answer
                        after_table = ""
                        
                        # Traiter le tableau d'abord
                        if has_table:
                            # Récupérer les données du tableau
                            table_data = ai_engine.get_last_table_data()
                            # Diviser la réponse autour du tableau
                            parts = before_table.split("```TABLEAU_STREAMLIT```")
                            before_table = parts[0]
                            after_table = parts[1] if len(parts) > 1 else ""
                        
                        # Traiter les graphiques
                        if has_graphs:
                            # Récupérer les données des graphiques
                            graph_data = ai_engine.get_last_graph_data()
                            
                            # Debug: vérifier si les données sont présentes
                            if graph_data is None:
                                st.warning("⚠️ Aucune donnée de graphique récupérée de l'IA")
                            elif not graph_data.get('data'):
                                st.warning("⚠️ Données de graphique vides")
                            
                            # Si le marqueur est dans after_table, le nettoyer
                            if "```GRAPHIQUES_STREAMLIT```" in after_table:
                                after_table = after_table.replace("```GRAPHIQUES_STREAMLIT```", "").strip()
                            # Si le marqueur est dans before_table (pas de tableau), le nettoyer aussi
                            elif "```GRAPHIQUES_STREAMLIT```" in before_table:
                                before_table = before_table.replace("```GRAPHIQUES_STREAMLIT```", "").strip()
                        
                        # Construire le message de réponse
                        message_dict = {
                            'type': 'assistant',
                            'content': before_table
                        }
                        
                        if table_data is not None:
                            message_dict['table_data'] = table_data
                            if after_table:
                                message_dict['after_table'] = after_table
                        
                        if graph_data is not None:
                            message_dict['graph_data'] = graph_data
                        
                        st.session_state.conversation_messages.append(message_dict)
                        
                        # Afficher un message de succès
                        st.success("✅ Réponse générée avec succès !")
                        
                        # Recharger pour afficher la nouvelle conversation
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la génération de la réponse: {e}")
        else:
            st.warning("⚠️ Veuillez entrer une question")

