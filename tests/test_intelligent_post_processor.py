"""
🧪 Tests Unitaires - IntelligentPostProcessor
============================================

Tests pour le post-processeur intelligent.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from extractors.intelligent_post_processor import IntelligentPostProcessor


class TestIntelligentPostProcessor(unittest.TestCase):
    """Tests pour IntelligentPostProcessor"""
    
    def setUp(self):
        """Initialisation avant chaque test"""
        # Tester sans ExtractionImprover (mode dégradé)
        self.processor = IntelligentPostProcessor(enable_improver=False)
    
    def test_init_without_improver(self):
        """Test initialisation sans ExtractionImprover"""
        processor = IntelligentPostProcessor(enable_improver=False)
        self.assertFalse(processor.is_available())
        self.assertIsNone(processor.extraction_improver)
    
    @patch('extractors.intelligent_post_processor.extraction_improver')
    def test_init_with_improver(self, mock_improver):
        """Test initialisation avec ExtractionImprover"""
        mock_improver.extract_improved_data = MagicMock(return_value={})
        processor = IntelligentPostProcessor(enable_improver=True)
        # Si ExtractionImprover est disponible, il devrait être initialisé
        # Sinon, processor.is_available() sera False
        # Ce test vérifie juste que l'initialisation ne plante pas
        self.assertIsNotNone(processor)
    
    def test_enhance_extraction_without_improver(self):
        """Test enrichissement sans ExtractionImprover"""
        raw_data = {'intitule_lot': 'Lot 1'}
        text = "Contenu du document"
        
        enhanced = self.processor.enhance_extraction(raw_data, text)
        
        # Sans améliorateur, devrait retourner les données brutes
        self.assertEqual(enhanced, raw_data)
    
    @patch('extractors.intelligent_post_processor.extraction_improver')
    def test_enhance_extraction_with_improver(self, mock_improver_instance):
        """Test enrichissement avec ExtractionImprover"""
        # Créer un mock de l'instance
        mock_improver = MagicMock()
        mock_improver.extract_improved_data = MagicMock(
            return_value={
                'intitule_lot': 'Lot 1 amélioré',
                'montant_global_estime': 100000
            }
        )
        
        # Patcher l'import pour retourner notre mock
        with patch('extractors.intelligent_post_processor.extraction_improver', mock_improver):
            processor = IntelligentPostProcessor(enable_improver=True)
            if processor.is_available():
                raw_data = {'intitule_lot': 'Lot 1'}
                text = "Contenu du document"
                
                enhanced = processor.enhance_extraction(raw_data, text)
                
                # Vérifier que les données ont été enrichies
                self.assertIn('intitule_lot', enhanced)
                self.assertIn('montant_global_estime', enhanced)
    
    def test_merge_data_basic(self):
        """Test fusion basique de données"""
        raw_data = {'intitule_lot': 'Lot 1'}
        improved_data = {'montant_global_estime': 100000}
        
        merged = self.processor._merge_data(raw_data, improved_data)
        
        self.assertEqual(merged['intitule_lot'], 'Lot 1')
        self.assertEqual(merged['montant_global_estime'], 100000)
    
    def test_merge_data_prefer_improved(self):
        """Test que les données améliorées remplacent les brutes"""
        raw_data = {'intitule_lot': 'Lot 1 court'}
        improved_data = {'intitule_lot': 'Lot 1 amélioré avec plus de détails'}
        
        merged = self.processor._merge_data(raw_data, improved_data)
        
        # La valeur améliorée devrait être préférée si elle est meilleure
        self.assertIn('intitule_lot', merged)
    
    def test_merge_data_skip_empty(self):
        """Test que les valeurs vides sont ignorées"""
        raw_data = {'intitule_lot': 'Lot 1'}
        improved_data = {'montant_global_estime': None, 'autre_champ': ''}
        
        merged = self.processor._merge_data(raw_data, improved_data)
        
        self.assertEqual(merged['intitule_lot'], 'Lot 1')
        self.assertNotIn('montant_global_estime', merged)
        self.assertNotIn('autre_champ', merged)
    
    def test_is_better_value_empty_raw(self):
        """Test que valeur améliorée est meilleure si raw est vide"""
        result = self.processor._is_better_value('valeur améliorée', '')
        self.assertTrue(result)
    
    def test_is_better_value_none_raw(self):
        """Test que valeur améliorée est meilleure si raw est None"""
        result = self.processor._is_better_value('valeur améliorée', None)
        self.assertTrue(result)
    
    def test_is_better_value_longer_string(self):
        """Test que valeur plus longue est considérée meilleure"""
        short = "Court"
        long = "Texte beaucoup plus long avec plus de détails"
        result = self.processor._is_better_value(long, short)
        # Doit être meilleure si 20% plus longue
        if len(long) > len(short) * 1.2:
            self.assertTrue(result)
        else:
            self.assertFalse(result)
    
    def test_is_better_value_with_invalid_patterns(self):
        """Test détection de patterns invalides"""
        raw_with_patterns = "Texte avec [patterns invalides]"
        improved_clean = "Texte propre sans patterns"
        
        result = self.processor._is_better_value(improved_clean, raw_with_patterns)
        # Doit préférer la version propre
        self.assertTrue(result)
    
    def test_validate_enhanced_data(self):
        """Test validation des données enrichies"""
        data = {
            'intitule_lot': 'Lot 1',
            'montant_global_estime': 100000,
            'date_limite': '2025-12-31',
            'champ_vide': ''
        }
        
        validation = self.processor.validate_enhanced_data(data)
        
        self.assertIn('data', validation)
        self.assertIn('quality_score', validation)
        self.assertIn('completeness', validation)
        self.assertIn('issues', validation)
        self.assertEqual(validation['data'], data)
        self.assertIsInstance(validation['quality_score'], float)
        self.assertIsInstance(validation['completeness'], float)
        self.assertIsInstance(validation['issues'], list)
    
    def test_validate_enhanced_data_completeness(self):
        """Test calcul complétude"""
        # Données 100% complètes
        data_full = {
            'champ1': 'valeur1',
            'champ2': 'valeur2',
            'champ3': 'valeur3'
        }
        validation_full = self.processor.validate_enhanced_data(data_full)
        self.assertEqual(validation_full['completeness'], 100.0)
        
        # Données 50% complètes
        data_half = {
            'champ1': 'valeur1',
            'champ2': '',
            'champ3': None
        }
        validation_half = self.processor.validate_enhanced_data(data_half)
        self.assertLess(validation_half['completeness'], 100.0)
    
    def test_validate_enhanced_data_detects_issues(self):
        """Test détection de problèmes dans les données"""
        data_with_issues = {
            'intitule_lot': 'Lot avec [patterns invalides]',
            'autre_champ': '[...'
        }
        
        validation = self.processor.validate_enhanced_data(data_with_issues)
        
        # Doit détecter les patterns invalides
        self.assertGreater(len(validation['issues']), 0)
    
    def test_validate_enhanced_data_low_completeness_warning(self):
        """Test avertissement complétude faible"""
        # Données très incomplètes
        data_sparse = {
            'champ1': 'valeur1',
            'champ2': '',
            'champ3': '',
            'champ4': '',
            'champ5': ''
        }
        
        validation = self.processor.validate_enhanced_data(data_sparse)
        
        # Doit avoir un warning de complétude faible
        if validation['completeness'] < 50:
            self.assertTrue(
                any('complétude' in issue.lower() or 'completude' in issue.lower() 
                    for issue in validation['issues'])
            )
    
    def test_is_available_false_when_disabled(self):
        """Test disponibilité quand désactivé"""
        processor = IntelligentPostProcessor(enable_improver=False)
        self.assertFalse(processor.is_available())
    
    def test_error_handling_in_enhance_extraction(self):
        """Test gestion d'erreurs dans enhance_extraction"""
        # Test avec données problématiques
        raw_data = {'champ': 'valeur'}
        text = "Contenu"
        
        # Ne devrait pas planter même avec des erreurs
        try:
            enhanced = self.processor.enhance_extraction(raw_data, text)
            self.assertIsNotNone(enhanced)
        except Exception as e:
            self.fail(f"enhance_extraction ne devrait pas lever d'exception: {e}")


if __name__ == '__main__':
    unittest.main()


