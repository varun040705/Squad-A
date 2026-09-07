"""
Heuristic Image-Quality Metrics for Task T1.5 (Edge-Case Set Curation).
Computes cheap, content-blind signals used to flag potentially difficult
floor-plan images: blur/sharpness, visual clutter, and rotation/skew.

------------------------------------------------------------------------------
ASSUMPTIONS / PLACEHOLDERS -- flagged explicitly, confirm before relying on
these downstream:

1. These are PIXEL-LEVEL PROXIES, not real difficulty labels. They have no
   understanding of floor-plan content (they can't tell "faded ink" from
   "genuinely low-res", or "hand-drawn" from "clean CAD"). They are only
   useful for ranking relative difficulty *within* a batch of similar images.

2. `has_text` / `has_dimensions` come from Tesseract OCR run on a downscaled
   copy of the image (960x540) for speed. `has_dimensions` is a crude proxy:
   true if OCR found 2+ numeric tokens anywhere in the image -- it cannot
   distinguish an actual dimension callout from an unrelated number (a room
   ID, a page number, etc).

3. `rotation_clean_frac` estimates how axis-aligned an image's straight edges
   are, using Hough line angles. It assumes floor plans are normally drawn
   with walls at 0/90 degrees -- a plan that is legitimately drawn at an
   angle (e.g. an angled building wing) will register as "rotated" even
   though nothing is actually wrong with the source image.

4. Quality/difficulty bucketing (see `bucket_quality`, `bucket_difficulty`)
   is PERCENTILE-RELATIVE to whatever batch of images you pass in, not an
   absolute standard. Re-running on a different or larger batch will shift
   the thresholds and can change which images land in which bucket.
------------------------------------------------------------------------------
"""

import re
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, List

import cv2
import numpy as np
import pytesseract

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

_NUM_RE = re.compile(r"\d+")
_OCR_RESIZE = (960, 540)
_OCR_CONFIG = "--psm 11 --oem 1"


@dataclass
class ImageMetrics:
    image_id: str
    filename: str
    width: int
    height: int
    orientation: str
    blur_var: float
    edge_density: float
    rotation_clean_frac: float
    has_text: bool
    has_dimensions: bool
    ocr_char_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_image_metrics(path: str, image_id: str, filename: str) -> ImageMetrics:
    """
    Computes all heuristic metrics for a single image. See module docstring
    for what each metric does and does not tell you.
    """
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Could not read image: {path}")

    h, w = img.shape[:2]
    orientation = "landscape" if w >= h else "portrait"
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.count_nonzero(edges)) / (w * h)

    rotation_clean_frac = _estimate_rotation_cleanliness(edges, w, h)

    has_text, has_dimensions, ocr_char_count = _run_ocr(gray, w)

    return ImageMetrics(
        image_id=image_id,
        filename=filename,
        width=w,
        height=h,
        orientation=orientation,
        blur_var=round(blur_var, 2),
        edge_density=round(edge_density, 5),
        rotation_clean_frac=round(rotation_clean_frac, 3),
        has_text=has_text,
        has_dimensions=has_dimensions,
        ocr_char_count=ocr_char_count,
    )


def _estimate_rotation_cleanliness(edges: np.ndarray, w: int, h: int) -> float:
    """
    Fraction of detected straight-line segments whose angle sits within 3
    degrees of an axis (0/90/180/270). High = plan is drawn axis-aligned.
    Low = plan appears rotated/skewed (see assumption 3 in module docstring).
    """
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=80,
        minLineLength=min(w, h) // 6, maxLineGap=10,
    )
    if lines is None or len(lines) == 0:
        return 0.0

    angles = []
    for l in lines[:, 0]:
        x1, y1, x2, y2 = l
        ang = np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180
        angles.append(ang)
    angles = np.array(angles)
    dist_to_axis = np.minimum(angles % 90, 90 - (angles % 90))
    return float(np.mean(dist_to_axis <= 3))


def _run_ocr(gray: np.ndarray, width: int):
    """Runs Tesseract on a downscaled copy for speed. See assumption 2."""
    small = cv2.resize(gray, _OCR_RESIZE) if width > _OCR_RESIZE[0] else gray
    try:
        text = pytesseract.image_to_string(small, config=_OCR_CONFIG)
    except Exception as e:
        logger.warning("OCR failed: %s", e)
        text = ""
    text_clean = text.strip()
    has_text = len(re.sub(r"[^A-Za-z0-9]", "", text_clean)) >= 3
    has_dimensions = len(_NUM_RE.findall(text_clean)) >= 2
    return has_text, has_dimensions, len(text_clean)


def bucket_quality(metrics: List[ImageMetrics]) -> Dict[str, str]:
    """
    Buckets each image into HIGH/MEDIUM/LOW sharpness, relative to the
    33rd/66th percentile of blur_var *within this batch* (see assumption 4).
    Returns {image_id: bucket}.
    """
    blur_sorted = sorted(m.blur_var for m in metrics)
    p33 = _percentile(blur_sorted, 0.33)
    p66 = _percentile(blur_sorted, 0.66)

    result = {}
    for m in metrics:
        if m.blur_var <= p33:
            result[m.image_id] = "LOW"
        elif m.blur_var <= p66:
            result[m.image_id] = "MEDIUM"
        else:
            result[m.image_id] = "HIGH"
    return result


def bucket_difficulty(metrics: List[ImageMetrics], quality: Dict[str, str]) -> Dict[str, str]:
    """
    Rule-of-thumb EASY/MEDIUM/HARD combining quality, clutter (edge density),
    and rotation cleanliness. Scoring: +1 for LOW quality, +1 for edge_density
    above the batch's 66th percentile, +1 for rotation_clean_frac < 0.9.
    0 -> EASY, 1 -> MEDIUM, 2+ -> HARD.
    """
    edge_sorted = sorted(m.edge_density for m in metrics)
    edge_p66 = _percentile(edge_sorted, 0.66)

    result = {}
    for m in metrics:
        score = 0
        if quality[m.image_id] == "LOW":
            score += 1
        if m.edge_density > edge_p66:
            score += 1
        if m.rotation_clean_frac < 0.9:
            score += 1
        result[m.image_id] = "EASY" if score == 0 else ("MEDIUM" if score == 1 else "HARD")
    return result


def _percentile(sorted_list: List[float], p: float) -> float:
    idx = int(len(sorted_list) * p)
    return sorted_list[min(idx, len(sorted_list) - 1)]
