from __future__ import annotations

from pathlib import Path
import json
import os
import sqlite3
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
DATA = ROOT / "datasets" / "project-owned"
DEMO = ROOT / "demo" / "outputs"
W, H = 1600, 1000
BG = "#071013"
PANEL = "#0c191d"
PANEL_2 = "#102329"
LINE = "#234048"
TEXT = "#e9f4f1"
MUTED = "#89a2a5"
CYAN = "#43d8c4"
AMBER = "#f0bf5b"
RED = "#ff645e"
GREEN = "#70d69a"
FONT_REG = "/usr/share/fonts/truetype/lato/Lato-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/lato/Lato-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def font(size: int, bold: bool = False, mono: bool = False):
    candidates = []
    if mono:
        candidates.extend([FONT_MONO, "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/lucon.ttf"])
    elif bold:
        candidates.extend([FONT_BOLD, "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"])
    else:
        candidates.extend([FONT_REG, "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"])
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def rect(draw, xy, fill=PANEL, outline=LINE, radius=12, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text(draw, xy, value, size=20, fill=TEXT, bold=False, mono=False, anchor=None):
    draw.text(xy, str(value), font=font(size, bold, mono), fill=fill, anchor=anchor)


def shell(title: str):
    image = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, 248, H), fill="#061015")
    d.line((248, 0, 248, H), fill=LINE, width=2)
    rect(d, (28, 26, 78, 76), fill="#14373c", outline=CYAN, radius=8)
    text(d, (53, 51), "OI", 19, CYAN, True, True, "mm")
    text(d, (92, 33), "OPENINSPECT", 18, TEXT, True)
    text(d, (92, 57), "OS / INTEGRITY CONTROL", 10, MUTED, mono=True)
    nav = ["Platform", "Command", "Facilities", "Assets", "Missions", "Evidence", "Coverage", "MLOps", "Reports"]
    for i, item in enumerate(nav):
        y = 122 + i * 55
        active = item.lower() in title.lower()
        if active:
            d.rounded_rectangle((18, y - 12, 228, y + 27), 7, fill="#123036")
        d.ellipse((31, y, 39, y + 8), fill=CYAN if active else "#48636a")
        text(d, (54, y - 5), item.upper(), 12, TEXT if active else MUTED, bold=active, mono=True)
    text(d, (28, 930), "● API CONNECTED", 11, GREEN, mono=True)
    text(d, (28, 955), "PROJECT-OWNED DEMO DATA", 9, MUTED, mono=True)
    text(d, (286, 30), "ASSET INTEGRITY OPERATIONS", 11, CYAN, True, True)
    text(d, (286, 56), title, 32, TEXT, True)
    text(d, (1510, 52), "LIVE DEMO", 11, CYAN, True, True, "rm")
    return image, d


