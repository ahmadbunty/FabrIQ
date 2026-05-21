"""
FabrIQ — tracking + roll distance for moving-web fabric inspection.

Lifecycle (IoU tracker):
  - Each frame: YOLO boxes are matched to existing tracks by class + IoU (greedy, high conf first).
  - Matched tracks update bbox/centroid and reset a miss counter.
  - Unmatched tracks increment misses; after MAX_MISSED_FRAMES (3) the track is removed.
  - New detections spawn a new persistent tracking_id.

Distance model:
  - roll_distance_m accumulates: d += machine_speed_mps * delta_t between frames.
  - PIXEL_TO_CM_RATIO: centimeters of web travel per pixel in the image (calibrate from camera height / FOV).
  - Vertical center y of the bbox maps pixel position to along-web offset:
        D_total_m = roll_distance_m + y_center * (PIXEL_TO_CM_RATIO / 100.0)

If the web moves horizontally in your setup, use x_center instead and adjust calibration accordingly.

Logging (Firestore dedupe):
  - log_once_events: emitted only for tracking_ids created this frame (first sighting).
  - Optional: extend with "track_lost" events using removed track metadata if you need exit logging.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

MAX_MISSED_FRAMES = 3
DEFAULT_IOU_MATCH_THRESHOLD = 0.25


def bbox_iou(a: List[float], b: List[float]) -> float:
    """Intersection-over-union for [x1, y1, x2, y2] (xyxy)."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    iw = max(0.0, inter_x2 - inter_x1)
    ih = max(0.0, inter_y2 - inter_y1)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return float(inter / union) if union > 0 else 0.0


@dataclass
class Track:
    tracking_id: int
    class_name: str
    bbox: List[int]
    confidence: float
    missed_frames: int = 0
    first_seen_ts: Optional[dt.datetime] = None
    last_seen_ts: Optional[dt.datetime] = None


class IoUFabricTracker:
    """Greedy IoU + class consistency matching across consecutive frames."""

    def __init__(
        self,
        iou_threshold: float = DEFAULT_IOU_MATCH_THRESHOLD,
        max_missed: int = MAX_MISSED_FRAMES,
    ) -> None:
        self.iou_threshold = iou_threshold
        self.max_missed = max_missed
        self._tracks: Dict[int, Track] = {}
        self._next_id = 1

    def reset(self) -> None:
        self._tracks.clear()
        self._next_id = 1

    def _new_id(self) -> int:
        tid = self._next_id
        self._next_id += 1
        return tid

    def update(
        self,
        detections: List[Dict[str, Any]],
        frame_timestamp: dt.datetime,
    ) -> Tuple[List[Track], List[int]]:
        """
        Returns:
            active_tracks: all tracks still alive after this frame
            new_track_ids: ids created this frame (for one-time logging)
        """
        dets = [d for d in detections if d.get("bbox") and len(d["bbox"]) == 4 and d.get("class")]
        dets = sorted(dets, key=lambda d: -float(d.get("confidence", 0.0)))

        prev_ids = list(self._tracks.keys())
        used_track_ids: set = set()
        used_det_indices: set = set()

        for di, det in enumerate(dets):
            cls = str(det["class"])
            bbox = [float(x) for x in det["bbox"]]
            best_tid: Optional[int] = None
            best_iou = self.iou_threshold
            for tid in prev_ids:
                if tid in used_track_ids or tid not in self._tracks:
                    continue
                tr = self._tracks[tid]
                if tr.class_name != cls:
                    continue
                iou = bbox_iou(bbox, [float(x) for x in tr.bbox])
                if iou >= best_iou:
                    best_iou = iou
                    best_tid = tid
            if best_tid is not None:
                used_track_ids.add(best_tid)
                used_det_indices.add(di)
                tr = self._tracks[best_tid]
                tr.bbox = [int(round(x)) for x in bbox]
                tr.confidence = float(det.get("confidence", tr.confidence))
                tr.missed_frames = 0
                tr.last_seen_ts = frame_timestamp
                if tr.first_seen_ts is None:
                    tr.first_seen_ts = frame_timestamp

        new_track_ids: List[int] = []
        for di, det in enumerate(dets):
            if di in used_det_indices:
                continue
            tid = self._new_id()
            bbox_i = [int(round(x)) for x in det["bbox"]]
            tr = Track(
                tracking_id=tid,
                class_name=str(det["class"]),
                bbox=bbox_i,
                confidence=float(det.get("confidence", 0.0)),
                missed_frames=0,
                first_seen_ts=frame_timestamp,
                last_seen_ts=frame_timestamp,
            )
            self._tracks[tid] = tr
            new_track_ids.append(tid)
            used_track_ids.add(tid)

        for tid in prev_ids:
            if tid in used_track_ids:
                continue
            if tid not in self._tracks:
                continue
            tr = self._tracks[tid]
            tr.missed_frames += 1
            if tr.missed_frames > self.max_missed:
                del self._tracks[tid]

        return list(self._tracks.values()), new_track_ids


