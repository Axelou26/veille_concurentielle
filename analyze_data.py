#!/usr/bin/env python3
"""
Script d'analyse des données pour diagnostiquer les problèmes de recherche
"""

from database_manager import DatabaseManager
import pandas as pd

def analyze_data():
    print("🔍 Analyse des données...")
    
    # Charger les données
    db = DatabaseManager()
    data = db.get_all_data()
    
    print(f"📊 Total des enregistrements: {len(data)}")
    print(f"📋 Total des colonnes: {len(data.columns)}")
    
    # Recherche de "resah" (insensible à la casse)
    print("\n🔍 Recherche de 'resah'...")
    found_resah = False
    
    for col in data.columns:
        try:
            # Recherche insensible à la casse
            matches = data[col].astype(str).str.contains('resah', case=False, na=False)
            if matches.any():
                count = matches.sum()
                print(f"✅ Colonne '{col}': {count} résultats")
                # Afficher un exemple
                example = data[col][matches].iloc[0]
                print(f"   Exemple: {example}")
                found_resah = True
        except Exception as e:
            print(f"❌ Erreur dans colonne '{col}': {e}")
    
    if not found_resah:
        print("❌ Aucun 'resah' trouvé dans les données")
        
        # Chercher des variations
        print("\n🔍 Recherche de variations...")
        variations = ['RESAH', 'Resah', 'resah', 'Résah', 'résah']
        for variation in variations:
            found = False
            for col in data.columns:
                try:
                    matches = data[col].astype(str).str.contains(variation, case=False, na=False)
                    if matches.any():
                        print(f"✅ Trouvé '{variation}' dans '{col}': {matches.sum()} résultats")
                        found = True
                        break
                except:
                    pass
            if not found:
                print(f"❌ '{variation}' non trouvé")
    
    # Analyser les colonnes de texte principales
    print("\n📋 Analyse des colonnes de texte principales...")
    text_columns = ['mots_cles', 'univers', 'groupement', 'intitule_procedure', 'intitule_lot', 'infos_complementaires']
    
    for col in text_columns:
        if col in data.columns:
            non_null = data[col].notna().sum()
            print(f"📝 {col}: {non_null} valeurs non nulles sur {len(data)}")
            if non_null > 0:
                # Afficher quelques exemples
                examples = data[col].dropna().head(3).tolist()
                print(f"   Exemples: {examples}")
    
    # Analyser les performances potentielles
    print("\n⚡ Analyse des performances...")
    print(f"📊 Taille des données: {data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    # Vérifier les index
    print("\n🗂️ Vérification des index...")
    cursor = db.connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    indexes = cursor.fetchall()
    print(f"📋 Index disponibles: {[idx[0] for idx in indexes]}")
    
    db.close()

if __name__ == "__main__":
    analyze_data()
