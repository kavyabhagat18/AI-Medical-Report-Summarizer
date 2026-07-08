import streamlit as st
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.footer import render_footer
from components.uploader import render_upload_widget

# Render Header / Sidebar layout
render_navbar()
render_sidebar()

# Page Title Context
st.markdown(
    """
    <div style="margin-bottom: 25px;">
        <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 5px;">Report Submission Desk</h2>
        <p style="color: #64748B; margin-top: 0; font-size: 1rem;">
            Submit your laboratory summaries, biochemistry records, or imaging logs to initiate AI parsing.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Render Uploader Component
render_upload_widget()

# Additional user instructions inside clean dashboard layout
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("💡 Tips for Best AI OCR Extraction Results"):
    st.markdown(
        """
        - **Good Lighting & Resolution**: When uploading photos of printed reports, ensure the image is bright and taken directly from above.
        - **Supported Documents**: Ensure the file contains text structures (PDF, PNG, JPG, or TXT).
        - **Simulated Patient Testing Mode**:
          - Upload a file containing the word **"Rahul"** (e.g., `rahul_blood_report.txt`) to load simulated **Complete Blood Count (CBC)** details.
          - Upload any other filename to trigger a generic health check extraction (e.g. Jane Smith).
        """
    )

# Render Footer
render_footer()
