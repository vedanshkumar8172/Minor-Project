"""
OCR module for Product Packet Analyser.
Handles integration with Tesseract OCR (pytesseract).

Windows path configuration:
  Tesseract 5.5.3 is installed at C:\\Program Files\\Tesseract-OCR\\tesseract.exe
  We set the path explicitly so it works regardless of PATH configuration.

OCR strategy:
  - Run multiple PSM passes (6, 4, 11) and pick the richest result.
  - Clean the raw OCR text to fix common character confusions before returning.

Critical rule: never fabricate OCR text. On failure, return success=False.
"""

import os
import re
from typing import Dict, Any
from PIL import Image

# ── Try to import pytesseract ────────────────────────────────────────────────
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

# ── Set Tesseract executable path explicitly ─────────────────────────────────
_WINDOWS_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\pc#\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    r"C:\tesseract\tesseract.exe",
]

if PYTESSERACT_AVAILABLE and os.name == "nt":
    for _candidate in _WINDOWS_TESSERACT_PATHS:
        if os.path.isfile(_candidate):
            pytesseract.pytesseract.tesseract_cmd = _candidate
            break


# ── OCR text normalisation ───────────────────────────────────────────────────

def _clean_ocr_text(raw: str) -> str:
    """
    Cleans raw OCR output to fix common confusions that break regex extraction.

    Rules applied (conservative — only when context is clear):
    - Collapse 3+ blank lines to 2.
    - Fix fused number+unit: "28g" OCR'd as "289" → restore the 'g' so
      downstream regex can match it.  Pattern: a digit sequence ending in
      9/0 that appears on a nutrition-table line gets a space+g appended
      when the last char was likely a fused 'g'.
    - 'Rs.' and common currency OCR errors.
    - Common label keyword fixes (Mig→Mfg, Ingredbents→Ingredients, etc.)
    """
    if not raw:
        return raw

    # ── 1. Normalise line endings ────────────────────────────────────────────
    text = raw.replace('\r\n', '\n').replace('\r', '\n')

    # ── 2. Collapse excessive blank lines ───────────────────────────────────
    text = re.sub(r'\n{3,}', '\n\n', text)

    # ── 3. Fix fused numeric unit: e.g. "489" where last digit is OCR'd 'g'
    #   This is the main cause of wrong nutrition values.
    #   Context: lines that contain kcal/energy/fat/protein/carb/sugar/sodium/salt
    #   Pattern: <digits><optional decimal><optional space><fused-9-or-0>
    #   We only apply this on lines that look like nutrition rows.
    #
    #   Strategy: for each line, if it matches a nutrition label pattern and
    #   the value ends with a digit followed by what should be a unit letter
    #   (OCR as 9 for g, or as 0 for o), we insert a space and the unit.
    #
    #   IMPORTANT: only do this when the number would be unreasonably large
    #   if taken at face value (e.g. 689 kcal is plausible, but 689g fat
    #   is not — however we can't know that without context).
    #   Instead: use a simpler heuristic: on nutrition lines where the OCR
    #   likely fused a 'g' suffix, the number ends in '9' (g→9 is the most
    #   common Tesseract confusion) or the unit is absent.
    #
    # Approach: run nutrition-specific line repair.
    repaired_lines = []
    for line in text.splitlines():
        repaired_lines.append(_repair_nutrition_line(line))
    text = '\n'.join(repaired_lines)

    # ── 4. Fix common keyword OCR errors ───────────────────────────────────
    # Manufacturing date keywords
    text = re.sub(r'\bMig\b', 'Mfg', text)
    text = re.sub(r'\bMig\.\b', 'Mfg.', text)
    text = re.sub(r'\bMtg\b', 'Mfg', text)
    text = re.sub(r'\bMfd\b', 'Mfd', text)  # keep as-is (correct)
    text = re.sub(r'\bDale\b', 'Date', text)
    text = re.sub(r'\bDale:\b', 'Date:', text)

    # Expiry / best before
    text = re.sub(r'\bBes[t!]\b', 'Best', text)
    text = re.sub(r'\bBefore\b', 'Before', text)  # keep
    text = re.sub(r'\bExpiry\b', 'Expiry', text)
    text = re.sub(r'\bExp\b', 'Exp', text)

    # Ingredient heading
    text = re.sub(r'Ingredbents?\s*:', 'Ingredients:', text, flags=re.IGNORECASE)
    text = re.sub(r'Ingredien[st]s?\s*:', 'Ingredients:', text, flags=re.IGNORECASE)
    text = re.sub(r'Ingredien[ct]s?\s*:', 'Ingredients:', text, flags=re.IGNORECASE)

    # MRP / price
    text = re.sub(r'\bPs\.?\s*', 'Rs. ', text)   # Ps → Rs.
    text = re.sub(r'\bMRP:\s*Ps', 'MRP: Rs.', text, flags=re.IGNORECASE)

    # Common letter confusions in ingredient names (conservative)
    text = re.sub(r'\bOnl\b', 'Oil', text)        # Onl → Oil
    text = re.sub(r'\bSail\b', 'Salt', text)      # Sail → Salt
    text = re.sub(r'\bMardal\b', 'Maida', text)   # Mardal → Maida
    text = re.sub(r'\bHydrogenaled\b', 'Hydrogenated', text)
    text = re.sub(r'\bCocea\b', 'Cocoa', text)
    text = re.sub(r'\bCocca\b', 'Cocoa', text)

    # ── 5. Remove stray box-drawing or non-ASCII garbage characters ──────────
    # Keep: printable ASCII + common Indian currency ₹ + basic punctuation
    text = re.sub(r'[^\x20-\x7E₹\n]', ' ', text)
    text = re.sub(r' {3,}', '  ', text)

    return text.strip()


