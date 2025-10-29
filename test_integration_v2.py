#!/usr/bin/env python3
"""
Test d'intégration pour la version V2 de l'extracteur d'AO
"""

import sys
import os
import pandas as pd
from io import BytesIO
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_import_v2():
    """Test d'import de la version V2"""
    try:
        from ao_extractor_v2 import AOExtractorV2
        logger.info("✅ Import AOExtractorV2 réussi")
        return True
    except ImportError as e:
        logger.error(f"❌ Erreur import AOExtractorV2: {e}")
        return False

def test_import_modules():
    """Test d'import des modules spécialisés"""
    try:
        from extractors.pattern_manager import PatternManager
        from extractors.lot_detector import LotDetector
        from extractors.validation_engine import ValidationEngine
        from extractors.pdf_extractor import PDFExtractor
        from extractors.excel_extractor import ExcelExtractor
        from extractors.text_extractor import TextExtractor
        logger.info("✅ Import des modules spécialisés réussi")
        return True
    except ImportError as e:
        logger.error(f"❌ Erreur import modules spécialisés: {e}")
        return False

def test_initialization():
    """Test d'initialisation de l'extracteur V2"""
    try:
        from ao_extractor_v2 import AOExtractorV2
        
        # Créer des données de test
        test_data = pd.DataFrame({
            'reference_procedure': ['TEST-001', 'TEST-002'],
            'intitule_procedure': ['Test 1', 'Test 2'],
            'montant_global_estime': [100000, 200000]
        })
        
        # Initialiser l'extracteur V2
        extractor = AOExtractorV2(reference_data=test_data)
        
        # Vérifier les attributs
        assert hasattr(extractor, 'pattern_manager'), "PatternManager manquant"
        assert hasattr(extractor, 'lot_detector'), "LotDetector manquant"
        assert hasattr(extractor, 'validation_engine'), "ValidationEngine manquant"
        assert hasattr(extractor, 'performance_metrics'), "Métriques d'extraction manquantes"
        
        logger.info("✅ Initialisation AOExtractorV2 réussie")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur initialisation: {e}")
        return False

def test_file_type_detection():
    """Test de détection du type de fichier"""
    try:
        from ao_extractor_v2 import AOExtractorV2
        
        extractor = AOExtractorV2()
        
        # Test PDF
        pdf_file = BytesIO(b"PDF content")
        pdf_file.name = "test.pdf"
        file_type = extractor._detect_file_type(pdf_file, {})
        assert file_type == 'pdf_avance', f"Type PDF incorrect: {file_type}"
        
        # Test Excel
        excel_file = BytesIO(b"Excel content")
        excel_file.name = "test.xlsx"
        file_type = extractor._detect_file_type(excel_file, {})
        assert file_type == 'excel', f"Type Excel incorrect: {file_type}"
        
        logger.info("✅ Détection de type de fichier réussie")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur détection type fichier: {e}")
        return False

def test_lot_detection():
    """Test de détection des lots"""
    try:
        from ao_extractor_v2 import AOExtractorV2
        
        extractor = AOExtractorV2()
        
        # Texte de test avec lots (format structuré)
        test_text = """
        1 MAINTENANCE INFORMATIQUE 50000 60000
        2 FORMATION 30000 40000
        3 CONSULTING 20000 25000
        """
        
        lots = extractor.detect_lots(test_text)
        
        logger.info(f"Lots détectés: {len(lots)}")
        for i, lot in enumerate(lots):
            logger.info(f"Lot {i+1}: {lot}")
        
        assert len(lots) >= 3, f"Nombre de lots détectés insuffisant: {len(lots)}"
        
        # Vérifier la structure des lots
        for lot in lots:
            # Les lots peuvent être des objets LotInfo ou des dictionnaires
            if hasattr(lot, 'numero'):
                # Objet LotInfo
                assert lot.numero > 0, f"Numéro de lot invalide: {lot.numero}"
                assert lot.intitule.strip(), f"Intitulé de lot vide: {lot.intitule}"
            elif isinstance(lot, dict):
                # Dictionnaire
                assert 'numero' in lot, f"Numéro de lot manquant dans: {lot}"
                assert 'intitule' in lot, f"Intitulé de lot manquant dans: {lot}"
                assert lot['numero'] > 0, f"Numéro de lot invalide: {lot['numero']}"
                assert lot['intitule'].strip(), f"Intitulé de lot vide: {lot['intitule']}"
            else:
                raise AssertionError(f"Format de lot non reconnu: {type(lot)}")
        
        logger.info(f"✅ Détection de {len(lots)} lots réussie")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur détection lots: {e}")
        return False

