import streamlit as st
from typing import List, Dict, Any

def render_hero_card(title: str, subtitle: str, description: str):
    """Renders a large styled hero section card."""
    html = f"""
    <div class="hero-card">
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
        <div class="hero-desc">{description}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_feature_card(icon: str, title: str, description: str):
    """Renders a feature card for the landing page."""
    html = f"""
    <div class="feature-card">
        <div class="feature-icon">{icon}</div>
        <div class="feature-title">{title}</div>
        <div class="feature-desc">{description}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_patient_info_card(data: Dict[str, Any]):
    """Renders the Patient Information Card with tabular metadata."""
    html = f"""
    <div class="card">
        <h4 style="margin-top: 0; margin-bottom: 20px; color: #1E3A8A; display: flex; align-items: center; gap: 8px;">
            👤 Patient Information
        </h4>
        <div class="patient-info-grid">
            <div class="patient-info-item">
                <div class="patient-info-label">Full Name</div>
                <div class="patient-info-value">{data.get('patient_name', 'N/A')}</div>
            </div>
            <div class="patient-info-item">
                <div class="patient-info-label">Age / Gender</div>
                <div class="patient-info-value">{data.get('age', 'N/A')} yrs / {data.get('gender', 'N/A')}</div>
            </div>
            <div class="patient-info-item">
                <div class="patient-info-label">Hospital / Clinic</div>
                <div class="patient-info-value">{data.get('hospital', 'N/A')}</div>
            </div>
            <div class="patient-info-item">
                <div class="patient-info-label">Attending Doctor</div>
                <div class="patient-info-value">{data.get('doctor', 'N/A')}</div>
            </div>
            <div class="patient-info-item">
                <div class="patient-info-label">Report Date</div>
                <div class="patient-info-value">{data.get('date', 'N/A')}</div>
            </div>
            <div class="patient-info-item">
                <div class="patient-info-label">Report ID</div>
                <div class="patient-info-value" style="font-family: monospace; color: #2563EB;">{data.get('id', 'N/A')}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_doctor_notes_card(notes: str):
    """Renders the Doctor's original diagnostic notes."""
    html = f"""
    <div class="card">
        <h4 style="margin-top: 0; margin-bottom: 15px; color: #1E3A8A; display: flex; align-items: center; gap: 8px;">
            📋 Primary Clinician Notes
        </h4>
        <div style="background-color: #F8FAFC; border-left: 4px solid #2563EB; padding: 15px; border-radius: 4px 12px 12px 4px; font-style: italic; color: #334155; line-height: 1.6;">
            "{notes if notes else 'No clinician notes available for this report.'}"
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_ai_summary_card(bullets: List[str]):
    """Renders the AI Medical Summary containing bulleted insights."""
    bullet_items = "".join([f'<li style="margin-bottom: 10px; line-height: 1.5;">{b}</li>' for b in bullets])
    html = f"""
    <div class="card" style="border-left: 5px solid #2563EB;">
        <h4 style="margin-top: 0; margin-bottom: 15px; color: #1E3A8A; display: flex; align-items: center; gap: 8px;">
            🤖 AI Clinical Insights & Summary
        </h4>
        <p style="color: #64748B; font-size: 0.9rem; margin-bottom: 15px;">
            The following diagnostic insights were extracted and simplified by the AI model.
        </p>
        <ul style="padding-left: 20px; color: #1E293B; margin-bottom: 0;">
            {bullet_items if bullet_items else '<li style="color: #64748B;">No summary bullets available.</li>'}
        </ul>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_diet_recommendations_card(diet_data: Dict[str, Any]):
    """Renders customized dietary and lifestyle advisory card."""
    includes = diet_data.get("include", [])
    avoids = diet_data.get("avoid", [])
    hydration = diet_data.get("hydration", "Maintain consistent hydration.")
    
    include_html = "".join([f'<div style="display: flex; gap: 10px; margin-bottom: 8px; font-size: 0.9rem;"><span style="color: #16A34A;">✓</span><span>{item}</span></div>' for item in includes])
    avoid_html = "".join([f'<div style="display: flex; gap: 10px; margin-bottom: 8px; font-size: 0.9rem;"><span style="color: #DC2626;">✗</span><span>{item}</span></div>' for item in avoids])
    
    html = f"""
    <div class="card">
        <h4 style="margin-top: 0; margin-bottom: 20px; color: #1E3A8A; display: flex; align-items: center; gap: 8px;">
            🥗 AI Nutritional Guidance
        </h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px;">
            <div style="background-color: #F0FDF4; border: 1px solid #DCFCE7; border-radius: 12px; padding: 20px;">
                <h5 style="margin-top: 0; margin-bottom: 12px; color: #16A34A; display: flex; align-items: center; gap: 6px;">
                    🟢 Recommended Foods
                </h5>
                {include_html if include_html else '<div style="color: #64748B;">No specific diet inclusions.</div>'}
            </div>
            
            <div style="background-color: #FEF2F2; border: 1px solid #FEE2E2; border-radius: 12px; padding: 20px;">
                <h5 style="margin-top: 0; margin-bottom: 12px; color: #DC2626; display: flex; align-items: center; gap: 6px;">
                    🔴 Foods to Restrict
                </h5>
                {avoid_html if avoid_html else '<div style="color: #64748B;">No specific diet exclusions.</div>'}
            </div>
        </div>
        
        <div style="margin-top: 20px; background-color: #F0F9FF; border: 1px solid #E0F2FE; border-radius: 12px; padding: 15px; display: flex; gap: 12px; align-items: center;">
            <span style="font-size: 1.5rem;">💧</span>
            <div>
                <strong style="color: #0369A1; font-size: 0.9rem;">Hydration Advisory:</strong>
                <p style="margin: 0; font-size: 0.85rem; color: #0284C7; font-weight: 500;">{hydration}</p>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
