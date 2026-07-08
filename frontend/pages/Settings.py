import streamlit as st
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.footer import render_footer

# Render headers / layout
render_navbar()
render_sidebar()

# Check and show settings success message after rerun
if st.session_state.pop("settings_saved", False):
    st.success("✅ Application configuration updated successfully!")

# Page title
st.markdown(
    """
    <div style="margin-bottom: 25px;">
        <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 5px;">Dashboard Settings & Profile</h2>
        <p style="color: #64748B; margin-top: 0; font-size: 1rem;">
            Customize translation parameters, system themes, notifications, and review client licensing details.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Settings Form layout in a beautiful card
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("<h4 style='color: #1E3A8A; margin-top: 0;'>⚙️ System Configuration</h4>", unsafe_allow_html=True)

# Language Select (Direct session state key binding)
languages = ["English", "Hindi", "Telugu", "Tamil"]
st.selectbox(
    "🌐 Default Synthesis Language",
    options=languages,
    key="selected_language",
    help="Select the default translation output language for AI reports and diagnostic insights."
)

# Theme Select (Direct session state key binding)
themes = ["Light", "Dark"]
st.selectbox(
    "🌓 Workspace Theme Mode",
    options=themes,
    key="theme",
    help="Toggle between light theme colors and dark high-contrast mode."
)

# Notification Toggle (Direct session state key binding)
st.toggle(
    "🔔 Enable Real-Time Desktop Notifications",
    key="notifications",
    help="Enable audio alerts and status notifications during OCR generation and translation compiles."
)

# Save settings action
if st.button("💾 Apply Configuration", type="primary"):
    st.session_state["settings_saved"] = True
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# About Application Section
st.markdown('<div class="card" style="margin-top: 25px;">', unsafe_allow_html=True)
st.markdown(
    """
    <h4 style="color: #1E3A8A; margin-top: 0; margin-bottom: 15px;">🛡️ Compliance & Core System Specifications</h4>
    <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem; color: #334155;">
        <tr style="border-bottom: 1px solid #F1F5F9;">
            <td style="padding: 10px 0; font-weight: 600; color: #64748B;">Application Version</td>
            <td style="padding: 10px 0; text-align: right; font-weight: 700; color: #1E293B;">v1.0.0-Stable</td>
        </tr>
        <tr style="border-bottom: 1px solid #F1F5F9;">
            <td style="padding: 10px 0; font-weight: 600; color: #64748B;">Clinical NLP Engine</td>
            <td style="padding: 10px 0; text-align: right; color: #2563EB; font-weight: 500;">Med-PaLM-2 Custom Adapter</td>
        </tr>
        <tr style="border-bottom: 1px solid #F1F5F9;">
            <td style="padding: 10px 0; font-weight: 600; color: #64748B;">OCR Module</td>
            <td style="padding: 10px 0; text-align: right; color: #16A34A; font-weight: 500;">Tesseract Engine V5 / Vision-OCR API</td>
        </tr>
        <tr style="border-bottom: 1px solid #F1F5F9;">
            <td style="padding: 10px 0; font-weight: 600; color: #64748B;">HIPAA Encryption Status</td>
            <td style="padding: 10px 0; text-align: right;"><span class="badge badge-success">Enabled (AES-256 Mock)</span></td>
        </tr>
        <tr>
            <td style="padding: 10px 0; font-weight: 600; color: #64748B;">Developer Support Contacts</td>
            <td style="padding: 10px 0; text-align: right; color: #475569;">health-pulse-devs@stjude.org</td>
        </tr>
    </table>
    
    <div style="margin-top: 20px; padding: 15px; background-color: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0; font-size: 0.82rem; color: #64748B; line-height: 1.5;">
        <strong>System Integrity Check:</strong> HealthPulse AI utilizes sandbox endpoints in offline mode. If integration with FastAPI core is desired, set <code>API_URL</code> environment variable matching your backend deployment network configurations.
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("</div>", unsafe_allow_html=True)

# Render Footer
render_footer()
