import streamlit as st
import os

def render_sidebar():
    """Renders customized and rich supplementary content on the Streamlit sidebar."""
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 20px; padding: 15px; background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border-radius: 12px; border: 1px solid #BFDBFE;">
                <h4 style="margin: 0; color: #1E3A8A; font-weight: 700;">Active Portal</h4>
                <p style="margin: 5px 0 0 0; font-size: 0.8rem; color: #3B82F6; font-weight: 500;">Clinical Dashboard v1.0.0</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # User details card
        st.markdown(
            """
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 15px; margin-bottom: 25px;">
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">Active Practitioner</div>
                <div style="font-weight: 700; color: #1E293B; font-size: 0.95rem;">Dr. Evelyn Vance</div>
                <div style="font-size: 0.8rem; color: #475569;">St. Jude Medical Center</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Quick Actions
        st.markdown("### ⚡ Quick Navigation")
        if st.button("📤 Upload New Report", use_container_width=True, type="primary"):
            st.switch_page("pages/Upload_Report.py")
        if st.button("📜 View History", use_container_width=True):
            st.switch_page("pages/History.py")
        
        st.markdown("---")
        
        # Healthcare Disclaimer
        st.markdown(
            """
            <div style="background-color: #FEF2F2; border: 1px solid #FEE2E2; border-radius: 12px; padding: 15px; margin-top: 20px;">
                <div style="display: flex; gap: 8px; align-items: center; color: #DC2626; font-weight: 700; font-size: 0.85rem; margin-bottom: 5px;">
                    ⚠️ Medical Disclaimer
                </div>
                <p style="font-size: 0.75rem; color: #991B1B; line-height: 1.4; margin: 0;">
                    HealthPulse AI is an administrative tool powered by OCR & AI to assist in summarizing documents. It is <strong>not a medical device</strong> and should <strong>never replace professional clinical judgment</strong>, diagnosis, or treatment.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown(
            """
            <div style="text-align: center; font-size: 0.7rem; color: #94A3B8; margin-top: 30px;">
                © 2026 HealthPulse AI Inc.<br>All rights reserved.
            </div>
            """,
            unsafe_allow_html=True
        )
