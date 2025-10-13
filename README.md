# 🚀 IA Veille Concurrentielle - Analyse d'Appels d'Offres

## 📋 Description

Système d'**Intelligence Artificielle ultra performant** conçu pour analyser votre base de données de veille concurrentielle et extraire les informations pertinentes selon les lots d'appels d'offres. Chaque ligne représente un lot d'appel d'offres avec des données structurées.

## ✨ Fonctionnalités Principales

### 🔍 **Recherche IA Avancée**
- **Recherche sémantique** dans vos données avec embeddings vectoriels
- **Questions-réponses naturelles** en français
- **Analyse contextuelle** des lots d'appels d'offres

### 📊 **Analyse des Données**
- **Vue d'ensemble** complète de votre base de données
- **Statistiques détaillées** par colonne et type de données
- **Visualisations interactives** avec Plotly
- **Export des données** filtrées

### 🧠 **Intelligence Artificielle**
- **Moteur d'IA** basé sur LangChain et OpenAI
- **Embeddings vectoriels** pour la recherche sémantique
- **Analyse automatique** des lots avec insights stratégiques
- **Recommandations** basées sur vos données

### 💡 **Insights Automatiques**
- **Analyse générale** de votre veille concurrentielle
- **Insights personnalisés** selon vos besoins
- **Détection d'opportunités** et de risques
- **Recommandations stratégiques** pour chaque lot

## 🛠️ Technologies Utilisées

- **Python 3.8+** - Langage principal
- **Streamlit** - Interface utilisateur moderne et intuitive
- **LangChain** - Framework d'IA et traitement du langage naturel
- **OpenAI GPT-4** - Modèle de langage avancé
- **Sentence Transformers** - Embeddings vectoriels
- **FAISS** - Recherche vectorielle ultra-rapide
- **Pandas** - Manipulation et analyse des données
- **Plotly** - Visualisations interactives
- **OpenPyXL** - Lecture des fichiers Excel

## 🚀 Installation et Configuration

### 1. **Prérequis**
```bash
# Python 3.8 ou supérieur
python --version

# Git pour cloner le projet
git --version
```

### 2. **Installation des dépendances**
```bash
# Installation des packages Python
pip install -r requirements.txt
```

### 3. **Configuration OpenAI (Optionnel mais recommandé)**
```bash
# Créer un fichier .env
echo "OPENAI_API_KEY=votre_cle_api_ici" > .env
```

**Note :** Sans clé OpenAI, l'application fonctionne en mode local avec les embeddings et la recherche sémantique, mais sans l'IA conversationnelle avancée.

### 4. **Lancement de l'application**
```bash
# Démarrer l'application Streamlit
streamlit run app.py
```

L'application sera accessible à l'adresse : `http://localhost:8501`

## 📁 Structure du Projet

```
IA-veille-concurrentielle/
├── app.py                 # Application principale Streamlit
├── ai_engine.py          # Moteur d'IA ultra performant
├── data_processor.py     # Traitement des données Excel
├── config.py             # Configuration de l'application
├── requirements.txt      # Dépendances Python
├── README.md            # Documentation
└── Veille concurrentielle BDD (1).xlsx  # Votre base de données
```

## 🔧 Utilisation

### **1. Chargement des Données**
- L'application charge automatiquement votre fichier Excel
- **Nettoyage automatique** des données (suppression des lignes vides, nettoyage des colonnes)
- **Détection automatique** de la structure des données

### **2. Vue d'Ensemble**
- **Métriques clés** : nombre total de lots, colonnes disponibles
- **Aperçu des données** : premières lignes de votre base
- **Structure des données** : types, valeurs uniques, valeurs manquantes

### **3. Recherche IA**
- **Initialisation** du moteur d'IA (une seule fois)
- **Recherche sémantique** : trouvez des lots similaires selon vos critères
- **Questions-réponses** : posez des questions naturelles en français

### **4. Analyse des Lots**
- **Sélection** d'un lot spécifique dans votre base
- **Affichage détaillé** de toutes les informations du lot
- **Analyse IA** : points clés, opportunités, risques, recommandations

### **5. Statistiques et Visualisations**
- **Graphiques interactifs** pour les colonnes numériques
- **Analyse des distributions** et valeurs aberrantes
- **Top des valeurs** pour les colonnes textuelles

### **6. Insights IA**
- **Génération automatique** d'insights sur vos données
- **Analyse personnalisée** selon vos besoins spécifiques
- **Recommandations stratégiques** basées sur l'analyse des données

## 🔑 Configuration OpenAI

Pour activer toutes les fonctionnalités d'IA :

1. **Obtenez une clé API** sur [OpenAI Platform](https://platform.openai.com/)
2. **Configurez la clé** dans l'interface de l'application
3. **Profitez** de l'IA conversationnelle avancée !

## 📊 Format des Données

Votre fichier Excel doit contenir :
- **Une ligne par lot** d'appel d'offres
- **Des colonnes structurées** (ID, nom, description, montant, etc.)
- **Données cohérentes** pour une analyse optimale

## 🚨 Dépannage

### **Erreur de chargement des données**
- Vérifiez que le fichier Excel est accessible
- Assurez-vous que le format est correct (.xlsx)
- Vérifiez les permissions du fichier

### **Erreur d'initialisation de l'IA**
- Vérifiez votre clé API OpenAI
- Assurez-vous d'avoir une connexion internet
- Vérifiez les quotas de votre compte OpenAI

### **Performance lente**
- L'initialisation de l'IA prend du temps (première fois)
- Les recherches suivantes sont ultra-rapides
- Utilisez des filtres pour réduire le volume de données

## 🔮 Fonctionnalités Futures

- **Export PDF** des analyses
- **Notifications** automatiques sur nouveaux appels d'offres
- **API REST** pour intégration avec d'autres systèmes
- **Machine Learning** pour prédiction des tendances
- **Interface mobile** responsive

## 📞 Support

Pour toute question ou problème :
- **Vérifiez** la documentation ci-dessus
- **Consultez** les logs de l'application
- **Contactez** l'équipe de développement

## 📄 Licence

Ce projet est développé pour un usage interne et professionnel.

---

**🚀 Prêt à révolutionner votre veille concurrentielle avec l'IA ? Lancez l'application et découvrez la puissance de l'analyse intelligente !**
