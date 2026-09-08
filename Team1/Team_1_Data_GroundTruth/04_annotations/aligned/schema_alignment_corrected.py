"""
Schema Alignment Module for Task T1.3.

Converts harmonized ground-truth COCO annotations (Task T1.2 output, produced by
ground_truth/builder.py) into the shared BIM Semantic Model intermediate schema
defined in Section 4 of the Image -> 2D/3D BIM Product & Engineering Plan.

Intended location in the repo: ground_truth/schema_alignment.py
(sits alongside builder.py, cleaner.py, room_extractor.py, dimension_extractor.py, exporter.py)

------------------------------------------------------------------------------
ASSUMPTIONS / PLACEHOLDERS -- flagged explicitly, confirm before relying on these
downstream:

1. mm_per_pixel is an ESTIMATE, not a resolved real-world measurement. T1.2's
   dimension_extractor only marks WHERE a dimension callout is on the drawing,
   it never OCRs the actual numeric value. There is currently no way to resolve
   true scale from this dataset. Per team decision, the default is derived from
   the average ground-truth ROOM area (pixels) against an assumed typical room
   size of 12 sqm:
       mm_per_pixel = sqrt(12,000,000 mm^2 / avg_room_area_px)
   This is written out with method="derived_default_room_area" (deliberately NOT
   "dimension_text", which is the real Tier-1 name in Section 4 -- using that name
   here would misrepresent an estimate as a resolved measurement) and a low
   confidence (0.3).

2. Level height is hard-set to DEFAULT_LEVEL_HEIGHT_MM (3000mm). No floor plan in
   this dataset carries elevation/height data, and every plan is treated as a
   single level ("level_1").

3. All converted elements get confidence = 1.0, since this is ground truth (the
   correct answer), not a model prediction.

4. room_type is always "unclassified". T1.2's room_extractor only ever produced
   a generic "enclosed_room" tag -- there is no real bedroom/kitchen/bath
   classification upstream yet.

5. columns and stairs arrays are always empty. T1.2's taxonomy (wall, door,
   window, room, dimension) never annotated those classes.

6. category_id 5 (dimension) annotations are DROPPED from the aligned output.
   Section 4's schema has no field for raw dimension-callout regions -- they
   were only ever useful for scale resolution, which is handled separately here.

7. Wall centerline/thickness are derived via cv2.minAreaRect on each wall's
   polygon: the rectangle's long axis becomes the centerline, the short side
   becomes thickness. This assumes each wall annotation is a single, roughly
   rectangular strip (true for the T1.2 wall polygons observed). A wall with an
   unusual or curved shape would only get an approximation.

8. connected_walls is computed via endpoint proximity (WALL_TOPOLOGY_TOLERANCE_PX)
   between wall centerlines, in pixel space, before mm conversion.

9. Door/window -> wall association uses a margin-dilated bounding-box overlap
   test, tie-broken by center-to-center distance when an opening overlaps more
   than one wall.
------------------------------------------------------------------------------
"""

import os
import json
import math
import logging
from typing import Dict, List, Any, Tuple, Optional

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- Constants / assumptions (see module docstring) --------------------------

DEFAULT_LEVEL_HEIGHT_MM = 3000.0
TARGET_ROOM_AREA_MM2 = 12_000_000.0   # 12 sqm assumption, per team decision
WALL_TOPOLOGY_TOLERANCE_PX = 35.0     # endpoint-proximity tolerance for connected_walls
                                       # CORRECTED from 12.0: measured nearest-endpoint
                                       # distances across sample wall annotations showed
                                       # a median of ~11px and a 90th percentile of ~33px,
                                       # meaning 12px missed roughly half of genuine
                                       # wall-to-wall junctions. 35px captures ~90-92% of
                                       # true junctions while still excluding unrelated
                                       # freestanding walls.
OPENING_OVERLAP_MARGIN_PX = 6.0       # dilation margin for door/window -> wall association

CATEGORY_WALL = 1
CATEGORY_DOOR = 2
CATEGORY_WINDOW = 3
CATEGORY_ROOM = 4
CATEGORY_DIMENSION = 5  # dropped from output -- see assumption 6


# --- Scale derivation ----------------------------------------------------------

