"""
🧪 Test Complet - Reproduction du comportement de l'Application
==============================================================

Ce test reproduit exactement le comportement de l'application Streamlit
avec database_manager et apprentissage depuis la BDD.
"""

import sys
import logging
from pathlib import Path
from io import BytesIO

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import des modules
try:
    from database_manager import DatabaseManager
    from ao_extractor_v2 import AOExtractorV2
except ImportError as e:
    logger.error(f"❌ Impossible d'importer les modules: {e}")
    sys.exit(1)

def test_extraction_comme_app(pdf_path: str):
    """
    Teste l'extraction exactement comme dans l'application Streamlit
    """
    logger.info("=" * 80)
    logger.info("🧪 TEST COMPLET - Reproduction Application")
    logger.info("=" * 80)
    
    # 1. Initialiser DatabaseManager (comme dans app.py)
    logger.info("\n📊 Étape 1: Initialisation DatabaseManager...")
    try:
        db_manager = DatabaseManager()
        logger.info("✅ DatabaseManager initialisé")
    except Exception as e:
        logger.error(f"❌ Erreur DatabaseManager: {e}")
        return None
    
    # 2. Charger les données depuis la BDD (comme dans app.py ligne 133)
    logger.info("\n📊 Étape 2: Chargement des données depuis la BDD...")
    try:
        data = db_manager.get_all_data()
        logger.info(f"✅ {len(data)} enregistrements chargés depuis la BDD")
        
        if data.empty:
            logger.warning("⚠️ Aucune donnée dans la BDD - l'apprentissage sera limité")
        else:
            logger.info(f"   Colonnes disponibles: {list(data.columns)[:10]}...")
    except Exception as e:
        logger.error(f"❌ Erreur chargement données: {e}")
        data = None
    
    # 3. Initialiser l'extracteur AVEC les données de référence ET database_manager
    # (comme dans app.py ligne 169)
    logger.info("\n🚀 Étape 3: Initialisation extracteur avec BDD...")
    try:
        ao_extractor = AOExtractorV2(
            reference_data=data if data is not None and not data.empty else None,
            database_manager=db_manager
        )
        logger.info("✅ Extracteur initialisé avec BDD")
    except Exception as e:
        logger.error(f"❌ Erreur initialisation extracteur: {e}")
        return None
    
    # 4. Lire le fichier PDF
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        logger.error(f"❌ Fichier non trouvé: {pdf_path}")
        return None
    
    logger.info(f"\n📄 Fichier: {pdf_file.name}")
    logger.info(f"📁 Chemin: {pdf_file.absolute()}")
    
    # 5. Créer un objet fichier simulé (comme Streamlit)
    logger.info("\n📖 Lecture du fichier PDF...")
    with open(pdf_file, 'rb') as f:
        file_content = BytesIO(f.read())
    
    class MockFile:
        def __init__(self, name, content):
            self.name = name
            self.type = 'application/pdf'
            self.size = len(content.getvalue())
            self.read = lambda: content.getvalue()
            self.seek = content.seek
            self.tell = content.tell
    
    mock_file = MockFile(pdf_file.name, file_content)
    
    # 6. Préparer file_analysis (comme dans app.py ligne 920-926)
    file_analysis = {
        'nom': pdf_file.name,
        'type': 'application/pdf',
        'taille': mock_file.size,
        'contenu_extraite': {'type': 'pdf'},
        'erreur': None
    }
    
    # 7. Obtenir les colonnes cibles (comme dans app.py ligne 927)
    target_columns = None
    if data is not None and not data.empty:
        target_columns = data.columns.tolist()
        logger.info(f"📋 Colonnes cibles: {len(target_columns)} colonnes")
    
    # 8. Extraire (comme dans app.py ligne 927)
    logger.info("\n🔍 EXTRACTION EN COURS (comme dans l'application)...")
    logger.info("-" * 80)
    
    try:
        extracted_entries = ao_extractor.extract_from_file(
            mock_file,
            file_analysis=file_analysis,
            target_columns=target_columns
        )
        
        if not extracted_entries:
            logger.error("❌ Aucune donnée extraite")
            return None
        
        logger.info(f"✅ Extraction réussie: {len(extracted_entries)} entrée(s)")
        logger.info("-" * 80)
        
        # 9. Afficher les résultats (comme dans l'application)
        for idx, entry in enumerate(extracted_entries, 1):
            logger.info(f"\n📊 ENTRÉE {idx}/{len(extracted_entries)}")
            logger.info("=" * 80)
            
            valeurs_extraites = entry.get('valeurs_extraites', {})
            valeurs_generees = entry.get('valeurs_generees', {})
            
            # Afficher les valeurs extraites
            logger.info("\n✅ VALEURS EXTRAITES:")
            logger.info("-" * 80)
            for key, value in sorted(valeurs_extraites.items()):
                if value:
                    logger.info(f"   {key}: {value}")
            
            # Afficher les valeurs générées
            if valeurs_generees:
                logger.info("\n🤖 VALEURS GÉNÉRÉES:")
                logger.info("-" * 80)
                for key, value in sorted(valeurs_generees.items()):
                    if value:
                        logger.info(f"   {key}: {value}")
            
            # Tests spécifiques
            logger.info("\n🎯 TESTS DES AMÉLIORATIONS:")
            logger.info("-" * 80)
            
            # Test 1: Intitulé
            intitule = valeurs_extraites.get('intitule_procedure', 'NON TROUVÉ')
            logger.info(f"\n1. INTITULÉ:")
            if intitule and intitule != 'NON TROUVÉ':
                logger.info(f"   ✅ {intitule[:80]}...")
                logger.info(f"   Longueur: {len(intitule)} caractères")
            else:
                logger.error("   ❌ NON TROUVÉ")
            
            # Test 2: Univers
            univers = valeurs_extraites.get('univers') or valeurs_generees.get('univers', 'NON TROUVÉ')
            logger.info(f"\n2. UNIVERS:")
            if univers and univers != 'NON TROUVÉ':
                logger.info(f"   ✅ {univers}")
            else:
                logger.error("   ❌ NON GÉNÉRÉ")
            
            # Test 3: Segment
            segment = valeurs_extraites.get('segment') or valeurs_generees.get('segment', 'NON TROUVÉ')
            logger.info(f"\n3. SEGMENT:")
            if segment and segment != 'NON TROUVÉ':
                logger.info(f"   ✅ {segment}")
                logger.info(f"   Source: {'extrait' if 'segment' in valeurs_extraites else 'généré'}")
            else:
                logger.warning("   ⚠️ NON GÉNÉRÉ")
            
            # Test 4: Famille
            famille = valeurs_extraites.get('famille') or valeurs_generees.get('famille', 'NON TROUVÉ')
            logger.info(f"\n4. FAMILLE:")
            if famille and famille != 'NON TROUVÉ':
                logger.info(f"   ✅ {famille}")
                logger.info(f"   Source: {'extrait' if 'famille' in valeurs_extraites else 'généré'}")
            else:
                logger.warning("   ⚠️ NON GÉNÉRÉE")
            
            # Compteur
            total_extraites = len([v for v in valeurs_extraites.values() if v])
            total_generees = len([v for v in valeurs_generees.values() if v])
            logger.info(f"\n📊 STATISTIQUES:")
            logger.info(f"   Valeurs extraites: {total_extraites}")
            logger.info(f"   Valeurs générées: {total_generees}")
            logger.info(f"   Total: {total_extraites + total_generees}")
        
        return extracted_entries
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'extraction: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    pdf_path = "rapports/2024-R001-000-000_RC.pdf"
    
    logger.info("\n" + "=" * 80)
    logger.info("🧪 TEST COMPLET - Reproduction Application")
    logger.info("=" * 80)
    
    result = test_extraction_comme_app(pdf_path)
    
    logger.info("\n" + "=" * 80)
    if result:
        logger.info("✅ TEST TERMINÉ - Vérifiez les résultats ci-dessus")
        logger.info("📝 Comparez avec ce que vous voyez dans l'application Streamlit")
    else:
        logger.info("❌ TEST ÉCHOUÉ")
    logger.info("=" * 80)

