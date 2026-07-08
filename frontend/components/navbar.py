import os
import base64
import streamlit as st

def get_base64_image(image_path: str) -> str:
    """Converts a local image file to base64 encoding."""
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            return ""
    return ""

def render_navbar():
    """Renders a premium healthcare-themed navigation bar at the top of the page."""
    # Find logo path relative to app root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(os.path.dirname(current_dir), "assets", "logo.png")
    
    # Check if logo needs to be copied from brain directory
    if not os.path.exists(logo_path):
        brain_logo_path = r"C:\Users\91799\.gemini\antigravity\brain\10a3c72b-f4b3-4bcd-801f-8863f58f1b37\logo_1782824168539.png"
        if os.path.exists(brain_logo_path):
            try:
                import shutil
                os.makedirs(os.path.dirname(logo_path), exist_ok=True)
                shutil.copy(brain_logo_path, logo_path)
            except Exception:
                pass

    # Load custom CSS
    css_path = os.path.join(os.path.dirname(current_dir), "assets", "style.css")
    if os.path.exists(css_path):
        try:
            with open(css_path, "r") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception:
            pass

    logo_base64 = get_base64_image(logo_path)
    
    # Determine current status badge
    status_text = "Idle"
    status_class = "badge-info"
    
    if st.session_state.get("generating_summary", False):
        status_text = "Summarizing"
        status_class = "badge-warning"
    elif st.session_state.get("current_report_id"):
        status_text = "Report Active"
        status_class = "badge-success"
    
    current_lang = st.session_state.get("selected_language", "English")
    
    logo_html = ""
    if logo_base64:
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="40" height="40" style="border-radius: 8px; object-fit: contain;" />'
    else:
        # Fallback icon using styling
        logo_html = '<div style="width: 40px; height: 40px; border-radius: 8px; background-color: #2563EB; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.2rem;">🏥</div>'
        
    navbar_html = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 24px; background-color: #FFFFFF; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 25px; border: 1px solid #E2E8F0;">
        <div style="display: flex; align-items: center; gap: 16px;">
            {logo_html}
            <div>
                <h3 style="margin: 0; color: #1E3A8A; font-weight: 700; font-size: 1.3rem; line-height: 1.2;">HealthPulse AI</h3>
                <span style="font-size: 0.75rem; color: #64748B; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase;">Medical Report Summarizer</span>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 16px;">
            <span class="badge {status_class}">{status_text}</span>
            <div style="display: flex; align-items: center; gap: 6px; background-color: #F1F5F9; padding: 6px 12px; border-radius: 20px; border: 1px solid #E2E8F0;">
                <span style="font-size: 0.85rem; font-weight: 600; color: #475569;">🌐 {current_lang}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(navbar_html, unsafe_allow_html=True)
