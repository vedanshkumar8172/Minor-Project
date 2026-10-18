"""
Product Packet Analyser
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
      Screen 2: Holographic Upload Scanner Chamber (Supports Multi-Image Upload)
      Screen 3: Analysis Results & Nutrition Telemetry Matrix
"""

import os
import time
import streamlit as st
import pandas as pd
from PIL import Image

# Core backend modules
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
    """Renders a realistic floating food package mockup with laser scan line."""
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
    """Renders the landing hero."""
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
Discover product details, ingredients, and nutrition information from packet images.
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
# UI Component: Feature Chips
# ==============================================================================
def render_features():
    """Renders three core feature cards."""
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
# UI Component: How It Works
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
<div class="step-desc">Capture or select multiple packaged food label photos (Front, Back, Nutrition Table).</div>
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
# SCREEN 1: LANDING PAGE
# ==============================================================================
def render_screen_1_landing():
    render_hero()
    render_features()
    render_how_it_works()


# ==============================================================================
# SCREEN 2: MULTI-IMAGE UPLOAD SCANNER CHAMBER
# ==============================================================================
def render_screen_2_upload():
    """Upload chamber interface supporting multiple image uploads (up to 4 images)."""
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
Drop multiple product images into the scanner (Front, Nutrition Table, Dates). We'll combine and extract the details.
</div>
</div>""", unsafe_allow_html=True)

    uploaded_files = st.session_state.get("uploaded_file_obj")

    st.markdown('<div class="scanner-chamber-wrap"><div class="chamber-portal">', unsafe_allow_html=True)

    if not uploaded_files:
        st.markdown("""<div class="chamber-empty-hologram">
<div style="font-size:3.5rem; margin-bottom:12px;">📡</div>
<div style="font-family:'Space Grotesk',sans-serif; font-size:1.3rem; font-weight:700; color:#FFFFFF; margin-bottom:6px;">
Drop Product Images Here
</div>
<div style="font-size:0.86rem; color:#9AA7B5; max-width:380px; margin:0 auto 16px auto;">
Upload 1 to 4 packet label images (JPG, JPEG, or PNG up to 10MB each).
</div>
</div>""", unsafe_allow_html=True)

        new_files = st.file_uploader(
            "CHOOSE PRODUCT IMAGES",
            type=["jpg", "jpeg", "png"],
            key="chamber_uploader",
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if new_files:
            st.session_state["uploaded_file_obj"] = new_files
            st.rerun()

    else:
        if not isinstance(uploaded_files, list):
            uploaded_files = [uploaded_files]

        st.markdown(f"""<div class="preview-chamber-frame">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
<span style="font-family:'JetBrains Mono',monospace; font-size:0.76rem; color:#34D399; font-weight:700;">
● {len(uploaded_files)} PRODUCT IMAGE(S) INGESTED IN CHAMBER
</span>
</div>""", unsafe_allow_html=True)

        cols = st.columns(min(len(uploaded_files), 4))
        for idx, file_obj in enumerate(uploaded_files[:4]):
            with cols[idx]:
                active_img = image_utils.load_image(file_obj)
                st.image(active_img, use_container_width=True)
                st.caption(f"{file_obj.name}")

        st.markdown('</div>', unsafe_allow_html=True)

        st.write("")
        col_act1, col_act2 = st.columns([1.6, 1])
        with col_act1:
            run_ocr = st.button("🔬 ANALYZE LABELS", key="btn_run_analyze_label", use_container_width=True)
        with col_act2:
            if st.button("🗑️ Clear All / Reset", key="btn_remove_chamber", use_container_width=True):
                st.session_state["uploaded_file_obj"] = None
                st.session_state["analysis_results"] = None
                st.rerun()

        if run_ocr:
            st.session_state["is_demo_mode"] = False
            ocr_diag = ocr_utils.check_ocr_availability()

            if not ocr_diag["available"]:
                st.error(f"❌ OCR Engine Unavailable:\n{ocr_diag['message']}")
                st.info("💡 **Demo Available:** Return to the Landing Page and click 'Sample Demo Packet'!")
            else:
                progress_placeholder = st.empty()
                combined_raw_text = ""
                combined_raw_ocr_unclean = ""

                with progress_placeholder.container():
                    st.markdown("""<div class="chamber-terminal">