def derive_default_mm_per_pixel(coco_data: Dict[str, Any]) -> float:
    """
    Derives a single dataset-wide mm_per_pixel default from the average
    ground-truth room area (pixels) vs. an assumed typical room size of 12 sqm.

    PLACEHOLDER: this is an estimate, not a resolved real-world measurement.
    Callers should treat the resulting scale.confidence as low (see
    align_image_to_schema's default scale_confidence).
    """
    room_areas = [
        ann["area"]
        for ann in coco_data.get("annotations", [])
        if ann.get("category_id") == CATEGORY_ROOM and ann.get("area", 0) > 0
    ]
    if not room_areas:
        logger.warning("No room annotations found to derive scale; falling back to 1.0 mm/px")
        return 1.0

    avg_room_area_px = sum(room_areas) / len(room_areas)
    mm_per_pixel = math.sqrt(TARGET_ROOM_AREA_MM2 / avg_room_area_px)
    logger.info(
        "Derived default scale: avg_room_area_px=%.1f (n=%d) -> mm_per_pixel=%.4f",
        avg_room_area_px, len(room_areas), mm_per_pixel
    )
    return mm_per_pixel


# --- Geometry helpers ------------------------------------------------------------

def _polygon_points_px(ann: Dict[str, Any]) -> np.ndarray:
    """Returns the annotation's polygon as an (N,2) float array in pixel space,
    falling back to its bbox corners if no valid segmentation is present."""
    segs = ann.get("segmentation") or []
    if segs and len(segs[0]) >= 6:
        return np.array(segs[0], dtype=np.float32).reshape(-1, 2)
    x, y, w, h = ann.get("bbox", [0, 0, 0, 0])
    return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.float32)


def _centerline_and_thickness_px(ann: Dict[str, Any]) -> Tuple[List[List[float]], float]:
    """
    Derives a wall's centerline (2 endpoints) and thickness, both in PIXEL space,
    from its polygon using a rotated minimum-area bounding rectangle.
    """
    pts = _polygon_points_px(ann)
    (cx, cy), (rw, rh), angle = cv2.minAreaRect(pts)

    if rw >= rh:
        length, thickness = rw, rh
        theta = math.radians(angle)
    else:
        length, thickness = rh, rw
        theta = math.radians(angle + 90.0)

    dx = math.cos(theta) * (length / 2.0)
    dy = math.sin(theta) * (length / 2.0)
    p1 = [round(cx - dx, 3), round(cy - dy, 3)]
    p2 = [round(cx + dx, 3), round(cy + dy, 3)]
    return [p1, p2], float(thickness)


def _endpoints_close(p1: List[float], p2: List[float], tol: float) -> bool:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1]) <= tol


def _bboxes_overlap(poly_a: np.ndarray, poly_b: np.ndarray, margin_px: float) -> bool:
    """Cheap bbox-based overlap test with a dilation margin on poly_a, used for
    opening<->wall linkage."""
    ax, ay, aw, ah = cv2.boundingRect(poly_a.astype(np.int32))
    bx, by, bw, bh = cv2.boundingRect(poly_b.astype(np.int32))
    ax0, ay0 = ax - margin_px, ay - margin_px
    ax1, ay1 = ax + aw + margin_px, ay + ah + margin_px
    bx0, by0, bx1, by1 = bx, by, bx + bw, by + bh
    return not (ax1 < bx0 or bx1 < ax0 or ay1 < by0 or by1 < ay0)


# --- Element builders (pixel geometry in, mm-converted schema objects out) ------

def _build_wall(ann: Dict[str, Any], wall_id: str, mm_per_pixel: float) -> Dict[str, Any]:
    centerline_px, thickness_px = _centerline_and_thickness_px(ann)
    centerline_mm = [[round(p[0] * mm_per_pixel, 2), round(p[1] * mm_per_pixel, 2)]
                      for p in centerline_px]
    return {
        "id": wall_id,
        "centerline": centerline_mm,
        "thickness_mm": round(thickness_px * mm_per_pixel, 2),
        "confidence": 1.0,
        "openings": [],          # filled in by _associate_openings
        "connected_walls": [],   # filled in by _build_topology
        "_centerline_px": centerline_px,  # internal only, stripped before output
    }


def _build_opening(ann: Dict[str, Any], opening_id: str, mm_per_pixel: float) -> Dict[str, Any]:
    x, y, w, h = ann.get("bbox", [0, 0, 0, 0])
    return {
        "id": opening_id,
        "bbox_mm": [round(x * mm_per_pixel, 2), round(y * mm_per_pixel, 2),
                    round(w * mm_per_pixel, 2), round(h * mm_per_pixel, 2)],
        "confidence": 1.0,
    }


