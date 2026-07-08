import os
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import A4

from reports.templates.report_template import build_story

OUTPUT_DIR = "outputs"


def generate_pdf(report_data):

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    patient = report_data.get("patient_name", "Patient").replace(" ", "_")

    pdf_path = os.path.join(
        OUTPUT_DIR,
        f"{patient}_Medical_Report.pdf"
    )

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4
    )

    story = []

    build_story(story, report_data)

    doc.build(story)

    return pdf_path