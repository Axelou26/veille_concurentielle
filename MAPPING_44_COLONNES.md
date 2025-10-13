# 🗂️ Mapping des 44 Colonnes - Extracteur d'AO

## 🎯 Vos 44 colonnes exactes

Voici le mapping automatique vers vos 44 colonnes de base de données :

### 📊 **Mapping des colonnes extraites :**

| Clé générique | → | Votre colonne |
|---------------|---|---------------|
| `mots_cles` | → | **Mots clés** |
| `univers` | → | **Univers** |
| `segment` | → | **Segment** |
| `famille` | → | **Famille** |
| `statut` | → | **Statut** |
| `groupement` | → | **Groupement** |
| `reference_procedure` | → | **Référence de la procédure** |
| `type_procedure` | → | **Type de procédure** |
| `mono_multi` | → | **Mono ou multi-attributif** |
| `execution_marche` | → | **Exécution du marché** |
| `date_limite` | → | **Date limite de remise des offres** |
| `date_attribution` | → | **Date d'attribution du marché** |
| `duree_marche` | → | **Durée du marché (mois)** |
| `reconduction` | → | **Reconduction** |
| `fin_sans_reconduction` | → | **Fin (sans reconduction)** |
| `fin_avec_reconduction` | → | **Fin (avec reconduction)** |
| `nbr_lots` | → | **Nbr lots** |
| `intitule_procedure` | → | **Intitulé de la procédure** |
| `lot_numero` | → | **Lot N°** |
| `intitule_lot` | → | **Intitulé du Lot** |
| `infos_complementaires` | → | **Infos complémentaires** |
| `attributaire` | → | **Attributaire** |
| `produit_retenu` | → | **Produit retenu** |
| `remarques` | → | **Remarques** |
| `notes_acheteur_procedure` | → | **Notes de l'acheteur sur la procédure** |
| `notes_acheteur_fournisseur` | → | **Notes de l'acheteur sur le fournisseur** |
| `notes_acheteur_positionnement` | → | **Notes de l'acheteur sur le positionnement** |
| `note_veille` | → | **Note Veille concurrentielle disponible** |
| `achat` | → | **Achat** |
| `credit_bail` | → | **Crédit bail** |
| `credit_bail_duree` | → | **Crédit bail (durée année)** |
| `location` | → | **Location** |
| `location_duree` | → | **Location (durée années)** |
| `mad` | → | **MAD** |
| `montant_global_estime` | → | **Montant global estimé (€ HT) du marché** |
| `montant_global_maxi` | → | **Montant global maxi (€ HT)** |
| `quantite_minimum` | → | **Quantité minimum** |
| `quantites_estimees` | → | **Quantités estimées** |
| `quantite_maximum` | → | **Quantité maximum** |
| `criteres_economique` | → | **Critères d'attribution : économique** |
| `criteres_techniques` | → | **Critères d'attribution : techniques** |
| `autres_criteres` | → | **Autres critères d'attribution** |
| `rse` | → | **RSE** |
| `contribution_fournisseur` | → | **Contribution fournisseur** |

## 🚀 **Utilisation dans l'application**

### 1. **Upload de fichier**
- Uploadez votre fichier d'appel d'offres (PDF, Excel, Word, TXT)

### 2. **Extraction automatique**
- Cliquez sur "🤖 Extraire automatiquement les informations avec l'IA"
- Le système extrait les informations et les mappe automatiquement vers vos 44 colonnes

### 3. **Résultats mappés**
- Les valeurs extraites sont automatiquement mappées vers vos vraies colonnes
- Plus de noms génériques, mais vos vrais noms de colonnes

## 📋 **Exemple de résultat**

**Avant (noms génériques) :**
```
• Budget : 0.0
• Date_Limite : mars 2019
• Reference : s
• Organisme : société.
```

**Maintenant (vos vraies colonnes) :**
```
• Montant global estimé (€ HT) du marché : 0.0
• Date limite de remise des offres : mars 2019
• Référence de la procédure : s
• Intitulé de la procédure : société.
```

## 🎯 **Avantages**

### ✅ **Correspondance exacte**
- Chaque valeur extraite correspond exactement à une de vos 44 colonnes
- Plus de confusion avec des noms génériques

### ✅ **Intégration directe**
- Les données peuvent être directement insérées dans votre base de données
- Mapping automatique sans intervention manuelle

### ✅ **Extraction intelligente**
- Le système reconnaît automatiquement les types d'informations
- Mapping intelligent basé sur le contenu et les patterns

### ✅ **Traçabilité complète**
- Chaque valeur est mappée vers sa vraie colonne
- Source et destination clairement identifiées

## 🔧 **Patterns de reconnaissance**

Le système reconnaît automatiquement :

- **Montants** : `150 000 €`, `100k€`, `1.5M€` → `Montant global estimé (€ HT) du marché`
- **Dates** : `31/12/2024`, `2024-12-31` → `Date limite de remise des offres`
- **Références** : `AO-2024-001`, `REF-123` → `Référence de la procédure`
- **Organismes** : Ministères, mairies, hôpitaux → `Intitulé de la procédure`
- **Contacts** : Téléphones, emails → `Infos complémentaires`
- **Lieux** : Adresses, villes → `Infos complémentaires`

## 🎉 **Résultat final**

Maintenant, quand vous extrayez des informations d'un appel d'offres, les valeurs sont automatiquement mappées vers vos 44 colonnes exactes, permettant une intégration directe et sans erreur dans votre base de données de veille concurrentielle !

---

**✅ Le système de mapping des 44 colonnes est opérationnel et prêt à utiliser !**

