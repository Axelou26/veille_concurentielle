#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Test d'extraction complète des 44 colonnes
============================================

Test du système d'extraction intelligent pour toutes les 44 colonnes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extraction_improver import extraction_improver
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_extraction_complete_44_colonnes():
    """Test complet de l'extraction des 44 colonnes"""
    
    # Document d'exemple complet
    sample_document = """
    APPEL D'OFFRES PUBLIC
    ====================
    
    Groupement: RESAH
    Référence de la procédure: 2024-R075
    Type de procédure: Appel d'offres ouvert
    Intitulé de la procédure: Fourniture d'équipements médicaux pour les hôpitaux du réseau RESAH
    
    OBJET DU MARCHÉ
    ===============
    
    Intitulé du lot: Fourniture de congélateurs -80°C pour laboratoires
    Lot N°: 1
    Exécution du marché: Fournitures
    Mono ou multi-attributif: Multi-attributif
    Nombre de lots: 3
    
    MONTANT ET DURÉE
    ================
    
    Montant global estimé: 2 500 000 €
    Montant global maximum: 3 000 000 €
    Date limite de remise des offres: 15/12/2024
    Date d'attribution du marché: 20/12/2024
    Durée du marché: 24 mois
    Reconduction: Oui
    Fin sans reconduction: 15/12/2026
    Fin avec reconduction: 15/12/2027
    
    QUANTITÉS
    =========
    
    Quantité minimum: 5
    Quantités estimées: 10
    Quantité maximum: 15
    
    MODALITÉS
    =========
    
    Achat: Oui
    Crédit bail: Non
    Location: Oui
    Location durée: 2 ans
    Mise à disposition: Non
    
    CRITÈRES D'ÉVALUATION
    =====================
    
    Critères économiques: Prix (70%), Qualité (30%)
    Critères techniques: Conformité aux normes CE, Performance énergétique
    Autres critères: RSE, Innovation
    RSE: Oui
    Contribution fournisseur: Oui
    
    RÉSULTATS
    =========
    
    Attributaire: Laboratoires ABC
    Produit retenu: Congélateur UltraCool -80°C
    
    INFORMATIONS COMPLÉMENTAIRES
    =============================
    
    Installation incluse, Formation du personnel, Garantie 3 ans
    Remarques: Marché prioritaire pour la recherche médicale
    Notes de l'acheteur sur la procédure: Procédure complexe multi-lots
    Notes de l'acheteur sur le fournisseur: Fournisseur expérimenté
    Notes de l'acheteur sur le positionnement: Bon positionnement prix/qualité
    Note Veille concurrentielle disponible: Analyse complète réalisée
    """
    
    print("🧪 **Test d'extraction complète des 44 colonnes**\n")
    
    print("📄 **Document d'exemple:**")
    print(sample_document)
    print("\n" + "="*80 + "\n")
    
    # Extraction intelligente
    print("🔧 **Extraction intelligente en cours...**")
    extracted_data = extraction_improver.extract_improved_data(sample_document)
    
    print(f"\n✅ **Résultats de l'extraction:**")
    print(f"📊 **Total de champs extraits:** {len(extracted_data)}")
    
    # Afficher les résultats par catégorie
    categories = {
        'Identité': ['mots_cles', 'univers', 'segment', 'famille', 'statut', 'groupement'],
        'Procédure': ['reference_procedure', 'type_procedure', 'mono_multi', 'execution_marche', 'nbr_lots', 'intitule_procedure', 'lot_numero', 'intitule_lot'],
        'Temporel': ['date_limite', 'date_attribution', 'duree_marche', 'reconduction', 'fin_sans_reconduction', 'fin_avec_reconduction'],
        'Financier': ['montant_global_estime', 'montant_global_maxi', 'achat', 'credit_bail', 'credit_bail_duree', 'location', 'location_duree', 'mad'],
        'Quantités': ['quantite_minimum', 'quantites_estimees', 'quantite_maximum'],
        'Critères': ['criteres_economique', 'criteres_techniques', 'autres_criteres', 'rse', 'contribution_fournisseur'],
        'Résultats': ['attributaire', 'produit_retenu'],
        'Notes': ['infos_complementaires', 'remarques', 'notes_acheteur_procedure', 'notes_acheteur_fournisseur', 'notes_acheteur_positionnement', 'note_veille']
    }
    
    for category, fields in categories.items():
        print(f"\n📋 **{category}:**")
        category_data = {field: extracted_data.get(field, 'Non trouvé') for field in fields}
        for field, value in category_data.items():
            status = "✅" if value != 'Non trouvé' else "❌"
            print(f"  {status} {field}: {value}")
    
    # Statistiques détaillées
    print(f"\n📈 **Statistiques détaillées:**")
    
    total_fields = 44
    extracted_fields = len(extracted_data)
    missing_fields = total_fields - extracted_fields
    
    print(f"- Champs extraits: {extracted_fields}/{total_fields} ({extracted_fields/total_fields*100:.1f}%)")
    print(f"- Champs manquants: {missing_fields}")
    
    # Analyse par type de données
    data_types = {
        'Texte': 0,
        'Numérique': 0,
        'Date': 0,
        'Booléen': 0
    }
    
    for field, value in extracted_data.items():
        if isinstance(value, str):
            if value in ['Oui', 'Non']:
                data_types['Booléen'] += 1
            elif '/' in value and len(value.split('/')) == 3:  # Date
                data_types['Date'] += 1
            else:
                data_types['Texte'] += 1
        elif isinstance(value, (int, float)):
            data_types['Numérique'] += 1
    
    print(f"\n📊 **Répartition par type de données:**")
    for data_type, count in data_types.items():
        print(f"- {data_type}: {count} champs")
    
    # Test de validation
    print(f"\n🔍 **Test de validation:**")
    
    validation_tests = [
        ('univers', 'Médical', 'Univers correctement détecté'),
        ('groupement', 'RESAH', 'Groupement correctement identifié'),
        ('montant_global_estime', 2500000.0, 'Montant correctement extrait'),
        ('date_limite', '15/12/2024', 'Date limite correctement extraite'),
        ('nbr_lots', 3, 'Nombre de lots correctement extrait'),
        ('reconduction', 'Oui', 'Reconduction correctement détectée'),
        ('rse', 'Oui', 'RSE correctement détectée')
    ]
    
    for field, expected, description in validation_tests:
        actual = extracted_data.get(field)
        if actual == expected:
            print(f"✅ {description}: {actual}")
        else:
            print(f"❌ {description}: Attendu {expected}, Obtenu {actual}")
    
    # Test de déduction intelligente
    print(f"\n🧠 **Test de déduction intelligente:**")
    
    deduction_tests = [
        ('segment', 'Santé', 'Segment déduit de l\'univers Médical'),
        ('famille', 'Fourniture', 'Famille déduite de l\'intitulé du lot'),
        ('mono_multi', 'Multi-attributif', 'Mono/Multi déduit du nombre de lots'),
        ('execution_marche', 'Fournitures', 'Exécution déduite du contexte')
    ]
    
    for field, expected, description in deduction_tests:
        actual = extracted_data.get(field)
        if actual == expected:
            print(f"✅ {description}: {actual}")
        else:
            print(f"❌ {description}: Attendu {expected}, Obtenu {actual}")
    
    # Test de génération intelligente
    print(f"\n🎯 **Test de génération intelligente:**")
    
    generation_tests = [
        ('mots_cles', 'équipements, médicaux, hôpitaux, réseau, fourniture', 'Mots-clés générés automatiquement'),
        ('infos_complementaires', 'Informations financières disponibles; Dates et durées spécifiées; Critères techniques détaillés; Marché complexe multi-lots', 'Informations complémentaires générées')
    ]
    
    for field, expected_pattern, description in generation_tests:
        actual = extracted_data.get(field)
        if actual and expected_pattern.lower() in actual.lower():
            print(f"✅ {description}: {actual}")
        else:
            print(f"❌ {description}: Attendu contenant '{expected_pattern}', Obtenu '{actual}'")
    
    print(f"\n🎉 **Test terminé !**")
    print(f"📊 **Performance globale:** {extracted_fields/total_fields*100:.1f}% des 44 colonnes extraites")
    
    return extracted_data

if __name__ == "__main__":
    test_extraction_complete_44_colonnes()

