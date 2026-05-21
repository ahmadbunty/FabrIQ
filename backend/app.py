"""
FabrIQ Backend API
Flask backend for fabric defect detection system
"""

from flask import Flask, request, jsonify, send_from_directory, url_for, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import mimetypes
import jwt
import datetime
import base64
from functools import wraps
from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path
import threading
import time
import sys
from typing import Any, Dict, List, Optional, Tuple

from fabriq_tracking import FabricInspectionPipeline, bbox_iou

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fabriq-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # allow video uploads (200MB)

CORS(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Fix for PyTorch 2.6 weights_only issue (must be done BEFORE loading model)
try:
    import torch.serialization as ts
    from ultralytics.nn.tasks import DetectionModel
    if hasattr(ts, "add_safe_globals"):
        ts.add_safe_globals([DetectionModel])
        print("✅ PyTorch 2.6 compatibility fix applied")
    else:
        print("ℹ️ torch.serialization.add_safe_globals not available; skipping (older PyTorch)")
except Exception as e:
    print(f"⚠️ Could not apply PyTorch fix: {e}")

# Load YOLO model (update path to your trained model)
# Priority: ENV(FABRIQ_MODEL_PATH) > repo-root better.pt > cwd-relative better.pt > yolov8n.pt
MODEL_PATH_ENV = os.getenv("FABRIQ_MODEL_PATH")
_REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH_BETTER_REPO = _REPO_ROOT / "runs" / "detect" / "fabriq_defect_detection" / "weights" / "better.pt"
MODEL_PATH_BETTER_CWD = Path("runs/detect/fabriq_defect_detection/weights/better.pt")

MODEL_PATH = None
if MODEL_PATH_ENV and Path(MODEL_PATH_ENV).expanduser().exists():
    MODEL_PATH = str(Path(MODEL_PATH_ENV).expanduser().resolve())
    print(f"📁 Found model (env): {MODEL_PATH}")
elif MODEL_PATH_BETTER_REPO.exists():
    MODEL_PATH = str(MODEL_PATH_BETTER_REPO.resolve())
    print(f"📁 Found model (repo): {MODEL_PATH}")
elif MODEL_PATH_BETTER_CWD.exists():
    MODEL_PATH = str(MODEL_PATH_BETTER_CWD.resolve())
    print(f"📁 Found model (relative to cwd): {MODEL_PATH}")
else:
    # Fallback to pretrained model if trained model not found
    MODEL_PATH = "yolov8n.pt"
    print("⚠️ better.pt not found, using pretrained yolov8n.pt")

# Load YOLO model
model = None
try:
    print(f"📦 Attempting to load model from: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    print(f"✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ ERROR: Could not load model: {e}")
    print(f"   Model path: {MODEL_PATH}")
    import traceback
    traceback.print_exc()
    # Try fallback to pretrained model
    try:
        print("\n🔄 Attempting fallback to pretrained yolov8n.pt...")
        model = YOLO("yolov8n.pt")
        print("✅ Fallback model loaded (pretrained, not custom trained)")
    except Exception as e2:
        print(f"❌ CRITICAL: Could not load even pretrained model: {e2}")
        model = None

# Class names (7 classes) — order MUST match your YOLO data.yaml / trained weights indices 0..6
CLASSES = [
    'contamination',
    'selvet',
    'gray_stitch',
    'cut',
    'baekra',
    'color_issue',
    'stain',
]

DEFAULT_CAMERA_INDEX = int(os.getenv("FABRIQ_CAMERA_INDEX", "0"))
LIVE_CAMERA_INDEX = DEFAULT_CAMERA_INDEX
live_camera = None
live_streaming_active = False
live_lock = threading.Lock()
live_frame_id = 0
live_latest_payload = {
    'frameId': 0,
    'timestamp': None,
    'cameraIndex': LIVE_CAMERA_INDEX,
    'defects': [],
    'tracked_defects': [],
    'log_once_events': [],
    'roll_distance_meters': 0.0,
}

# Live session: IoU tracking + roll distance (reset on /live/start and /live/stop)
live_pipeline: Optional[FabricInspectionPipeline] = None
# Calibration: cm of fabric travel per pixel in image (set via env or POST /live/start body)
PIXEL_TO_CM_RATIO = float(os.getenv('FABRIQ_PIXEL_TO_CM_RATIO', '0.05'))
DEFAULT_MACHINE_SPEED_MPS = float(os.getenv('FABRIQ_MACHINE_SPEED_MPS', '0.0'))

def _likely_solid_green_screen(frame):
    """Detect classic virtual-webcam 'green screen' (decoder/format glitch), not real green fabric."""
    if frame is None or frame.size == 0 or frame.ndim != 3 or frame.shape[2] < 3:
        return False
    b, g, r = cv2.split(frame)
    mg, mr, mb = float(g.mean()), float(r.mean()), float(b.mean())
    if mg < 210 or mr > 90 or mb > 90:
        return False
    if float(g.std()) > 14 or float(r.std()) > 14 or float(b.std()) > 14:
        return False
    return True


def _open_local_camera(index: int):
    """Open a local capture device.

    On Windows, virtual webcams (DroidCam, iVCam) often show a solid green image when OpenCV
    uses the wrong backend or unpacks YUY2 incorrectly. Prefer DirectShow + MJPEG, then fall back.
    """
    if sys.platform != 'win32':
        return cv2.VideoCapture(index)

    mjpg = cv2.VideoWriter_fourcc(*'MJPG')
    specs = [
        (cv2.CAP_DSHOW, mjpg),
        (cv2.CAP_DSHOW, None),
        (cv2.CAP_MSMF, mjpg),
        (cv2.CAP_MSMF, None),
    ]
    for backend, fourcc in specs:
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            continue
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        if fourcc is not None:
            cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        # Virtual cams are happiest at common sizes after FOURCC is set
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        for _ in range(12):
            ok, frame = cap.read()
            if not ok or frame is None or frame.size == 0:
                continue
            if _likely_solid_green_screen(frame):
                continue
            return cap
        cap.release()

    return cv2.VideoCapture(index)


COLORS = {
    'contamination': (0, 0, 255),
    'selvet': (0, 255, 0),
    'gray_stitch': (255, 0, 0),
    'cut': (255, 165, 0),
    'baekra': (180, 105, 255),
    'color_issue': (0, 215, 255),
    'stain': (42, 42, 165),
}

# Mock users (replace with database in production)
USERS = {
    'admin@fabriq.com': {
        'password': 'admin123',
        'name': 'Admin User',
        'role': 'admin',
    },
    'supervisor@fabriq.com': {
        'password': 'super123',
        'name': 'Supervisor',
        'role': 'supervisor',
    },
}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token_header = request.headers.get('Authorization')
        token_query = request.args.get('token')
        if not token_header and not token_query:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            if token_header and token_header.startswith('Bearer '):
                token = token_header.split(' ')[1]
            elif token_query:
                token = token_query
            else:
                return jsonify({'message': 'Token is invalid'}), 401
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except Exception:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(*args, **kwargs)
    return decorated


def run_yolo_detection(frame, conf_threshold=0.25) -> Tuple[List[Dict[str, Any]], int, int]:
    """Run YOLO once; return raw defect dicts (class, confidence, bbox, bbox_normalized) and frame size."""
    frame_h, frame_w = frame.shape[:2]
    defects: List[Dict[str, Any]] = []
    results = model(frame, conf=conf_threshold)

    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            if cls >= len(CLASSES):
                continue

            class_name = CLASSES[cls]
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            defects.append({
                'class': class_name,
                'confidence': conf,
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'bbox_normalized': [x1 / frame_w, y1 / frame_h, x2 / frame_w, y2 / frame_h],
            })

    return defects, frame_w, frame_h


def annotate_from_detections(frame, rows: List[Dict[str, Any]]) -> Any:
    """Draw boxes/labels from detection or tracked rows (keys: class or class_name, bbox or bounding_box)."""
    annotated = frame.copy()
    for row in rows:
        cls = row.get('class_name') or row.get('class')
        bbox = row.get('bounding_box') or row.get('bbox')
        if not cls or not bbox or len(bbox) != 4:
            continue
        x1, y1, x2, y2 = [int(x) for x in bbox]
        conf = float(row.get('confidence', 0))
        color = COLORS.get(str(cls), (255, 165, 0))
        tid = row.get('tracking_id')
        dist = row.get('distance_meters')
        if tid is not None and dist is not None:
            label = f"ID{tid} {cls} {dist:.2f}m {conf:.2f}"
        elif tid is not None:
            label = f"ID{tid} {cls}: {conf:.2f}"
        else:
            label = f"{cls}: {conf:.2f}"

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        label_y = max(y1 - 8, label_size[1] + 8)
        cv2.rectangle(
            annotated,
            (x1, label_y - label_size[1] - 4),
            (x1 + label_size[0] + 2, label_y + 4),
            color,
            -1,
        )
        cv2.putText(
            annotated,
            label,
            (x1, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )
    return annotated


def _public_upload_url(filename: str) -> str:
    """Relative URL so Vite dev proxy (/api -> :5000) and production both work."""
    return f'/api/uploads/{filename}'


def _open_video_writer(output_path: str, fps: float, frame_size: tuple) -> cv2.VideoWriter:
    """Pick a browser-friendly MP4 codec when OpenCV supports it (fallback: mp4v)."""
    width, height = frame_size
    for fourcc_str in ('avc1', 'H264', 'mp4v'):
        fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if writer.isOpened():
            return writer
        writer.release()
    return cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))


def _merge_tracking_into_raw_defects(
    raw_defects: List[Dict[str, Any]],
    tracked_rows: List[Dict[str, Any]],
    iou_threshold: float = 0.15,
) -> List[Dict[str, Any]]:
    """Attach tracking_id and distance_meters to each raw YOLO row for API backward compatibility."""
    out = []
    for d in raw_defects:
        row = dict(d)
        bb = d.get('bbox')
        if not bb:
            out.append(row)
            continue
        best_iou = iou_threshold
        best_tid = None
        best_dist = None
        for t in tracked_rows:
            if t.get('class_name') != d.get('class'):
                continue
            tb = t.get('bounding_box')
            if not tb:
                continue
            iou = bbox_iou([float(x) for x in bb], [float(x) for x in tb])
            if iou >= best_iou:
                best_iou = iou
                best_tid = t.get('tracking_id')
                best_dist = t.get('distance_meters')
        if best_tid is not None:
            row['tracking_id'] = best_tid
            row['distance_meters'] = best_dist
        out.append(row)
    return out


def annotate_frame(frame, conf_threshold=0.25):
    """Single-frame YOLO + draw (no tracking)."""
    defects, frame_w, frame_h = run_yolo_detection(frame, conf_threshold)
    rows = [{**d, 'class_name': d['class'], 'bounding_box': d['bbox']} for d in defects]
    annotated = annotate_from_detections(frame, rows)
    return annotated, defects, frame_w, frame_h

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if email in USERS and USERS[email]['password'] == password:
        token = jwt.encode(
            {
                'email': email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return jsonify({
            'token': token,
            'user': {
                'email': email,
                'name': USERS[email]['name'],
                'role': USERS[email]['role'],
            }
        }), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/detection/analyze', methods=['POST'])
@token_required
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'message': 'No image or video provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    if model is None:
        return jsonify({
            'message': 'Model not loaded. Please check backend logs for errors.',
            'error': 'Model initialization failed. The system cannot perform detection without a loaded model.'
        }), 500
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Determine file type
        ext = Path(filename).suffix.lower()
        is_video = ext in ['.mp4', '.mov', '.avi', '.mkv']
        
        defects = []
        annotated_img = None
        annotated_video_path = None
        annotated_video_url = None
        annotated_preview_base64 = None
        img_width, img_height = 0, 0

        if is_video:
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                return jsonify({'message': 'Could not open video file'}), 400

            fps = cap.get(cv2.CAP_PROP_FPS) or 24
            img_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            img_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            annotated_video_filename = f"annotated_{Path(filename).stem}.mp4"
            annotated_video_path = os.path.join(app.config['UPLOAD_FOLDER'], annotated_video_filename)
            writer = _open_video_writer(
                annotated_video_path,
                float(fps),
                (img_width, img_height),
            )

            if not writer.isOpened():
                cap.release()
                return jsonify({'message': 'Failed to initialize video writer for annotated output'}), 500

            frame_idx = 0
            while True:
                success, frame = cap.read()
                if not success or frame is None:
                    break

                annotated_frame, frame_defects, _, _ = annotate_frame(frame, conf_threshold=0.25)
                for defect in frame_defects:
                    defect['frame'] = frame_idx
                defects.extend(frame_defects)

                writer.write(annotated_frame)

                if frame_idx == 0:
                    _, buffer_prev = cv2.imencode('.jpg', annotated_frame)
                    annotated_preview_base64 = base64.b64encode(buffer_prev).decode('utf-8')

                frame_idx += 1

            cap.release()
            writer.release()
            if frame_idx == 0:
                return jsonify({'message': 'No frames could be read from the video'}), 400

            if not os.path.isfile(annotated_video_path) or os.path.getsize(annotated_video_path) < 1024:
                return jsonify({'message': 'Annotated video file was not created or is empty'}), 500

            annotated_video_url = _public_upload_url(annotated_video_filename)
        else:
            img = cv2.imread(filepath)
            if img is None:
                return jsonify({'message': 'Unsupported file or corrupt media'}), 400

            img_height, img_width = img.shape[:2]

            annotated_img, defects, _, _ = annotate_frame(img, conf_threshold=0.25)

        annotated_img_base64 = None
        if annotated_img is not None:
            annotated_filename = f"annotated_{filename}"
            annotated_path = os.path.join(app.config['UPLOAD_FOLDER'], annotated_filename)
            cv2.imwrite(annotated_path, annotated_img)
            _, buffer = cv2.imencode('.jpg', annotated_img)
            annotated_img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Clean up uploaded file (keep annotated for now, can be cleaned later)
        # os.remove(filepath)
        
        return jsonify({
            'defects': defects,
            'defectCount': len(defects),
            'annotatedImage': f'data:image/jpeg;base64,{annotated_img_base64}' if annotated_img_base64 else (f'data:image/jpeg;base64,{annotated_preview_base64}' if annotated_preview_base64 else None),
            'annotatedVideo': annotated_video_url if annotated_video_url else None,
            'imageWidth': img_width,
            'imageHeight': img_height,
            'isVideo': is_video,
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Detection error: {e}")
        print(error_trace)
        return jsonify({
            'message': f'Detection failed: {str(e)}',
            'error': str(e)
        }), 500


@app.route('/api/live/start', methods=['POST'])
@token_required
def start_live_stream():
    global live_camera, live_streaming_active, LIVE_CAMERA_INDEX, live_pipeline, PIXEL_TO_CM_RATIO
    if model is None:
        return jsonify({'message': 'Model not loaded'}), 500

    payload = request.get_json(silent=True) or {}
    requested_camera_index = payload.get('cameraIndex', LIVE_CAMERA_INDEX)
    try:
        requested_camera_index = int(requested_camera_index)
    except (TypeError, ValueError):
        return jsonify({'message': 'cameraIndex must be an integer'}), 400

    pixel_ratio = payload.get('pixelToCmRatio', PIXEL_TO_CM_RATIO)
    try:
        pixel_ratio = float(pixel_ratio)
    except (TypeError, ValueError):
        return jsonify({'message': 'pixelToCmRatio must be a number (cm per pixel)'}), 400

    speed = payload.get('machineSpeedMps', DEFAULT_MACHINE_SPEED_MPS)
    try:
        speed = float(speed)
    except (TypeError, ValueError):
        return jsonify({'message': 'machineSpeedMps must be a number (meters per second)'}), 400

    with live_lock:
        # If source changes, release old camera first.
        if requested_camera_index != LIVE_CAMERA_INDEX and live_camera is not None:
            if live_camera.isOpened():
                live_camera.release()
            live_camera = None

        LIVE_CAMERA_INDEX = requested_camera_index
        if live_camera is None or not live_camera.isOpened():
            live_camera = _open_local_camera(LIVE_CAMERA_INDEX)
            if not live_camera.isOpened():
                live_camera = None
                return jsonify({
                    'message': f'Failed to open camera index {LIVE_CAMERA_INDEX}. Check roller camera connection.'
                }), 500
        live_streaming_active = True
        PIXEL_TO_CM_RATIO = pixel_ratio
        live_pipeline = FabricInspectionPipeline(
            pixel_to_cm_ratio=pixel_ratio,
            machine_speed_mps=speed,
        )

    return jsonify({
        'message': 'Live stream started',
        'cameraIndex': LIVE_CAMERA_INDEX,
        'pixelToCmRatio': pixel_ratio,
        'machineSpeedMps': speed,
    }), 200


@app.route('/api/live/stop', methods=['POST'])
@token_required
def stop_live_stream():
    global live_camera, live_streaming_active, live_pipeline
    with live_lock:
        live_streaming_active = False
        if live_camera is not None and live_camera.isOpened():
            live_camera.release()
        live_camera = None
        live_pipeline = None
    return jsonify({'message': 'Live stream stopped'}), 200


def live_frame_generator():
    global live_camera, live_streaming_active, live_frame_id, live_latest_payload, live_pipeline
    while True:
        with live_lock:
            if not live_streaming_active or live_camera is None or not live_camera.isOpened():
                break
            ok, frame = live_camera.read()

        if not ok or frame is None:
            time.sleep(0.02)
            continue

        try:
            frame_ts = datetime.datetime.utcnow()
            defects, _, _ = run_yolo_detection(frame, conf_threshold=0.25)

            with live_lock:
                pl = live_pipeline

            if pl is not None:
                track_out = pl.process_frame(defects, frame_ts)
                tracked_defects = track_out['tracked_defects']
                log_once_events = track_out['log_once_events']
                roll_distance_m = track_out['roll_distance_meters']
                annotated = annotate_from_detections(frame, tracked_defects)
                merged_defects = _merge_tracking_into_raw_defects(defects, tracked_defects)
            else:
                tracked_defects = []
                log_once_events = []
                roll_distance_m = 0.0
                rows = [{**d, 'class_name': d['class'], 'bounding_box': d['bbox']} for d in defects]
                annotated = annotate_from_detections(frame, rows)
                merged_defects = defects

            with live_lock:
                live_frame_id += 1
                live_latest_payload = {
                    'frameId': live_frame_id,
                    'timestamp': frame_ts.isoformat() + 'Z',
                    'cameraIndex': LIVE_CAMERA_INDEX,
                    'defects': merged_defects,
                    'tracked_defects': tracked_defects,
                    'log_once_events': log_once_events,
                    'roll_distance_meters': roll_distance_m,
                }
            success, buffer = cv2.imencode('.jpg', annotated)
            if not success:
                continue
            jpg = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')
        except Exception as e:
            print(f"Live streaming frame error: {e}")
            continue


@app.route('/api/live/stream', methods=['GET'])
@token_required
def live_stream():
    return Response(
        live_frame_generator(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/api/live/latest', methods=['GET'])
@token_required
def live_latest():
    with live_lock:
        payload = dict(live_latest_payload)
        payload['defects'] = list(live_latest_payload.get('defects', []))
        payload['isStreaming'] = live_streaming_active
    return jsonify(payload), 200


@app.route('/api/live/sources', methods=['GET'])
@token_required
def live_sources():
    # Common source presets for current laptop and future Jetson setup.
    return jsonify({
        'activeCameraIndex': LIVE_CAMERA_INDEX,
        'defaultCameraIndex': DEFAULT_CAMERA_INDEX,
        'sources': [
            {'label': 'Built-in webcam (0)', 'cameraIndex': 0},
            {'label': 'USB / DroidCam or iVCam phone (1)', 'cameraIndex': 1},
            {'label': 'Arducam / CSI / extra camera (2)', 'cameraIndex': 2},
            {'label': 'Custom index (3)', 'cameraIndex': 3},
        ],
    }), 200

@app.route('/api/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats():
    # Mock data - replace with database queries
    return jsonify({
        'totalInspections': 1250,
        'defectsDetected': 234,
        'qualityScore': 85,
        'avgProcessingTime': 245,
    }), 200

@app.route('/api/dashboard/recent-detections', methods=['GET'])
@token_required
def get_recent_detections():
    # Mock data with today's date - replace with database queries
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    
    return jsonify([
        {'class': 'contamination', 'timestamp': (now - timedelta(minutes=30)).isoformat() + 'Z'},
        {'class': 'stain', 'timestamp': (now - timedelta(minutes=25)).isoformat() + 'Z'},
        {'class': 'gray_stitch', 'timestamp': (now - timedelta(hours=1)).isoformat() + 'Z'},
        {'class': 'cut', 'timestamp': (now - timedelta(hours=2)).isoformat() + 'Z'},
    ]), 200

@app.route('/api/analytics/defect-distribution', methods=['GET'])
@token_required
def get_defect_distribution():
    # Mock data - replace with database queries
    return jsonify([
        {'name': 'contamination', 'value': 22},
        {'name': 'selvet', 'value': 18},
        {'name': 'gray_stitch', 'value': 15},
        {'name': 'cut', 'value': 12},
        {'name': 'baekra', 'value': 10},
        {'name': 'color_issue', 'value': 14},
        {'name': 'stain', 'value': 20},
    ]), 200

@app.route('/api/uploads/<path:filename>', methods=['GET'])
@app.route('/uploads/<path:filename>', methods=['GET'])
def serve_uploaded_file(filename):
    """Serve annotated media; ?download=1 forces browser download."""
    download = request.args.get('download', '').lower() in ('1', 'true', 'yes')
    mime, _ = mimetypes.guess_type(filename)
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        mimetype=mime or 'application/octet-stream',
        as_attachment=download,
        download_name=Path(filename).name if download else None,
    )

@app.route('/api/analytics/defect-trends', methods=['GET'])
@token_required
def get_defect_trends():
    range_param = request.args.get('range', '7d')
    # Mock data - replace with database queries
    return jsonify([
        {'date': '2024-01-01', 'count': 45},
        {'date': '2024-01-02', 'count': 52},
        {'date': '2024-01-03', 'count': 38},
        {'date': '2024-01-04', 'count': 61},
        {'date': '2024-01-05', 'count': 48},
    ]), 200

@app.route('/api/analytics/quality-trends', methods=['GET'])
@token_required
def get_quality_trends():
    # Mock data - replace with database queries
    return jsonify([
        {'date': '2024-01-01', 'grade': 'A', 'count': 120},
        {'date': '2024-01-01', 'grade': 'B', 'count': 80},
        {'date': '2024-01-01', 'grade': 'C', 'count': 30},
    ]), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - redirects to API info"""
    return jsonify({
        'message': 'FabrIQ API Server',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'login': '/api/auth/login',
            'detection': '/api/detection/analyze',
            'dashboard': '/api/dashboard/stats',
        },
        'model_loaded': model is not None,
    }), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
    }), 200

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 FabrIQ Backend API Server")
    print("="*60)
    print(f"📡 Server running on: http://0.0.0.0:5000")
    print(f"🔗 API Base URL: http://localhost:5000/api")
    print(f"✅ Model Status: {'Loaded' if model is not None else 'Not Loaded'}")
    print("="*60)
    print("\n💡 Frontend should connect to: http://localhost:5000/api")
    print("📝 Test API: http://localhost:5000/api/health\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

