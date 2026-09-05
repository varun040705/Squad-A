from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

REAL_DATA_DIR = PROJECT_ROOT / "real_data"

GROUND_TRUTH_DIR = REAL_DATA_DIR / "ground_truth"

PREDICTIONS_DIR = REAL_DATA_DIR / "predictions"

REPORTS_DIR = PROJECT_ROOT / "reports"


# Evaluation tolerances
WALL_TOLERANCE = 10.0

DOOR_TOLERANCE = 10.0

WINDOW_TOLERANCE = 10.0

ROOM_TOLERANCE = 10.0