def command_view(summary: dict, metrics: dict):
    image, d = shell("Command")
    x0, y0 = 286, 118
    rect(d, (x0, y0, 1550, 300), fill="#0b1b20")
    text(d, (x0 + 28, y0 + 25), summary["dashboard"]["organization"]["name"].upper(), 11, CYAN, True, True)
    text(d, (x0 + 28, y0 + 58), "Inspection evidence, coverage and maintenance decisions", 34, TEXT, True)
    text(d, (x0 + 28, y0 + 102), "in one controlled chain.", 34, TEXT, True)
    text(d, (x0 + 28, y0 + 150), "Structural surfaces · underwater pipelines · sonar-linked missions · offline edge devices", 15, MUTED)
    rect(d, (1320, 145, 1515, 270), fill="#091519", outline=CYAN)
    text(d, (1343, 165), "RISK INDEX", 10, MUTED, True, True)
    text(d, (1343, 193), summary["dashboard"]["risk_trend"][-1], 48, TEXT, True, True)
    text(d, (1465, 245), "↓ 11", 13, GREEN, True, True)

    labels = [
        ("FACILITIES", summary["dashboard"]["facilities"]),
        ("ASSETS", summary["dashboard"]["assets"]),
        ("MISSIONS", summary["dashboard"]["active_missions"]),
        ("FINDINGS", sum(1 for _ in sqlite3.connect(DEMO / "openinspect_demo.db").execute("select id from findings"))),
        ("COVERAGE", f'{summary["dashboard"]["coverage_percent"]:.1f}%'),
        ("WORK BACKLOG", summary["dashboard"]["work_order_backlog"]),
    ]
    for i, (label, value) in enumerate(labels):
        x = x0 + i * 207
        rect(d, (x, 330, x + 190, 448), fill=PANEL)
        text(d, (x + 18, 350), label, 10, MUTED, True, True)
        text(d, (x + 18, 383), value, 30, TEXT, True, True)
        d.line((x + 18, 427, x + 170, 427), fill=LINE, width=1)

    rect(d, (x0, 482, 1050, 942), fill=PANEL)
    text(d, (x0 + 24, 507), "MISSION CONTROL", 10, CYAN, True, True)
    text(d, (x0 + 24, 533), "Facility integrity map", 22, TEXT, True)
    mapbox = (x0 + 24, 578, 1026, 916)
    d.rounded_rectangle(mapbox, 9, fill="#07161a", outline=LINE)
    for yy in range(600, 910, 36):
        d.line((x0 + 25, yy, 1025, yy), fill="#10272c")
    for xx in range(x0 + 50, 1020, 48):
        d.line((xx, 579, xx, 915), fill="#10272c")
    route = [(360, 800), (470, 745), (610, 770), (760, 670), (930, 620)]
    d.line(route, fill=CYAN, width=5, joint="curve")
    for x, y in route:
        d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=BG, outline=CYAN, width=3)
    text(d, (377, 822), "BRIDGE LAB", 10, TEXT, True, True)
    text(d, (888, 594), "RAS LAFFAN DEMO", 10, TEXT, True, True)

    rect(d, (1075, 482, 1550, 942), fill=PANEL)
    text(d, (1100, 507), "MODEL + EDGE STATUS", 10, CYAN, True, True)
    cards = [
        ("Structural Classical CV", f'IoU {metrics["structural"]["iou"]:.3f}', "candidate"),
        ("Underwater Pipeline CV", f'IoU {metrics["pipeline"]["iou"]:.3f}', "candidate"),
        ("Edge Node A-17", "CPU / v0.1.0", "online"),
    ]
    for i, (name, note, status) in enumerate(cards):
        y = 550 + i * 102
        rect(d, (1098, y, 1528, y + 82), fill=PANEL_2)
        text(d, (1120, y + 18), name, 15, TEXT, True)
        text(d, (1120, y + 46), note, 11, MUTED, mono=True)
        text(d, (1504, y + 29), status.upper(), 10, GREEN if status == "online" else AMBER, True, True, "rm")
    return image


