import streamlit as st
import os
from utils.api_client import upload_report

def render_upload_widget():
    """Renders a premium file uploader component with previews, limits, and progress indicator."""
    st.markdown(
        """
        <div style="background-color: #FFFFFF; border: 2px dashed #3B82F6; border-radius: 16px; padding: 30px; text-align: center; margin-bottom: 25px; background-color: #F8FAFC;">
            <div style="font-size: 3rem; color: #3B82F6; margin-bottom: 10px;">📤</div>
            <h4 style="margin: 0; color: #1E3A8A; font-weight: 700;">Upload Medical Report</h4>
            <p style="margin: 5px 0 0 0; font-size: 0.875rem; color: #64748B;">Drag and drop or browse files. Max file size: 10MB.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Supported extensions
    allowed_types = ["pdf", "png", "jpeg", "jpg", "txt"]
    
    # Initialize uploader version if not present
    if "uploader_version" not in st.session_state:
        st.session_state["uploader_version"] = 0

    # Custom File Uploader Widget using a versioned key
    uploaded_file = st.file_uploader(
        label="Select a medical report to analyze",
        type=allowed_types,
        label_visibility="collapsed",
        key=f"uploader_widget_{st.session_state['uploader_version']}"
    )
    
    if uploaded_file is not None:
        # File info extraction
        file_name = uploaded_file.name
        file_type = uploaded_file.type
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        # Validation: check large files (10MB limit)
        if file_size_mb > 10.0:
            st.error(f"❌ File size exceeds the 10MB limit ({file_size_mb:.2f} MB uploaded). Please upload a smaller file.")
            if st.button("Reset File", use_container_width=True):
                st.session_state["uploader_version"] = st.session_state.get("uploader_version", 0) + 1
                st.rerun()
            return
            
        # Display File Details Card
        st.markdown(
            f"""
            <div class="card" style="margin-top: 15px; border-left: 5px solid #2563EB;">
                <h5 style="margin-top: 0; margin-bottom: 12px; color: #1E3A8A;">📄 Selected Document Details</h5>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; font-size: 0.875rem;">
                    <div>
                        <span style="color: #64748B; font-weight: 500;">Filename:</span><br>
                        <strong style="color: #1E293B;">{file_name}</strong>
                    </div>
                    <div>
                        <span style="color: #64748B; font-weight: 500;">File Type:</span><br>
                        <strong style="color: #1E293B;">{file_type if file_type else 'Unknown'}</strong>
                    </div>
                    <div>
                        <span style="color: #64748B; font-weight: 500;">Size:</span><br>
                        <strong style="color: #1E293B;">{file_size_mb:.2f} MB</strong>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # File Preview Section
        st.write("🔍 **Document Preview**")
        
        # Render Previews based on File Type
        try:
            if file_name.endswith(".txt"):
                # Preview text contents
                text_content = uploaded_file.getvalue().decode("utf-8")
                st.code(text_content[:800] + ("\n... [Truncated for preview]" if len(text_content) > 800 else ""), language="text")
            elif file_name.lower().endswith((".png", ".jpg", ".jpeg")):
                # Preview image
                st.image(uploaded_file, caption="Uploaded Medical Report Image", use_column_width=True)
            elif file_name.endswith(".pdf"):
                # PDF Icon/Metainfo since standard Streamlit can't embed PDF streams directly without large iframe hacks
                st.markdown(
                    """
                    <div style="background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 8px; padding: 25px; text-align: center;">
                        <span style="font-size: 2.5rem;">📕</span>
                        <h5 style="margin: 10px 0 5px 0; color: #475569;">PDF Document Ready</h5>
                        <p style="margin: 0; font-size: 0.8rem; color: #64748B;">Direct preview of PDF text extraction is ready for synthesis.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        except Exception as e:
            st.warning(f"Unable to generate document preview: {str(e)}")
            
        # Action Buttons
        col1, col2 = st.columns(2)
        
        with col1:
            generate_clicked = st.button("🚀 Generate Summary", type="primary", use_container_width=True)
        with col2:
            reset_clicked = st.button("🔄 Reset", type="secondary", use_container_width=True)
            
        if reset_clicked:
            st.session_state["uploader_version"] = st.session_state.get("uploader_version", 0) + 1
            st.session_state.pop("uploaded_file", None)
            st.session_state.pop("current_report_id", None)
            st.rerun()
            
        if generate_clicked:
            # Progress Spinner
            progress_bar = st.progress(0, text="Initiating secure report transmission...")
            
            try:
                # Read file bytes
                file_bytes = uploaded_file.getvalue()
                
                # Update progress
                progress_bar.progress(30, text="Uploading report to FastAPI backend...")
                
                # Make upload & process HTTP call
                result = upload_report(file_bytes, file_name, file_type)
                
                if result.get("success"):
                    progress_bar.progress(100, text="Summary generated successfully!")
                    st.success("✅ Document successfully uploaded and processed!")
                    st.session_state["current_report_id"] = result["report_id"]
                    
                    # Redirect to summary page after a short delay
                    import time
                    time.sleep(1.0)
                    st.switch_page("pages/Summary.py")
                    st.rerun()
                else:
                    st.error(f"❌ Synthesis failed: {result.get('message')}")
            except Exception as e:
                st.error(f"❌ Unexpected connection failure: {str(e)}")
    else:
        # Prompt user if no file uploaded
        st.info("ℹ️ Please upload a medical file (PDF, Image, or Text) to start summary synthesis.")