&gt; [CAMERA] Reading optical sensor array for all frames...<br>
&gt; [PREPROCESS] Normalizing image channels &amp; contrast across photos...
</div>""", unsafe_allow_html=True)
                    time.sleep(0.3)

                for file_obj in uploaded_files[:4]:
                    try:
                        img = image_utils.load_image(file_obj)
                        processed_img = image_utils.preprocess_image_for_ocr(img)
                        ocr_result = ocr_utils.extract_raw_text(processed_img)
                        
                        if ocr_result["success"]:
                            combined_raw_text += "\n" + ocr_result["text"]
                            combined_raw_ocr_unclean += f"\n--- [{file_obj.name}] ---\n" + ocr_result.get("raw_text", "")
                    except Exception as e:
                        st.warning(f"⚠️ Error processing {file_obj.name}: {e}")

                progress_placeholder.empty()

                if not combined_raw_text.strip():
                    st.warning("⚠️ Could not extract readable text from the uploaded images.")
                else:
                    fields = extractor.extract_product_fields(combined_raw_text)
                    nutrients = extractor.extract_nutrition_values(combined_raw_text)
                    risk_analysis = risk_engine.run_full_risk_analysis(
                        nutrients,
                        fields.get("ingredients")
                    )

                    st.session_state["analysis_results"] = {
                        "is_demo": False,
                        "raw_text": combined_raw_text,
                        "raw_ocr_text": combined_raw_ocr_unclean,
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
    risk = results.get("risk_analysis")
    if not risk:
        return

    is_demo = results.get("is_demo", False)

    st.markdown(f"""
<div style="font-family:'Space Grotesk',sans-serif; font-size:1.35rem; font-weight:700;
color:#FFFFFF; margin:28px 0 6px 0; display:flex; align-items:center; gap:8px;">
<span style="color:#F87171;">🚨</span> Nutrition Risk Alerts
</div>
<div style="font-size:0.82rem; color:#9AA7B5; margin-bottom:16px; line-height:1.5;
font-family:'Inter',sans-serif; max-width:820px;">
<strong style="color:#FBBF24;">Educational disclaimer:</strong>
Alerts are informational comparisons against documented reference thresholds.
{'<br><strong style="color:#34D399;">ℹ This is a demonstration with sample data — not a real OCR result.</strong>' if is_demo else ''}
</div>
""", unsafe_allow_html=True)

    quant = risk.get("quantitative_alerts", [])

    if not risk.get("nutrition_available"):
        st.markdown("""<div class="risk-no-data-box">
<span style="font-size:1.1rem;">📊</span>
<div>
<strong>Nutrition facts table not detected in scan</strong>
</div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="font-family:'JetBrains Mono',monospace; font-size:0.74rem;
color:#34D399; letter-spacing:0.1em; font-weight:700; margin-bottom:10px;">
PART A — QUANTITATIVE NUTRITION ALERTS (per 100g thresholds)
</div>""", unsafe_allow_html=True)

        for alert in quant:
            status = alert["status"]
            badge = _risk_badge_html(status)
            border_color = {"HIGH": "rgba(248,113,113,0.45)", "MODERATE": "rgba(251,191,36,0.45)", "OK": "rgba(52,211,153,0.3)"}.get(status, "rgba(100,116,139,0.3)")
            bg_color = {"HIGH": "rgba(248,113,113,0.06)", "MODERATE": "rgba(251,191,36,0.05)", "OK": "rgba(52,211,153,0.04)"}.get(status, "rgba(100,116,139,0.05)")

            expanded_content = ""
            if status in ("HIGH", "MODERATE"):
                expanded_content = f"""
<div class="risk-detail-row"><span class="risk-detail-label">Why this matters</span><span class="risk-detail-text">{alert['why']}</span></div>
<div class="risk-detail-row"><span class="risk-detail-label">Possible long-term risk</span><span class="risk-detail-text" style="color:#FBBF24;">{alert['risk']}</span></div>
<div class="risk-detail-row"><span class="risk-detail-label">Suggestion</span><span class="risk-detail-text" style="color:#A7F3D0;">{alert['suggestion']}</span></div>"""

            st.markdown(f"""
