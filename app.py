"""
VEDANSHU - Product Packet Analyser
Production-grade AI food label analysis platform.

UI Architecture:
  - styles.css: Single injected design system (CSS variables, responsive scale, button hierarchy)
  - render_navbar(): Top header with brand logo & status badge
  - render_hero(): Center-aligned headline with gradient accent, subtext & primary/secondary CTAs
  - render_packet_mockup(): 3D floating food packet visual with laser scanning animation
  - render_features(): 3 Feature cards (Ingredients, Allergens, Nutrition)
  - render_how_it_works(): 3-step workflow & health score telemetry preview
  - Screens:
      Screen 1: Landing (Hero + Features + How It Works + Health Score)
      Screen 2: Holographic Upload Scanner Chamber
      Screen 3: Analysis Results & Nutrition Telemetry Matrix
"""

import os
import time
import streamlit as st
import pandas as pd
from PIL import Image

# Core backend modules (Preserved untouched)
import image_utils
import ocr_utils
import extractor
import nutrition_rules
import risk_engine

# ==============================================================================
# Page Configuration
# ==============================================================================
st.set_page_config(
    page_title="VEDANSHU | Product Packet Analyser",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ==============================================================================
# CSS Injection Helper
# ==============================================================================
def inject_custom_css():
    """Loads and injects the unified styles.css design system into Streamlit."""
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


inject_custom_css()

# ==============================================================================
# Session State Lifecycle Initialization
# ==============================================================================
if "screen" not in st.session_state:
    st.session_state["screen"] = "landing"

if "uploaded_file_obj" not in st.session_state:
    st.session_state["uploaded_file_obj"] = None

if "analysis_results" not in st.session_state:
    st.session_state["analysis_results"] = None

if "is_demo_mode" not in st.session_state:
    st.session_state["is_demo_mode"] = False


def go_to_screen(target: str):
    """Router helper for navigating between screens."""
    st.session_state["screen"] = target


# ==============================================================================
# UI Component: Top Navigation Bar
# ==============================================================================
def render_navbar():
    """Renders the top branding navigation bar with logo and status badge."""
    nav_html = """<div class="vedanshu-nav-bar">
<div class="brand-wrapper">
<div class="brand-icon">⚡</div>
<span class="brand-logo-text">VEDANSHU</span>
</div>
<div style="display:flex; align-items:center;">
<span class="brand-sub-badge">PRODUCT PACKET ANALYSER</span>
</div>
</div>"""
    st.markdown(nav_html, unsafe_allow_html=True)


# ==============================================================================
# UI Component: Rendered Food Packet Mockup
# ==============================================================================
def render_packet_mockup():
    """
    Renders a realistic floating food package mockup with laser scan line,
    authentic scan badge, AI Core chip, and telemetry strip.
    Eliminates indentation to prevent Streamlit markdown escaping.
    """
    mockup_html = """<div class="mockup-stage-wrap">
<div class="mockup-packet-card">
<div class="mockup-laser-line"></div>
<div class="mockup-header-row">
<span class="mockup-badge-authentic"><span>⚡</span> AUTHENTIC SCAN</span>
<span class="mockup-badge-core">AI CORE</span>
</div>
<div class="mockup-center-graphic">
<div class="mockup-food-icon">🥣</div>
<div class="mockup-product-name">CRUNCHY WHOLE GRAIN</div>
<div class="mockup-product-sub">Oats &amp; Honey &bull; High Fiber</div>
</div>
<div class="mockup-nutrition-strip">
<div class="mockup-nutrient-line">
<span class="mockup-nutrient-label">SUGAR: 12.8g</span>
<span class="mockup-nutrient-status-alert">HIGH</span>
</div>
<div class="mockup-nutrient-line">
<span class="mockup-nutrient-label">FAT: 4.5g</span>
<span class="mockup-nutrient-status-good">WITHIN LIMIT</span>
</div>
<div class="mockup-nutrient-line">
<span class="mockup-nutrient-label">PROTEIN: 7.2g</span>
<span class="mockup-nutrient-status-good">OPTIMAL</span>
</div>
</div>
</div>
</div>"""
    st.markdown(mockup_html, unsafe_allow_html=True)


# ==============================================================================
# UI Component: Hero Section
# ==============================================================================
def render_hero():
    """Renders the landing hero: Eyebrow, Gradient Headline, Subtext, CTAs & Mockup."""
    col_text, col_mockup = st.columns([1.15, 0.85], gap="large")

    with col_text:
        hero_text_html = """<div class="hero-container">
<div class="hero-eyebrow">
<span class="hero-pulse-dot"></span>
AI-POWERED FOOD LABEL DECODER
</div>
<div class="hero-headline">
Analyze your <span class="gradient-text">product.</span>
</div>
<div class="hero-subtext">
Discover product details, ingredients, and nutrition information from a single packet image.
</div>
</div>"""
        st.markdown(hero_text_html, unsafe_allow_html=True)

        btn_col1, btn_col2 = st.columns([1.3, 1.2])
        with btn_col1:
            if st.button("Analyze Your Product →", type="primary", key="cta_go_upload", use_container_width=True):
                go_to_screen("upload")
                st.rerun()

        with btn_col2:
            if st.button("▶ Sample Demo Packet", type="secondary", key="cta_demo_landing", use_container_width=True):
                st.session_state["is_demo_mode"] = True
                demo_data = extractor.get_demo_packet_data()
                demo_data["risk_analysis"] = risk_engine.run_full_risk_analysis(
                    demo_data["nutrients"],
                    demo_data["fields"].get("ingredients")
                )
                st.session_state["analysis_results"] = demo_data
                go_to_screen("results")
                st.rerun()

    with col_mockup:
        render_packet_mockup()


# ==============================================================================
# UI Component: Feature Chips (Ingredients, Allergens, Nutrition)
# ==============================================================================
def render_features():
    """Renders three core feature cards highlighting platform capabilities."""
    st.markdown("""<div class="features-container">
<div class="section-label">CAPABILITIES</div>
<div class="section-title">Precision Insights from Any Package</div>
</div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown("""<div class="feature-card">
<div class="feature-icon-box">🌿</div>
<div class="feature-title">Ingredients Parsing</div>
<div class="feature-desc">Detect hidden sugars, palm oils, artificial sweeteners, and E-number chemical additives instantly.</div>
</div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("""<div class="feature-card">
<div class="feature-icon-box">⚠️</div>
<div class="feature-title">Allergen Detection</div>
<div class="feature-desc">Spot critical allergens including gluten, dairy, peanuts, soy, and shellfish before consumption.</div>
</div>""", unsafe_allow_html=True)

    with c3:
        st.markdown("""<div class="feature-card">
<div class="feature-icon-box">📊</div>
<div class="feature-title">Nutrition Benchmarks</div>
<div class="feature-desc">Compare sugars, saturated fats, and sodium against per-100g regulatory health guidelines.</div>
</div>""", unsafe_allow_html=True)


# ==============================================================================
# UI Component: How It Works & Health Score Preview
# ==============================================================================
def render_how_it_works():
    """Renders 3-step workflow row and interactive sample health-score preview card."""
    st.markdown("""<div class="how-it-works-container">
<div class="section-label">HOW IT WORKS</div>
<div class="section-title">Three Steps to Transparent Nutrition</div>
</div>""", unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3, gap="medium")

    with s1:
        st.markdown("""<div class="step-card">
<span class="step-number">STEP 01</span>
<div class="step-title">Upload Package</div>
<div class="step-desc">Capture or select any packaged food label photo in JPG or PNG format.</div>
</div>""", unsafe_allow_html=True)

    with s2:
        st.markdown("""<div class="step-card">
<span class="step-number">STEP 02</span>
<div class="step-title">Optical AI Analysis</div>
<div class="step-desc">Tesseract OCR extracts tables, ingredient blocks, MRP, and manufacturing dates.</div>
</div>""", unsafe_allow_html=True)

    with s3:
        st.markdown("""<div class="step-card">
<span class="step-number">STEP 03</span>
<div class="step-title">Explore Insights</div>
<div class="step-desc">Receive instant health benchmarks, nutrient thresholds, and allergen tags.</div>
</div>""", unsafe_allow_html=True)

    st.write("")
    # Health Score Preview Card
    preview_score_html = """<div class="health-score-preview-box">
<div class="score-badge-circle">
<div class="score-number-pill">78</div>
<div>
<div class="score-details-heading">Sample Telemetry Preview: Balanced Profile</div>
<div class="score-details-sub">Based on Crunchy Whole Grain Cereal standard 100g nutritional evaluation</div>
</div>
</div>
<div class="score-metrics-strip">
<span class="score-chip score-chip-accent">🌾 High Fiber (+6.4g)</span>
<span class="score-chip score-chip-accent">🛡️ Low Sodium (120mg)</span>
<span class="score-chip" style="color:#FBBF24; border-color:rgba(245,158,11,0.3);">⚠️ Added Sugar (12.8g)</span>
</div>
</div>"""
    st.markdown(preview_score_html, unsafe_allow_html=True)


# ==============================================================================
# SCREEN 1: REDESIGNED LANDING PAGE
# ==============================================================================
def render_screen_1_landing():
    """Composes the full shippable landing page."""
    render_hero()
    render_features()
    render_how_it_works()


# ==============================================================================
# SCREEN 2: HOLOGRAPHIC 3D PRODUCT UPLOAD SCANNER
# ==============================================================================
def render_screen_2_upload():
    """Upload chamber interface preserving existing OCR pipeline and validations."""
    if st.button("← Back to Landing", key="back_to_landing"):
        go_to_screen("landing")
        st.rerun()

    st.markdown("""<div style="text-align:center; max-width:720px; margin:10px auto 30px auto;">
<div style="font-family:'JetBrains Mono',monospace; font-size:0.76rem; color:#34D399; letter-spacing:0.18em; text-transform:uppercase; margin-bottom:6px;">
HOLOGRAPHIC SCANNER CHAMBER
</div>
<div style="font-family:'Space Grotesk',sans-serif; font-size:2.5rem; font-weight:800; color:#FFFFFF; margin-bottom:10px; letter-spacing:-0.02em;">
LET'S ANALYZE YOUR PRODUCT
</div>
<div style="font-size:1.02rem; color:#9AA7B5; line-height:1.6;">
Drop your product into the scanner. We'll extract the details that matter.
</div>
</div>""", unsafe_allow_html=True)

    uploaded_file = st.session_state.get("uploaded_file_obj")

    st.markdown('<div class="scanner-chamber-wrap"><div class="chamber-portal">', unsafe_allow_html=True)

    if uploaded_file is None:
        st.markdown("""<div class="chamber-empty-hologram">
<div style="font-size:3.5rem; margin-bottom:12px;">📡</div>
<div style="font-family:'Space Grotesk',sans-serif; font-size:1.3rem; font-weight:700; color:#FFFFFF; margin-bottom:6px;">
Drop Product Image Here
</div>
<div style="font-size:0.86rem; color:#9AA7B5; max-width:380px; margin:0 auto 16px auto;">
Supports JPG, JPEG, and PNG packet labels up to 10MB.
</div>
</div>""", unsafe_allow_html=True)

        new_file = st.file_uploader(
            "CHOOSE PRODUCT IMAGE",
            type=["jpg", "jpeg", "png"],
            key="chamber_uploader",
            label_visibility="collapsed"
        )
        if new_file is not None:
            st.session_state["uploaded_file_obj"] = new_file
            st.rerun()

    else:
        is_valid, validation_err = image_utils.validate_image_file(uploaded_file)
        if not is_valid:
            st.error(f"❌ {validation_err}")
            if st.button("Try Another File", key="err_reset_btn"):
                st.session_state["uploaded_file_obj"] = None
                st.rerun()
        else:
            active_img = image_utils.load_image(uploaded_file)
            meta = image_utils.get_image_metadata(active_img, uploaded_file.name, uploaded_file.size)

            st.markdown(f"""<div class="preview-chamber-frame">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
<span style="font-family:'JetBrains Mono',monospace; font-size:0.76rem; color:#34D399; font-weight:700;">
● PRODUCT INGESTED IN CHAMBER
</span>
<span style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#9AA7B5;">
{meta['filename']}
</span>
</div>""", unsafe_allow_html=True)

            st.image(active_img, use_container_width=True)

            st.markdown(f"""<div class="meta-chip-row">
<span class="meta-chip"><span>📐</span> RESOLUTION: <strong>{meta['resolution']}</strong></span>
<span class="meta-chip"><span>💾</span> FILE SIZE: <strong>{meta['filesize']}</strong></span>
<span class="meta-chip"><span>🏷️</span> FORMAT: <strong>{meta['format']}</strong></span>
</div>
</div>""", unsafe_allow_html=True)

            st.write("")
            col_act1, col_act2 = st.columns([1.6, 1])
            with col_act1:
                run_ocr = st.button("🔬 ANALYZE LABEL", key="btn_run_analyze_label", use_container_width=True)
            with col_act2:
                if st.button("🗑️ Remove / Replace", key="btn_remove_chamber", use_container_width=True):
                    st.session_state["uploaded_file_obj"] = None
                    st.session_state["analysis_results"] = None
                    st.rerun()

            if run_ocr:
                st.session_state["is_demo_mode"] = False
                ocr_diag = ocr_utils.check_ocr_availability()

                if not ocr_diag["available"]:
                    st.error(f"❌ OCR Engine Unavailable:\n{ocr_diag['message']}")
                    st.info("💡 **Demo Available:** Return to the Landing Page and click 'Sample Demo Packet' to inspect the full results flow with sample cereal data!")
                else:
                    progress_placeholder = st.empty()
                    with progress_placeholder.container():
                        st.markdown("""<div class="chamber-terminal">
&gt; [CAMERA] Reading optical sensor array...<br>
&gt; [PREPROCESS] Normalizing image channels &amp; contrast...
</div>""", unsafe_allow_html=True)
                        time.sleep(0.3)
                        processed_img = image_utils.preprocess_image_for_ocr(active_img)

                    with progress_placeholder.container():
                        st.markdown("""<div class="chamber-terminal">
&gt; [PREPROCESS] Normalizing complete. [OK]<br>
&gt; [OCR] Extracting packaging text with Tesseract...
</div>""", unsafe_allow_html=True)
                        time.sleep(0.3)
                        ocr_result = ocr_utils.extract_raw_text(processed_img)

                    progress_placeholder.empty()

                    if not ocr_result["success"]:
                        st.warning(f"⚠️ {ocr_result['error_message']}")
                        # Still show the raw OCR if we got any text before failure
                        if ocr_result.get("raw_text"):
                            with st.expander("📄 Raw OCR output (for debugging)", expanded=True):
                                st.text_area("Raw OCR", value=ocr_result["raw_text"], height=180,
                                             disabled=True, label_visibility="collapsed")
                    else:
                        extracted_text = ocr_result["text"]
                        raw_ocr_text   = ocr_result.get("raw_text", extracted_text)
                        fields = extractor.extract_product_fields(extracted_text)
                        nutrients = extractor.extract_nutrition_values(extracted_text)
                        risk_analysis = risk_engine.run_full_risk_analysis(
                            nutrients,
                            fields.get("ingredients")
                        )

                        st.session_state["analysis_results"] = {
                            "is_demo": False,
                            "raw_text": extracted_text,     # cleaned text used for extraction
                            "raw_ocr_text": raw_ocr_text,   # unmodified Tesseract output
                            "fields": fields,
                            "nutrients": nutrients,
                            "risk_analysis": risk_analysis,
                        }
                        go_to_screen("results")
                        st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)


# ==============================================================================
# UI Component: Nutrition Risk Alert Panel
# ==============================================================================

def _risk_badge_html(status: str) -> str:
    """Return a small inline badge for a risk status."""
    cfg = {
        "HIGH":     ("risk-badge-high",     "🔴 HIGH"),
        "MODERATE": ("risk-badge-moderate", "🟡 MODERATE"),
        "OK":       ("risk-badge-ok",       "🟢 OK"),
        "UNKNOWN":  ("risk-badge-unknown",  "⬜ UNKNOWN"),
    }
    css, label = cfg.get(status, ("risk-badge-unknown", status))
    return f'<span class="{css}">{label}</span>'


def _ing_badge_html(severity: str) -> str:
    sev_map = {
        "high":     ("risk-badge-high",     "⚠ High Concern"),
        "moderate": ("risk-badge-moderate", "⚡ Moderate Note"),
        "info":     ("risk-badge-info",     "ℹ Info"),
    }
    css, label = sev_map.get(severity, ("risk-badge-info", "Info"))
    return f'<span class="{css}">{label}</span>'


def render_risk_alerts(results: dict) -> None:
    """
    Renders the Nutrition Risk Alert section inside Screen 3.

    Two clearly separated parts:
      A. Quantitative Nutrition Alerts (based on extracted values + thresholds)
      B. Ingredient Flags (based on terms found in OCR ingredients text)

    IMPORTANT: Always displays the educational disclaimer.
    """
    risk = results.get("risk_analysis")
    if not risk:
        return

    is_demo = results.get("is_demo", False)

    # ── Section heading ───────────────────────────────────────────────────────
    st.markdown("""
<div style="font-family:'Space Grotesk',sans-serif; font-size:1.35rem; font-weight:700;
color:#FFFFFF; margin:28px 0 6px 0; display:flex; align-items:center; gap:8px;">
<span style="color:#F87171;">🚨</span> Nutrition Risk Alerts
</div>
<div style="font-size:0.82rem; color:#9AA7B5; margin-bottom:16px; line-height:1.5;
font-family:'Inter',sans-serif; max-width:820px;">
<strong style="color:#FBBF24;">Educational disclaimer:</strong>
Alerts are informational comparisons against documented reference thresholds.
They are <em>not</em> a medical diagnosis, a safety verdict, or a recommendation to avoid any food.
Reference sources are cited for each nutrient below.
{'<br><strong style="color:#34D399;">ℹ This is a demonstration with sample data — not a real OCR result.</strong>' if is_demo else ''}
</div>
""", unsafe_allow_html=True)

    # ── A. Quantitative alerts ────────────────────────────────────────────────
    quant = risk.get("quantitative_alerts", [])

    if not risk.get("nutrition_available"):
        st.markdown("""<div class="risk-no-data-box">
<span style="font-size:1.1rem;">📊</span>
<div>
<strong>Nutrition facts table not detected in scan</strong><br>
<span style="color:#9AA7B5; font-size:0.88rem;">
The optical scan could not locate a nutritional facts table on this packaging image.
If the packet has multiple sides, scan the nutrition facts panel for quantitative benchmarks.
Ingredient flags (below) will still apply if ingredients text was found.
</span>
</div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="font-family:'JetBrains Mono',monospace; font-size:0.74rem;
color:#34D399; letter-spacing:0.1em; font-weight:700; margin-bottom:10px;">
PART A — QUANTITATIVE NUTRITION ALERTS (per 100g thresholds)
</div>""", unsafe_allow_html=True)

        # Distinguish detected alerts, optimal/ok, uncertain basis, and not-detected
        high_alerts       = [a for a in quant if a["status"] == "HIGH"]
        mod_alerts        = [a for a in quant if a["status"] == "MODERATE"]
        ok_alerts         = [a for a in quant if a["status"] == "OK"]
        uncertain_alerts  = [a for a in quant if a["status"] == "UNKNOWN" and a.get("basis_warning")]
        not_detected      = [a for a in quant if a["status"] == "UNKNOWN" and not a.get("basis_warning")]

        actionable_alerts = high_alerts + mod_alerts + ok_alerts + uncertain_alerts

        for alert in actionable_alerts:
            status = alert["status"]
            basis_warn = alert.get("basis_warning")
            badge = _risk_badge_html(status) if not basis_warn else '<span class="risk-badge-moderate">⚠️ UNCERTAIN BASIS</span>'

            # Card border colour by status
            border_color = {
                "HIGH":     "rgba(248,113,113,0.45)",
                "MODERATE": "rgba(251,191,36,0.45)",
                "OK":       "rgba(52,211,153,0.3)",
                "UNKNOWN":  "rgba(251,191,36,0.45)" if basis_warn else "rgba(100,116,139,0.3)",
            }.get(status, "rgba(100,116,139,0.3)")

            bg_color = {
                "HIGH":     "rgba(248,113,113,0.06)",
                "MODERATE": "rgba(251,191,36,0.05)",
                "OK":       "rgba(52,211,153,0.04)",
                "UNKNOWN":  "rgba(251,191,36,0.05)" if basis_warn else "rgba(100,116,139,0.05)",
            }.get(status, "rgba(100,116,139,0.05)")

            # Only show risk/suggestion blocks for HIGH and MODERATE to keep OK compact
            expanded_content = ""
            if status in ("HIGH", "MODERATE"):
                expanded_content = f"""
<div class="risk-detail-row">
<span class="risk-detail-label">Why this matters</span>
<span class="risk-detail-text">{alert['why']}</span>
</div>
<div class="risk-detail-row">
<span class="risk-detail-label">Possible long-term risk</span>
<span class="risk-detail-text" style="color:#FBBF24;">{alert['risk']}</span>
</div>
<div class="risk-detail-row">
<span class="risk-detail-label">Suggestion</span>
<span class="risk-detail-text" style="color:#A7F3D0;">{alert['suggestion']}</span>
</div>"""

            basis_warn_html = ""
            if basis_warn:
                basis_warn_html = f"""
<div style="background:rgba(251,191,36,0.08); border:1px solid rgba(251,191,36,0.3);
border-radius:8px; padding:8px 12px; margin-top:8px; font-size:0.82rem; color:#FDE68A;">
⚠ Serving basis note: {basis_warn}
</div>"""

            st.markdown(f"""
<div style="background:{bg_color}; border:1px solid {border_color};
border-radius:14px; padding:16px 20px; margin-bottom:12px;">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
<div style="font-family:'Space Grotesk',sans-serif; font-size:1.05rem;
font-weight:700; color:#FFFFFF;">{alert['nutrient']}</div>
{badge}
</div>
<div style="display:flex; flex-wrap:wrap; gap:20px; margin-top:10px;
font-family:'JetBrains Mono',monospace; font-size:0.8rem;">
<span style="color:#E2E8F0;">Value: <strong>{alert['value_display']}</strong></span>
<span style="color:#9AA7B5;">Threshold: {alert['threshold_text']}</span>
</div>
<div style="font-size:0.77rem; color:#64748B; margin-top:6px;
font-family:'Inter',sans-serif;">Source: {alert['source']}</div>
{expanded_content}
{basis_warn_html}
</div>
""", unsafe_allow_html=True)

        # Clear, non-intrusive grouping for undetected monitored nutrients
        if not_detected:
            missing_names = ", ".join(f"<code>{a['nutrient']}</code>" for a in not_detected)
            st.markdown(f"""
<div style="background:rgba(100,116,139,0.06); border:1px solid rgba(100,116,139,0.25);
border-radius:12px; padding:12px 16px; margin-bottom:14px; font-size:0.84rem;">
<strong style="color:#94A3B8;">ℹ Monitored nutrients not detected on label:</strong> {missing_names}<br>
<span style="color:#64748B; font-size:0.78rem;">
These nutrients were not identified in the packaging OCR text. No health warnings or assumptions are made for undetected values.
</span>
</div>
""", unsafe_allow_html=True)

    st.write("")

    # ── B. Ingredient flags ───────────────────────────────────────────────────
    ing_flags = risk.get("ingredient_flags", [])

    st.markdown("""<div style="font-family:'JetBrains Mono',monospace; font-size:0.74rem;
color:#34D399; letter-spacing:0.1em; font-weight:700; margin-bottom:10px;">
PART B — INGREDIENT FLAGS (based on terms found in OCR text)
</div>""", unsafe_allow_html=True)

    if not risk.get("ingredients_available"):
        st.markdown("""<div class="risk-no-data-box">
<span style="font-size:1.1rem;">🥗</span>
<div>
<strong>No ingredients text detected</strong><br>
<span style="color:#9AA7B5; font-size:0.88rem;">
Ingredient flags require a readable ingredients list in the OCR output.
</span>
</div>
</div>""", unsafe_allow_html=True)
    elif not ing_flags:
        st.markdown("""<div class="risk-no-data-box" style="border-color:rgba(52,211,153,0.3);
background:rgba(52,211,153,0.04);">
<span style="font-size:1.1rem;">✅</span>
<div>
<strong style="color:#34D399;">No flagged ingredients detected</strong><br>
<span style="color:#9AA7B5; font-size:0.88rem;">
None of the monitored ingredient terms were found in the extracted ingredients text.
This does not mean the product is free of all concerns — it means these specific
monitored terms are not present.
</span>
</div>
</div>""", unsafe_allow_html=True)
    else:
        # Sort: high severity first
        sev_order = {"high": 0, "moderate": 1, "info": 2}
        ing_flags_sorted = sorted(ing_flags, key=lambda f: sev_order.get(f["severity"], 3))

        for flag in ing_flags_sorted:
            sev   = flag["severity"]
            badge = _ing_badge_html(sev)
            border_color = {
                "high":     "rgba(248,113,113,0.4)",
                "moderate": "rgba(251,191,36,0.4)",
                "info":     "rgba(52,211,153,0.25)",
            }.get(sev, "rgba(100,116,139,0.3)")
            bg_color = {
                "high":     "rgba(248,113,113,0.05)",
                "moderate": "rgba(251,191,36,0.04)",
                "info":     "rgba(52,211,153,0.03)",
            }.get(sev, "rgba(100,116,139,0.04)")

            found_str = ", ".join(f"<code>{t}</code>" for t in flag["found_terms"])

            st.markdown(f"""
<div style="background:{bg_color}; border:1px solid {border_color};
border-radius:14px; padding:16px 20px; margin-bottom:12px;">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
<div style="font-family:'Space Grotesk',sans-serif; font-size:1.0rem;
font-weight:700; color:#FFFFFF;">{flag['name']}</div>
{badge}
</div>
<div style="font-size:0.8rem; color:#94A3B8; margin-top:6px;
font-family:'JetBrains Mono',monospace;">
Category: {flag['category']} &nbsp;·&nbsp; Found in label: {found_str}
</div>
<div style="font-size:0.88rem; color:#E2E8F0; margin-top:10px;
line-height:1.6; font-family:'Inter',sans-serif;">{flag['note']}</div>
<div style="font-size:0.84rem; color:#A7F3D0; margin-top:8px;
font-family:'Inter',sans-serif;"><strong>Suggestion:</strong> {flag['suggestion']}</div>
</div>
""", unsafe_allow_html=True)

    # ── Footer note ───────────────────────────────────────────────────────────
    st.markdown("""
<div style="background:rgba(100,116,139,0.06); border:1px solid rgba(100,116,139,0.2);
border-radius:10px; padding:12px 16px; margin-top:8px; font-size:0.8rem;
color:#64748B; line-height:1.6; font-family:'Inter',sans-serif;">
⚠ <strong style="color:#94A3B8;">Important:</strong>
These alerts are educational comparisons against publicly available reference thresholds
(NHS UK, WHO, FSSAI). They are not medical diagnoses, safety guarantees, or dietary prescriptions.
Individual nutritional needs vary. Consult a registered dietitian for personal dietary advice.
Ingredient notes are educational; presence of a flagged ingredient does not mean the product
is harmful at normal serving amounts.
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# SCREEN 3: ANALYSIS RESULTS & NUTRITION TELEMETRY
# ==============================================================================
def render_screen_3_results():
    """Results dashboard displaying detected fields, nutrient matrices, and raw OCR."""
    top_col1, _ = st.columns([1, 4])
    with top_col1:
        if st.button("← Scan Another", key="btn_scan_another"):
            go_to_screen("upload")
            st.rerun()

    results = st.session_state.get("analysis_results")

    if not results:
        st.warning("⚠️ No analysis data available in the current session buffer.")
        if st.button("Go to Scanner"):
            go_to_screen("upload")
            st.rerun()
        return

    fields = results.get("fields", {})

    # ── Pull all fields with safe fallbacks ──────────────────────────────────
    p_name    = fields.get("product_name") or "Not detected"
    p_brand   = fields.get("brand_name")   or "Not detected"
    p_mrp     = fields.get("mrp")          or "Not detected"
    p_mfg     = fields.get("mfg_date")     or "Not detected"
    p_pack    = fields.get("pack_date")    or "Not detected"
    p_exp     = fields.get("expiry_date")  or "Not detected"
    p_best    = fields.get("best_before")  or "Not detected"
    p_ing     = fields.get("ingredients")  or "Not detected"
    p_serving = fields.get("serving_size") or "Not detected"

    name_detected = bool(fields.get("product_name"))

    # ── Hero card ─────────────────────────────────────────────────────────────
    st.markdown(f"""<div class="results-hero-card">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#34D399; font-weight:700; letter-spacing:0.1em;">
EXTRACTED PRODUCT IDENTITY
</span>
<span class="status-pill {'status-success' if name_detected else 'status-muted'}">
{'DETECTED' if name_detected else 'NOT DETECTED'}
</span>
</div>
<div class="product-hero-title">{p_name}</div>
<div style="display:flex; flex-wrap:wrap; gap:16px; font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#9AA7B5; margin-top:6px;">
<span>BRAND: <strong style="color:#FFFFFF;">{p_brand}</strong></span>
<span>&bull;</span>
<span>MRP: <strong style="color:#FFFFFF;">{p_mrp}</strong></span>
<span>&bull;</span>
<span>MFG: <strong style="color:#FFFFFF;">{p_mfg}</strong></span>
<span>&bull;</span>
<span>BEST BEFORE: <strong style="color:#FFFFFF;">{p_best if p_best != "Not detected" else p_exp}</strong></span>
</div>
</div>""", unsafe_allow_html=True)

    # ── Telemetry cards row 1 (MRP, MFG, Pack date, Expiry) ──────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="telemetry-card">
<div class="telemetry-label">💳 MRP / PRICE</div>
<div class="telemetry-value">{p_mrp}</div>
</div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="telemetry-card">
<div class="telemetry-label">🏭 MFG DATE</div>
<div class="telemetry-value">{p_mfg}</div>
</div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="telemetry-card">
<div class="telemetry-label">📦 PACK DATE</div>
<div class="telemetry-value">{p_pack}</div>
</div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="telemetry-card">
<div class="telemetry-label">⏳ EXPIRY DATE</div>
<div class="telemetry-value">{p_exp}</div>
</div>""", unsafe_allow_html=True)

    st.write("")

    # ── Telemetry cards row 2 (Best before, Serving size, Brand, Ingredients count) ──
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.markdown(f"""<div class="telemetry-card">
<div class="telemetry-label">📅 BEST BEFORE</div>
<div class="telemetry-value" style="font-size:1rem;">{p_best}</div>
</div>""", unsafe_allow_html=True)
    with d2:
        st.markdown(f"""<div class="telemetry-card">
<div class="telemetry-label">🥣 SERVING SIZE</div>
<div class="telemetry-value" style="font-size:1rem;">{p_serving}</div>
</div>""", unsafe_allow_html=True)
    with d3:
        st.markdown(f"""<div class="telemetry-card">
<div class="telemetry-label">🏷️ BRAND</div>
<div class="telemetry-value" style="font-size:1rem;">{p_brand}</div>
</div>""", unsafe_allow_html=True)
    with d4:
        ing_count = len(p_ing.split(",")) if fields.get("ingredients") else 0
        st.markdown(f"""<div class="telemetry-card">
<div class="telemetry-label">🌱 INGREDIENTS COUNT</div>
<div class="telemetry-value">{f"{ing_count} detected" if ing_count else "Not detected"}</div>
</div>""", unsafe_allow_html=True)

    st.write("")

    # ── Ingredients block ─────────────────────────────────────────────────────
    st.markdown(f"""<div class="telemetry-card" style="margin-bottom:24px;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
<div class="telemetry-label" style="margin-bottom:0;">🥗 FULL INGREDIENTS LISTING</div>
<span class="status-pill {'status-success' if fields.get('ingredients') else 'status-muted'}">
{'PARSED' if fields.get('ingredients') else 'NOT DETECTED'}
</span>
</div>
<div style="font-size:0.95rem; line-height:1.65; color:{'#F1F5F9' if fields.get('ingredients') else '#64748B'};">
{p_ing}
</div>
</div>""", unsafe_allow_html=True)

    # ── Nutrition matrix heading ───────────────────────────────────────────────
    st.markdown("""<div style="font-family:'Space Grotesk',sans-serif; font-size:1.35rem; font-weight:700; color:#FFFFFF; margin-bottom:14px; display:flex; align-items:center; gap:8px;">
<span style="color:#34D399;">📊</span> Nutrition Evaluation Matrix (Per 100g Guidelines)
</div>""", unsafe_allow_html=True)

    nutrients_data = results.get("nutrients", {})
    evaluation_rows = nutrition_rules.compare_all_nutrients(nutrients_data)

    # ── 5-column metric cards (first 5 nutrients) ─────────────────────────────
    nc1, nc2, nc3, nc4, nc5 = st.columns(5)
    cols_map_a = [nc1, nc2, nc3, nc4, nc5]
    for idx, row in enumerate(evaluation_rows[:5]):
        st_type = row["status_type"]
        badge_class = f"status-{st_type}" if st_type in ["success", "alert", "warning", "neutral"] else "status-muted"
        val_display = (
            f"{row['extracted_value']} {row['unit']}"
            if row['extracted_value'] != "Not detected" else "Not detected"
        )
        val_color = (
            "#F87171" if st_type == "alert"
            else "#34D399" if st_type == "success"
            else "#FBBF24" if st_type == "warning"
            else "#F1F5F9"
        )
        with cols_map_a[idx]:
            st.markdown(f"""<div class="nutrient-metric-box">
<div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#A7F3D0; font-weight:700; text-transform:uppercase;">
{row['nutrient']}
</div>
<div class="nutrient-metric-value" style="color:{val_color};">
{val_display}
</div>
<div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#9AA7B5; margin-bottom:10px;">
BENCHMARK: {row['threshold']}
</div>
<span class="status-pill {badge_class}">{row['status']}</span>
</div>""", unsafe_allow_html=True)

    st.write("")

    # ── Second row of 5 metric cards (nutrients 6-10) ─────────────────────────
    na1, na2, na3, na4, na5 = st.columns(5)
    cols_map_b = [na1, na2, na3, na4, na5]
    for idx, row in enumerate(evaluation_rows[5:]):
        st_type = row["status_type"]
        badge_class = f"status-{st_type}" if st_type in ["success", "alert", "warning", "neutral"] else "status-muted"
        val_display = (
            f"{row['extracted_value']} {row['unit']}"
            if row['extracted_value'] != "Not detected" else "Not detected"
        )
        val_color = (
            "#F87171" if st_type == "alert"
            else "#34D399" if st_type == "success"
            else "#FBBF24" if st_type == "warning"
            else "#F1F5F9"
        )
        with cols_map_b[idx % len(cols_map_b)]:
            st.markdown(f"""<div class="nutrient-metric-box">
<div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#A7F3D0; font-weight:700; text-transform:uppercase;">
{row['nutrient']}
</div>
<div class="nutrient-metric-value" style="color:{val_color};">
{val_display}
</div>
<div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#9AA7B5; margin-bottom:10px;">
BENCHMARK: {row['threshold']}
</div>
<span class="status-pill {badge_class}">{row['status']}</span>
</div>""", unsafe_allow_html=True)

    st.write("")

    # ── Full nutrition table ──────────────────────────────────────────────────
    rows_html = ""
    for row in evaluation_rows:
        st_type = row["status_type"]
        badge_class = f"status-{st_type}" if st_type in ["success", "alert", "warning", "neutral"] else "status-muted"
        badge_html = f'<span class="status-pill {badge_class}">{row["status"]}</span>'
        ext_display = (
            f"{row['extracted_value']} {row['unit']}"
            if row['extracted_value'] != "Not detected"
            else '<span style="color:#64748B; font-style:italic;">Not detected</span>'
        )
        rows_html += f"""<tr>
<td style="font-weight:600; color:#FFFFFF;">{row['nutrient']}</td>
<td style="font-family:'JetBrains Mono',monospace; font-weight:600;">{ext_display}</td>
<td style="color:#9AA7B5; font-family:'JetBrains Mono',monospace;">{row['serving_basis']}</td>
<td style="color:#CBD5E1; font-family:'JetBrains Mono',monospace;">{row['threshold']}</td>
<td>{badge_html}</td>
</tr>"""

    table_full_html = f"""<table class="cyber-table">
<thead>
<tr>
<th>Nutrient Component</th>
<th>Extracted Value</th>
<th>Serving Basis</th>
<th>Configured Threshold</th>
<th>Status</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>"""
    st.markdown(table_full_html, unsafe_allow_html=True)

    # ── Missing / uncertain fields notice ────────────────────────────────────
    missing_fields = [
        name for name, val in {
            "Product Name": fields.get("product_name"),
            "Brand": fields.get("brand_name"),
            "MRP": fields.get("mrp"),
            "Mfg Date": fields.get("mfg_date"),
            "Expiry / Best Before": fields.get("expiry_date") or fields.get("best_before"),
            "Ingredients": fields.get("ingredients"),
            "Serving Size": fields.get("serving_size"),
        }.items()
        if not val
    ]
    missing_nutrients = [
        row["nutrient"] for row in evaluation_rows
        if row["extracted_value"] == "Not detected"
    ]
    all_missing = missing_fields + missing_nutrients
    if all_missing:
        st.write("")
        missing_items_str = ", ".join(all_missing)
        st.markdown(f"""<div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.3);
border-radius:12px; padding:14px 18px; margin-top:4px;">
<span style="font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:#FBBF24; font-weight:700;">
⚠ NOT DETECTED / NEEDS REVIEW
</span>
<div style="font-size:0.88rem; color:#CBD5E1; margin-top:6px; line-height:1.6;">
The following fields could not be reliably extracted from the label:
<strong style="color:#FDE68A;">{missing_items_str}</strong>.<br>
Please verify these directly on the physical product packaging.
</div>
</div>""", unsafe_allow_html=True)

    st.write("")

    # ── Risk Alert section ────────────────────────────────────────────────────
    render_risk_alerts(results)

    st.write("")

    # ── Raw OCR text expander ─────────────────────────────────────────────────
    with st.expander("📄 View Raw Extracted OCR Text", expanded=False):
        raw_stream = results.get("raw_text", "")
        raw_ocr_unclean = results.get("raw_ocr_text", "")
        if not raw_stream.strip():
            st.warning("No readable text detected in current buffer.")
        else:
            if results.get("is_demo"):
                st.caption("💡 Stream sourced from sample demonstration packet (not real OCR output):")
            st.caption("Cleaned text (used for extraction):")
            st.text_area("Cleaned Text Buffer", value=raw_stream, height=180,
                         disabled=True, label_visibility="collapsed", key="cleaned_ocr_ta")
            if raw_ocr_unclean and raw_ocr_unclean != raw_stream:
                st.caption("Raw Tesseract output (before cleanup):")
                st.text_area("Raw OCR Buffer", value=raw_ocr_unclean, height=140,
                             disabled=True, label_visibility="collapsed", key="raw_ocr_ta")


# ==============================================================================
# UI Component: Footer
# ==============================================================================
def render_footer():
    """Renders minimal footer with informational disclaimer."""
    st.markdown("""<div class="vedanshu-footer">
VEDANSHU &bull; PRODUCT PACKET ANALYSER &bull; INFORMATIONAL PROTOTYPE &bull; NOT MEDICAL ADVICE
</div>""", unsafe_allow_html=True)


# ==============================================================================
# Main Router Execution
# ==============================================================================
render_navbar()

current_screen = st.session_state.get("screen", "landing")

if current_screen == "landing":
    render_screen_1_landing()
elif current_screen == "upload":
    render_screen_2_upload()
elif current_screen == "results":
    render_screen_3_results()

render_footer()