def _score_ocr_quality(text: str) -> float:
    """
    Evaluates OCR output quality based on food-label content and linguistic plausibility,
    rather than raw character length.

    Selecting the longest output (max by len) frequently picks PSM 11 (sparse text)
    which hallucinates repetitive noise symbols, barcode streaks, and garbled characters.
    This scoring function prioritises recognized packaging keywords, plausible words,
    and structured nutrition lines while penalizing symbol noise.
    """
    if not text or not text.strip():
        return 0.0

    score = 0.0
    text_lower = text.lower()

    # Core packaging section landmarks
    high_value_keywords = [
        "nutrition", "nutritional", "ingredients", "ingredient",
        "mrp", "mfg", "mfd", "expiry", "best before", "serving size", "net wt"
    ]
    for kw in high_value_keywords:
        if kw in text_lower:
            score += 25.0

    # Specific nutrient keywords
    nutrient_keywords = [
        "energy", "carbohydrate", "carbohydrates", "carbs", "sugar", "sugars",
        "added sugar", "fat", "saturated", "trans fat", "protein", "proteins",
        "fibre", "fiber", "dietary fibre", "sodium", "salt", "calories"
    ]
    for kw in nutrient_keywords:
        if re.search(rf'\b{re.escape(kw)}\b', text_lower):
            score += 15.0

    # Recognized units and currency
    units = ["kcal", "100g", "100 g", "mg", "₹", "rs.", "rs "]
    for u in units:
        if u in text_lower:
            score += 10.0

    # Bonus for structured nutrient lines: <word> + <number> + <optional unit>
    structured_rows = re.findall(
        r'\b(?:energy|protein|fat|sugar|sodium|salt|carb)\b[^\n\d]*\d+(?:\.\d+)?\s*(?:g|mg|kcal|kj)?',
        text_lower
    )
    score += len(structured_rows) * 12.0

    # Count plausible dictionary/label words (3+ alpha chars)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
    score += min(len(words) * 0.5, 40.0)

    # Penalties for symbol noise and hallucinated character streaks
    total_chars = len(text)
    if total_chars > 0:
        symbols = re.findall(r'[^a-zA-Z0-9\s.,:;()/\-₹]', text)
        symbol_ratio = len(symbols) / total_chars
        if symbol_ratio > 0.15:
            score -= (symbol_ratio - 0.15) * 150.0

    # Penalize repetitive punctuation streaks (common in PSM 11 noise)
    streaks = len(re.findall(r'[|\-_.~=^]{3,}', text))
    score -= streaks * 15.0

    return max(score, 0.0)


