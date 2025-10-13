"""
Configuration centralisée pour l'application de veille concurrentielle
Contient toutes les définitions de colonnes et mappings
"""

# Configuration des 44 colonnes standard
COLUMNS_CONFIG = {
    'french_names': [
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
    ],
    'technical_names': [
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
}

# Mapping des champs de lot
LOT_FIELDS_MAPPING = {
    'numero': 'lot_numero',
    'intitule': 'intitule_lot',
    'attributaire': 'attributaire',
    'produit_retenu': 'produit_retenu',
    'infos_complementaires': 'infos_complementaires',
    'montant_estime': 'montant_global_estime',
    'montant_maximum': 'montant_global_maxi',
    'quantite_minimum': 'quantite_minimum',
    'quantites_estimees': 'quantites_estimees',
    'quantite_maximum': 'quantite_maximum',
    'criteres_economique': 'criteres_economique',
    'criteres_techniques': 'criteres_techniques',
    'autres_criteres': 'autres_criteres',
    'rse': 'rse',
    'contribution_fournisseur': 'contribution_fournisseur'
}

# Options pour les selectbox
SELECTBOX_OPTIONS = {
    'univers': ['MÉDICAL', 'TECHNIQUE', 'GÉNÉRAL', 'INFORMATIQUE', 'LOGISTIQUE', 'MAINTENANCE', 'AUTRE'],
    'statut': ['AO EN COURS', 'AO ATTRIBUÉ', 'AO ANNULÉ', 'AO REPORTÉ', 'AO SUSPENDU', 'AO CLÔTURÉ'],
    'groupement': ['RESAH', 'UNIHA', 'UGAP', 'CAIH', 'AUTRE'],
    'type_procedure': ['Appel d\'offres ouvert', 'Appel d\'offres restreint', 'Procédure adaptée', 'Marché de gré à gré', 'Accord-cadre'],
    'mono_multi': ['Mono-attributif', 'Multi-attributif'],
    'reconduction': ['Oui', 'Non', 'Non spécifié'],
    'achat': ['Oui', 'Non', 'Non spécifié'],
    'credit_bail': ['Oui', 'Non', 'Non spécifié'],
    'location': ['Oui', 'Non', 'Non spécifié'],
    'mad': ['Oui', 'Non', 'Non spécifié']
}

# Configuration des onglets
TAB_CONFIG = {
    'main_tabs': [
        "📊 Vue d'ensemble", 
        "🤖 IA", 
        "📈 Statistiques",
        "📥 Insertion AO",
        "🗄️ Base de données"
    ],
    'edit_tabs': [
        "📋 Général", "📅 Dates", "📝 Autres"
    ]
}

# Messages d'interface
UI_MESSAGES = {
    'success': {
        'extraction': "✅ Extraction réussie!",
        'save': "✅ Données sauvegardées dans la base de données avec succès !",
        'insert': "✅ {count} ligne(s) insérée(s) dans la base de données (une ligne par lot)",
        'ai_init': "✅ IA initialisée avec {count} documents!",
        'ai_update': "✅ IA mise à jour avec {count} documents!"
    },
    'warning': {
        'no_data': "⚠️ Aucune donnée trouvée dans la base. Importez d'abord un fichier Excel.",
        'partial_extraction': "⚠️ Extraction partielle - Vérifiez et complétez manuellement",
        'incomplete_columns': "⚠️ **{count} colonnes manquantes** dans votre base de données :",
        'no_lots': "⚠️ Aucune donnée à insérer"
    },
    'error': {
        'init': "❌ Erreur lors de l'initialisation des composants",
        'ai_init': "❌ Erreur initialisation IA: {error}",
        'ai_update': "❌ Erreur mise à jour IA: {error}",
        'save': "❌ Erreur lors de la sauvegarde en base : {error}",
        'insert': "❌ Erreur lors de l'insertion: {error}"
    },
    'info': {
        'lots_detected': "🎯 **{count} lots détectés par l'IA !**",
        'lots_total': "📋 **{count} lots détectés** - Chaque ligne représente un lot",
        'ai_loading': "🧠 Initialisation de l'IA avec toutes les données...",
        'ai_updating': "🔄 Mise à jour de l'IA avec les nouvelles données...",
        'data_loading': "📊 Chargement des données depuis la base...",
        'file_analysis': "🔍 Analyse du fichier...",
        'backup_created': "💾 Sauvegarde automatique créée"
    }
}
