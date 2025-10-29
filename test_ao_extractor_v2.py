#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Test AOExtractor V2 - Architecture Modulaire
===============================================

Tests pour valider le bon fonctionnement de la nouvelle architecture modulaire.
"""

import sys
import os
import pandas as pd
from datetime import datetime
import tempfile
import json

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ao_extractor_v2 import AOExtractorV2
from extractors import PatternManager, ValidationEngine, PDFExtractor, ExcelExtractor, TextExtractor, LotDetector

def test_initialization():
    """Test de l'initialisation de AOExtractorV2"""
    print("🧪 Test d'initialisation...")
    
    try:
        # Test avec données de référence
        reference_data = pd.DataFrame({
            'id': [1, 2, 3],
            'groupement': ['RESAH', 'UGAP', 'UNIHA'],
            'univers': ['Médical', 'Informatique', 'Formation']
        })
        
        extractor = AOExtractorV2(reference_data=reference_data)
        
        # Vérifier que les composants sont initialisés
        assert extractor.pattern_manager is not None
        assert extractor.validation_engine is not None
        assert extractor.lot_detector is not None
        assert extractor.pdf_extractor is not None
        assert extractor.excel_extractor is not None
        assert extractor.text_extractor is not None
        
        print("✅ Initialisation réussie")
        return True
        
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        return False

def test_pattern_manager():
    """Test du gestionnaire de patterns"""
    print("🧪 Test du gestionnaire de patterns...")
    
    try:
        pattern_manager = PatternManager()
        
        # Test récupération des patterns
        patterns = pattern_manager.get_field_patterns('montant_global_estime')
        assert len(patterns) > 0
        print(f"✅ Patterns montant_global_estime: {len(patterns)} trouvés")
        
        # Test ajout de pattern personnalisé
        pattern_manager.add_pattern('test', 'custom', r'test_pattern')
        test_patterns = pattern_manager.get_patterns('test', 'custom')
        assert 'test_pattern' in test_patterns
        print("✅ Pattern personnalisé ajouté")
        
        # Test compilation de pattern
        compiled = pattern_manager.compile_pattern(r'\d+')
        assert compiled is not None
        print("✅ Compilation de pattern réussie")
        
        print("✅ Gestionnaire de patterns fonctionnel")
        return True
        
    except Exception as e:
        print(f"❌ Erreur gestionnaire de patterns: {e}")
        return False

def test_validation_engine():
    """Test du moteur de validation"""
    print("🧪 Test du moteur de validation...")
    
    try:
        validation_engine = ValidationEngine()
        
        # Test avec des données valides
        valid_data = {
            'reference_procedure': '2024-R001-000-000',
            'intitule_procedure': 'Appel d\'offres test',
            'montant_global_estime': 100000,
            'date_limite': '31/12/2024',
            'groupement': 'RESAH'
        }
        
        result = validation_engine.validate_extraction(valid_data)
        assert result is not None
        assert result.is_valid
        assert result.confidence > 0.5
        print(f"✅ Validation données valides: confiance {result.confidence:.2%}")
        
        # Test avec des données invalides
        invalid_data = {
            'reference_procedure': '',
            'intitule_procedure': '',
            'montant_global_estime': -1000,
            'date_limite': 'invalid_date'
        }
        
        result = validation_engine.validate_extraction(invalid_data)
        assert result is not None
        assert not result.is_valid
        assert len(result.errors) > 0
        print(f"✅ Validation données invalides: {len(result.errors)} erreurs détectées")
        
        print("✅ Moteur de validation fonctionnel")
        return True
        
    except Exception as e:
        print(f"❌ Erreur moteur de validation: {e}")
        return False

def test_lot_detector():
    """Test du détecteur de lots"""
    print("🧪 Test du détecteur de lots...")
    
    try:
        lot_detector = LotDetector()
        
        # Test avec un texte contenant des lots
        test_text = """
        ALLOTISSEMENT
        
        1 FORMATIONS TRANSVERSES SANTE 150000 200000
        2 FORMATIONS TECHNIQUES 100000 150000
        3 FORMATIONS MANAGEMENT 80000 120000
        """
        
        lots = lot_detector.detect_lots(test_text)
        assert len(lots) > 0
        print(f"✅ Lots détectés: {len(lots)}")
        
        for lot in lots:
            assert lot.numero > 0
            assert lot.intitule
            print(f"  - Lot {lot.numero}: {lot.intitule[:50]}...")
        
        print("✅ Détecteur de lots fonctionnel")
        return True
        
    except Exception as e:
        print(f"❌ Erreur détecteur de lots: {e}")
        return False

