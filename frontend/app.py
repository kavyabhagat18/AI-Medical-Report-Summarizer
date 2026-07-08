import streamlit as st
import os

# 1. Page Configuration (Must be first Streamlit command)
st.set_page_config(
    page_title="HealthPulse AI - Medical Summarizer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Session State Initialization
# Self-healing check to move generated logo to destination assets folder
try:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if not os.path.exists(logo_path):
        brain_logo_path = r"C:\Users\91799\.gemini\antigravity\brain\10a3c72b-f4b3-4bcd-801f-8863f58f1b37\logo_1782824168539.png"
        if os.path.exists(brain_logo_path):
            import shutil
            os.makedirs(os.path.dirname(logo_path), exist_ok=True)
            shutil.copy(brain_logo_path, logo_path)
except Exception:
    pass

if "selected_language" not in st.session_state:
    st.session_state["selected_language"] = "English"

if "uploaded_file" not in st.session_state:
    st.session_state["uploaded_file"] = None

if "current_report_id" not in st.session_state:
    st.session_state["current_report_id"] = None

if "history" not in st.session_state:
    st.session_state["history"] = []

if "theme" not in st.session_state:
    st.session_state["theme"] = "Light"

if "notifications" not in st.session_state:
    st.session_state["notifications"] = True

if "translation" not in st.session_state:
    st.session_state["translation"] = None

if "generating_summary" not in st.session_state:
    st.session_state["generating_summary"] = False

# 3. Multi-page Navigation Config
# Define pages referencing the pages/ folder structures
home_page = st.Page("pages/Home.py", title="Home", icon="🏠", default=True)
upload_page = st.Page("pages/Upload_Report.py", title="Upload Report", icon="📤")
summary_page = st.Page("pages/Summary.py", title="Report Summary", icon="📝")
history_page = st.Page("pages/History.py", title="History Logs", icon="📜")
settings_page = st.Page("pages/Settings.py", title="Settings", icon="⚙️")

# Build navigation
pg = st.navigation({
    "Main Portal": [home_page, upload_page],
    "Analytics": [summary_page, history_page],
    "Configuration": [settings_page]
})

# Run the navigation routing
pg.run()