def _repair_nutrition_line(line: str) -> str:
    """
    Repairs a single nutrition-table line where Tesseract has fused the unit
    letter into the number digit or confused letters/digits.

    Most common confusions on food labels:
      - 'g' read as '9' (e.g. '28g' -> '289', '25g' -> '259')
      - 'O' or 'o' read for '0' (e.g. 'Og' -> '0g', 'O.Og' -> '0.0g')
      - 'l' or 'I' read for '1' (e.g. 'I.5g' -> '1.5g')
    """
    # Only repair lines that look like nutrition entries
    nutrition_keywords = re.compile(
        r'\b(energy|calories?|carbohydrates?|carbs?|sugars?|fats?|saturated|trans|proteins?|'
        r'fibres?|fibers?|sodium|salt|dietary|serving)\b',
        re.IGNORECASE
    )
    if not nutrition_keywords.search(line):
        return line

    # 1. Fix letter O used as digit 0 in numbers and units
    line = re.sub(r'\bO\.(\d+)', r'0.\1', line)           # O.5 -> 0.5
    line = re.sub(r'(\d+)\.O\b', r'\g<1>.0', line)         # 1.O -> 1.0
    line = re.sub(r'\b[Oo]\s*g\b', '0g', line)             # Og -> 0g
    line = re.sub(r'\b[Oo]\.0\s*g\b', '0.0g', line)        # O.0g -> 0.0g
    line = re.sub(r'\b0\.[Oo]\s*g\b', '0.0g', line)        # 0.Og -> 0.0g

    # 2. Fix letter l or I used as digit 1 in decimals (e.g. I.5g -> 1.5g)
    line = re.sub(r'\b[lI]\.(\d+)\s*(g|mg|kcal)?\b', r'1.\1\2', line)

    # Skip lines with 'kcal' or 'kj' for fused-9 repairs (energy can legitimately exceed 100)
    if re.search(r'\b(kcal|kj|cal)\b', line, re.IGNORECASE):
        return line

    # 3. Fix trailing '9' that was likely an OCR'd 'g'
    def fix_fused_unit(m):
        full_num_str = m.group(0)
        last_char = full_num_str[-1]
        core_num_str = full_num_str[:-1]

        try:
            core_val = float(core_num_str)
            full_val = float(full_num_str)
        except ValueError:
            return full_num_str

        # Case A: Integer fused 'g' — '689' -> '68g', '289' -> '28g', '259' -> '25g'
        if last_char == '9' and core_val <= 100.0 and full_val > 100.0:
            return core_num_str + 'g'

        # Case B: Decimal fused 'g' — '1.59' where core is '1.5' -> '1.5g'
        if '.' in core_num_str and last_char == '9':
            parts = core_num_str.split('.')
            if len(parts) == 2 and len(parts[1]) == 1:
                return core_num_str + 'g'

        return full_num_str

    repaired = re.sub(
        r'\b(\d+(?:\.\d+)?)\b(?!\s*(?:g|mg|ml|kcal|kj|%|gm))',
        fix_fused_unit,
        line
    )
    return repaired


