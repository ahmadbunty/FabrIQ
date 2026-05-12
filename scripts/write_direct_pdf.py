"""
FabrIQ Technical Report — direct PDF generation (no Markdown).

Install:
  pip install reportlab

Run:
  python write_direct_pdf.py

Output:
  ../docs/FabrIQ_Report_Direct.pdf
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUT_PDF = ROOT / "docs" / "FabrIQ_Report_Direct.pdf"


def esc(text: str) -> str:
    return html.escape(text.strip())


def bold_xml(text: str) -> str:
    """Escape then wrap **segments** as <b>."""
    t = html.escape(text.strip())
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)


def p_story(styles, story: list, body: str) -> None:
    story.append(Paragraph(bold_xml(body), styles["Body"]))
    story.append(Spacer(1, 6))


def bullets_story(styles, story: list, items: list[str]) -> None:
    for it in items:
        story.append(Paragraph(f"&#8226; {bold_xml(it)}", styles["Body"]))
    story.append(Spacer(1, 6))


def mono_block(styles, story: list, text: str) -> None:
    safe = html.escape(text.strip()).replace("\n", "<br/>")
    story.append(Paragraph(f"<font face='Courier' size='8'>{safe}</font>", styles["Body"]))
    story.append(Spacer(1, 8))


def build() -> None:
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["Normal"],
            alignment=TA_JUSTIFY,
            fontSize=10,
            leading=13,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Ttl",
            parent=styles["Title"],
            fontSize=17,
            leading=21,
            spaceAfter=10,
            textColor=colors.HexColor("#1565c0"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1",
            parent=styles["Heading1"],
            fontSize=13,
            leading=17,
            spaceBefore=10,
            spaceAfter=8,
            textColor=colors.HexColor("#0d47a1"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=6,
        )
    )

    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="FabrIQ Technical Report",
        author="FabrIQ Project",
    )
    story: list = []

    story.append(
        Paragraph(
            "FabrIQ: An End-to-End Fabric Defect Detection System<br/>"
            "Using YOLOv8 and a Web Dashboard",
            styles["Ttl"],
        )
    )
    story.append(Spacer(1, 4))
    p_story(
        styles,
        story,
        "**Technical Report** (draft for conference / journal paper). "
        "**Authors:** [Your Name(s)]. **Affiliation:** [Your Institution]. "
        "**Date:** May 2026. **Version:** 1.0.",
    )

    story.append(Paragraph("Abstract", styles["H1"]))
    p_story(
        styles,
        story,
        "Fabric defect detection is critical for quality assurance in textile manufacturing. "
        "Commercial inspection systems are often costly and poorly suited to small and medium enterprises (SMEs). "
        "This report describes **FabrIQ**, an integrated software stack that combines **YOLOv8-based object detection**, "
        "a **Flask REST API**, a **React (Vite) dashboard**, **Firebase (Firestore + Storage)** for persistence, "
        "and **live camera streaming** with server-side inference suitable for laptop prototyping through edge devices "
        "such as NVIDIA Jetson Nano with industrial or Arducam sensors. "
        "The system supports image and video upload, frame-wise annotated video output, real-time MJPEG streams with "
        "bounding boxes, and analytics derived from stored defect records. "
        "Quantitative benchmarks should be inserted after formal evaluation on a held-out test set.",
    )
    p_story(
        styles,
        story,
        "**Keywords:** fabric defect detection, YOLOv8, computer vision, Flask, React, Firebase, MLOps, "
        "edge deployment, textile industry.",
    )

    story.append(Paragraph("1. Introduction", styles["H1"]))
    p_story(
        styles,
        story,
        "Textile production involves continuous material movement on rollers, making automated visual inspection "
        "valuable for reducing waste and maintaining grade consistency. Deep learning detectors such as YOLO variants "
        "offer a practical balance between accuracy and inference latency.",
    )
    bullets_story(
        styles,
        story,
        [
            "Standardized pipeline from messy folders to YOLO-compatible datasets.",
            "Training scripts for classification and detection (including pseudo-annotations where box labels are scarce).",
            "Web application: detection UI, dashboard metrics, analytics, exportable reports.",
            "Firebase for defect persistence and optional annotated images.",
            "Live inspection via backend camera capture and streamed annotated frames.",
        ],
    )

    story.append(Paragraph("2. Related Work and Background", styles["H1"]))
    p_story(
        styles,
        story,
        "Fabric defect detection spans handcrafted features, classical ML, CNNs, and modern detectors/segmentation. "
        "**FabrIQ** emphasizes **operational completeness** (API + UI + storage + streaming + CI) and deployment "
        "to edge cameras rather than a novel backbone architecture.",
    )

    story.append(Paragraph("3. Problem Statement", styles["H1"]))
    bullets_story(
        styles,
        story,
        [
            "**Inputs:** Images/video of fabric; optional live camera on laptop, workstation, or Jetson.",
            "**Outputs:** Bounding boxes and class labels; annotated previews; stored records for analytics.",
            "**Constraints:** Low cost, simple UX, swap weights via configuration; edge limits on model size and cameras (USB/CSI).",
        ],
    )

    story.append(Paragraph("4. Dataset and Preparation", styles["H1"]))
    story.append(Paragraph("4.1 Organization", styles["H2"]))
    p_story(
        styles,
        story,
        "**organize_dataset.py** maps folder/filename cues to a **20-class** taxonomy, fuzzy term mapping, "
        "standardized filenames, and **80/20 train/validation** split under FabrIQ_Final_Dataset.",
    )
    story.append(Paragraph("4.2 Detection Dataset", styles["H2"]))
    p_story(
        styles,
        story,
        "**create_pseudo_annotations.py** can bootstrap full-image YOLO boxes; replace with real annotations over time.",
    )
    story.append(Paragraph("4.3 Application Schema", styles["H2"]))
    p_story(
        styles,
        story,
        "Backend inference classes: **hole**, **objects**, **oil_spot**, **thread_error**. "
        "Firestore normalizes to hole / stain / broken_thread / misweave. "
        "**CLASSES** in backend/app.py must match **YOLO class order** in weights.",
    )

    story.append(Paragraph("5. Model Training", styles["H1"]))
    p_story(
        styles,
        story,
        "**Ultralytics YOLOv8** via train_yolo_detection.py; CUDA when available, CPU with reduced batch/epochs. "
        "Address NumPy/OpenCV/PyTorch alignment, corrupt JPEG cleanup, and PyTorch 2.6 weights loading where needed.",
    )
    p_story(
        styles,
        story,
        "**Evaluation:** Report precision, recall, mAP@0.5, mAP@0.5:0.95, FPS, hardware, resolution, confidence threshold.",
    )

    story.append(Paragraph("6. System Architecture", styles["H1"]))
    mono_block(
        styles,
        story,
        "Frontend     React, Vite, Material UI   UX, charts, JWT client\n"
        "Backend      Flask, OpenCV, Ultralytics Inference, uploads, live MJPEG\n"
        "Persistence  Firebase Firestore/Storage Defects, optional images\n"
        "Ops          Docker Compose, GitHub Actions Packaging and CI",
    )
    p_story(
        styles,
        story,
        "**Upload:** POST /api/detection/analyze — JSON defects, annotated image base64, annotated video URL for uploads.",
    )
    p_story(
        styles,
        story,
        "**Live:** POST /api/live/start — cv2.VideoCapture(index); GET /api/live/stream — MJPEG with boxes; "
        "GET /api/live/latest — latest frame defect metadata.",
    )
    p_story(
        styles,
        story,
        "**Model path priority:** FABRIQ_MODEL_PATH → relative runs/detect weights → absolute fallback → yolov8n.pt. "
        "**Camera:** FABRIQ_CAMERA_INDEX or UI-selected index.",
    )

    story.append(Paragraph("7. Frontend Application", styles["H1"]))
    bullets_story(
        styles,
        story,
        [
            "Login; Dashboard from Firestore; Detection upload + live stream + camera selector;",
            "Analytics and Reports; Firebase writes after inference (Storage fallback tolerant).",
        ],
    )

    story.append(Paragraph("8. Deployment", styles["H1"]))
    bullets_story(
        styles,
        story,
        [
            "Backend: venv, pip install -r backend/requirements.txt, python backend/app.py.",
            "Frontend: npm install, npm run dev, set VITE_API_URL.",
            "Jetson: ARM builds, camera index, consider TensorRT for latency.",
        ],
    )

    story.append(Paragraph("9. MLOps", styles["H1"]))
    p_story(
        styles,
        story,
        ".gitignore for weights/runs/datasets; GitHub Actions CI; MLOPS_GUIDE.md; tag releases with dataset/model versions.",
    )

    story.append(Paragraph("10. Limitations and Future Work", styles["H1"]))
    bullets_story(
        styles,
        story,
        [
            "Replace pseudo full-image boxes with precise labels.",
            "Batch or backend-write if live Firestore logging grows.",
            "Explainability, RBAC, TensorRT/GStreamer as extensions.",
        ],
    )

    story.append(Paragraph("11. Conclusion", styles["H1"]))
    p_story(
        styles,
        story,
        "FabrIQ provides a **complete modular stack** for fabric defect detection suitable for SMEs and edge rollout, "
        "ready for a full paper once empirical metrics are added.",
    )

    story.append(Paragraph("References (replace with formal citations)", styles["H1"]))
    bullets_story(
        styles,
        story,
        [
            "Ultralytics YOLOv8 — https://docs.ultralytics.com",
            "Flask — https://flask.palletsprojects.com",
            "Firebase — https://firebase.google.com/docs",
        ],
    )

    story.append(Paragraph("Appendix A: Key Files", styles["H1"]))
    mono_block(
        styles,
        story,
        "organize_dataset.py          Dataset structuring\n"
        "train_yolo_detection.py       Detection training\n"
        "create_pseudo_annotations.py Bootstrap labels\n"
        "backend/app.py                 API and live stream\n"
        "frontend/                      Dashboard\n"
        "fabriq_detection_data.yaml    YOLO data config\n"
        "MLOPS_GUIDE.md                Operations",
    )

    story.append(Paragraph("Appendix B: Figures for Camera-Ready Paper", styles["H1"]))
    bullets_story(
        styles,
        story,
        [
            "Architecture diagram",
            "Sample detections with bounding boxes",
            "Training/validation curves",
            "Dashboard screenshots",
        ],
    )

    doc.build(story)
    print(f"Wrote: {OUT_PDF}")


if __name__ == "__main__":
    build()
