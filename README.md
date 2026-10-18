# VEDANSHU — Product Packet Analyser

AI-powered food label analysis platform built with Streamlit and Python.
Upload a photo of any packaged food label to extract product details, ingredients,
nutrition values, and receive health-risk alerts with documented reference thresholds.

---

## Features

| Feature | Status |
|---|---|
| Image upload & validation (JPG, JPEG, PNG, up to 10 MB) | ✅ Complete |
| Corruption check on uploaded image | ✅ Complete |
| OpenCV preprocessing (upscale → greyscale → denoise → adaptive threshold) | ✅ Complete |
| Tesseract OCR with Windows auto-path detection | ✅ Complete |
| Multi-PSM OCR (best result kept) | ✅ Complete |
| 19-field extraction (name, brand, MRP, dates, ingredients, serving, 10 nutrients) | ✅ Complete |
| Added Sugar extraction when present | ✅ Complete |
| Per-100g / per-serving basis detection | ✅ Complete |
| Nutrition evaluation matrix (11 nutrients including Added Sugar) | ✅ Complete |
| Nutrition Risk Alerts — HIGH / MODERATE / OK / UNKNOWN | ✅ Complete |
| Per-serving vs per-100g comparison guard (no wrong comparisons) | ✅ Complete |
| Ingredient flags (Palm Oil, Trans Fat, Artificial Colour, MSG, Maida, etc.) | ✅ Complete |
| Missing-field panel (Not detected / Needs review) | ✅ Complete |
| Demo mode (sample cereal packet, no Tesseract needed) | ✅ Complete |
| Raw OCR text viewer (expandable) | ✅ Complete |
| 74-test backend suite (all passing) | ✅ Complete |

---

## Project Structure

```
MINOR PROJECT/
├── app.py               Main Streamlit app — UI, navigation, results screen
├── image_utils.py       Image validation, Pillow loading, OpenCV preprocessing
├── ocr_utils.py         Tesseract availability check + multi-PSM text extraction
├── extractor.py         Regex parsers — 19 product & nutrition fields
├── nutrition_rules.py   11-nutrient threshold engine (per-100g comparisons)
├── risk_engine.py       Nutrition Risk Alert engine (quantitative + ingredient flags)
├── styles.css           Dark design system (CSS variables, alert badge styles)
├── requirements.txt     Python dependencies
├── test_backend.py      74-test backend suite (run without Streamlit)
├── README.md            This file
└── assets/              Place test label images here
```

---

## Quick Start (Windows + VS Code)

### Step 1 — Install Python 3.9+

Download from https://www.python.org/downloads/
**Tick "Add Python to PATH"** during installation.

Verify:
```powershell
py --version
```

### Step 2 — Install Tesseract OCR (required for live scanning)

`pytesseract` is just a Python wrapper. Tesseract is a separate application.

1. Go to: https://github.com/UB-Mannheim/tesseract/wiki
2. Download `tesseract-ocr-w64-setup-5.x.x.exe` (64-bit Windows)
3. Run the installer — keep the default path: `C:\Program Files\Tesseract-OCR\`
4. Close and reopen VS Code after installation

No PATH changes needed. The app auto-detects the default install path.

Verify:
```powershell
tesseract --version
```

### Step 3 — Install Python dependencies

Open a terminal in the `MINOR PROJECT` folder:
```powershell
py -m pip install -r requirements.txt
```

Installs: streamlit, Pillow, pandas, pytesseract, opencv-python, numpy.

### Step 4 — Run the app

```powershell
py -m streamlit run app.py
```

Opens at **http://localhost:8501**

---

## Testing the Backend (No Browser Needed)

```powershell
py test_backend.py
```

All 74 tests run in about 5 seconds. Expected output: `74 passed / 0 failed`.

---

## Testing with a Real Food Packet Image

1. Take a clear photo of any packaged food label (e.g. biscuits, cereal, chips).
2. Make sure the label fills most of the frame and is well-lit with no glare.
3. Click **"Analyze Your Product →"** on the landing page.
4. Upload the image.
5. Click **"🔬 ANALYZE LABEL"**.
6. View extracted product details, nutrition matrix, and risk alerts.

**Tips for good results:**
- Minimum resolution: 800 × 600 px (phone camera photos work well)
- Flat, even lighting; avoid shadows and reflections
- Label text should be sharp and in focus

---

## No Tesseract? Use Demo Mode

Click **"▶ Sample Demo Packet"** on the landing page to see the full analysis with
built-in sample cereal data — no Tesseract installation required.
Demo results are clearly labelled as sample data.

---

## Nutrition Risk Alert — Reference Thresholds

| Nutrient | Status Levels | Threshold | Source |
|---|---|---|---|
| Sugar (total) | HIGH / MODERATE / OK | HIGH > 22.5g, MOD > 5g per 100g | NHS UK traffic-light |
| Saturated Fat | HIGH / MODERATE / OK | HIGH > 5g, MOD > 1.5g per 100g | NHS UK traffic-light |
| Trans Fat | HIGH / MODERATE / OK | HIGH > 2g, MOD > 0.2g per 100g | FSSAI 2022 / WHO |
| Sodium | HIGH / MODERATE / OK | HIGH > 600mg, MOD > 300mg per 100g | NHS UK traffic-light |
| Salt | HIGH / MODERATE / OK | HIGH > 1.5g, MOD > 0.3g per 100g | NHS UK traffic-light |
| Total Fat | HIGH / MODERATE / OK | HIGH > 17.5g, MOD > 3g per 100g | NHS UK traffic-light |

Values on a per-serving basis are never compared to per-100g thresholds.
If the serving basis does not match, the status is UNKNOWN with an explanation.

---

## Ingredient Flags Monitored

Palm Oil · Partially Hydrogenated Oil · High-Fructose Corn Syrup ·
Aspartame · Saccharin · MSG · Artificial Colours (Tartrazine, Sunset Yellow, etc.) ·
Sodium Benzoate · Refined Wheat Flour / Maida · Brown Sugar / Invert Sugar / Dextrose

Flags are raised **only when the term is found in the OCR text**.
Flags are educational notes, not diagnoses.

---

## Known Limitations

- OCR accuracy depends on image quality. Blurry, low-contrast, or angled photos produce less text.
- Some nutrition labels use per-serving values only; these receive UNKNOWN status in risk alerts.
- Extraction uses regex; unusual label layouts may miss some fields.
- Real OCR on a food packet image requires Tesseract to be installed.

---

## Disclaimer

VEDANSHU is an educational college project prototype. Nutrition comparisons use publicly
available reference thresholds (NHS UK, WHO, FSSAI). They are informational only and do not
constitute medical, dietary, or safety advice. Always verify extracted details on the
physical product packaging.
