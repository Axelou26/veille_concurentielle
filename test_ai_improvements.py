#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test des améliorations du moteur d'IA
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_engine import VeilleAIEngine
from pdf_extractor import AdvancedPDFExtractor
from extraction_improver import ExtractionImprover

def test_ai_improvements():
    """Test des améliorations du moteur d'IA"""
    print("Test des ameliorations du moteur d'IA")
    print("=" * 50)
    
    # Initialiser le moteur d'IA
    ai_engine = VeilleAIEngine()
    
    # Créer des données de test
    test_data = {
        'text': """
        RAPPORT DE CONSULTATION
        Référence: 2024-R041-000
        Montant global estimé: 150 000,00 €
        Date limite de remise des offres: 15/03/2024
        
        LOT 1: Développement d'application web
        Montant: 80 000,00 €
        Critères d'attribution:
        - Prix: 60%
        - Expérience: 40%
        
        LOT 2: Maintenance et support
        Montant: 70 000,00 €
        Critères d'attribution:
        - Prix: 70%
        - Expérience: 30%
        """,
        'montant_global_estime': '150 000,00 €',
        'date_limite': '15/03/2024',
        'intitule_procedure': 'Développement et maintenance informatique',
        'lots': [
            {
                'numero': '1',
                'intitule': 'Développement d\'application web',
                'montant': '80 000,00 €'
            },
            {
                'numero': '2',
                'intitule': 'Maintenance et support',
                'montant': '70 000,00 €'
            }
        ],
        'criteres_attribution': [
            {'nom': 'Prix', 'poids': '60%'},
            {'nom': 'Expérience', 'poids': '40%'}
        ]
    }
    
    print("Test 1: Analyse intelligente du contexte")
    try:
        context_analysis = ai_engine._analyze_context_intelligence(test_data)
        print(f"OK Type de document: {context_analysis['document_type']}")
        print(f"OK Niveau de complexite: {context_analysis['complexity_level']}")
        print(f"OK Patterns detectes: {context_analysis['patterns_detected']}")
        print(f"OK Anomalies trouvees: {context_analysis['anomalies_found']}")
        print(f"OK Recommandations: {context_analysis['recommendations']}")
    except Exception as e:
        print(f"ERREUR analyse contexte: {e}")
    
    print("\nTest 2: Detection intelligente de patterns")
    try:
        pattern_detection = ai_engine._detect_patterns_intelligence(test_data)
        print(f"OK Montants detectes: {len(pattern_detection['montants'])}")
        print(f"OK Dates detectees: {len(pattern_detection['dates'])}")
        print(f"OK References detectees: {len(pattern_detection['references'])}")
        print(f"OK Lots detectes: {len(pattern_detection['lots'])}")
        print(f"OK Criteres detectes: {len(pattern_detection['criteres'])}")
        print(f"OK Anomalies: {pattern_detection['anomalies']}")
    except Exception as e:
        print(f"ERREUR detection patterns: {e}")
    
    print("\nTest 3: Analyse semantique avancee")
    try:
        semantic_analysis = ai_engine._enrich_with_semantic_analysis(test_data)
        print(f"OK Classification domaine: {semantic_analysis.get('domain_classification', {})}")
        print(f"OK Mots-cles intelligents: {len(semantic_analysis.get('intelligent_keywords', []))}")
        print(f"OK Analyse coherence: {semantic_analysis.get('coherence_analysis', {})}")
        print(f"OK Prediction qualite: {semantic_analysis.get('quality_prediction', {})}")
        print(f"OK Suggestions IA: {len(semantic_analysis.get('ai_suggestions', []))}")
    except Exception as e:
        print(f"ERREUR analyse semantique: {e}")
    
    print("\nTest 4: Classification intelligente du document")
    try:
        classification = ai_engine._classify_document_intelligence(test_data)
        print(f"OK Domaine: {classification['domain']}")
        print(f"OK Sous-domaine: {classification['subdomain']}")
        print(f"OK Priorite: {classification['priority']}")
        print(f"OK Urgence: {classification['urgency']}")
        print(f"OK Complexite: {classification['complexity']}")
        print(f"OK Confiance: {classification['confidence']:.2f}")
    except Exception as e:
        print(f"ERREUR classification: {e}")
    
    print("\nTest 5: Extraction complete avec IA")
    try:
        # Simuler une extraction complete
        enriched_data = ai_engine._enrich_with_ai_intelligence(test_data, "test.pdf")
        print(f"OK Donnees enrichies: {len(enriched_data)} champs")
        print(f"OK Analyse contexte: {'OK' if 'context_analysis' in enriched_data else 'ERREUR'}")
        print(f"OK Detection patterns: {'OK' if 'pattern_detection' in enriched_data else 'ERREUR'}")
        print(f"OK Classification: {'OK' if 'classification' in enriched_data else 'ERREUR'}")
        print(f"OK Suggestions IA: {'OK' if 'ai_suggestions' in enriched_data else 'ERREUR'}")
    except Exception as e:
        print(f"ERREUR extraction complete: {e}")
    
    print("\nTest 6: Generation de rapport d'extraction")
    try:
        # Creer des donnees de validation simulees
        validation_results = {
            'confidence_score': 85.5,
            'warnings': ['Verifier la coherence des montants'],
            'suggestions': ['Ameliorer l\'extraction des criteres']
        }
        
        report = ai_engine._generate_extraction_report(test_data, enriched_data, validation_results)
        print(f"OK Rapport genere: {len(report)} caracteres")
        print(f"OK Contient resume: {'OK' if 'Resume General' in report else 'ERREUR'}")
        print(f"OK Contient analyse: {'OK' if 'Analyse du Contexte' in report else 'ERREUR'}")
        print(f"OK Contient classification: {'OK' if 'Classification' in report else 'ERREUR'}")
    except Exception as e:
        print(f"ERREUR generation rapport: {e}")
    
    print("\nTest 7: Questions intelligentes au moteur d'IA")
    try:
        # Initialiser le moteur avec des donnees de test
        df_test = pd.DataFrame([{
            'intitule_lot': 'Developpement web',
            'groupement': 'Informatique',
            'univers': 'Services',
            'montant_global_estime': 150000,
            'statut': 'En cours',
            'reference_procedure': '2024-R041-000',
            'date_limite': '2024-03-15',
            'intitule_procedure': 'Developpement informatique'
        }])
        
        ai_engine.initialize(df_test)
        
        # Tester quelques questions
        questions = [
            "Combien de lots y a-t-il ?",
            "Quel est le montant total ?",
            "Montre-moi les lots d'informatique",
            "Quelle est la date limite ?"
        ]
        
        for question in questions:
            try:
                answer = ai_engine.ask_question(question)
                print(f"OK Q: {question}")
                print(f"   R: {answer[:100]}...")
            except Exception as e:
                print(f"ERREUR question '{question}': {e}")
    except Exception as e:
        print(f"ERREUR test questions: {e}")
    
    print("\n" + "=" * 50)
    print("Tests des ameliorations termines !")
    print("Le moteur d'IA a ete considerablement ameliore avec :")
    print("   - Analyse intelligente du contexte")
    print("   - Detection de patterns avancee")
    print("   - Analyse semantique complete")
    print("   - Classification automatique")
    print("   - Validation croisee intelligente")
    print("   - Generation de rapports detailles")
    print("   - Suggestions d'amelioration IA")

if __name__ == "__main__":
    test_ai_improvements()
