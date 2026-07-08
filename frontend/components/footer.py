import streamlit as st

def render_footer():
    """Renders a unified footer with developer info and application status."""
    st.markdown(
        """
        <div class="footer-text">
            <p style="margin-bottom: 5px;"><strong>HealthPulse AI</strong> • Advanced Medical Report Analytics Dashboard</p>
            <p style="margin: 0; font-size: 0.8rem;">
                Built by AI Health Engineering Team • App Version 1.0.0 • 🛡️ HIPAA Compliant Encryption Mock
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
