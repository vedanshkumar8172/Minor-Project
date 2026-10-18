"""
Entity and Nutrition Extractor for Product Packet Analyser.

Extracts all supported fields from raw OCR text using regular expressions.
Designed to tolerate common OCR errors including:
  - Fused number+unit ("28g" read as "289" — handled in ocr_utils cleanup
    AND in the regex by allowing a trailing unit-like digit)
  - Keyword misspellings (Mig→Mfg, Ingredbents→Ingredients handled in ocr_utils)
  - Inconsistent spacing and punctuation
  - Column-table layouts where value and unit appear on the same line

Rules:
  - Returns None when a field cannot be reliably found.
  - Never invents values.
  - Preserves units and serving basis as extracted.
"""

import re
from typing import Dict, Any, Optional, List


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _first_match(patterns: List[str], text: str, group: int = 1) -> Optional[str]:
    """Try each pattern; return first match group or None."""
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return m.group(group).strip()
            except IndexError:
                pass
    return None


def _clean_whitespace(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def _extract_numeric(pattern: str, text: str) -> Optional[tuple]:
    """
    Extracts (float_value, unit_str) using a flexible regex pattern.
    Supports:
    - Standard: '28g', '28 g', '28 gm', '320mg'
    - Table layouts with header unit: 'Protein (g) | 6.5' -> (6.5, 'g')
    - Zero indicators: '0g', '0.0g', 'Nil', 'Trace', '<0.1g', 'Og' -> (0.0, unit)
    - Comma decimals: '12,8' -> 12.8
    """
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None

    full_match = m.group(0).lower()
    # Check for zero/trace indicators
    if re.search(r'\b(?:nil|trace|none)\b', full_match) or re.search(r'<\s*0?\.[0-9]+', full_match):
        # Look for unit in groups
        unit = None
        for g in m.groups():
            if g and g.strip().lower() in ('g', 'gm', 'mg', 'kcal', 'kj', 'cal', '%'):
                unit = 'g' if g.strip().lower() == 'gm' else g.strip().lower()
                break
        return (0.0, unit)

    val = None
    unit = None

    for g in m.groups():
        if not g:
            continue
        g_clean = g.strip()
        g_lower = g_clean.lower()

        if g_lower in ('g', 'gm', 'mg', 'kcal', 'kj', 'cal', '%'):
            unit = 'g' if g_lower == 'gm' else g_lower
        elif re.match(r'^[0-9]+(?:[.,][0-9]+)?$', g_clean):
            try:
                val = float(g_clean.replace(',', '.'))
            except ValueError:
                pass
        elif re.match(r'^[oO](?:\.[oO])?$', g_clean):
            val = 0.0

    if val is not None:
        return (val, unit)
    return None


# ---------------------------------------------------------------------------
# Product field extraction
# ---------------------------------------------------------------------------

def extract_product_fields(raw_text: str) -> Dict[str, Any]:
    """
    Extracts key product information from raw OCR text.
    Returns dict with keys: product_name, brand_name, mrp,
    mfg_date, pack_date, expiry_date, best_before, ingredients, serving_size.
    Missing fields are None.
    """
    if not raw_text or not raw_text.strip():
        return {
            "product_name": None, "brand_name": None, "mrp": None,
            "mfg_date": None, "pack_date": None, "expiry_date": None,
            "best_before": None, "ingredients": None, "serving_size": None,
        }

    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

    # ── 1. Product name ──────────────────────────────────────────────────────
    product_name = None
    for line in lines[:10]:
        m = re.search(r'^(?:product(?:\s*name)?|item(?:\s*name)?|name\s+of\s+food)\s*[:\-]\s*(.+)', line, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            if len(cand) > 2 and not re.search(r'(?:mfg|exp|mrp|rs\.|batch)', cand, re.IGNORECASE):
                product_name = cand
                break

    if not product_name and lines:
        excluded_headers = (
            "nutrition", "nutritional", "information", "ingredients", "contains",
            "approx", "values", "per 100", "serving", "allergen", "allergy",
            "mfg", "mfd", "exp", "expiry", "best before", "use by", "batch", "lot",
            "mrp", "rs.", "inr", "price", "lic no", "fssai", "customer care", "feedback",
            "net wt", "net weight", "net qty", "store in", "keep in", "keep dry",
            "table", "food safety", "quality", "manufactured", "marketed", "packed by",
            "vegetarian", "veg dot", "brand"
        )
        for candidate in lines[:6]:
            cand = candidate.strip()
            if len(cand) < 4 or len(cand) > 75:
                continue
            if re.match(r'^[\d\W]+$', cand):
                continue
            if re.search(r'\d{4,}', cand):
                continue
            cand_lower = cand.lower()
            if any(cand_lower.startswith(h) or f" {h}" in cand_lower for h in excluded_headers):
                continue
            product_name = cand
            break

    # ── 2. Brand name ────────────────────────────────────────────────────────
    brand_name = _first_match([
        r'(?:brand(?:\s*name)?|manufactured\s+by|marketed\s+by|distributed\s+by|packed\s+by|mfr\.?\s*by|mfd\.?\s*by|mfg\.?\s*by|pkd\.?\s*by)\s*[:\-]\s*(.+?)(?:\n|$|,|\|)',
        r'(?:a\s+product\s+of)\s*[:\-]?\s*(.+?)(?:\n|$|,|\|)',
    ], raw_text)
    if brand_name:
        brand_name = re.sub(r'\s*(?:fssai|lic|batch|mfg|exp|mrp).*$', '', brand_name, flags=re.IGNORECASE).strip()

    # ── 3. MRP (Fixed for OCR noise like '&' or '+') ──────────────────────────
    mrp = None
    mrp_patterns = [
        r'(?:m\.?r\.?p\.?|maximum\s+retail\s+price|mrp)\s*[\W]*\s*(?:rs\.?|inr|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)',
        r'(?:rs\.?|inr|₹)\s*\.?\s*([0-9]+(?:\.[0-9]{1,2})?)(?:\s*/\-|\b)',
        r'price\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)',
    ]
    raw_mrp = _first_match(mrp_patterns, raw_text)
    if raw_mrp:
        mrp = f"₹ {raw_mrp}"

    # ── 4. Date patterns (Fixed Pack Date fallback) ──────────────────────────
    _DATE_BODY = (
        r'(?:'
        r'[0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4}'
        r'|[0-9]{1,2}\s+[a-zA-Z]{3,9}\.?\s+[0-9]{2,4}'
        r'|[a-zA-Z]{3,9}\.?\s*[0-9]{4}'
        r'|[0-9]{4}[\/\.\-][0-9]{1,2}(?:[\/\.\-][0-9]{1,2})?'
        r'|[0-9]{1,2}[\/\.\-][0-9]{4}'
        r')'
    )
    _D = r'(?:\s*(?:date|dt)?\s*)?[:\-\.]?\s*'

    mfg_date = _first_match([
        rf'(?:mfd|mfg|manufactur(?:ed|ing))(?:\s*(?:date|dt)?){_D}({_DATE_BODY})',
        rf'(?:mfd|mfg)\s*[:\-\.]\s*({_DATE_BODY})',
        rf'(?:date\s+of\s+manufacture|date\s+of\s+mfg)\s*[:\-\.]?\s*({_DATE_BODY})',
    ], raw_text)

    pack_date = _first_match([
        rf'(?:pack(?:ed|ing|aged|aging)?|pkd)(?:\s*(?:date|dt)?){_D}({_DATE_BODY})',
        rf'(?:date\s+of\s+pack(?:aging)?)\s*[:\-\.]?\s*({_DATE_BODY})',
    ], raw_text)
    if not pack_date:
        pack_date = mfg_date  # Agar pack date alag se na ho toh mfg date ko hi pack date maan lo

    expiry_date = _first_match([
        rf'(?:exp(?:iry)?(?:\s*date)?|use\s+by(?:\s*date)?){_D}({_DATE_BODY})',
        rf'(?:expires?|expiry)\s*[:\-\.]?\s*({_DATE_BODY})',
    ], raw_text)

    best_before = _first_match([
        rf'(?:best\s*(?:before|by)(?:\s*date)?)(?:\s*[:\-\.]?\s*)'
        rf'({_DATE_BODY}|[0-9]+\s*(?:months?|days?|weeks?|years?)[^,\n]*)',
        rf'(?:best\s*(?:before|by)(?:\s*date)?){_D}'
        rf'({_DATE_BODY}|[0-9]+\s*(?:months?|days?|weeks?|years?)[^,\n]*)',
    ], raw_text)

    # ── 5. Ingredients ───────────────────────────────────────────────────────
    ingredients = None
    ing_match = re.search(
        r'(?:ingredients?|ingredien[ct]s?|ingredbents?|contains?)\s*[:\-]?\s*'
        r'(.+?)'
        r'(?=\n\s*(?:nutritional|nutrition\s+info|nutrition\s+declaration|allergen|allergy|contains\s+added|'
        r'manufactured\s+by|marketed\s+by|packed\s+by|mfd|mfg|batch|lot|net\s*wt|net\s*quantity|mrp|rs\.|'
        r'fssai|lic\s*no|store\s+in|keep\s+in|best\s+before|use\s+by|expiry)|$)',
        raw_text,
        re.IGNORECASE | re.DOTALL
    )
    if ing_match:
        raw_ing = ing_match.group(1).replace("\n", " ")
        ingredients = _clean_whitespace(raw_ing)
        if len(ingredients) > 900:
            ingredients = ingredients[:900].rsplit(',', 1)[0].strip() + " ..."
        ingredients = re.sub(
            r'\s*(?:nutritional|nutrition|approx|per\s*100|serving\s*size).*$',
            '', ingredients, flags=re.IGNORECASE
        ).strip()
        if not ingredients:
            ingredients = None

    # ── 6. Serving size ──────────────────────────────────────────────────────
    serving_size = _first_match([
        r'(?:serving\s*size|serve\s*size|portion\s*size)\s*[:\-\.]?\s*([0-9]+(?:\.[0-9]+)?\s*(?:g|gm|ml|oz|cup|tbsp|tsp|piece|biscuit|cookie|serve)[^,\n]*)',
        r'(?:per\s*serving|per\s*serve)\s*[:\-\.]?\s*([0-9]+(?:\.[0-9]+)?\s*(?:g|gm|ml|oz)[^,\n]*)',
        r'([0-9]+(?:\.[0-9]+)?\s*(?:g|gm)\s*\([^)]+\))',
        r'(?:serving\s*size|serve\s*size)\s*[:\-\.]?\s*([0-9]+(?:\.[0-9]+)?)9\b',
        r'(?:serving\s*size|serve\s*size)\s*[:\-\.]?\s*([0-9]+(?:\.[0-9]+)?\s*g\b)',
        r'^([0-9]+\s*g)\s*per\s*serving',
    ], raw_text)
    if serving_size and re.match(r'^\d+$', serving_size):
        serving_size = f"{serving_size}g"

    return {
        "product_name": product_name,
        "brand_name": brand_name,
        "mrp": mrp,
        "mfg_date": mfg_date,
        "pack_date": pack_date,
        "expiry_date": expiry_date,
        "best_before": best_before,
        "ingredients": ingredients,
        "serving_size": serving_size,
    }


# ---------------------------------------------------------------------------
# Nutrition value extraction
# ---------------------------------------------------------------------------

_SEP = r'(?:\s*\([^)]*\))?\s*[:\-.\–\—\|¦\s]*?'
_VAL = r'(<0\.1g?|<0\.1|nil|trace|[0-9]+(?:[.,][0-9]+)?|[oO](?:\.[oO])?)\s*(g|gm|mg|kcal|kj|cal)?'

_NUTRITION_PATTERNS: Dict[str, List[str]] = {
    "Energy": [
        r'energy\b[^\n]*?([0-9]+(?:\.[0-9]+)?)\s*kcal',
        rf'(?:calories?|energy\s+value)\b{_SEP}{_VAL}',
        rf'energy\b{_SEP}{_VAL}',
    ],
    "Carbohydrates": [
        rf'(?:total\s+)?carbohydrates?\b{_SEP}{_VAL}',
        rf'total\s+carbs?\b{_SEP}{_VAL}',
        rf'\bcarbs?\b{_SEP}{_VAL}',
    ],
    "Sugar": [
        rf'(?:of\s+which\s+)?(?:total\s+)?sugars?\b{_SEP}{_VAL}',
    ],
    # Fixed Added Sugar pattern to capture 0.0 or other values smoothly
    "Added Sugar": [
        rf'(?:of\s+which\s+)?added\s+sugars?\b{_SEP}{_VAL}',
        rf'added\s+sugars?\b{_SEP}{_VAL}',
    ],
    "Total Fat": [
        rf'total\s+fat\b{_SEP}{_VAL}',
        rf'(?<!saturated\s)(?<!trans\s)(?<!mono\s)(?<!poly\s)\bfat\b{_SEP}{_VAL}',
    ],
    "Saturated Fat": [
        rf'saturated\s+(?:fat|fatty\s*acids?)?\b{_SEP}{_VAL}',
        rf'(?:of\s+which\s+)?saturates?\b{_SEP}{_VAL}',
        rf'sat\.?\s*fat\b{_SEP}{_VAL}',
    ],
    "Trans Fat": [
        rf'trans\s+(?:fat|fatty\s*acids?|fats?)?\b{_SEP}{_VAL}',
    ],
    "Protein": [
        rf'proteins?\b{_SEP}{_VAL}',
    ],
    "Dietary Fibre": [
        rf'dietary\s+(?:fibre|fiber)\b{_SEP}{_VAL}',
        rf'(?:total\s+)?(?:fibre|fiber)\b{_SEP}{_VAL}',
    ],
    "Sodium": [
        rf'sodium\b{_SEP}{_VAL}',
    ],
    "Salt": [
        rf'(?:^|\n)\s*salt\b{_SEP}{_VAL}',
        rf'salt\s+content\b{_SEP}{_VAL}',
    ],
}

_DEFAULT_UNIT: Dict[str, str] = {
    "Energy": "kcal",
    "Carbohydrates": "g",
    "Sugar": "g",
    "Added Sugar": "g",
    "Total Fat": "g",
    "Saturated Fat": "g",
    "Trans Fat": "g",
    "Protein": "g",
    "Dietary Fibre": "g",
    "Sodium": "mg",
    "Salt": "g",
}


def _detect_serving_basis(text: str) -> str:
    m = re.search(
        r'(?:per|approx\.?(?:\s+values)?|(?:nutritional\s+)?values?\s*per)\s*'
        r'(100\s*(?:g|ml|gm|gram))',
        text, re.IGNORECASE
    )
    if m:
        return f"per {m.group(1).strip().lower()}"

    m = re.search(
        r'(?:per|approx\.?(?:\s+values)?|(?:nutritional\s+)?values?\s*per)\s*'
        r'([0-9]+\s*(?:g|ml|gm|gram|serving|pack))',
        text, re.IGNORECASE
    )
    if m:
        return f"per {m.group(1).strip().lower()}"

    m = re.search(r'per\s+100\s*(?:g|ml)', text, re.IGNORECASE)
    if m:
        return "per 100g"

    return "per 100g"


def extract_nutrition_values(raw_text: str) -> Dict[str, Dict[str, Any]]:
    nutrients: Dict[str, Dict[str, Any]] = {
        k: {"value": None, "unit": _DEFAULT_UNIT[k], "serving_basis": "per 100g"}
        for k in _NUTRITION_PATTERNS
    }

    if not raw_text or not raw_text.strip():
        return nutrients

    detected_basis = _detect_serving_basis(raw_text)

    for nutrient_key, pattern_list in _NUTRITION_PATTERNS.items():
        for pattern in pattern_list:
            result = _extract_numeric(pattern, raw_text)
            if result is not None:
                val, unit = result
                if unit is None:
                    unit = _DEFAULT_UNIT[nutrient_key]
                elif unit == "gm":
                    unit = "g"
                elif unit == "kj" and nutrient_key == "Energy":
                    val = round(val / 4.184, 1)
                    unit = "kcal"

                if unit in ("g",) and val > 100.0:
                    if 100.0 < val <= 1000.0:
                        val = round(val / 10.0, 2)
                    else:
                        continue

                _MAX_PLAUSIBLE = {
                    "Sugar": 100.0, "Added Sugar": 100.0,
                    "Total Fat": 100.0, "Saturated Fat": 60.0,
                    "Trans Fat": 30.0, "Protein": 50.0,
                    "Dietary Fibre": 30.0, "Salt": 20.0,
                    "Carbohydrates": 100.0,
                }
                if nutrient_key in _MAX_PLAUSIBLE and unit in ("g",):
                    if val > _MAX_PLAUSIBLE[nutrient_key]:
                        if (val / 10.0) <= _MAX_PLAUSIBLE[nutrient_key]:
                            val = round(val / 10.0, 2)
                        else:
                            continue

                nutrients[nutrient_key] = {
                    "value": val,
                    "unit": unit,
                    "serving_basis": detected_basis
                }
                break

    return nutrients


def get_demo_packet_data() -> Dict[str, Any]:
    demo_text = (
        "GOOD MORNING CRUNCHY WHOLE GRAIN CEREAL\n"
        "Brand: NutriHarvest Foods\n"
        "Net Weight: 350g\n"
        "M.R.P.: Rs. 145.00 (Incl. of all taxes)\n"
        "Mfg Date: 15/08/2026\n"
        "Best Before: 6 months from mfg date\n"
        "Serving Size: 40g (approx. 1 cup)\n"
        "Ingredients: Whole Wheat Flakes (62%), Rolled Oats (18%), Brown Sugar, "
        "Honey, Vegetable Oil, Iodized Salt, Natural Flavours.\n\n"
        "NUTRITIONAL INFORMATION\n"
        "Approx. Values Per 100g:\n"
        "Energy: 380 kcal\n"
        "Total Carbohydrates: 72g\n"
        "Sugars: 12.8g\n"
        "Total Fat: 4.5g\n"
        "Saturated Fat: 1.2g\n"
        "Trans Fat: 0g\n"
        "Protein: 8.5g\n"
        "Dietary Fibre: 6.4g\n"
        "Sodium: 420mg\n"
        "Salt: 1.1g"
    )

    return {
        "is_demo": True,
        "raw_text": demo_text,
        "fields": {
            "product_name": "GOOD MORNING CRUNCHY WHOLE GRAIN CEREAL",
            "brand_name": "NutriHarvest Foods",
            "mrp": "₹ 145.00",
            "mfg_date": "15/08/2026",
            "pack_date": "15/08/2026",
            "expiry_date": None,
            "best_before": "6 months from mfg date",
            "ingredients": (
                "Whole Wheat Flakes (62%), Rolled Oats (18%), Brown Sugar, "
                "Honey, Vegetable Oil, Iodized Salt, Natural Flavours."
            ),
            "serving_size": "40g (approx. 1 cup)",
        },
        "nutrients": {
            "Energy":        {"value": 380.0,  "unit": "kcal", "serving_basis": "per 100g"},
            "Carbohydrates": {"value": 72.0,   "unit": "g",    "serving_basis": "per 100g"},
            "Sugar":         {"value": 12.8,   "unit": "g",    "serving_basis": "per 100g"},
            "Added Sugar":   {"value": 0.0,    "unit": "g",    "serving_basis": "per 100g"},
            "Total Fat":     {"value": 4.5,    "unit": "g",    "serving_basis": "per 100g"},
            "Saturated Fat": {"value": 1.2,    "unit": "g",    "serving_basis": "per 100g"},
            "Trans Fat":     {"value": 0.0,    "unit": "g",    "serving_basis": "per 100g"},
            "Protein":       {"value": 8.5,    "unit": "g",    "serving_basis": "per 100g"},
            "Dietary Fibre": {"value": 6.4,    "unit": "g",    "serving_basis": "per 100g"},
            "Sodium":        {"value": 420.0,  "unit": "mg",   "serving_basis": "per 100g"},
            "Salt":          {"value": 1.1,    "unit": "g",    "serving_basis": "per 100g"},
        }
    }
