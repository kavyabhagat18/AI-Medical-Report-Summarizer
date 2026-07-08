import streamlit as st
import time
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.footer import render_footer
from components.cards import (
    render_patient_info_card,
    render_doctor_notes_card,
    render_ai_summary_card,
    render_diet_recommendations_card
)
from utils.api_client import get_summary, translate_summary, download_pdf

def get_status_badge(status: str) -> str:
    """Returns HTML markup for custom colored badges based on test result status."""
    status_lower = status.lower()
    if status_lower in ["normal", "stable", "optimal"]:
        return f'<span class="badge badge-success">{status}</span>'
    elif status_lower in ["low", "borderline", "caution"]:
        return f'<span class="badge badge-warning">{status}</span>'
    elif status_lower in ["high", "critical", "danger"]:
        return f'<span class="badge badge-danger">{status}</span>'
    else:
        return f'<span class="badge badge-info">{status}</span>'

# Render layouts
render_navbar()
render_sidebar()

# Page title
st.markdown(
    """
    <div style="margin-bottom: 25px;">
        <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 5px;">Diagnostic Synthesis Summary</h2>
        <p style="color: #64748B; margin-top: 0; font-size: 1rem;">
            Review structured lab parameters, clinical indicators, and AI-generated insights.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Determine Report ID
report_id = st.session_state.get("current_report_id")

if report_id:
    col_hdr1, col_hdr2 = st.columns([3, 1])
    with col_hdr1:
        st.info(f"📋 Currently viewing uploaded report: **{report_id}**")
    with col_hdr2:
        if st.button("Clear View", use_container_width=True):
            st.session_state.pop("current_report_id", None)
            st.session_state.pop("translation", None)
            st.rerun()
else:
    # Patient Selection for Mock Visualizations if no report is active
    st.markdown('<div class="card" style="padding: 15px; margin-bottom: 20px;">', unsafe_allow_html=True)
    col_toggle, col_desc = st.columns([1.5, 2.5])
    with col_toggle:
        patient_choice = st.selectbox(
            "👥 Select Mock Patient Profile:",
            options=["Rahul Sharma (Diabetes Panel)", "Jane Smith (Lipid/Thyroid Panel)"]
        )
    with col_desc:
        st.markdown(
            """
            <div style="font-size: 0.85rem; color: #64748B; padding-top: 10px;">
                ℹ️ <strong>Mock View Toggle</strong>: Switch between patient profiles to verify table rendering rules, status flag badge styling, and layout flows.
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
    report_id = "rep_001" if "Rahul" in patient_choice else "rep_002"

# Fetch Summary
try:
    report = get_summary(report_id)
except Exception as e:
    st.warning(f"⚠️ Unable to reach FastAPI backend. Loading local mock profile for simulation.")
    # Local mock data fallback
    if report_id == "rep_001":
        report = {
            "id": "rep_001",
            "date": "2026-06-30",
            "patient_name": "Rahul Sharma",
            "age": 45,
            "gender": "Male",
            "report_type": "Comprehensive Blood & Diabetic Panel",
            "hospital": "Apollo Hospitals, Delhi",
            "doctor": "Dr. A. K. Sen",
            "summary": "Patient exhibits uncontrolled diabetic indicators marked by elevated fasting blood glucose.",
            "status": "Completed",
            "lab_results": [
                {"test": "Fasting Blood Sugar", "value": "165", "unit": "mg/dL", "reference": "70 - 99", "status": "High"},
                {"test": "HbA1c (Glycated Hemoglobin)", "value": "8.1", "unit": "%", "reference": "< 5.7", "status": "High"},
                {"test": "Vitamin D (25-OH)", "value": "18", "unit": "ng/mL", "reference": "30 - 100", "status": "Low"}
            ],
            "doctor_notes": "Patient has uncontrolled diabetes. Advised immediate dietary restriction.",
            "ai_summary": [
                "Metabolic Marker: Fasting Blood Sugar (165 mg/dL) and HbA1c (8.1%) are significantly elevated.",
                "Nutritional Marker: Vitamin D level (18 ng/mL) indicates clinical deficiency.",
                "Actionable Guidance: Restrict simple carbohydrates and sweets."
            ],
            "diet_recommendations": {
                "include": ["Soluble fiber-rich foods", "Green leafy vegetables", "Lean protein sources"],
                "avoid": ["Simple sugars", "Refined flour", "Saturated fats"],
                "hydration": "Drink 2.5 - 3 liters of water daily."
            }
        }
    else:
        report = {
            "id": "rep_002",
            "date": "2026-06-28",
            "patient_name": "Jane Smith",
            "age": 32,
            "gender": "Female",
            "report_type": "Lipid Profile & Thyroid Panel",
            "hospital": "Metro Health Clinic",
            "doctor": "Dr. Evelyn Vance",
            "summary": "Borderline high total cholesterol and elevated LDL levels.",
            "status": "Completed",
            "lab_results": [
                {"test": "Total Cholesterol", "value": "215", "unit": "mg/dL", "reference": "< 200", "status": "High"},
                {"test": "LDL Cholesterol", "value": "135", "unit": "mg/dL", "reference": "< 100", "status": "High"}
            ],
            "doctor_notes": "Mild hyperlipidemia and subclinical hypothyroidism.",
            "ai_summary": [
                "Cardiovascular Risk: Total cholesterol (215 mg/dL) and LDL (135 mg/dL) are elevated.",
                "Endocrine Status: TSH is slightly elevated, suggestive of subclinical hypothyroidism."
            ],
            "diet_recommendations": {
                "include": ["Soluble fiber oats", "Omega-3 rich foods", "Olive oil"],
                "avoid": ["Saturated fats", "Trans-fats"],
                "hydration": "Maintain consistent intake of water."
            }
        }

# 1. Patient Metadata Card
render_patient_info_card(report)

# 2. Lab Results Table Section
table_rows = []
for result in report.get("lab_results", []):
    badge = get_status_badge(result.get("status", "Normal"))
    row = f"""<tr>
<td style="font-weight: 600; color: #1E293B;">{result.get('test')}</td>
<td style="font-weight: 700; color: #2563EB;">{result.get('value')} {result.get('unit', '')}</td>
<td style="font-family: monospace; color: #475569;">{result.get('reference')}</td>
<td>{badge}</td>
</tr>"""
    table_rows.append(row)
    
table_html = f"""<div class="card">
<h4 style="margin-top: 0; margin-bottom: 10px; color: #1E3A8A; display: flex; align-items: center; gap: 8px;">
🔬 Laboratory Analyte Profile
</h4>
<p style="color: #64748B; font-size: 0.85rem; margin-bottom: 20px;">
Biochemical test values extracted from the document, comparing results against standard reference intervals.
</p>
<table class="medical-table">
<thead>
<tr>
<th>Test / Biomarker</th>
<th>Measured Value</th>
<th>Standard Reference Range</th>
<th>Status Evaluation</th>
</tr>
</thead>
<tbody>
{"".join(table_rows) if table_rows else "<tr><td colspan='4' style='text-align: center; color: #94A3B8;'>No parameters extracted.</td></tr>"}
</tbody>
</table>
</div>"""
st.markdown(table_html, unsafe_allow_html=True)

# Handle active translation swap
selected_lang = st.session_state.get("selected_language", "English")
doctor_notes = report.get("doctor_notes", "")
diet_recs = report.get("diet_recommendations", {})
ai_bullets = report.get("ai_summary", [])
translation_data = None

if st.session_state.get("translation") and st.session_state["translation"].get("language") == selected_lang:
    translation_data = st.session_state["translation"]
    doctor_notes = translation_data.get("translated_doctor_notes") or doctor_notes
    diet_recs = translation_data.get("translated_diet_recommendations") or diet_recs
    ai_bullets = translation_data.get("translated_bullets") or ai_bullets

# 3. Doctor Notes Card
render_doctor_notes_card(doctor_notes)

# 4. AI Summary Card Section
if translation_data:
    st.markdown(
        f"""
        <div style="background-color: #F0FDF4; border-left: 4px solid #16A34A; padding: 15px; margin-bottom: 20px; border-radius: 8px;">
            <strong style="color: #16A34A;">Translated Overview Summary ({selected_lang}):</strong>
            <p style="margin: 5px 0 0 0; color: #1E293B; font-style: italic; font-size: 0.95rem;">
                "{translation_data.get('translated_text')}"
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

render_ai_summary_card(ai_bullets)

# 5. Diet Recommendations Card
render_diet_recommendations_card(diet_recs)

# Action Buttons block
st.markdown("<br><hr style='border-top: 1px solid #E2E8F0;'><br>", unsafe_allow_html=True)

# UI controls for Translation and PDF actions
col_lang, col_action_btns = st.columns([1.5, 2.5])

with col_lang:
    selected_lang = st.selectbox(
        "🌐 Choose Target Language:",
        options=["English", "Hindi", "Telugu", "Tamil"],
        index=["English", "Hindi", "Telugu", "Tamil"].index(selected_lang) if selected_lang in ["English", "Hindi", "Telugu", "Tamil"] else 0
    )
    st.session_state["selected_language"] = selected_lang
    
    if st.button("Translate Summary", use_container_width=True):
        if selected_lang == "English":
            st.session_state["translation"] = None
            st.info("ℹ️ English is already selected. No translation required.")
            st.rerun()
        else:
            with st.spinner(f"Translating summary to {selected_lang}..."):
                result = translate_summary(report_id, selected_lang)
                if result.get("success"):
                    st.session_state["translation"] = result
                    st.success(f"✅ Summary translated to {selected_lang} successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Translation failed: {result.get('translated_text')}")

with col_action_btns:
    st.write("📂 **Available Actions**")
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        try:
            pdf_bytes = download_pdf(report_id)
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"{report.get('patient_name', 'Patient')}_Report.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            if st.button("📥 Download PDF", type="primary", use_container_width=True):
                st.error(f"PDF download unavailable: {e}")
            
    with btn_col2:
        if st.button("📤 Upload Another Report", use_container_width=True):
            st.session_state.pop("current_report_id", None)
            st.session_state.pop("translation", None)
            st.switch_page("pages/Upload_Report.py")
            st.rerun()

# Render footer
render_footer()