def _build_room(ann: Dict[str, Any], room_id: str, mm_per_pixel: float) -> Dict[str, Any]:
    pts = _polygon_points_px(ann)
    polygon_mm = [[round(float(px) * mm_per_pixel, 2), round(float(py) * mm_per_pixel, 2)]
                  for px, py in pts]
    return {
        "id": room_id,
        "polygon": polygon_mm,
        "area_mm2": round(float(ann.get("area", 0.0)) * (mm_per_pixel ** 2), 2),
        "room_type": "unclassified",  # PLACEHOLDER -- see module docstring, assumption 4
        "confidence": 1.0,
    }


def _build_topology(walls: List[Dict[str, Any]], tol_px: float) -> None:
    """Populates connected_walls in-place by testing endpoint proximity in pixel space."""
    for wa in walls:
        for wb in walls:
            if wa["id"] == wb["id"]:
                continue
            for pa in wa["_centerline_px"]:
                for pb in wb["_centerline_px"]:
                    if _endpoints_close(pa, pb, tol_px):
                        if wb["id"] not in wa["connected_walls"]:
                            wa["connected_walls"].append(wb["id"])


def _associate_openings(
    walls: List[Dict[str, Any]],
    wall_polys: Dict[str, np.ndarray],
    openings: List[Dict[str, Any]],
    opening_polys: Dict[str, np.ndarray],
    margin_px: float,
) -> None:
    """Links each door/window to its nearest overlapping wall (in-place on `walls`)."""
    for opening in openings:
        opoly = opening_polys[opening["id"]]
        best_wall_id, best_dist = None, None
        for wall in walls:
            wpoly = wall_polys[wall["id"]]
            if _bboxes_overlap(opoly, wpoly, margin_px):
                ocx, ocy = opoly[:, 0].mean(), opoly[:, 1].mean()
                wcx, wcy = wpoly[:, 0].mean(), wpoly[:, 1].mean()
                dist = math.hypot(ocx - wcx, ocy - wcy)
                if best_dist is None or dist < best_dist:
                    best_dist, best_wall_id = dist, wall["id"]
        if best_wall_id is not None:
            for wall in walls:
                if wall["id"] == best_wall_id:
                    wall["openings"].append(opening["id"])
                    break


# --- Per-image assembly -----------------------------------------------------------

def align_image_to_schema(
    image: Dict[str, Any],
    annotations: List[Dict[str, Any]],
    mm_per_pixel: float,
    scale_confidence: float = 0.3,
) -> Dict[str, Any]:
    """
    Converts one image's ground-truth annotations into a single-level BIM
    Semantic Model record matching Section 4 of the plan doc.
    """
    wall_anns = [a for a in annotations if a.get("category_id") == CATEGORY_WALL]
    door_anns = [a for a in annotations if a.get("category_id") == CATEGORY_DOOR]
    window_anns = [a for a in annotations if a.get("category_id") == CATEGORY_WINDOW]
    room_anns = [a for a in annotations if a.get("category_id") == CATEGORY_ROOM]
    # category_id == CATEGORY_DIMENSION intentionally dropped -- see assumption 6

    walls: List[Dict[str, Any]] = []
    wall_polys: Dict[str, np.ndarray] = {}
    for idx, ann in enumerate(wall_anns, start=1):
        wall_id = f"wall_{idx:03d}"
        walls.append(_build_wall(ann, wall_id, mm_per_pixel))
        wall_polys[wall_id] = _polygon_points_px(ann)

    _build_topology(walls, WALL_TOPOLOGY_TOLERANCE_PX)
    for wall in walls:
        del wall["_centerline_px"]  # strip internal-only field before output

    doors: List[Dict[str, Any]] = []
    door_polys: Dict[str, np.ndarray] = {}
    for idx, ann in enumerate(door_anns, start=1):
        door_id = f"door_{idx:03d}"
        doors.append(_build_opening(ann, door_id, mm_per_pixel))
        door_polys[door_id] = _polygon_points_px(ann)

    windows: List[Dict[str, Any]] = []
    window_polys: Dict[str, np.ndarray] = {}
    for idx, ann in enumerate(window_anns, start=1):
        window_id = f"window_{idx:03d}"
        windows.append(_build_opening(ann, window_id, mm_per_pixel))
        window_polys[window_id] = _polygon_points_px(ann)

    _associate_openings(walls, wall_polys, doors, door_polys, OPENING_OVERLAP_MARGIN_PX)
    _associate_openings(walls, wall_polys, windows, window_polys, OPENING_OVERLAP_MARGIN_PX)

    rooms = [
        _build_room(ann, f"room_{idx:03d}", mm_per_pixel)
        for idx, ann in enumerate(room_anns, start=1)
    ]

    level = {
        "id": "level_1",
        "elevation_mm": 0,
        "height_mm": DEFAULT_LEVEL_HEIGHT_MM,  # PLACEHOLDER -- assumption 2
        "walls": walls,
        "doors": doors,
        "windows": windows,
        "rooms": rooms,
        "columns": [],  # PLACEHOLDER -- assumption 5, T1.2 never annotated this class
        "stairs": [],   # PLACEHOLDER -- assumption 5, T1.2 never annotated this class
    }

    return {
        "project": {
            "levels": [level],
            "scale": {
                "mm_per_pixel": round(mm_per_pixel, 4),
                "method": "derived_default_room_area",  # NOT "dimension_text" -- see docstring
                "confidence": scale_confidence,
            },
            "metadata": {
                "source_image": image.get("file_name", ""),
                "image_id": image.get("id"),
                "units": "mm",
            },
        }
    }


