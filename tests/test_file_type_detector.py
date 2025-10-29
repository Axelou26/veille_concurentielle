"""
🧪 Tests Unitaires - FileTypeDetector
====================================

Tests pour le détecteur de type de fichier unifié.
"""

import unittest
import os
from extractors.file_type_detector import FileTypeDetector


class TestFileTypeDetector(unittest.TestCase):
    """Tests pour FileTypeDetector"""
    
    def setUp(self):
        """Initialisation avant chaque test"""
        self.detector = FileTypeDetector
    
    def test_detect_pdf_from_extension(self):
        """Test détection PDF depuis extension"""
        file_type = self.detector.detect(file_name="document.pdf")
        self.assertEqual(file_type, 'pdf')
    
    def test_detect_excel_from_extension_xlsx(self):
        """Test détection Excel depuis extension .xlsx"""
        file_type = self.detector.detect(file_name="data.xlsx")
        self.assertEqual(file_type, 'excel')
    
    def test_detect_excel_from_extension_xls(self):
        """Test détection Excel depuis extension .xls"""
        file_type = self.detector.detect(file_name="data.xls")
        self.assertEqual(file_type, 'excel')
    
    def test_detect_text_from_extension_txt(self):
        """Test détection texte depuis extension .txt"""
        file_type = self.detector.detect(file_name="document.txt")
        self.assertEqual(file_type, 'text')
    
    def test_detect_text_from_extension_md(self):
        """Test détection texte depuis extension .md"""
        file_type = self.detector.detect(file_name="readme.md")
        self.assertEqual(file_type, 'text')
    
    def test_detect_from_file_path(self):
        """Test détection depuis chemin de fichier"""
        file_type = self.detector.detect(file_path="/path/to/document.pdf")
        self.assertEqual(file_type, 'pdf')
    
    def test_detect_from_analysis(self):
        """Test détection depuis analyse préliminaire"""
        file_analysis = {
            'contenu_extraite': {
                'type': 'pdf_avance'
            }
        }
        file_type = self.detector.detect(file_analysis=file_analysis)
        self.assertEqual(file_type, 'pdf')
    
    def test_detect_from_analysis_excel(self):
        """Test détection Excel depuis analyse"""
        file_analysis = {
            'contenu_extraite': {
                'type': 'excel'
            }
        }
        file_type = self.detector.detect(file_analysis=file_analysis)
        self.assertEqual(file_type, 'excel')
    
    def test_detect_from_analysis_text(self):
        """Test détection texte depuis analyse"""
        file_analysis = {
            'contenu_extraite': {
                'type': 'texte'
            }
        }
        file_type = self.detector.detect(file_analysis=file_analysis)
        self.assertEqual(file_type, 'text')
    
    def test_detect_unknown_type(self):
        """Test détection type inconnu"""
        file_type = self.detector.detect(file_name="document.unknown")
        self.assertEqual(file_type, 'other')
    
    def test_analysis_priority_over_extension(self):
        """Test que l'analyse a priorité sur l'extension"""
        file_analysis = {
            'contenu_extraite': {
                'type': 'pdf'
            }
        }
        # Même avec extension différente, l'analyse doit prendre le dessus
        file_type = self.detector.detect(
            file_name="document.xlsx",
            file_analysis=file_analysis
        )
        self.assertEqual(file_type, 'pdf')
    
    def test_is_supported_pdf(self):
        """Test vérification support PDF"""
        self.assertTrue(self.detector.is_supported('pdf'))
    
    def test_is_supported_excel(self):
        """Test vérification support Excel"""
        self.assertTrue(self.detector.is_supported('excel'))
    
    def test_is_supported_text(self):
        """Test vérification support texte"""
        self.assertTrue(self.detector.is_supported('text'))
    
    def test_is_supported_other(self):
        """Test vérification non-support"""
        self.assertFalse(self.detector.is_supported('other'))
    
    def test_get_supported_extensions(self):
        """Test récupération extensions supportées"""
        extensions = self.detector.get_supported_extensions()
        self.assertIsInstance(extensions, list)
        self.assertIn('.pdf', extensions)
        self.assertIn('.xlsx', extensions)
        self.assertIn('.txt', extensions)
    
    def test_detect_csv_as_excel(self):
        """Test que CSV est traité comme Excel"""
        file_type = self.detector.detect(file_name="data.csv")
        self.assertEqual(file_type, 'excel')
    
    def test_detect_doc_as_text(self):
        """Test que DOC est traité comme texte"""
        file_type = self.detector.detect(file_name="document.doc")
        self.assertEqual(file_type, 'text')
    
    def test_detect_docx_as_text(self):
        """Test que DOCX est traité comme texte"""
        file_type = self.detector.detect(file_name="document.docx")
        self.assertEqual(file_type, 'text')
    
    def test_detect_empty_filename(self):
        """Test avec nom de fichier vide"""
        file_type = self.detector.detect(file_name="")
        self.assertEqual(file_type, 'other')
    
    def test_detect_none(self):
        """Test avec paramètres None"""
        file_type = self.detector.detect()
        self.assertEqual(file_type, 'other')
    
    def test_case_insensitive_extensions(self):
        """Test que les extensions sont insensibles à la casse"""
        file_type_upper = self.detector.detect(file_name="DOCUMENT.PDF")
        file_type_lower = self.detector.detect(file_name="document.pdf")
        self.assertEqual(file_type_upper, file_type_lower)
        self.assertEqual(file_type_upper, 'pdf')


if __name__ == '__main__':
    unittest.main()


