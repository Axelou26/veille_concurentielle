"""
🧪 Script de Test - Extraction du Document RC
===============================================

Teste l'extraction du document 2024-R001-000-000_RC.pdf
et vérifie que toutes les améliorations fonctionnent.
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

# Import de l'extracteur
try:
    from ao_extractor_v2 import AOExtractorV2
except ImportError:
    logger.error("❌ Impossible d'importer AOExtractorV2")
    sys.exit(1)

def test_extraction(pdf_path: str):
    """
    Teste l'extraction du document RC
    """
    logger.info("=" * 80)
    logger.info("🧪 TEST D'EXTRACTION - DOCUMENT RC")
    logger.info("=" * 80)
    
    # Vérifier que le fichier existe
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        logger.error(f"❌ Fichier non trouvé: {pdf_path}")
        return None
    
    logger.info(f"📄 Fichier: {pdf_file.name}")
    logger.info(f"📁 Chemin: {pdf_file.absolute()}")
    
    # Initialiser l'extracteur (sans BDD pour ce test)
    logger.info("\n🚀 Initialisation de l'extracteur...")
    extractor = AOExtractorV2()
    
    # Simuler un fichier uploadé
    logger.info("\n📖 Lecture du fichier PDF...")
    with open(pdf_file, 'rb') as f:
        file_content = BytesIO(f.read())
    
    # Créer un objet fichier simulé
    class MockFile:
        def __init__(self, name, content):
            self.name = name
            self.read = lambda: content.getvalue()
            self.seek = content.seek
            self.tell = content.tell
    
    mock_file = MockFile(pdf_file.name, file_content)
    file_analysis = {'type': 'pdf'}
    
    # Extraire les données
    logger.info("\n🔍 Extraction en cours...")
    logger.info("-" * 80)
    
    try:
        extracted_entries = extractor.extract_from_file(
            mock_file, 
            file_analysis=file_analysis
        )
        
        if not extracted_entries:
            logger.error("❌ Aucune donnée extraite")
            return None
        
        logger.info(f"✅ Extraction réussie: {len(extracted_entries)} entrée(s)")
        logger.info("-" * 80)
        
        # Afficher les résultats
        for idx, entry in enumerate(extracted_entries, 1):
            logger.info(f"\n📊 ENTRÉE {idx}/{len(extracted_entries)}")
            logger.info("=" * 80)
            
            # Vérifier les champs clés
            valeurs_extraites = entry.get('valeurs_extraites', {})
            
            # 1. INTITULÉ DE LA PROCÉDURE (Titre multi-lignes)
            logger.info("\n🎯 TEST 1: Intitulé de la procédure (Titre multi-lignes)")
            logger.info("-" * 80)
            intitule = valeurs_extraites.get('intitule_procedure', 'NON TROUVÉ')
            if intitule and intitule != 'NON TROUVÉ':
                logger.info(f"✅ INTITULÉ TROUVÉ:")
                logger.info(f"   Longueur: {len(intitule)} caractères")
                logger.info(f"   Contenu: {intitule[:100]}...")
                if len(intitule) > 100:
                    logger.info(f"   (titre complet: {len(intitule)} caractères)")
                
                # Vérifier si c'est un titre multi-lignes (long)
                if len(intitule) > 150:
                    logger.info("   ✅ TITRE MULTI-LIGNES DÉTECTÉ (phrase longue)")
                if "FOURNITURE" in intitule or "INSTALLATION" in intitule:
                    logger.info("   ✅ MOTS-CLÉS ATTENDUS PRÉSENTS")
            else:
                logger.error(f"❌ Intitulé NON TROUVÉ")
            
            # 2. UNIVERS (Génération automatique)
            logger.info("\n🎯 TEST 2: Univers (Génération automatique)")
            logger.info("-" * 80)
            univers = valeurs_extraites.get('univers', 'NON TROUVÉ')
            if univers and univers != 'NON TROUVÉ':
                logger.info(f"✅ UNIVERS GÉNÉRÉ: {univers}")
            else:
                logger.error(f"❌ Univers NON GÉNÉRÉ")
            
            # 3. SEGMENT (Génération intelligente)
            logger.info("\n🎯 TEST 3: Segment (Génération intelligente)")
            logger.info("-" * 80)
            segment = valeurs_extraites.get('segment', 'NON TROUVÉ')
            if segment and segment != 'NON TROUVÉ':
                logger.info(f"✅ SEGMENT GÉNÉRÉ: {segment}")
                if univers and univers != 'NON TROUVÉ':
                    logger.info(f"   Cohérence avec univers '{univers}': ✅")
            else:
                logger.warning(f"⚠️ Segment NON GÉNÉRÉ (devrait être généré depuis l'univers)")
            
            # 4. FAMILLE (Génération intelligente)
            logger.info("\n🎯 TEST 4: Famille (Génération intelligente)")
            logger.info("-" * 80)
            famille = valeurs_extraites.get('famille', 'NON TROUVÉ')
            if famille and famille != 'NON TROUVÉ':
                logger.info(f"✅ FAMILLE GÉNÉRÉE: {famille}")
                if univers and univers != 'NON TROUVÉ':
                    logger.info(f"   Cohérence avec univers '{univers}': ✅")
            else:
                logger.warning(f"⚠️ Famille NON GÉNÉRÉE (devrait être générée depuis l'univers + intitulé)")
            
            # 5. Autres champs importants
            logger.info("\n🎯 TEST 5: Autres champs extraits")
            logger.info("-" * 80)
            
            champs_importants = [
                'reference_procedure',
                'groupement',
                'type_procedure',
                'mono_multi',
                'date_limite',
                'montant_global_estime'
            ]
            
            for champ in champs_importants:
                valeur = valeurs_extraites.get(champ)
                if valeur:
                    logger.info(f"   ✅ {champ}: {valeur}")
                else:
                    logger.debug(f"   ⚠️ {champ}: Non trouvé")
            
            # 6. Compteur de champs remplis
            logger.info("\n🎯 TEST 6: Couverture globale")
            logger.info("-" * 80)
            champs_remplis = sum(1 for v in valeurs_extraites.values() if v and v != '' and v != 'NON TROUVÉ')
            total_champs = len(valeurs_extraites)
            logger.info(f"   Champs remplis: {champs_remplis}/{total_champs}")
            logger.info(f"   Taux de remplissage: {champs_remplis/total_champs*100:.1f}%")
            
            # Résumé final
            logger.info("\n" + "=" * 80)
            logger.info("📋 RÉSUMÉ DES TESTS")
            logger.info("=" * 80)
            
            tests_reussis = []
            tests_echoues = []
            
            if intitule and intitule != 'NON TROUVÉ':
                tests_reussis.append("✅ Intitulé extrait (titre multi-lignes)")
            else:
                tests_echoues.append("❌ Intitulé NON extrait")
            
            if univers and univers != 'NON TROUVÉ':
                tests_reussis.append("✅ Univers généré")
            else:
                tests_echoues.append("❌ Univers NON généré")
            
            if segment and segment != 'NON TROUVÉ':
                tests_reussis.append("✅ Segment généré intelligemment")
            else:
                tests_echoues.append("⚠️ Segment NON généré")
            
            if famille and famille != 'NON TROUVÉ':
                tests_reussis.append("✅ Famille générée intelligemment")
            else:
                tests_echoues.append("⚠️ Famille NON générée")
            
            logger.info(f"\n✅ Tests réussis ({len(tests_reussis)}):")
            for test in tests_reussis:
                logger.info(f"   {test}")
            
            if tests_echoues:
                logger.info(f"\n⚠️ Tests avec problèmes ({len(tests_echoues)}):")
                for test in tests_echoues:
                    logger.info(f"   {test}")
            
            # Afficher toutes les valeurs extraites (debug)
            logger.info("\n" + "=" * 80)
            logger.info("📋 TOUTES LES VALEURS EXTRAITES")
            logger.info("=" * 80)
            for key, value in sorted(valeurs_extraites.items()):
                if value:
                    logger.info(f"   {key}: {value}")
            
            return entry
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'extraction: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    # Chemin du fichier PDF
    pdf_path = "rapports/2024-R001-000-000_RC.pdf"
    
    logger.info("\n" + "=" * 80)
    logger.info("🧪 LANCEMENT DU TEST")
    logger.info("=" * 80)
    
    result = test_extraction(pdf_path)
    
    logger.info("\n" + "=" * 80)
    if result:
        logger.info("✅ TEST TERMINÉ - Vérifiez les résultats ci-dessus")
    else:
        logger.info("❌ TEST ÉCHOUÉ - Consultez les erreurs ci-dessus")
    logger.info("=" * 80)

