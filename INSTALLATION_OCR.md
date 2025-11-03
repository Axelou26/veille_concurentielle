# 📦 Installation des Dépendances OCR

## ✅ Packages Python Installés

Les packages Python suivants sont **déjà installés** :
- ✅ `pytesseract` - Interface Python pour Tesseract OCR
- ✅ `pdf2image` - Conversion PDF vers images
- ✅ `python-dateutil` - Parser de dates amélioré
- ✅ `Pillow` - Traitement d'images
- ✅ `easyocr` - OCR alternatif (pas de dépendances système)

---

## ⚠️ Tesseract OCR (Optionnel mais Recommandé)

Pour utiliser **pytesseract** (plus rapide et précis), vous devez installer Tesseract OCR sur votre système Windows.

### Installation Tesseract sur Windows

1. **Télécharger Tesseract OCR** :
   - Aller sur : https://github.com/UB-Mannheim/tesseract/wiki
   - Télécharger l'installeur Windows (ex: `tesseract-ocr-w64-setup-v5.x.x.exe`)

2. **Installer** :
   - Exécuter l'installeur
   - **Important** : Cochez la case "Add to PATH" pendant l'installation
   - Sélectionner la langue française (fra.traineddata)

3. **Vérifier l'installation** :
   ```powershell
   tesseract --version
   ```

4. **Si Tesseract n'est pas dans le PATH** :
   ```python
   import pytesseract
   # Définir le chemin manuellement (ajuster selon votre installation)
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

---

## 🚀 Utilisation Sans Tesseract

**Bonne nouvelle !** Votre code fonctionne **automatiquement avec EasyOCR** si Tesseract n'est pas disponible.

EasyOCR :
- ✅ **Aucune installation système requise**
- ✅ **Fonctionne immédiatement**
- ✅ **Support français inclus**
- ⚠️ Plus lent au premier lancement (télécharge les modèles)
- ⚠️ Nécessite plus de mémoire

**Votre extracteur utilisera automatiquement EasyOCR si Tesseract n'est pas disponible !**

---

## 📋 Résumé

### État Actuel
- ✅ **Packages Python** : Installés
- ⚠️ **Tesseract OCR** : Non installé (optionnel)
- ✅ **EasyOCR** : Disponible (fonctionne sans installation système)

### Recommandation

**Option 1 : Utiliser EasyOCR (Recommandé pour début)** 
- ✅ Aucune action requise
- ✅ Fonctionne immédiatement
- ⚠️ Premier lancement plus lent

**Option 2 : Installer Tesseract (Pour meilleures performances)**
- ⚠️ Nécessite installation système
- ✅ Plus rapide
- ✅ Moins de mémoire

---

## 🔧 Configuration Automatique

Votre code gère automatiquement le fallback :
1. Essaye d'abord avec **pytesseract** (si Tesseract installé)
2. Sinon, utilise **EasyOCR** automatiquement
3. Si aucun n'est disponible, continue sans OCR

**Aucune configuration manuelle nécessaire !**

---

## ✅ Test Rapide

Pour tester si tout fonctionne :

```python
from extractors.pdf_extractor import PDFExtractor

extractor = PDFExtractor()
# Tester avec un PDF scanné
# L'extraction utilisera automatiquement l'OCR disponible
```

---

## 📝 Note Importante

Les améliorations fonctionnent **même sans OCR** :
- ✅ Normalisation des erreurs OCR (pour textes déjà extraits)
- ✅ Parser de dates amélioré
- ✅ Normalisation des montants
- ✅ Correction automatique des incohérences
- ✅ Cache intelligent
- ✅ Métriques de qualité

L'OCR est **optionnel** et améliore seulement l'extraction des **PDFs scannés**.


