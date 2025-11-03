"""
📄 Extracteur PDF - Spécialisé
=============================

Extracteur spécialisé pour les documents PDF d'appels d'offres.
Utilise le détecteur de lots et les patterns modulaires.
"""

import logging
import re
import traceback
from io import BytesIO
from typing import Dict, Any, List, Optional
from .base_extractor import BaseExtractor
from .pattern_manager import PatternManager
from .lot_detector import LotDetector, LotInfo
from .validation_engine import ValidationEngine

logger = logging.getLogger(__name__)

class PDFExtractor(BaseExtractor):
    """Extracteur spécialisé pour les documents PDF"""
    
    def __init__(self, pattern_manager: PatternManager = None, validation_engine: ValidationEngine = None):
        """
        Initialise l'extracteur PDF
        
        Args:
            pattern_manager: Gestionnaire de patterns (optionnel)
            validation_engine: Moteur de validation (optionnel)
        """
        super().__init__(pattern_manager, validation_engine)
        self.lot_detector = LotDetector()
        self.pattern_manager = pattern_manager or PatternManager()
        self.validation_engine = validation_engine or ValidationEngine()
    
    def extract(self, source: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Extrait les données d'un document PDF
        
        Args:
            source: Source de données (fichier PDF, texte extrait, etc.)
            **kwargs: Arguments supplémentaires
            
        Returns:
            Liste des données extraites
        """
        try:
            logger.info("📄 Début de l'extraction PDF...")
            
            # Extraire le texte du PDF
            text_content = self._extract_text_from_pdf(source)
            if not text_content:
                logger.warning("⚠️ Aucun contenu texte extrait du PDF")
                return []
            
            # Détecter les lots
            lots_detected = self.lot_detector.detect_lots(text_content)
            
            if lots_detected:
                logger.info(f"✅ {len(lots_detected)} lots détectés dans le PDF")
                return self._create_entries_for_lots(lots_detected, text_content)
            else:
                logger.info("⚠️ Aucun lot détecté, extraction standard")
                return self._extract_single_entry(text_content)
                
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"❌ Erreur extraction PDF ({error_type}): {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            return [{
                'erreur': f"Erreur extraction PDF: {error_type} - {str(e)}",
                'error_type': error_type,
                'error_details': str(e)
            }]
    
    def _extract_text_from_pdf(self, source: Any) -> str:
        """
        Extrait le texte d'un PDF
        
        Args:
            source: Source PDF (fichier, bytes, etc.)
            
        Returns:
            Texte extrait
        """
        try:
            # Si c'est déjà du texte, le retourner
            if isinstance(source, str):
                return source
            
            # Si c'est un fichier uploadé (Streamlit)
            if hasattr(source, 'read'):
                # Sauvegarder la position actuelle
                try:
                    current_pos = source.tell()
                except:
                    current_pos = 0
                
                # Réinitialiser à la position 0 si nécessaire
                try:
                    if current_pos > 0:
                        source.seek(0)
                except:
                    pass
                
                # Lire le contenu du fichier
                try:
                    content = source.read()
                    # Réinitialiser après lecture pour permettre une réutilisation
                    try:
                        source.seek(0)
                    except:
                        pass
                    
                    if isinstance(content, bytes):
                        # Utiliser PyPDF2 ou pdfplumber pour extraire le texte
                        return self._extract_text_from_bytes(content)
                    else:
                        return str(content)
                except Exception as e:
                    logger.error(f"Erreur lecture fichier: {e}")
                    return ""
            
            # Si c'est un dictionnaire avec le contenu extrait
            if isinstance(source, dict) and 'text_content' in source:
                return source['text_content']
            
            # Si c'est une liste de pages
            if isinstance(source, list):
                return '\n'.join(str(page) for page in source)
            
            return str(source)
            
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"❌ Erreur extraction texte PDF ({error_type}): {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            return ""
    
    def _extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """
        Extrait le texte depuis des bytes PDF avec support OCR pour PDFs scannés
        
        Args:
            pdf_bytes: Contenu PDF en bytes
            
        Returns:
            Texte extrait
        """
        try:
            # Essayer d'abord avec PyPDF2
            try:
                import PyPDF2
                
                pdf_file = BytesIO(pdf_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                if text.strip() and len(text.strip()) > 100:
                    logger.info("✅ Texte extrait avec PyPDF2")
                    return text
                    
            except ImportError:
                logger.warning("PyPDF2 non disponible")
            except Exception as e:
                logger.warning(f"Erreur PyPDF2: {e}")
            
            # Essayer avec pdfplumber
            try:
                import pdfplumber
                
                with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
                if text.strip() and len(text.strip()) > 100:
                    logger.info("✅ Texte extrait avec pdfplumber")
                    return text
                    
            except ImportError:
                logger.warning("pdfplumber non disponible")
            except Exception as e:
                logger.warning(f"Erreur pdfplumber: {e}")
            
            # Essayer avec pymupdf
            try:
                import fitz  # PyMuPDF
                
                pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
                text = ""
                
                for page_num in range(pdf_document.page_count):
                    page = pdf_document[page_num]
                    text += page.get_text() + "\n"
                
                pdf_document.close()
                
                if text.strip() and len(text.strip()) > 100:
                    logger.info("✅ Texte extrait avec PyMuPDF")
                    return text
                    
            except ImportError:
                logger.warning("PyMuPDF non disponible")
            except Exception as e:
                logger.warning(f"Erreur PyMuPDF: {e}")
            
            # Si peu ou pas de texte, essayer OCR (PDF scanné)
            text = self._extract_text_with_ocr(pdf_bytes)
            if text and len(text.strip()) > 100:
                logger.info("✅ Texte extrait avec OCR")
                return text
            
            logger.warning("⚠️ Aucune bibliothèque PDF disponible ou texte insuffisant")
            return ""
            
        except Exception as e:
            logger.error(f"Erreur extraction texte depuis bytes: {e}")
            return ""
    
    def _extract_text_with_ocr(self, pdf_bytes: bytes) -> str:
        """
        Extrait le texte d'un PDF scanné avec OCR
        
        Args:
            pdf_bytes: Contenu PDF en bytes
            
        Returns:
            Texte extrait via OCR
        """
        try:
            # Essayer avec pytesseract
            try:
                import pytesseract
                from pdf2image import convert_from_bytes
                
                # Convertir le PDF en images
                images = convert_from_bytes(pdf_bytes, dpi=300)
                
                ocr_text = ""
                for img in images:
                    # Extraire le texte avec OCR (français)
                    page_text = pytesseract.image_to_string(img, lang='fra')
                    if page_text:
                        ocr_text += page_text + "\n"
                
                if ocr_text.strip():
                    logger.info(f"✅ OCR pytesseract: {len(ocr_text)} caractères extraits")
                    return ocr_text
                    
            except ImportError:
                logger.debug("pytesseract non disponible")
            except Exception as e:
                logger.debug(f"Erreur OCR pytesseract: {e}")
            
            # Essayer avec easyocr (alternative)
            try:
                import easyocr
                
                reader = easyocr.Reader(['fr', 'en'])
                images = convert_from_bytes(pdf_bytes, dpi=300)
                
                ocr_text = ""
                for img in images:
                    results = reader.readtext(img)
                    page_text = "\n".join([result[1] for result in results])
                    if page_text:
                        ocr_text += page_text + "\n"
                
                if ocr_text.strip():
                    logger.info(f"✅ OCR easyocr: {len(ocr_text)} caractères extraits")
                    return ocr_text
                    
            except ImportError:
                logger.debug("easyocr non disponible")
            except Exception as e:
                logger.debug(f"Erreur OCR easyocr: {e}")
            
            return ""
            
        except Exception as e:
            logger.debug(f"Erreur OCR: {e}")
            return ""
    
    def _extract_tables_from_pdf(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extrait les tableaux structurés du PDF
        
        Args:
            pdf_bytes: Contenu PDF en bytes
            
        Returns:
            Liste des tableaux extraits avec leurs données structurées
        """
        tables_data = []
        
        try:
            import pdfplumber
            
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    
                    for table_index, table in enumerate(tables):
                        if table and len(table) > 0:
                            # Structurer le tableau
                            structured_table = self._structure_table(table)
                            
                            if structured_table:
                                tables_data.append({
                                    'page': page_num + 1,
                                    'table_index': table_index,
                                    'rows': len(table),
                                    'columns': len(table[0]) if table else 0,
                                    'data': structured_table
                                })
                                logger.debug(f"📊 Tableau extrait page {page_num + 1}, table {table_index}: {len(structured_table)} entrées")
            
            if tables_data:
                logger.info(f"✅ {len(tables_data)} tableaux structurés extraits du PDF")
            
        except ImportError:
            logger.warning("pdfplumber non disponible pour extraction de tableaux")
        except Exception as e:
            logger.warning(f"Erreur extraction tableaux: {e}")
        
        return tables_data
    
    def _structure_table(self, table: List[List]) -> List[Dict[str, Any]]:
        """
        Structure un tableau extrait en dictionnaire
        
        Args:
            table: Tableau brut extrait (liste de listes)
            
        Returns:
            Liste de dictionnaires structurés
        """
        if not table or len(table) < 2:
            return []
        
        structured = []
        headers = [str(cell).strip() if cell else f"Col_{i}" 
                  for i, cell in enumerate(table[0])]
        
        for row in table[1:]:
            if not row or not any(cell for cell in row):
                continue
            
            row_dict = {}
            for i, cell in enumerate(row):
                header = headers[i] if i < len(headers) else f"Col_{i}"
                row_dict[header] = str(cell).strip() if cell else ""
            
            # Filtrer les lignes vides
            if any(row_dict.values()):
                structured.append(row_dict)
        
        return structured
    
    def _create_entries_for_lots(self, lots: List[LotInfo], text_content: str) -> List[Dict[str, Any]]:
        """
        Crée des entrées pour chaque lot détecté
        
        Args:
            lots: Liste des lots détectés
            text_content: Contenu texte du PDF
            
        Returns:
            Liste des entrées créées
        """
        entries = []
        
        try:
            logger.info(f"📝 Création des entrées pour {len(lots)} lots...")
            
            # Extraire les informations générales du PDF
            general_info = self._extract_general_info(text_content)
            
            # Extraire les critères par lot
            criteres_par_lot = self._extract_criteres_by_lot(text_content, lots)
            
            # Log des informations générales AVANT de créer les entrées
            logger.info(f"📋 General info avant création entrées: {list(general_info.keys())}")
            for date_field in ['date_limite', 'date_attribution', 'duree_marche', 'reconduction', 'fin_sans_reconduction', 'fin_avec_reconduction']:
                if date_field in general_info:
                    logger.info(f"✅ {date_field} dans general_info: '{general_info[date_field]}'")
            
            for lot in lots:
                # Créer une entrée pour ce lot
                lot_entry = {
                    'valeurs_extraites': general_info.copy(),
                    'valeurs_generees': {},
                    'statistiques': {}
                }
                
                # Ajouter les informations spécifiques au lot
                lot_entry['valeurs_extraites']['nbr_lots'] = len(lots)
                lot_entry['valeurs_extraites']['lot_numero'] = lot.numero
                lot_entry['valeurs_extraites']['intitule_lot'] = lot.intitule
                lot_entry['valeurs_extraites']['montant_global_estime'] = lot.montant_estime
                lot_entry['valeurs_extraites']['montant_global_maxi'] = lot.montant_maximum
                lot_entry['valeurs_extraites']['quantite_minimum'] = lot.quantite_minimum
                lot_entry['valeurs_extraites']['quantites_estimees'] = lot.quantites_estimees
                lot_entry['valeurs_extraites']['quantite_maximum'] = lot.quantite_maximum
                
                # Ajouter les critères spécifiques au lot si disponibles
                if lot.numero in criteres_par_lot:
                    lot_entry['valeurs_extraites']['criteres_economique'] = criteres_par_lot[lot.numero].get('criteres_economique', '')
                    lot_entry['valeurs_extraites']['criteres_techniques'] = criteres_par_lot[lot.numero].get('criteres_techniques', '')
                    lot_entry['valeurs_extraites']['autres_criteres'] = criteres_par_lot[lot.numero].get('autres_criteres', '')
                else:
                    # Utiliser les critères généraux
                    lot_entry['valeurs_extraites']['criteres_economique'] = lot.criteres_economique
                    lot_entry['valeurs_extraites']['criteres_techniques'] = lot.criteres_techniques
                    lot_entry['valeurs_extraites']['autres_criteres'] = lot.autres_criteres
                
                lot_entry['valeurs_extraites']['rse'] = lot.rse
                lot_entry['valeurs_extraites']['contribution_fournisseur'] = lot.contribution_fournisseur
                
                # Générer les valeurs manquantes
                lot_entry['valeurs_extraites'] = self.generate_missing_values(lot_entry['valeurs_extraites'])
                
                # Calculer les statistiques
                lot_entry['statistiques'] = self.calculate_extraction_stats(lot_entry['valeurs_extraites'])
                
                # Ajouter des métadonnées
                lot_entry['lot_id'] = f"LOT_{lot.numero}"
                lot_entry['extraction_source'] = lot.source
                lot_entry['extraction_timestamp'] = self._get_current_timestamp()
                lot_entry['text_source'] = text_content  # Pour l'enrichissement avec extraction_improver
                
                entries.append(lot_entry)
                logger.info(f"📦 Entrée PDF créée pour le lot {lot.numero}: {lot.intitule[:50]}...")
            
            logger.info(f"✅ Création des entrées PDF terminée: {len(entries)} entrées créées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des entrées PDF: {e}")
        
        return entries
    
    def _extract_single_entry(self, text_content: str) -> List[Dict[str, Any]]:
        """
        Extrait une seule entrée (pas de lots détectés)
        
        Args:
            text_content: Contenu texte du PDF
            
        Returns:
            Liste avec une seule entrée
        """
        try:
            logger.info("📄 Extraction d'entrée unique PDF...")
            
            # Extraire les informations générales
            general_info = self._extract_general_info(text_content)
            
            # Créer l'entrée
            entry = {
                'valeurs_extraites': general_info,
                'valeurs_generees': {},
                'statistiques': {}
            }
            
            # Ajouter des valeurs par défaut
            entry['valeurs_extraites']['nbr_lots'] = 1
            entry['valeurs_extraites']['lot_numero'] = 1
            entry['valeurs_extraites']['intitule_lot'] = entry['valeurs_extraites'].get('intitule_procedure', 'Lot unique')
            
            # Générer les valeurs manquantes
            entry['valeurs_extraites'] = self.generate_missing_values(entry['valeurs_extraites'])
            
            # Calculer les statistiques
            entry['statistiques'] = self.calculate_extraction_stats(entry['valeurs_extraites'])
            
            # Ajouter des métadonnées
            entry['extraction_source'] = 'pdf_single_entry'
            entry['extraction_timestamp'] = self._get_current_timestamp()
            entry['text_source'] = text_content  # Pour l'enrichissement avec extraction_improver
            
            logger.info("✅ Entrée PDF unique créée")
            return [entry]
            
        except Exception as e:
            logger.error(f"Erreur extraction entrée unique PDF: {e}")
            return [{'erreur': f"Erreur extraction entrée unique PDF: {e}"}]
    
    def _extract_general_info(self, text_content: str) -> Dict[str, Any]:
        """
        Extrait les informations générales du PDF
        
        Args:
            text_content: Contenu texte du PDF
            
        Returns:
            Dictionnaire des informations générales
        """
        general_info = {}
        try:
            # Extraire d'abord le titre du document pour l'intitulé de procédure (priorité)
            document_title = self._extract_document_title(text_content)
            if document_title and len(document_title.strip()) >= 10:
                general_info['intitule_procedure'] = document_title.strip()
                logger.info(f"📄 Titre du document détecté comme intitulé: {document_title[:60]}...")
            
            fields_to_extract = [
                'reference_procedure', 'intitule_procedure', 'groupement',
                'type_procedure', 'mono_multi', 'date_limite', 'date_attribution',
                'duree_marche', 'montant_global_estime', 'montant_global_maxi',
                'quantite_minimum', 'quantites_estimees', 'quantite_maximum',
                'criteres_economique', 'criteres_techniques', 'autres_criteres',
                'rse', 'contribution_fournisseur', 'infos_complementaires',
                'execution_marche', 'reconduction', 'fin_sans_reconduction', 'fin_avec_reconduction',
                'achat', 'credit_bail', 'credit_bail_duree', 'location', 'location_duree', 'mad',
                'attributaire', 'produit_retenu', 'segment', 'famille',
                'remarques', 'notes_acheteur_procedure', 'notes_acheteur_fournisseur', 
                'notes_acheteur_positionnement'
            ]

            # Préparer les groupes de patterns
            pattern_groups = {}
            for field in fields_to_extract:
                patterns = self.pattern_manager.get_field_patterns(field)
                if patterns:
                    pattern_groups[field] = patterns
                # Log pour les champs de dates importants
                if field in ['date_limite', 'date_attribution', 'duree_marche', 'reconduction']:
                    logger.debug(f"🔍 Patterns pour {field}: {len(patterns)} patterns chargés")

            # Extraire d'abord par sections pour réduire les faux positifs
            sections = self._split_into_sections(text_content)
            
            # Log des sections trouvées pour les dates
            for section_field in ['date_limite', 'date_attribution', 'duree_marche', 'reconduction', 'fin_sans_reconduction', 'fin_avec_reconduction']:
                if section_field in sections:
                    logger.info(f"📋 Section trouvée pour {section_field}: {sections[section_field][:100]}...")
                else:
                    logger.debug(f"⚠️ Pas de section trouvée pour {section_field}, recherche dans tout le texte")

            # Extraction combinée: par section (si disponible), sinon sur tout le texte
            if pattern_groups:
                parallel_results = {}
                for field, patterns in pattern_groups.items():
                    # Ne pas chercher intitule_procedure si déjà extrait depuis le titre du document
                    if field == 'intitule_procedure' and 'intitule_procedure' in general_info:
                        continue
                    
                    section_text = sections.get(field) or text_content
                    # Exécuter extraction ciblée champ par champ pour passer la section
                    values = self.extract_with_patterns(section_text, patterns, field)
                    parallel_results[field] = values
                    
                    # Log pour debug - TOUJOURS logger même si vide
                    if field in ['date_limite', 'date_attribution', 'duree_marche', 'reconduction', 'fin_sans_reconduction', 'fin_avec_reconduction']:
                        if values:
                            logger.info(f"✅ {field}: {values[:3]}")  # Afficher les 3 premières valeurs
                        else:
                            logger.warning(f"❌ {field}: Aucune valeur trouvée (section: {bool(sections.get(field))}, patterns: {len(patterns)})")
                for field, values in parallel_results.items():
                    if values:
                        cleaned_value = self.clean_extracted_value(values[0], self._get_field_type(field))
                        # Normaliser les valeurs spéciales
                        if field == 'type_procedure':
                            cleaned_value = self._normalize_type_procedure(cleaned_value)
                        elif field == 'mono_multi':
                            cleaned_value = self._normalize_mono_multi(cleaned_value, general_info.get('nbr_lots'))
                        
                        if cleaned_value:
                            # Ne pas écraser le titre du document si déjà présent
                            if field == 'intitule_procedure' and 'intitule_procedure' in general_info:
                                # Comparer les longueurs et garder le plus long (souvent plus complet)
                                if len(cleaned_value) > len(general_info['intitule_procedure']):
                                    general_info[field] = cleaned_value
                            else:
                                general_info[field] = cleaned_value

            logger.info(f"📊 Informations générales extraites: {len(general_info)} champs")
            
            # Log explicite des dates extraites (avec liste complète des champs)
            date_fields = ['date_limite', 'date_attribution', 'duree_marche', 'reconduction', 'fin_sans_reconduction', 'fin_avec_reconduction']
            logger.info(f"📋 Champs généraux disponibles: {list(general_info.keys())}")
            for date_field in date_fields:
                if date_field in general_info:
                    logger.info(f"✅ {date_field} EXTRAIT: '{general_info[date_field]}'")
                else:
                    logger.warning(f"❌ {date_field} MANQUANT dans general_info")
        except Exception as e:
            logger.error(f"Erreur extraction informations générales PDF: {e}")
            import traceback
            logger.error(traceback.format_exc())
        return general_info

    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """
        Découpe grossièrement le texte en sections clés et mappe vers les champs.
        """
        try:
            lowered = text.lower()
            sections: Dict[str, str] = {}

            def grab(after: str, until: List[str]) -> str:
                start = lowered.find(after)
                if start == -1:
                    return ""
                start_end = start + len(after)
                next_positions = [lowered.find(u, start_end) for u in until]
                next_positions = [p for p in next_positions if p != -1]
                end = min(next_positions) if next_positions else len(text)
                return text[start_end:end]

            # Définir des séparateurs génériques
            stops = ["\n\n", "\narticle", "\nsection", "\nchapitre", "\nannexe", "\nlot "]

            # Map sections -> champs
            # IMPORTANT: Ajouter les sections pour les dates importantes
            sections_raw = {
                'date_limite': grab('date limite', stops) or grab('échéance', stops) or grab('clôture', stops) or grab('cloture', stops) or grab('remise', stops) or grab('dépôt', stops) or grab('depot', stops),
                'date_attribution': grab('date attribution', stops) or grab('attribution', stops) or grab('attribué', stops) or grab('attribue', stops),
                'duree_marche': grab('durée', stops) or grab('duree', stops),
                'execution_marche': grab("exécution du marché", stops) or grab('execution du marche', stops),
                'reconduction': grab('reconduction', stops) or grab('renouvellement', stops),
                'fin_sans_reconduction': grab('fin sans reconduction', stops),
                'fin_avec_reconduction': grab('fin avec reconduction', stops),
                'rse': grab('rse', stops) or grab('responsabilité sociétale', stops) or grab('developpement durable', stops),
                'contribution_fournisseur': grab('contribution fournisseur', stops) or grab('participation fournisseur', stops),
                'infos_complementaires': grab('informations complémentaires', stops) or grab('renseignements complémentaires', stops) or grab('infos complémentaires', stops),
                'achat': grab('achat', stops) or grab('acquisition', stops),
                'credit_bail': grab('crédit-bail', stops) or grab('credit-bail', stops),
                'location': grab('location', stops),
                'mad': grab('mise à disposition', stops) or grab('mad', stops),
                'attributaire': grab('attributaire', stops) or grab('titulaire', stops) or grab('adjudicataire', stops),
                'produit_retenu': grab('produit retenu', stops) or grab('solution retenue', stops),
                'segment': grab('segment', stops),
                'famille': grab('famille', stops)
            }

            # Répliquer pour toutes les clés attendues
            for k, v in sections_raw.items():
                if v:
                    sections[k] = v
            return sections
        except Exception:
            return {}
    
    def _extract_criteres_by_lot(self, text_content: str, lots: List[LotInfo]) -> Dict[int, Dict[str, str]]:
        """
        Extrait les critères d'attribution par lot
        
        Args:
            text_content: Contenu texte du PDF
            lots: Liste des lots détectés
            
        Returns:
            Dictionnaire {numero_lot: {criteres}}
        """
        criteres_par_lot = {}
        
        try:
            logger.info("🔍 Extraction des critères par lot...")
            
            # Pour chaque lot, chercher les critères dans son contexte
            for lot in lots:
                lot_numero = lot.numero
                criteres_lot = {
                    'criteres_economique': '',
                    'criteres_techniques': '',
                    'autres_criteres': ''
                }
                
                # Chercher les critères dans le contexte du lot
                lot_context = self._extract_lot_context(text_content, lot_numero)
                if lot_context:
                    # Extraire les critères depuis le contexte
                    for critere_type in ['criteres_economique', 'criteres_techniques', 'autres_criteres']:
                        patterns = self.pattern_manager.get_field_patterns(critere_type)
                        if patterns:
                            values = self.extract_with_patterns(lot_context, patterns, critere_type)
                            if values:
                                criteres_lot[critere_type] = values[0]
                
                criteres_par_lot[lot_numero] = criteres_lot
                logger.info(f"📊 Critères lot {lot_numero}: Éco={criteres_lot['criteres_economique']}, Tech={criteres_lot['criteres_techniques']}")
            
        except Exception as e:
            logger.error(f"Erreur extraction critères par lot: {e}")
        
        return criteres_par_lot
    
    def _extract_lot_context(self, text: str, lot_numero: int) -> str:
        """
        Extrait le contexte autour d'un lot spécifique
        
        Args:
            text: Texte complet
            lot_numero: Numéro du lot
            
        Returns:
            Contexte du lot
        """
        try:
            # Chercher le lot dans le texte
            lot_pattern = rf'lot\s*n°?\s*{lot_numero}[^\n]*\n(.*?)(?=\nlot\s*n°?\s*\d+|\n\n|$)'
            match = re.search(lot_pattern, text, re.IGNORECASE | re.DOTALL)
            
            if match:
                return match.group(1)
            
            # Pattern alternatif plus large
            lot_pattern_alt = rf'lot\s*{lot_numero}[^\n]*\n(.*?)(?=\nlot\s*\d+|\n\n|$)'
            match_alt = re.search(lot_pattern_alt, text, re.IGNORECASE | re.DOTALL)
            
            if match_alt:
                return match_alt.group(1)
            
            return ""
            
        except Exception as e:
            logger.error(f"Erreur extraction contexte lot {lot_numero}: {e}")
            return ""
    
    def _get_field_type(self, field_name: str) -> str:
        """Détermine le type d'un champ pour le nettoyage"""
        if 'montant' in field_name.lower():
            return 'montant'
        elif 'date' in field_name.lower():
            return 'date'
        elif 'duree' in field_name.lower() or 'durée' in field_name.lower():
            return 'duree'
        elif 'reconduction' in field_name.lower():
            return 'reconduction'
        elif 'reference' in field_name.lower():
            return 'reference'
        else:
            return 'text'
    
    def _normalize_type_procedure(self, value: str) -> str:
        """
        Normalise la valeur du type de procédure
        
        Args:
            value: Valeur brute extraite
            
        Returns:
            Valeur normalisée ou None
        """
        if not value or not isinstance(value, str):
            return None
        
        value_lower = value.lower().strip()
        
        # Mapping des valeurs vers les types normalisés
        if 'ouvert' in value_lower and ('appel' in value_lower or 'offre' in value_lower or 'ao' in value_lower):
            return 'Appel d\'offres ouvert'
        elif 'restreint' in value_lower and ('appel' in value_lower or 'offre' in value_lower or 'ao' in value_lower):
            return 'Appel d\'offres restreint'
        elif 'consultation' in value_lower:
            return 'Consultation'
        elif 'achat direct' in value_lower or 'commande' in value_lower:
            return 'Achat direct'
        elif 'convention' in value_lower or 'accord cadre' in value_lower:
            return 'Convention'
        elif 'marché de services' in value_lower:
            return 'Consultation'
        elif len(value.strip()) > 5:  # Garder la valeur originale si elle est assez longue et non reconnue
            return value.strip()
        
        return None
    
    def _normalize_mono_multi(self, value: str, nbr_lots: int = None) -> str:
        """
        Normalise la valeur mono_multi
        
        Args:
            value: Valeur brute extraite
            nbr_lots: Nombre de lots détectés (pour inférence si nécessaire)
            
        Returns:
            Valeur normalisée ou None
        """
        if not value or not isinstance(value, str):
            # Inférer depuis le nombre de lots si disponible
            if nbr_lots is not None:
                return 'Multi-attributif' if nbr_lots > 1 else 'Mono-attributif'
            return None
        
        value_lower = value.lower().strip()
        
        # Mapping des valeurs
        if any(word in value_lower for word in ['multi', 'multiple', 'alloti', 'lotissement', 'lotti']):
            return 'Multi-attributif'
        elif any(word in value_lower for word in ['mono', 'unique', 'unitaire']):
            return 'Mono-attributif'
        elif nbr_lots is not None:
            # Inférer depuis le nombre de lots
            return 'Multi-attributif' if nbr_lots > 1 else 'Mono-attributif'
        
        return None
    
    def _extract_document_title(self, text_content: str) -> Optional[str]:
        """
        Extrait le titre du document (généralement un paragraphe en majuscules sur plusieurs lignes)
        
        Le titre du document est souvent l'intitulé de la procédure.
        Peut être sur plusieurs lignes, souvent dans le 2ème paragraphe en majuscules.
        
        Args:
            text_content: Contenu texte du PDF
            
        Returns:
            Titre du document ou None
        """
        try:
            lines = text_content.split('\n')
            
            # Prendre les 30 premières lignes (pour capturer le 2ème paragraphe aussi)
            first_lines = lines[:30]
            
            # Mots d'en-tête à exclure (ne sont pas le titre)
            header_keywords = [
                'règlement', 'reglement', 'règlement de consultation', 'rc',
                'appel d\'offres', 'appel d\'offre', 'ao', 'marche', 'marché',
                'procedure', 'procédure', 'consultation', 'avis',
                'reference', 'référence', 'ref', 'numero', 'numéro', 'n°',
                'date', 'groupement', 'organisme', 'acheteur',
                'lot', 'lots', 'lotissement', 'allotissement',
                'article', 'chapitre', 'section', 'annexe', 'centrale',
                'pouvoir adjudicateur', 'accord-cadre', 'accords-cadres'
            ]
            
            candidates = []
            multi_line_candidates = []  # Pour les titres sur plusieurs lignes
            
            # 1. Chercher des blocs de lignes en majuscules consécutives (titres multi-lignes)
            i = 0
            while i < len(first_lines) - 1:
                current_block = []
                start_idx = i
                
                # Chercher un bloc de lignes en majuscules consécutives
                while i < len(first_lines):
                    line = first_lines[i].strip()
                    line_lower = line.lower()
                    
                    # Ignorer les lignes vides
                    if not line:
                        i += 1
                        continue
                    
                    # Arrêter si on rencontre un en-tête évident
                    if any(keyword in line_lower for keyword in header_keywords):
                        if current_block:
                            break
                        i += 1
                        continue
                    
                    # Ignorer les dates et références
                    if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line):
                        if current_block:
                            break
                        i += 1
                        continue
                    if re.match(r'^\d{4}-[A-Z]\d{3}', line):
                        if current_block:
                            break
                        i += 1
                        continue
                    
                    # Si ligne en majuscules significative (≥ 20 chars)
                    # Vérifier si c'est principalement en majuscules (≥ 80% des lettres)
                    letters = [c for c in line if c.isalpha()]
                    upper_letters = [c for c in line if c.isupper()]
                    is_mostly_upper = len(letters) > 0 and (len(upper_letters) / len(letters)) >= 0.8
                    is_long_enough = len(line) >= 20
                    
                    is_upper = is_mostly_upper and is_long_enough
                    is_in_block = len(current_block) > 0
                    
                    # Accepter si majuscules OU si déjà dans un bloc (pour continuer le titre multi-lignes)
                    if is_upper or (is_in_block and len(line) >= 15 and is_mostly_upper):
                        current_block.append(line)
                        i += 1
                    else:
                        # Si on a déjà un bloc, l'arrêter
                        if current_block:
                            break
                        i += 1
                
                # Si on a un bloc de plusieurs lignes en majuscules, c'est probablement le titre
                if len(current_block) >= 1:
                    # Joindre les lignes du bloc
                    block_text = ' '.join(current_block)
                    
                    # Filtrer si trop court ou trop long
                    if 30 <= len(block_text) <= 500:
                        # Score basé sur plusieurs critères
                        score = 0
                        
                        # +15 si toutes les lignes sont principalement en majuscules (≥ 80%)
                        def is_mostly_uppercase(s):
                            letters = [c for c in s if c.isalpha()]
                            if not letters:
                                return False
                            upper_letters = [c for c in s if c.isupper()]
                            return (len(upper_letters) / len(letters)) >= 0.8
                        
                        if all(is_mostly_uppercase(l) for l in current_block if l):
                            score += 15
                        
                        # +10 si c'est un bloc de plusieurs lignes (2+)
                        if len(current_block) >= 2:
                            score += 10
                        
                        # +8 si dans les 15 premières lignes (2ème paragraphe souvent)
                        if start_idx < 15:
                            score += 8
                        
                        # +5 si contient des mots significatifs
                        block_lower = block_text.lower()
                        significant_words = [
                            'prestation', 'formation', 'achat', 'fourniture', 'fournitures',
                            'equipement', 'equipements', 'service', 'services', 'maintenance',
                            'logiciel', 'logiciels', 'materiel', 'consommable', 'mobilier',
                            'installation', 'mise en service', 'ventilation', 'transport',
                            'monitorage', 'localisation'
                        ]
                        if any(word in block_lower for word in significant_words):
                            score += 5
                        
                        # +3 si longueur optimale (50-300 caractères)
                        if 50 <= len(block_text) <= 300:
                            score += 3
                        
                        # -5 si contient trop de mots techniques
                        technical_words = ['page', 'total', 'code', 'article', 'dispositions']
                        tech_count = sum(1 for word in technical_words if word in block_lower)
                        score -= tech_count * 2
                        
                        if score > 0:
                            multi_line_candidates.append((score, block_text, start_idx, len(current_block)))
            
            # 2. Chercher aussi des lignes individuelles en majuscules (fallback)
            for i, line in enumerate(first_lines):
                line = line.strip()
                
                # Ignorer les lignes trop courtes ou trop longues
                if len(line) < 30 or len(line) > 500:
                    continue
                
                # Ignorer les lignes vides
                if not line:
                    continue
                
                # Ignorer les lignes qui sont clairement des en-têtes
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in header_keywords):
                    continue
                
                # Ignorer les lignes qui sont des dates ou références
                if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line):
                    continue
                if re.match(r'^\d{4}-[A-Z]\d{3}', line):
                    continue
                
                # Chercher des lignes principalement en majuscules significatives (titres longs)
                # Vérifier si ≥ 80% des lettres sont en majuscules
                letters = [c for c in line if c.isalpha()]
                if letters:
                    upper_ratio = len([c for c in line if c.isupper() and c.isalpha()]) / len(letters)
                    is_mostly_upper_line = upper_ratio >= 0.8 and len(line) >= 30
                else:
                    is_mostly_upper_line = False
                
                if is_mostly_upper_line:
                    score = 0
                    
                    # +10 si la ligne est en majuscules et longue
                    if len(line) >= 50:
                        score += 10
                    else:
                        score += 5
                    
                    # +5 si elle est dans les 15 premières lignes (2ème paragraphe)
                    if i < 15:
                        score += 5
                    
                    # +5 si elle contient des mots significatifs
                    significant_words = [
                        'prestation', 'formation', 'achat', 'fourniture', 'fournitures',
                        'equipement', 'equipements', 'service', 'services', 'maintenance',
                        'logiciel', 'logiciels', 'installation', 'ventilation'
                    ]
                    if any(word in line_lower for word in significant_words):
                        score += 5
                    
                    # +3 si longueur raisonnable (50-300 caractères)
                    if 50 <= len(line) <= 300:
                        score += 3
                    
                    if score > 0:
                        candidates.append((score, line, i))
            
            # Trier les candidats multi-lignes par score (priorité)
            multi_line_candidates.sort(key=lambda x: (-x[0], x[2]))
            
            # Trier les candidats simples
            candidates.sort(key=lambda x: (-x[0], x[2]))
            
            # Préférer les blocs multi-lignes si score élevé
            if multi_line_candidates and multi_line_candidates[0][0] >= 15:
                best_candidate = multi_line_candidates[0][1]
                logger.debug(f"📄 Titre multi-lignes détecté ({multi_line_candidates[0][3]} lignes)")
            elif candidates:
                best_candidate = candidates[0][1]
                logger.debug(f"📄 Titre ligne unique détecté")
            else:
                return None
            
            # Nettoyer le titre
            cleaned_title = best_candidate.strip()
            # Supprimer les caractères de formatage excessifs
            cleaned_title = re.sub(r'\s+', ' ', cleaned_title)
            # Limiter la longueur si vraiment trop long (garder jusqu'à 400 caractères pour phrases longues)
            if len(cleaned_title) > 400:
                cleaned_title = cleaned_title[:400].rsplit(' ', 1)[0] + '...'
            
            logger.info(f"📄 Titre du document extrait: {cleaned_title[:80]}...")
            return cleaned_title
            
        except Exception as e:
            logger.debug(f"Erreur extraction titre document: {e}")
            return None
    
    def _get_current_timestamp(self) -> str:
        """Retourne le timestamp actuel"""
        from datetime import datetime
        return datetime.now().isoformat()