class RollDistanceModel:
    """Integrates machine speed over time and maps pixel y to along-web meters."""

    def __init__(self, pixel_to_cm_ratio: float = 0.05) -> None:
        self.pixel_to_cm_ratio = float(pixel_to_cm_ratio)
        self._meters_per_pixel = self.pixel_to_cm_ratio / 100.0
        self.roll_distance_m = 0.0
        self._last_ts: Optional[dt.datetime] = None

    def reset(self) -> None:
        self.roll_distance_m = 0.0
        self._last_ts = None

    def set_pixel_to_cm_ratio(self, value: float) -> None:
        self.pixel_to_cm_ratio = float(value)
        self._meters_per_pixel = self.pixel_to_cm_ratio / 100.0

    def advance_roll(self, frame_timestamp: dt.datetime, machine_speed_mps: float) -> None:
        """D_roll += speed * delta_t (ignore non-monotonic or huge gaps)."""
        if self._last_ts is None:
            self._last_ts = frame_timestamp
            return
        delta = (frame_timestamp - self._last_ts).total_seconds()
        self._last_ts = frame_timestamp
        if delta <= 0 or delta > 2.0:
            return
        self.roll_distance_m += float(machine_speed_mps) * delta

    def total_distance_for_bbox(self, bbox: List[int]) -> float:
        """D_total_m = roll_distance_m + y_center * meters_per_pixel."""
        y1, y2 = int(bbox[1]), int(bbox[3])
        y_center = 0.5 * (y1 + y2)
        return float(self.roll_distance_m + y_center * self._meters_per_pixel)


class FabricInspectionPipeline:
    """Session state: distance integration + IoU tracker (live or offline video)."""

    def __init__(
        self,
        pixel_to_cm_ratio: float,
        machine_speed_mps: float,
        iou_threshold: float = DEFAULT_IOU_MATCH_THRESHOLD,
    ) -> None:
        self.distance = RollDistanceModel(pixel_to_cm_ratio=pixel_to_cm_ratio)
        self.tracker = IoUFabricTracker(iou_threshold=iou_threshold)
        self.machine_speed_mps = float(machine_speed_mps)

    def reset(self) -> None:
        self.distance.reset()
        self.tracker.reset()

    def set_machine_speed(self, mps: float) -> None:
        self.machine_speed_mps = float(mps)

    def set_pixel_to_cm_ratio(self, cm_per_px: float) -> None:
        self.distance.set_pixel_to_cm_ratio(cm_per_px)

    def process_frame(
        self,
        raw_detections: List[Dict[str, Any]],
        frame_timestamp: dt.datetime,
        machine_speed_mps: Optional[float] = None,
    ) -> Dict[str, Any]:
        speed = float(machine_speed_mps if machine_speed_mps is not None else self.machine_speed_mps)
        self.distance.advance_roll(frame_timestamp, speed)

        tracks, new_track_ids = self.tracker.update(raw_detections, frame_timestamp)

        tracked_defects_list: List[Dict[str, Any]] = []
        for tr in sorted(tracks, key=lambda t: t.tracking_id):
            d_m = self.distance.total_distance_for_bbox(tr.bbox)
            tracked_defects_list.append(
                {
                    "tracking_id": tr.tracking_id,
                    "class_name": tr.class_name,
                    "confidence": tr.confidence,
                    "distance_meters": round(d_m, 4),
                    "timestamp": (tr.last_seen_ts or frame_timestamp).isoformat() + "Z",
                    "bounding_box": list(tr.bbox),
                    "missed_frames": tr.missed_frames,
                }
            )

        log_once_events: List[Dict[str, Any]] = []
        for tid in new_track_ids:
            tr = next((t for t in tracks if t.tracking_id == tid), None)
            if tr is None:
                continue
            d_m = self.distance.total_distance_for_bbox(tr.bbox)
            log_once_events.append(
                {
                    "tracking_id": tr.tracking_id,
                    "class_name": tr.class_name,
                    "confidence": tr.confidence,
                    "distance_meters": round(d_m, 4),
                    "timestamp": (tr.first_seen_ts or frame_timestamp).isoformat() + "Z",
                    "bounding_box": list(tr.bbox),
                    "event": "first_track",
                }
            )

        return {
            "tracked_defects": tracked_defects_list,
            "log_once_events": log_once_events,
            "roll_distance_meters": round(self.distance.roll_distance_m, 4),
            "machine_speed_mps": speed,
            "pixel_to_cm_ratio": self.distance.pixel_to_cm_ratio,
        }