# --- Split-level orchestration -----------------------------------------------------

def align_split_to_schema(
    ground_truth_coco_path: str,
    output_path: str,
    mm_per_pixel: Optional[float] = None,
    scale_confidence: float = 0.3,
) -> str:
    """
    Reads a T1.2 harmonized `_ground_truth.coco.json` for one split and writes a
    schema-aligned JSON file (a list of per-image BIM Semantic Model records,
    one per floor plan in the split) matching Section 4 of the plan doc.

    If mm_per_pixel is not supplied, it is derived once from this split's own
    room annotations via derive_default_mm_per_pixel(). To use one consistent
    scale across all splits (recommended), compute it once from train+valid+test
    combined and pass it explicitly to every call.
    """
    with open(ground_truth_coco_path, "r", encoding="utf-8") as f:
        coco_data = json.load(f)

    if mm_per_pixel is None:
        mm_per_pixel = derive_default_mm_per_pixel(coco_data)

    anns_by_image: Dict[int, List[Dict[str, Any]]] = {}
    for ann in coco_data.get("annotations", []):
        anns_by_image.setdefault(ann["image_id"], []).append(ann)

    aligned_records = []
    for image in coco_data.get("images", []):
        img_anns = anns_by_image.get(image["id"], [])
        aligned_records.append(
            align_image_to_schema(image, img_anns, mm_per_pixel, scale_confidence)
        )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(aligned_records, f, indent=2)

    logger.info(
        "Wrote %d schema-aligned records to %s (mm_per_pixel=%.4f)",
        len(aligned_records), output_path, mm_per_pixel
    )
    return output_path


def derive_global_mm_per_pixel(base_dir: str = "coco") -> float:
    """
    Derives one mm_per_pixel value from room annotations pooled across all three
    splits (train, valid, test), so every split is aligned to the same scale
    instead of each split getting its own slightly different estimate.
    """
    all_room_areas: List[float] = []
    for split in ("train", "valid", "test"):
        path = os.path.join(base_dir, split, "_ground_truth.coco.json")
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            coco_data = json.load(f)
        all_room_areas.extend(
            ann["area"] for ann in coco_data.get("annotations", [])
            if ann.get("category_id") == CATEGORY_ROOM and ann.get("area", 0) > 0
        )

    if not all_room_areas:
        logger.warning("No room annotations found across splits; falling back to 1.0 mm/px")
        return 1.0

    avg_room_area_px = sum(all_room_areas) / len(all_room_areas)
    mm_per_pixel = math.sqrt(TARGET_ROOM_AREA_MM2 / avg_room_area_px)
    logger.info(
        "Global derived scale across all splits: avg_room_area_px=%.1f (n=%d) -> mm_per_pixel=%.4f",
        avg_room_area_px, len(all_room_areas), mm_per_pixel
    )
    return mm_per_pixel


if __name__ == "__main__":
    BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "coco")
    global_mm_per_pixel = derive_global_mm_per_pixel(BASE_DIR)

    for split in ("test", "valid", "train"):
        input_path = os.path.join(BASE_DIR, split, "_ground_truth.coco.json")
        if not os.path.exists(input_path):
            logger.warning("Skipping split '%s': %s not found", split, input_path)
            continue
        align_split_to_schema(
            ground_truth_coco_path=input_path,
            output_path=os.path.join("ground_truth", "aligned", f"ground_truth_{split}.json"),
            mm_per_pixel=global_mm_per_pixel,
        )