def evidence_view(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    finding = conn.execute("select * from findings order by confidence desc limit 1").fetchone()
    image, d = shell("Evidence")
    rect(d, (286, 118, 1135, 942), fill=PANEL)
    text(d, (310, 145), "EVIDENCE REVIEW", 10, CYAN, True, True)
    text(d, (310, 174), finding["finding_type"].replace("_", " ").title(), 25, TEXT, True)
    text(d, (1108, 165), finding["severity"].upper(), 10, AMBER, True, True, "rm")
    frame_box = (310, 225, 1110, 746)
    d.rounded_rectangle(frame_box, 8, fill="#050b0d", outline=LINE)
    evidence_path = Path(finding["evidence_path"])
    if evidence_path.exists():
        frame = Image.open(evidence_path).convert("RGB")
        frame.thumbnail((780, 500))
        px = 310 + (800 - frame.width) // 2
        py = 225 + (521 - frame.height) // 2
        image.paste(frame, (px, py))
    text(d, (328, 716), "GENERATED MASK OVERLAY · SHA-LINKED EVIDENCE", 10, TEXT, True, True)
    for i in range(6):
        x = 310 + i * 130
        rect(d, (x, 775, x + 112, 842), fill=PANEL_2, outline=CYAN if i == 2 else LINE, radius=5)
        text(d, (x + 56, 808), f"{i+1:04d}", 11, MUTED, True, True, "mm")
    text(d, (310, 876), f'PROVENANCE  {finding["provenance"]}', 10, MUTED, True, True)
    text(d, (755, 876), f'STATUS  {finding["status"]}', 10, MUTED, True, True)

    rect(d, (1160, 118, 1550, 942), fill=PANEL)
    text(d, (1185, 145), "INSPECTOR CONTROLS", 10, CYAN, True, True)
    text(d, (1185, 177), "Finding decision", 23, TEXT, True)
    d.ellipse((1260, 230, 1450, 420), outline=LINE, width=18)
    d.arc((1260, 230, 1450, 420), -90, -90 + int(finding["confidence"] * 360), fill=CYAN, width=18)
    text(d, (1355, 310), f'{finding["confidence"]*100:.0f}%', 36, TEXT, True, True, "mm")
    text(d, (1355, 351), "MODEL CONFIDENCE", 9, MUTED, True, True, "mm")
    measurements = json.loads(finding["measurement_json"])
    rows = [("Provenance", finding["provenance"]), ("Model", finding["model_version"])] + list(measurements.items())[:5]
    for i, (k, v) in enumerate(rows):
        y = 460 + i * 45
        d.line((1185, y + 34, 1525, y + 34), fill=LINE)
        text(d, (1185, y), str(k).replace("_", " ").upper(), 9, MUTED, True, True)
        text(d, (1525, y), f"{v:.3f}" if isinstance(v, float) else v, 11, TEXT, True, True, "ra")
    buttons = [("ACCEPT", GREEN), ("REJECT", RED), ("REQUEST REINSPECTION", AMBER), ("CREATE WORK ORDER", CYAN)]
    for i, (label, color) in enumerate(buttons):
        y = 790 + (i // 2) * 58
        x = 1185 + (i % 2) * 174
        rect(d, (x, y, x + 160, y + 42), fill="#0a171b", outline=color, radius=5)
        text(d, (x + 80, y + 21), label, 9, color, True, True, "mm")
    return image


def coverage_view(db_path: Path):
    conn = sqlite3.connect(db_path)
    row = conn.execute("select name, summary_json from missions where mission_type='pipeline' limit 1").fetchone()
    payload = json.loads(row[1])
    coverage = payload["coverage"]
    segments = coverage["segments"]
    image, d = shell("Coverage")
    rect(d, (286, 118, 1010, 942), fill=PANEL)
    text(d, (310, 145), "CALCULATED LINEAR COVERAGE", 10, CYAN, True, True)
    text(d, (310, 177), row[0], 24, TEXT, True)
    text(d, (980, 172), f'{coverage["coverage_percent"]:.1f}%', 20, CYAN, True, True, "rm")
    line_y = 450
    d.line((340, line_y, 955, line_y), fill="#5c7a80", width=18)
    total = segments[-1]["end_m"]
    for i, seg in enumerate(segments):
        x1 = 340 + int(615 * seg["start_m"] / total)
        x2 = 340 + int(615 * seg["end_m"] / total)
        color = GREEN if seg["covered"] else (AMBER if seg["reason"] == "low-visibility" else RED)
        d.line((x1, line_y, x2 - 3, line_y), fill=color, width=18)
        d.ellipse((x1 - 8, line_y - 8, x1 + 8, line_y + 8), fill=BG, outline=color, width=2)
        text(d, (x1, line_y + 34), f'{seg["start_m"]:.0f}m', 9, MUTED, True, True, "mm")
    text(d, (340, 535), "MISSION DISTANCE", 10, MUTED, True, True)
    text(d, (340, 562), f"{total:.1f} m", 26, TEXT, True, True)
    text(d, (570, 535), "LOW VISIBILITY", 10, MUTED, True, True)
    text(d, (570, 562), coverage["low_confidence_segments"], 26, AMBER, True, True)
    text(d, (785, 535), "MISSING", 10, MUTED, True, True)
    text(d, (785, 562), coverage["missing_segments"], 26, RED, True, True)
    rect(d, (310, 650, 985, 900), fill="#09161a")
    text(d, (334, 674), "QUALITY HEATMAP", 10, CYAN, True, True)
    for i, seg in enumerate(segments):
        x = 335 + i * 51
        h = max(20, int(150 * seg["visibility"]))
        color = GREEN if seg["covered"] else AMBER
        d.rectangle((x, 865 - h, x + 34, 865), fill=color)
        text(d, (x + 17, 882), i + 1, 8, MUTED, True, True, "mm")

    rect(d, (1035, 118, 1550, 942), fill=PANEL)
    text(d, (1060, 145), "REINSPECTION", 10, CYAN, True, True)
    text(d, (1060, 177), "Calculated exception segments", 23, TEXT, True)
    exceptions = [s for s in segments if not s["covered"]]
    for i, seg in enumerate(exceptions):
        y = 235 + i * 115
        rect(d, (1060, y, 1525, y + 92), fill=PANEL_2)
        text(d, (1082, y + 18), f'{seg["start_m"]:.0f}-{seg["end_m"]:.0f} m', 17, TEXT, True, True)
        text(d, (1082, y + 50), seg["reason"].upper(), 10, AMBER if seg["reason"] == "low-visibility" else RED, True, True)
        text(d, (1498, y + 18), f'{seg["visibility"]:.2f}', 20, TEXT, True, True, "ra")
        text(d, (1498, y + 53), "REPEAT WITH IMPROVED VISIBILITY", 8, MUTED, True, True, "ra")
    return image


def mlops_view(metrics: dict):
    image, d = shell("MLOps")
    rect(d, (286, 118, 1080, 942), fill=PANEL)
    text(d, (310, 145), "MODEL REGISTRY", 10, CYAN, True, True)
    text(d, (310, 177), "Inspection model versions", 24, TEXT, True)
    models = [("Structural Classical CV", "crack segmentation", metrics["structural"]), ("Underwater Pipeline CV", "pipeline visibility", metrics["pipeline"])]
    for i, (name, task, m) in enumerate(models):
        y = 235 + i * 282
        rect(d, (310, y, 1055, y + 250), fill=PANEL_2)
        text(d, (335, y + 25), task.upper(), 10, CYAN, True, True)
        text(d, (335, y + 54), name, 23, TEXT, True)
        text(d, (1025, y + 28), "CANDIDATE", 10, AMBER, True, True, "ra")
        values = [("PRECISION", m["precision"]), ("RECALL", m["recall"]), ("IOU", m["iou"]), ("F1", m["f1"]), ("CPU MEAN", m["cpu_latency_ms_mean"])]
        for j, (label, value) in enumerate(values):
            x = 335 + j * 137
            text(d, (x, y + 120), label, 8, MUTED, True, True)
            display = f"{value:.3f}" if j < 4 else f"{value:.0f}ms"
            text(d, (x, y + 148), display, 20, TEXT, True, True)
            d.line((x, y + 184, x + 112, y + 184), fill=LINE, width=3)
            fraction = min(1.0, value if j < 4 else 150 / max(value, 150))
            d.line((x, y + 184, x + int(112 * fraction), y + 184), fill=CYAN if fraction >= .75 else AMBER, width=3)
        text(d, (335, y + 215), "METRICS APPLY ONLY TO THE PROJECT-OWNED SYNTHETIC VALIDATION SET", 9, MUTED, True, True)

    rect(d, (1105, 118, 1550, 942), fill=PANEL)
    text(d, (1130, 145), "RELEASE GATE", 10, CYAN, True, True)
    text(d, (1130, 177), "Candidate evaluation", 23, TEXT, True)
    gates = [("Model card", True), ("Failure analysis", True), ("Critical recall", False), ("CPU latency", False), ("Dataset provenance", True)]
    for i, (label, passed) in enumerate(gates):
        y = 245 + i * 88
        rect(d, (1130, y, 1525, y + 64), fill=PANEL_2)
        text(d, (1152, y + 23), label.upper(), 10, TEXT, True, True)
        text(d, (1502, y + 23), "PASS" if passed else "REVIEW", 10, GREEN if passed else AMBER, True, True, "ra")
    text(d, (1130, 730), "A successful demo never auto-promotes a model.", 15, TEXT, True)
    text(d, (1130, 768), "Deployment requires field validation,", 13, MUTED)
    text(d, (1130, 794), "calibration and qualified approval.", 13, MUTED)
    return image


def make_gif():
    frames = []
    for path in sorted((DATA / "pipeline").glob("*.png")):
        img = Image.open(path).convert("RGB")
        img.thumbnail((960, 540))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, 960, 36), fill="#071013")
        text(draw, (18, 10), f"OPENINSPECT PIPELINE EVIDENCE · {path.stem}", 12, CYAN, True, True)
        frames.append(img)
    if frames:
        frames[0].save(DEMO / "pipeline_evidence.gif", save_all=True, append_images=frames[1:], duration=220, loop=0, optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = json.loads((DEMO / "demo_summary.json").read_text())
    metrics = json.loads((DEMO / "model_performance.json").read_text())
    images = {
        "command-center.png": command_view(summary, metrics),
        "evidence-review.png": evidence_view(DEMO / "openinspect_demo.db"),
        "coverage.png": coverage_view(DEMO / "openinspect_demo.db"),
        "mlops.png": mlops_view(metrics),
    }
    for name, image in images.items():
        image.save(OUT / name, quality=94)
    make_gif()
    print(
        json.dumps(
            {"screenshots": [f"docs/screenshots/{name}" for name in images], "gif": "demo/outputs/pipeline_evidence.gif"},
            indent=2,
        ),
        flush=True,
    )
    # Pillow/native codecs can retain worker state on some CI images. Outputs
    # are fully written above, so force a deterministic command-line exit.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