def _clean_ocr_text(raw: str) -> str:
    """
    Cleans raw OCR output to fix common confusions that break regex extraction.
    """
    if not raw:
        return raw

    # ── 1. Normalise line endings ────────────────────────────────────────────
    text = raw.replace('\r\n', '\n').replace('\r', '\n')

    # ── 2. Collapse excessive blank lines ───────────────────────────────────
    text = re.sub(r'\n{3,}', '\n\n', text)

    # ── 3. Run nutrition-specific line repair ─────────────────────────────────
    repaired_lines = []
    for line in text.splitlines():
        repaired_lines.append(_repair_nutrition_line(line))
    text = '\n'.join(repaired_lines)

    # ── 4. Fix common keyword OCR errors ───────────────────────────────────
    # Manufacturing date keywords
    text = re.sub(r'\bMig\b', 'Mfg', text)
    text = re.sub(r'\bMig\.\b', 'Mfg.', text)
    text = re.sub(r'\bMtg\b', 'Mfg', text)
    text = re.sub(r'\bDale\b', 'Date', text)
    text = re.sub(r'\bDale:\b', 'Date:', text)

    # Expiry / best before
    text = re.sub(r'\bBes[t!1]\b', 'Best', text)
    text = re.sub(r'\bBefore\b', 'Before', text)
    text = re.sub(r'\bExpiry\b', 'Expiry', text)
    text = re.sub(r'\bExp\b', 'Exp', text)

    # Ingredient heading
    text = re.sub(r'Ingredbents?\s*:', 'Ingredients:', text, flags=re.IGNORECASE)
    text = re.sub(r'Ingredien[st]s?\s*:', 'Ingredients:', text, flags=re.IGNORECASE)
    text = re.sub(r'Ingredien[ct]s?\s*:', 'Ingredients:', text, flags=re.IGNORECASE)

    # MRP / price
    text = re.sub(r'\bPs\.?\s*', 'Rs. ', text)   # Ps -> Rs.
    text = re.sub(r'\bMRP:\s*Ps', 'MRP: Rs.', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMAP:\s*', 'MRP: ', text, flags=re.IGNORECASE)

    # Common letter confusions in ingredient names
    text = re.sub(r'\bOnl\b', 'Oil', text)
    text = re.sub(r'\bSail\b', 'Salt', text)
    text = re.sub(r'\bMardal\b', 'Maida', text)
    text = re.sub(r'\bHydrogenaled\b', 'Hydrogenated', text)
    text = re.sub(r'\bCocea\b', 'Cocoa', text)
    text = re.sub(r'\bCocca\b', 'Cocoa', text)

    # ── 5. Clean stray box-drawing or non-ASCII garbage characters ──────────
    text = re.sub(r'[^\x20-\x7E₹\n]', ' ', text)
    text = re.sub(r' {3,}', '  ', text)

    return text.strip()


def check_ocr_availability() -> Dict[str, Any]:
    """
    Checks if pytesseract and the Tesseract binary are both available.
    """
    if not PYTESSERACT_AVAILABLE:
        return {
            "available": False,
            "engine": "Tesseract OCR",
            "message": (
                "The Python package 'pytesseract' is not installed.\n\n"
                "Fix: open a terminal in your project folder and run:\n"
                "  pip install pytesseract opencv-python\n\n"
                "You also need the Tesseract application installed separately — "
                "see README.md for the download link."
            )
        }

    try:
        version = pytesseract.get_tesseract_version()
        return {
            "available": True,
            "engine": f"Tesseract OCR v{version}",
            "message": "OCR engine is ready and active."
        }
    except pytesseract.TesseractNotFoundError:
        return {
            "available": False,
            "engine": "Tesseract OCR",
            "message": (
                "Tesseract OCR is not installed or could not be found.\n\n"
                "Windows installation steps:\n"
                "1. Download the installer from:\n"
                "   https://github.com/UB-Mannheim/tesseract/wiki\n"
                "   (choose tesseract-ocr-w64-setup-5.x.x.exe for 64-bit Windows)\n"
                "2. Run the installer — keep the default install path:\n"
                "   C:\\Program Files\\Tesseract-OCR\\\n"
                "3. Restart your terminal / VS Code after installation.\n\n"
                "You can still use 'Sample Demo Packet' on the landing page to see\n"
                "the full analysis flow without Tesseract installed."
            )
        }
    except Exception as exc:
        return {
            "available": False,
            "engine": "Tesseract OCR",
            "message": f"Unexpected error checking Tesseract: {exc}"
        }


def extract_raw_text(image: Image.Image) -> Dict[str, Any]:
    """
    Runs Tesseract OCR on a PIL Image and returns the cleaned extracted text.

    Multi-pass strategy:
    - Runs structured page segmentation modes (PSM 6: uniform block, PSM 4: single column,
      PSM 3: fully automatic layout).
    - If needed, evaluates soft-enhanced variant to avoid contrast degradation.
    - Selects the best result using _score_ocr_quality() rather than raw character length
      (which prevents selecting noisy, hallucinated text from PSM 11).
    - Applies _clean_ocr_text() to repair known OCR confusions.
    """
    status = check_ocr_availability()
    if not status["available"]:
        return {
            "success": False,
            "text": "",
            "raw_text": "",
            "error_message": status["message"]
        }

    try:
        candidates = []

        # PSM 6: uniform block (optimal for nutrition tables and structured paragraphs)
        # PSM 4: single column variable text (good for tall label columns)
        # PSM 3: fully automatic layout analysis
        psm_modes = (6, 4, 3)

        for psm in psm_modes:
            config = f"--oem 3 --psm {psm}"
            try:
                txt = pytesseract.image_to_string(image, config=config, lang="eng")
                txt = txt.strip()
                if txt:
                    score = _score_ocr_quality(txt)
                    candidates.append((score, txt))
            except Exception:
                continue

        # If standard modes found very little text, try sparse text PSM 11 as fallback
        if not candidates or max(s for s, _ in candidates) < 20.0:
            try:
                txt_11 = pytesseract.image_to_string(image, config="--oem 3 --psm 11", lang="eng").strip()
                if txt_11:
                    candidates.append((_score_ocr_quality(txt_11), txt_11))
            except Exception:
                pass

        if not candidates:
            return {
                "success": False,
                "text": "",
                "raw_text": "",
                "error_message": (
                    "OCR processed the image but could not extract any readable text.\n\n"
                    "Tips for better results:\n"
                    "• Use a well-lit, sharp photo with the label filling most of the frame.\n"
                    "• Avoid glare, shadows, and extreme angles.\n"
                    "• Minimum recommended resolution: 1000 × 800 px.\n"
                    "• Hold the phone/camera steady and as parallel to the label as possible."
                )
            }

        # Select candidate with the HIGHEST QUALITY SCORE (not merely longest string)
        best_score, best_raw = max(candidates, key=lambda item: item[0])
        cleaned = _clean_ocr_text(best_raw)

        if not cleaned.strip():
            return {
                "success": False,
                "text": "",
                "raw_text": best_raw,
                "error_message": "OCR returned text that was entirely noise after cleaning."
            }

        return {
            "success": True,
            "text": cleaned,
            "raw_text": best_raw,
            "error_message": None
        }

    except Exception as exc:
        return {
            "success": False,
            "text": "",
            "raw_text": "",
            "error_message": f"An unexpected error occurred during OCR: {exc}"
        }
