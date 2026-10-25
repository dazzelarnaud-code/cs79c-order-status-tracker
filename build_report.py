"""Render the CS 79C final project report and evidence."""

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "final-report.md"
OUTPUT = BASE / "Arnaud-CS79C-Final-Project.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="ProjectTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=17, leading=21, textColor=colors.HexColor("#173b60"),
    spaceAfter=11,
))
styles.add(ParagraphStyle(
    name="ProjectHeading", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=12, leading=15, textColor=colors.HexColor("#173b60"),
    spaceBefore=15, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="ProjectBody", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=10.5, leading=15.5, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="DraftNote", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=9, leading=12, textColor=colors.HexColor("#934a00"),
    spaceAfter=11,
))


def footer(canvas, document):
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(0.7 * inch, 0.42 * inch, "Daz Arnaud | CS 79C | Final project")
    canvas.drawRightString(letter[0] - 0.7 * inch, 0.42 * inch, str(document.page))


def build():
    lines = SOURCE.read_text().splitlines()
    story = []
    for line in lines:
        if not line.strip():
            continue
        if line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), styles["ProjectTitle"]))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), styles["ProjectHeading"]))
        elif line.startswith("Daz Arnaud. CS 79C."):
            story.append(Paragraph(escape(line), styles["DraftNote"]))
        else:
            story.append(Paragraph(escape(line.replace("`", "")), styles["ProjectBody"]))

    screenshots = [
        ("Architecture and data flow", BASE / "assets" / "architecture.svg"),
        ("CloudFormation deployment", BASE / "evidence" / "stack-create-complete.jpg"),
        ("Stack outputs", BASE / "evidence" / "stack-outputs.jpg"),
        ("Saved order in DynamoDB", BASE / "evidence" / "dynamodb-sample-order.jpg"),
        ("SNS event received by SQS", BASE / "evidence" / "sqs-event-body.jpg"),
        ("Successful Lambda lookup", BASE / "evidence" / "lambda-successful-lookup.jpg"),
    ]
    story.append(PageBreak())
    story.append(Paragraph("Evidence appendix", styles["ProjectTitle"]))
    for index, (title, path) in enumerate(screenshots):
        if path.suffix == ".svg":
            story.append(Paragraph("The architecture diagram is embedded in the repository README.", styles["ProjectBody"]))
            continue
        image = Image(str(path))
        max_width, max_height = 6.8 * inch, 5.3 * inch
        scale = min(max_width / image.imageWidth, max_height / image.imageHeight)
        image.drawWidth = image.imageWidth * scale
        image.drawHeight = image.imageHeight * scale
        story.append(Paragraph(title, styles["ProjectHeading"]))
        story.append(image)
        story.append(Spacer(1, 0.12 * inch))
        if index < len(screenshots) - 1:
            story.append(PageBreak())
    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=letter,
        leftMargin=0.82 * inch, rightMargin=0.82 * inch,
        topMargin=0.82 * inch, bottomMargin=0.82 * inch,
        title="CS 79C final project report",
        author="Daz Arnaud",
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    build()
