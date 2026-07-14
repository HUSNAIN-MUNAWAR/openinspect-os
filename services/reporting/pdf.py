from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak


def _format_measurement(key: str, value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if key.endswith("_percent"):
            return f"{value:.3f}%"
        if key.endswith("_px") or key in {"pixel_length", "pixel_width"}:
            return f"{value:.2f} px"
        if key.endswith("_mm"):
            return f"{value:.3f} mm"
        if key.endswith("_m"):
            return f"{value:.2f} m"
        return f"{value:.4f}"
    return str(value)


def generate_mission_report(data: dict, output_path: str | Path) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    story = [Paragraph("OpenInspect OS — Inspection Mission Report", styles["Title"]), Spacer(1, 8)]
    summary = [
        ["Mission", data.get("mission", "")],
        ["Facility", data.get("facility", "")],
        ["Asset", data.get("asset", "")],
        ["Inspector", data.get("inspector", "")],
        ["Capture device", data.get("capture_device", "")],
        ["Inspection date", data.get("inspection_date", "")],
        ["Coverage", f"{data.get('coverage_percent', 0):.1f}%"],
        ["Model version", data.get("model_version", "")],
        ["Review status", data.get("review_status", "")],
    ]
    table = Table(summary, colWidths=[42*mm, 120*mm])
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (0,-1), colors.HexColor("#e8edf0")), ("GRID", (0,0), (-1,-1), 0.5, colors.grey), ("VALIGN", (0,0), (-1,-1), "TOP"), ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold")]))
    story += [table, Spacer(1, 12), Paragraph("Findings", styles["Heading2"])]
    findings = data.get("findings", [])
    if not findings:
        story.append(Paragraph("No findings recorded.", styles["BodyText"]))
    for idx, finding in enumerate(findings, 1):
        story.append(Paragraph(f"{idx}. {finding.get('type', 'Finding')} — {finding.get('severity', 'unrated')}", styles["Heading3"]))
        story.append(Paragraph(finding.get("notes", ""), styles["BodyText"]))
        measurement = finding.get("measurement", {})
        if measurement:
            rows = [[k.replace('_',' ').title(), _format_measurement(k, v)] for k, v in measurement.items() if v is not None]
            mt = Table(rows, colWidths=[62*mm, 100*mm])
            mt.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey), ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f6f8f9"))]))
            story.append(mt)
        evidence = finding.get("evidence")
        if idx <= 4 and evidence and Path(evidence).exists():
            story += [Spacer(1, 6), Image(evidence, width=128*mm, height=72*mm)]
        elif evidence:
            story.append(Paragraph("Evidence retained in object storage; omitted from this condensed report view.", styles["Italic"]))
        story.append(Spacer(1, 10))
    story += [PageBreak(), Paragraph("Coverage and Audit", styles["Heading2"]), Paragraph(data.get("coverage_notes", "Coverage calculated from synchronized navigation and usable-frame observations."), styles["BodyText"]), Spacer(1, 10)]
    audit_rows = [[e.get("timestamp", ""), e.get("action", ""), e.get("actor", "")] for e in data.get("audit", [])]
    if audit_rows:
        at = Table([["Timestamp", "Action", "Actor"], *audit_rows], colWidths=[45*mm, 80*mm, 38*mm])
        at.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#d8e2e8")), ("GRID", (0,0), (-1,-1), 0.4, colors.grey)]))
        story.append(at)
    story += [Spacer(1, 18), Paragraph("Sign-off", styles["Heading2"]), Paragraph(data.get("sign_off", "Pending inspector approval"), styles["BodyText"])]
    doc.build(story)
    return str(output)