<div style="background:{bg_color}; border:1px solid {border_color}; border-radius:14px; padding:16px 20px; margin-bottom:12px;">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
<div style="font-family:'Space Grotesk',sans-serif; font-size:1.05rem; font-weight:700; color:#FFFFFF;">{alert['nutrient']}</div>
{badge}
</div>
<div style="display:flex; flex-wrap:wrap; gap:20px; margin-top:10px; font-family:'JetBrains Mono',monospace; font-size:0.8rem;">
<span style="color:#E2E8F0;">Value: <strong>{alert['value_display']}</strong></span>
<span style="color:#9AA7B5;">Threshold: {alert['threshold_text']}</span>
</div>
{expanded_content}
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# SCREEN 3: ANALYSIS RESULTS & NUTRITION TELEMETRY
# ==============================================================================
def render_screen_3_results():
    top_col1, _ = st.columns([1, 4])
    with top_col1:
        if st.button("← Scan Another", key="btn_scan_another"):
            go_to_screen("upload")
            st.rerun()

    results = st.session_state.get("analysis_results")
    if not results:
        st.warning("⚠️ No analysis data available.")
        return

    fields = results.get("fields", {})
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
<span>BRAND: <strong style="color:#FFFFFF;">{p_brand}</strong></span> &bull;
<span>MRP: <strong style="color:#FFFFFF;">{p_mrp}</strong></span> &bull;
<span>MFG: <strong style="color:#FFFFFF;">{p_mfg}</strong></span>
</div>
</div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="telemetry-card"><div class="telemetry-label">💳 MRP</div><div class="telemetry-value">{p_mrp}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="telemetry-card"><div class="telemetry-label">🏭 MFG DATE</div><div class="telemetry-value">{p_mfg}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="telemetry-card"><div class="telemetry-label">📦 PACK DATE</div><div class="telemetry-value">{p_pack}</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="telemetry-card"><div class="telemetry-label">⏳ EXPIRY DATE</div><div class="telemetry-value">{p_exp}</div></div>', unsafe_allow_html=True)

    st.write("")

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

    st.markdown("""<div style="font-family:'Space Grotesk',sans-serif; font-size:1.35rem; font-weight:700; color:#FFFFFF; margin-bottom:14px;">
📊 Nutrition Evaluation Matrix (Per 100g Guidelines)
</div>""", unsafe_allow_html=True)

    nutrients_data = results.get("nutrients", {})
    evaluation_rows = nutrition_rules.compare_all_nutrients(nutrients_data)

    rows_html = ""
    for row in evaluation_rows:
        st_type = row["status_type"]
        badge_class = f"status-{st_type}" if st_type in ["success", "alert", "warning", "neutral"] else "status-muted"
        badge_html = f'<span class="status-pill {badge_class}">{row["status"]}</span>'
        ext_display = f"{row['extracted_value']} {row['unit']}" if row['extracted_value'] != "Not detected" else '<span style="color:#64748B; font-style:italic;">Not detected</span>'
        rows_html += f"<tr><td style='font-weight:600; color:#FFFFFF;'>{row['nutrient']}</td><td style='font-family:'JetBrains Mono',monospace;'>{ext_display}</td><td>{row['serving_basis']}</td><td>{row['threshold']}</td><td>{badge_html}</td></tr>"

    st.markdown(f'<table class="cyber-table"><thead><tr><th>Nutrient</th><th>Value</th><th>Basis</th><th>Threshold</th><th>Status</th></tr></thead><tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)

    render_risk_alerts(results)


# ==============================================================================
# Footer & Main Router
# ==============================================================================
def render_footer():
    st.markdown("""<div class="vedanshu-footer">
VEDANSHU &bull; PRODUCT PACKET ANALYSER &bull; INFORMATIONAL PROTOTYPE
</div>""", unsafe_allow_html=True)


render_navbar()
current_screen = st.session_state.get("screen", "landing")

if current_screen == "landing":
    render_screen_1_landing()
elif current_screen == "upload":
    render_screen_2_upload()
elif current_screen == "results":
    render_screen_3_results()

render_footer()