def test_validation():
    """Test du système de validation"""
    try:
        from ao_extractor_v2 import AOExtractorV2
        
        extractor = AOExtractorV2()
        
        # Données de test
        test_data = {
            'reference_procedure': 'TEST-001',
            'intitule_procedure': 'Test de validation',
            'montant_global_estime': 100000,
            'date_limite': '2024-12-31'
        }
        
        # Validation
        validation_result = extractor.validate_extraction(test_data)
        
        assert hasattr(validation_result, 'is_valid'), "Validité manquante"
        assert hasattr(validation_result, 'confidence'), "Confiance manquante"
        assert hasattr(validation_result, 'errors'), "Erreurs manquantes"
        assert hasattr(validation_result, 'warnings'), "Avertissements manquants"
        assert hasattr(validation_result, 'suggestions'), "Suggestions manquantes"
        
        logger.info("✅ Système de validation fonctionnel")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur validation: {e}")
        return False

def test_extraction_complete():
    """Test d'extraction complète"""
    try:
        from ao_extractor_v2 import AOExtractorV2
        
        extractor = AOExtractorV2()
        
        # Fichier de test (simulation)
        test_file = BytesIO(b"Test content")
        test_file.name = "test.txt"
        
        file_analysis = {
            'contenu_extraite': {
                'type': 'texte',
                'text_content': """
                RÉFÉRENCE: TEST-001
                INTITULÉ: Test d'extraction complète
                MONTANT: 100 000 €
                DATE LIMITE: 31/12/2024
                
                LOT 1 - MAINTENANCE
                50 000 € - 60 000 €
                
                LOT 2 - FORMATION
                30 000 € - 40 000 €
                """
            }
        }
        
        # Extraction
        results = extractor.extract_from_file(test_file, file_analysis)
        
        assert len(results) > 0, "Aucun résultat d'extraction"
        
        # Vérifier la structure des résultats
        for result in results:
            logger.info(f"Résultat: {result}")
            assert 'validation_report' in result, f"Rapport de validation manquant dans: {result}"
            # La source peut être dans extraction_source ou dans valeurs_extraites
            has_source = ('extraction_source' in result or 
                         ('valeurs_extraites' in result and 'source' in result['valeurs_extraites']))
            assert has_source, f"Source manquante dans: {result}"
        
        logger.info(f"✅ Extraction complète réussie: {len(results)} résultats")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur extraction complète: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🚀 Démarrage des tests d'intégration V2")
    
    tests = [
        ("Import V2", test_import_v2),
        ("Import modules", test_import_modules),
        ("Initialisation", test_initialization),
        ("Détection type fichier", test_file_type_detection),
        ("Détection lots", test_lot_detection),
        ("Validation", test_validation),
        ("Extraction complète", test_extraction_complete)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"🧪 Test: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name}: RÉUSSI")
            else:
                logger.error(f"❌ {test_name}: ÉCHEC")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERREUR - {e}")
        logger.info("-" * 50)
    
    logger.info(f"📊 Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        logger.info("🎉 Tous les tests d'intégration V2 sont réussis!")
        return True
    else:
        logger.error(f"⚠️ {total - passed} tests ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
