"""
Edge-Case Curator for Task T1.5.
Orchestrates: compute metrics for every image in a source folder -> bucket
quality/difficulty -> select edge-case candidates -> copy them into an
output folder -> write a manifest CSV recording why each was selected.
"""

import os
import csv
import glob
import shutil
import logging
from typing import List, Optional

from edge_cases.metrics import compute_image_metrics, bucket_quality, bucket_difficulty, ImageMetrics
from edge_cases.selector import select_edge_cases

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MANIFEST_FIELDS = [
    "image_id", "filename", "reasons", "quality", "difficulty",
    "blur_var", "edge_density", "rotation_clean_frac",
]


class EdgeCaseCurator:
    """
    Curates a T1.5 stress-test subset from a directory of source images.

    Usage:
        curator = EdgeCaseCurator(
            source_dir="Team_1_Data_GroundTruth/01_raw_images/cad",
            output_dir="Team_1_Data_GroundTruth/05_edge_cases",
        )
        manifest_rows = curator.run()
    """

    def __init__(
        self,
        source_dir: str,
        output_dir: str,
        top_n_per_criterion: int = 20,
        pattern: str = "*.jpg",
    ):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.top_n_per_criterion = top_n_per_criterion
        self.pattern = pattern

    def compute_all_metrics(self, limit: Optional[int] = None) -> List[ImageMetrics]:
        paths = sorted(glob.glob(os.path.join(self.source_dir, self.pattern)))
        if limit:
            paths = paths[:limit]

        logger.info("Computing metrics for %d images in %s...", len(paths), self.source_dir)
        results = []
        for i, path in enumerate(paths, 1):
            filename = os.path.basename(path)
            image_id = os.path.splitext(filename)[0]
            try:
                results.append(compute_image_metrics(path, image_id, filename))
            except ValueError as e:
                logger.warning("Skipping unreadable image %s: %s", filename, e)

            if i % 100 == 0 or i == len(paths):
                logger.info("Processed %d / %d images...", i, len(paths))
        return results

    def run(self, limit: Optional[int] = None) -> List[dict]:
        """Runs the full T1.5 curation pipeline and returns the manifest rows."""
        metrics = self.compute_all_metrics(limit=limit)
        if not metrics:
            logger.warning("No images found/processed in %s; nothing to curate.", self.source_dir)
            return []

        quality = bucket_quality(metrics)
        difficulty = bucket_difficulty(metrics, quality)
        reasons = select_edge_cases(metrics, difficulty, top_n_per_criterion=self.top_n_per_criterion)

        logger.info("Selected %d edge-case candidates out of %d images.", len(reasons), len(metrics))

        os.makedirs(self.output_dir, exist_ok=True)
        metrics_by_id = {m.image_id: m for m in metrics}

        manifest_rows = []
        for image_id in sorted(reasons.keys()):
            m = metrics_by_id[image_id]
            src_path = os.path.join(self.source_dir, m.filename)
            dst_path = os.path.join(self.output_dir, m.filename)
            shutil.copy(src_path, dst_path)

            manifest_rows.append({
                "image_id": image_id,
                "filename": m.filename,
                "reasons": "|".join(reasons[image_id]),
                "quality": quality[image_id],
                "difficulty": difficulty[image_id],
                "blur_var": m.blur_var,
                "edge_density": m.edge_density,
                "rotation_clean_frac": m.rotation_clean_frac,
            })

        manifest_path = os.path.join(self.output_dir, "edge_case_manifest.csv")
        with open(manifest_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
            writer.writeheader()
            writer.writerows(manifest_rows)
        logger.info("Wrote manifest for %d edge cases to %s", len(manifest_rows), manifest_path)

        return manifest_rows


if __name__ == "__main__":
    curator = EdgeCaseCurator(
        source_dir="Team_1_Data_GroundTruth/01_raw_images/cad",
        output_dir="Team_1_Data_GroundTruth/05_edge_cases",
    )
    curator.run()
