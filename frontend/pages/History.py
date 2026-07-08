import streamlit as st
import time
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.footer import render_footer
from utils.api_client import get_history, delete_report, download_pdf

# Render layout headers
render_navbar()
render_sidebar()

# Page title
st.markdown(
    """
    <div style="margin-bottom: 25px;">
        <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 5px;">Historical Record Vault</h2>
        <p style="color: #64748B; margin-top: 0; font-size: 1rem;">
            Query, inspect, download, or manage past diagnostic syntheses and OCR outputs.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Fetch History
try:
    history_data = get_history()
    if not history_data:
        # Fallback simulated logs if DB is empty or backend is fresh
        history_data = [
            {
                "id": "rep_001",
                "date": "2026-06-30",
                "patient_name": "Rahul Sharma",
                "age": 45,
                "gender": "Male",
                "report_type": "Comprehensive Blood & Diabetic Panel",
                "status": "Completed",
                "hospital": "Apollo Hospitals, Delhi",
                "doctor": "Dr. A. K. Sen"
            },
            {
                "id": "rep_002",
                "date": "2026-06-28",
                "patient_name": "Jane Smith",
                "age": 32,
                "gender": "Female",
                "report_type": "Lipid Profile & Thyroid Panel",
                "status": "Completed",
                "hospital": "Metro Health Clinic",
                "doctor": "Dr. Evelyn Vance"
            }
        ]
    st.session_state["history"] = history_data
except Exception as e:
    st.warning("⚠️ FastAPI backend is unreachable. Viewing offline local history logs.")
    history_data = st.session_state.get("history", [])
    if not history_data:
        history_data = [
            {
                "id": "rep_001",
                "date": "2026-06-30",
                "patient_name": "Rahul Sharma",
                "age": 45,
                "gender": "Male",
                "report_type": "Comprehensive Blood & Diabetic Panel",
                "status": "Completed",
                "hospital": "Apollo Hospitals, Delhi",
                "doctor": "Dr. A. K. Sen"
            }
        ]

# Search and Filters Layout Card
st.markdown('<div class="card" style="margin-bottom: 25px;">', unsafe_allow_html=True)
col_s1, col_s2 = st.columns([3, 1])

with col_s1:
    search_query = st.text_input("🔍 Search Logs", placeholder="Search by patient name, clinic, or report type...")
with col_s2:
    status_filter = st.selectbox("📋 Status Filter", options=["All", "Completed", "Pending"])
st.markdown('</div>', unsafe_allow_html=True)

# Filter Logic
filtered_logs = []
for log in history_data:
    match_query = (
        search_query.lower() in log.get("patient_name", "").lower() or
        search_query.lower() in log.get("report_type", "").lower() or
        search_query.lower() in log.get("hospital", "").lower() or
        search_query.lower() in log.get("doctor", "").lower()
    )
    
    match_status = (
        status_filter == "All" or 
        log.get("status", "").lower() == status_filter.lower()
    )
    
    if match_query and match_status:
        filtered_logs.append(log)

# Display Table Header
if not filtered_logs:
    st.markdown(
        """
        <div style="text-align: center; padding: 40px; background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0;">
            <p style="color: #64748B; font-size: 1rem; margin: 0;">No matching clinical logs found in vault database.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # Table Header Labels in Columns
    st.markdown(
        """
        <div style="background-color: #F1F5F9; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; border: 1px solid #E2E8F0;">
            <div style="display: grid; grid-template-columns: 1.2fr 1.8fr 2.2fr 1.2fr 2.6fr; gap: 10px; align-items: center; font-weight: 700; color: #475569; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">
                <div>Date</div>
                <div>Patient Name</div>
                <div>Report Type</div>
                <div>Status</div>
                <div style="text-align: center;">Actions</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Render individual rows
    for index, log in enumerate(filtered_logs):
        log_id = log["id"]
        patient = log.get("patient_name", "N/A")
        report_date = log.get("date", "N/A")
        report_type = log.get("report_type", "N/A")
        status = log.get("status", "Completed")
        
        # Format Badge
        badge_style = "badge-success" if status == "Completed" else "badge-warning"
        
        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border-radius: 12px; padding: 16px; margin-bottom: 10px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.01);">
                <div style="display: grid; grid-template-columns: 1.2fr 1.8fr 2.2fr 1.2fr 2.6fr; gap: 10px; align-items: center; font-size: 0.9rem; color: #334155;">
                    <div style="font-weight: 500; color: #64748B;">{report_date}</div>
                    <div style="font-weight: 600; color: #1E293B;">{patient}</div>
                    <div>{report_type}</div>
                    <div><span class="badge {badge_style}">{status}</span></div>
                    <div id="actions-cell-{log_id}"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        row_cols = st.columns([1.2, 1.8, 2.2, 1.2, 2.6])
        
        with row_cols[0]:
            st.empty() # Placeholder since text is rendered in the markdown container
        with row_cols[4]:
            # Sub-columns inside Action column for nice compact horizontal buttons
            btn1, btn2, btn3 = st.columns([1, 1, 1])
            
            with btn1:
                if st.button("👁️ View", key=f"view_btn_{log_id}_{index}", use_container_width=True):
                    st.session_state["current_report_id"] = log_id
                    st.switch_page("pages/Summary.py")
                    st.rerun()
                    
            with btn2:
                try:
                    pdf_bytes = download_pdf(log_id)
                    st.download_button(
                        label="📥 PDF",
                        data=pdf_bytes,
                        file_name=f"{patient.replace(' ', '_')}_Report.pdf",
                        mime="application/pdf",
                        key=f"pdf_dl_{log_id}_{index}",
                        use_container_width=True
                    )
                except Exception as e:
                    if st.button("📥 PDF", key=f"pdf_dl_err_{log_id}_{index}", use_container_width=True):
                        st.error(f"Unavailable: {e}")
                    
            with btn3:
                if st.button("🗑️ Del", key=f"del_rec_{log_id}_{index}", type="secondary", use_container_width=True):
                    if delete_report(log_id):
                        st.success("Deleted!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to delete.")

st.markdown("<br><br>", unsafe_allow_html=True)

# Render Footer
render_footer()
