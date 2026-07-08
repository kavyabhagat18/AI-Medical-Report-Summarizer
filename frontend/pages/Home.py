import streamlit as st
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.footer import render_footer
from components.cards import render_hero_card, render_feature_card

# Render Header / Layout components
render_navbar()
render_sidebar()

# Hero Section
render_hero_card(
    title="Intelligent Health Report Summarizer",
    subtitle="Simpler Medical Reports. Better Health Conversations.",
    description="Upload raw clinical sheets, laboratory blood panels, or scan images. Our medical OCR and Clinical AI engine parses complex diagnostic terms into friendly, actionable health insights within seconds."
)

# Call-to-Action upload button
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    if st.button("✨ Upload Your Medical Report Now", type="primary", use_container_width=True):
        st.switch_page("pages/Upload_Report.py")

st.markdown("<br><br>", unsafe_allow_html=True)

# Features Header
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 25px;">
        <h3 style="color: #1E3A8A; font-weight: 700;">Platform Capabilities</h3>
        <p style="color: #64748B; font-size: 1rem;">Clinical grade tools designed to demystify complex medical documents</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Feature Grid Columns
col_feat1, col_feat2, col_feat3 = st.columns(3)

with col_feat1:
    render_feature_card(
        icon="👁️",
        title="OCR Text Extraction",
        description="Extract structured text from scanned document pages, images, and raw PDFs with clinical-grade accuracy."
    )

with col_feat2:
    render_feature_card(
        icon="🧠",
        title="AI Medical Summary",
        description="Transform complex medical jargon and abbreviations into simple, plain English summaries."
    )

with col_feat3:
    render_feature_card(
        icon="📊",
        title="Diagnostic Extraction",
        description="Isolate laboratory bio-markers, blood panel stats, reference ranges, and highlight flag alerts."
    )

# Feature Grid Row 2
st.markdown("<br>", unsafe_allow_html=True)
col_feat4, col_feat5, col_feat6 = st.columns(3)

with col_feat4:
    render_feature_card(
        icon="🌐",
        title="Instant Translation",
        description="Translate diagnostic findings and doctor's explanations into regional Indian languages instantly."
    )

with col_feat5:
    render_feature_card(
        icon="📥",
        title="PDF Synthesis",
        description="Export structured patient records, blood test grids, and AI recommendations as clinical PDFs."
    )

with col_feat6:
    render_feature_card(
        icon="🔒",
        title="Secure Data Vault",
        description="Compliance-ready security protocols to ensure patient confidentiality and private processing."
    )

st.markdown("<br><br>", unsafe_allow_html=True)

# Workflow Section
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 25px;">
        <h3 style="color: #1E3A8A; font-weight: 700;">How It Works</h3>
        <p style="color: #64748B; font-size: 1rem;">Simple 6-step medical digitization pipeline</p>
    </div>
    """,
    unsafe_allow_html=True
)

workflow_html = """
<div class="workflow-container">
    <div class="workflow-step">
        <span style="font-size: 1.8rem;">📤</span>
        <div style="font-weight: 600; font-size: 0.9rem; margin-top: 8px; color: #1E3A8A;">1. Upload</div>
        <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">PDF, PNG, JPG, TXT</div>
    </div>
    <div class="workflow-arrow">→</div>
    <div class="workflow-step">
        <span style="font-size: 1.8rem;">👁️</span>
        <div style="font-weight: 600; font-size: 0.9rem; margin-top: 8px; color: #1E3A8A;">2. OCR</div>
        <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">Text recognition</div>
    </div>
    <div class="workflow-arrow">→</div>
    <div class="workflow-step">
        <span style="font-size: 1.8rem;">🔍</span>
        <div style="font-weight: 600; font-size: 0.9rem; margin-top: 8px; color: #1E3A8A;">3. Extraction</div>
        <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">Lab values & info</div>
    </div>
    <div class="workflow-arrow">→</div>
    <div class="workflow-step">
        <span style="font-size: 1.8rem;">🧠</span>
        <div style="font-weight: 600; font-size: 0.9rem; margin-top: 8px; color: #1E3A8A;">4. Summary</div>
        <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">AI clinical insights</div>
    </div>
    <div class="workflow-arrow">→</div>
    <div class="workflow-step">
        <span style="font-size: 1.8rem;">🌐</span>
        <div style="font-weight: 600; font-size: 0.9rem; margin-top: 8px; color: #1E3A8A;">5. Translation</div>
        <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">Multi-language support</div>
    </div>
    <div class="workflow-arrow">→</div>
    <div class="workflow-step">
        <span style="font-size: 1.8rem;">📥</span>
        <div style="font-weight: 600; font-size: 0.9rem; margin-top: 8px; color: #1E3A8A;">6. Download</div>
        <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">PDF report copy</div>
    </div>
</div>
"""
st.markdown(workflow_html, unsafe_allow_html=True)

# Render Footer
render_footer()
