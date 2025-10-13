#!/usr/bin/env python3
"""
Test simple de l'IA conversationnelle
"""

from ai_engine import VeilleAIEngine
from database_manager import DatabaseManager

def test_ai_conversational():
    """Test de l'IA conversationnelle"""
    try:
        print("[INIT] Initialisation...")
        db = DatabaseManager()
        data = db.get_all_data()
        ai = VeilleAIEngine()
        ai.initialize(data, load_heavy_models=False)
        
        print("[TEST] === TEST IA CONVERSATIONNELLE ===")
        
        # Test des réponses conversationnelles
        test_questions = [
            'salut',
            'aide',
            'qui es-tu ?',
            'merci'
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{i}. Question: '{question}'")
            try:
                result = ai.ask_question(question)
                print(f"Réponse: {result[:150]}...")
            except Exception as e:
                print(f"Erreur: {e}")
        
        print("\n[OK] Test terminé avec succès !")
        
    except Exception as e:
        print(f"[ERROR] Erreur lors du test: {e}")

if __name__ == "__main__":
    test_ai_conversational()
