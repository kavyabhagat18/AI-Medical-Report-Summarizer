from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import TableStyle

styles = getSampleStyleSheet()

# ---------------- TITLE ----------------

title_style = styles["Heading1"]
title_style.alignment = TA_CENTER
title_style.textColor = colors.darkblue
title_style.spaceAfter = 20

# ---------------- HEADINGS ----------------

heading_style = styles["Heading2"]
heading_style.textColor = colors.darkblue
heading_style.spaceAfter = 10

# ---------------- NORMAL TEXT ----------------

normal_style = styles["BodyText"]
normal_style.spaceAfter = 8

# ---------------- DISCLAIMER ----------------

disclaimer_style = styles["Italic"]
disclaimer_style.textColor = colors.red

# ---------------- FOOTER ----------------

footer_style = styles["Normal"]
footer_style.alignment = TA_CENTER
footer_style.textColor = colors.grey

# ---------------- PATIENT DETAILS TABLE ----------------

def patient_table_style():

    return TableStyle([

        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

        ("TOPPADDING", (0, 0), (-1, -1), 8),

    ])

# ---------------- LAB VALUES TABLE ----------------

def lab_table_style():

    return TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565C0")),

        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),

        ("ALIGN", (0, 0), (-1, -1), "CENTER"),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),

        ("TOPPADDING", (0, 1), (-1, -1), 8),

    ])