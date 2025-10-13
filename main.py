"""
🚀 Application de Veille Concurrentielle IA
========================================

Interface interactive pour le moteur d'IA de veille concurrentielle
"""

import pandas as pd
from ai_engine import VeilleAIEngine
import logging
from pathlib import Path

def main():
    print("🤖 Démarrage de l'assistant IA de veille concurrentielle...")
    
    # Initialiser le moteur d'IA
    engine = VeilleAIEngine()
    
    # Vérifier si le fichier de données existe
    data_file = Path("data.csv")
    if not data_file.exists():
        print("⚠️ Aucun fichier de données trouvé.")
        print("💡 Créons un exemple de données pour démonstration...")
        
        # Créer des données de démonstration
        demo_data = {
            'id': range(1, 6),
            'groupement': ['RESAH', 'UNIHA', 'UGAP', 'RESAH', 'UNIHA'],
            'univers': ['Médical', 'Informatique', 'Équipement', 'Médical', 'Mobilier'],
            'intitule_lot': [
                'Équipements d\'imagerie médicale',
                'Serveurs et stockage',
                'Véhicules électriques',
                'Matériel de laboratoire',
                'Mobilier de bureau ergonomique'
            ],
            'montant_global_estime': [1500000, 800000, 2000000, 300000, 150000],
            'date_limite': ['2025-12-31', '2025-11-30', '2025-10-31', '2025-09-30', '2025-08-31'],
            'statut': ['En cours', 'Attribué', 'En cours', 'En cours', 'Attribué'],
            'mots_cles': [
                'imagerie,radiologie,scanner',
                'informatique,serveur,stockage',
                'véhicule,électrique,mobilité',
                'laboratoire,analyse,recherche',
                'mobilier,bureau,ergonomie'
            ]
        }
        df = pd.DataFrame(demo_data)
        df.to_csv(data_file, index=False)
        print("✅ Données de démonstration créées!")
    
    # Charger les données
    print("📊 Chargement des données...")
    data = pd.read_csv(data_file)
    
    # Initialiser le moteur avec les données
    print("🔄 Initialisation du moteur d'IA...")
    engine.initialize(data, load_heavy_models=False)  # Désactiver les modèles lourds pour le moment
    
    print("\n✨ Assistant IA prêt !")
    print("""
💡 Exemples de questions :
- "Montre-moi les offres du RESAH"
- "Cherche les lots médicaux"
- "Combien de lots ai-je par univers ?"
- "Analyse la répartition des budgets"
    """)
    
    # Boucle interactive
    while True:
        try:
            question = input("\n🤔 Votre question (ou 'q' pour quitter) : ")
            
            if question.lower() in ['q', 'quit', 'exit', 'quitter']:
                print("\n👋 Au revoir ! À bientôt !")
                break
            
            if question.strip():
                print("\n" + engine.ask_question(question))
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir ! À bientôt !")
            break
        except Exception as e:
            print(f"\n❌ Erreur : {str(e)}")
            print("N'hésitez pas à réessayer ou à reformuler votre question.")

if __name__ == "__main__":
    main()