def test_text_extraction():
    """Test de l'extraction de texte"""
    print("🧪 Test de l'extraction de texte...")
    
    try:
        text_extractor = TextExtractor()
        
        # Test avec un texte d'appel d'offres
        test_text = """
        RAPPORT DE CONSULTATION
        Référence: 2024-R001-000-000
        Intitulé: Appel d'offres pour formations
        Groupement: RESAH
        Montant global estimé: 500 000 €
        Date limite: 31/12/2024
        """
        
        results = text_extractor.extract(test_text)
        assert len(results) > 0
        
        entry = results[0]
        assert 'valeurs_extraites' in entry
        assert 'statistiques' in entry
        
        extracted_data = entry['valeurs_extraites']
        print(f"✅ Données extraites: {len(extracted_data)} champs")
        
        # Vérifier quelques champs clés
        if 'reference_procedure' in extracted_data:
            print(f"  - Référence: {extracted_data['reference_procedure']}")
        if 'montant_global_estime' in extracted_data:
            print(f"  - Montant: {extracted_data['montant_global_estime']}")
        
        print("✅ Extraction de texte fonctionnelle")
        return True
        
    except Exception as e:
        print(f"❌ Erreur extraction de texte: {e}")
        return False

def test_excel_extraction():
    """Test de l'extraction Excel"""
    print("🧪 Test de l'extraction Excel...")
    
    try:
        excel_extractor = ExcelExtractor()
        
        # Créer un DataFrame de test
        test_data = {
            'Lot': [1, 2, 3],
            'Intitulé': ['Formation 1', 'Formation 2', 'Formation 3'],
            'Montant estimé': [100000, 150000, 200000],
            'Montant maximum': [120000, 180000, 250000],
            'Référence': ['2024-R001', '2024-R002', '2024-R003']
        }
        
        df = pd.DataFrame(test_data)
        
        # Simuler un fichier uploadé
        class MockFile:
            def read(self):
                return df.to_excel()
        
        mock_file = MockFile()
        
        results = excel_extractor.extract(df)
        assert len(results) > 0
        
        print(f"✅ Extraction Excel: {len(results)} entrées")
        
        print("✅ Extraction Excel fonctionnelle")
        return True
        
    except Exception as e:
        print(f"❌ Erreur extraction Excel: {e}")
        return False

def test_ao_extractor_v2_integration():
    """Test d'intégration complet d'AOExtractorV2"""
    print("🧪 Test d'intégration AOExtractorV2...")
    
    try:
        # Initialiser l'extracteur
        extractor = AOExtractorV2()
        
        # Test des métriques
        metrics = extractor.get_performance_metrics()
        assert 'total_extractions' in metrics
        print("✅ Métriques initialisées")
        
        # Test des patterns
        patterns = extractor.get_patterns_for_field('montant_global_estime')
        assert len(patterns) > 0
        print(f"✅ Patterns récupérés: {len(patterns)}")
        
        # Test d'ajout de pattern personnalisé
        extractor.add_custom_pattern('test', 'custom', r'test_pattern')
        print("✅ Pattern personnalisé ajouté")
        
        # Test de détection de lots
        test_text = """
        1 FORMATION SANTE 100000 120000
        2 FORMATION TECHNIQUE 80000 100000
        """
        lots = extractor.detect_lots(test_text)
        print(f"✅ Lots détectés: {len(lots)}")
        
        # Test de validation
        test_data = {
            'reference_procedure': '2024-R001',
            'intitule_procedure': 'Test',
            'montant_global_estime': 100000
        }
        validation = extractor.validate_extraction(test_data)
        if validation:
            print(f"✅ Validation: confiance {validation.confidence:.2%}")
        
        # Test de sauvegarde/chargement de configuration
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            extractor.save_patterns_config(config_file)
            print("✅ Configuration sauvegardée")
            
            # Recharger la configuration
            extractor.load_patterns_config(config_file)
            print("✅ Configuration rechargée")
            
        finally:
            os.unlink(config_file)
        
        # Test du résumé
        summary = extractor.get_extraction_summary()
        assert 'total_extractions' in summary
        print("✅ Résumé généré")
        
        print("✅ Intégration AOExtractorV2 réussie")
        return True
        
    except Exception as e:
        print(f"❌ Erreur intégration: {e}")
        return False

def run_all_tests():
    """Lance tous les tests"""
    print("🚀 Démarrage des tests AOExtractor V2")
    print("=" * 50)
    
    tests = [
        test_initialization,
        test_pattern_manager,
        test_validation_engine,
        test_lot_detector,
        test_text_extraction,
        test_excel_extraction,
        test_ao_extractor_v2_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} échoué: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés !")
        return True
    else:
        print("⚠️ Certains tests ont échoué")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

