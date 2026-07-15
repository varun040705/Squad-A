from squad_h.models import AEHit, SensorGeometry, LoadSample, LoadPhase
from squad_h.engine import run_ae_engine
from defect_engine.rules import detect_defects
import pandas as pd
hits = [

    AEHit(
        sensor_id="S1",
        timestamp=0.1,
        amplitude=45,
        duration=1,
        energy=50,
        rise_time=0.4,   # ratio 0.4 -> not noise
        counts=15,
        peak_frequency=220,
        quality_score=95,
    ),

    AEHit(
        sensor_id="S2",
        timestamp=0.3,
        amplitude=10,
        duration=1,
        energy=5,
        rise_time=0.6,   # ratio 0.6 > 0.5 -> flagged as noise
        counts=2,
        peak_frequency=180,
        quality_score=90,
    ),
]

# Element-specific sensor array layout -- without this, localization
# will correctly report insufficient data rather than a fake location.
# NOTE: sensors must NOT be coplanar for a 3D solve -- S4 is placed
# off-plane (z=1.0) here, or the triangulation will correctly refuse to
# guess a depth it can't resolve.
sensor_positions = {
    "S1": SensorGeometry(sensor_id="S1", x=0.0, y=0.0, z=0.0),
    "S2": SensorGeometry(sensor_id="S2", x=1.0, y=0.0, z=0.0),
    "S3": SensorGeometry(sensor_id="S3", x=0.0, y=1.0, z=0.0),
    "S4": SensorGeometry(sensor_id="S4", x=1.0, y=1.0, z=1.0),
}

# Load-cell stream correlated to the AE monitoring timeline -- without
# this, calm_ratio/felicity_ratio (and therefore grade) stay undetermined.
load_samples = [
    LoadSample(timestamp=0.0, load=100.0, phase=LoadPhase.LOADING),
    LoadSample(timestamp=0.2, load=150.0, phase=LoadPhase.UNLOADING),
    LoadSample(timestamp=0.4, load=120.0, phase=LoadPhase.RELOADING),
]

context = run_ae_engine(
    inspection_id="AE-001",
    element_ref="C-07",
    hits=hits,
    sensor_positions=sensor_positions,
    load_samples=load_samples,
)

print(context)

from defect_engine.loader import load_bridge_dataset

records = load_bridge_dataset(
    "datasets/bridge_digital_twin_dataset.csv"
)

print(f"Total Records: {len(records)}")
print(records[0])

from defect_engine.detector import run_defect_detector

result = run_defect_detector(records)
from integration.engine import build_inspection_context

inspection = build_inspection_context(
    context,
    result,
)

print("\nINTEGRATED INSPECTION")
print("---------------------")
print(inspection)

print("\nDEFECT DETECTION")
print("----------------")
print(f"Records Analysed : {result.total_records}")
print(f"Defects Found    : {result.total_defects}")

if result.defects:
    print("\nFirst Defect:")
    print(result.defects[0])
else:
    print("\nNo defects detected.")
    


df = pd.read_csv("datasets/bridge_digital_twin_dataset.csv")

columns = [
    "Acoustic_Emissions_levels",
    "Crack_Propagation_mm",
    "Corrosion_Level_percent",
    "Fatigue_Accumulation_au",
    "Structural_Health_Index_SHI",
    "Probability_of_Failure_PoF",
]

print(df[columns].describe())
df = pd.read_csv("datasets/bridge_digital_twin_dataset.csv")

columns = [
    "Acoustic_Emissions_levels",
    "Crack_Propagation_mm",
    "Corrosion_Level_percent",
    "Fatigue_Accumulation_au",
    "Structural_Health_Index_SHI",
    "Anomaly_Detection_Score",
    "Probability_of_Failure_PoF",
]

for col in columns:
    print("\n", col)
    print("Min :", df[col].min())
    print("Max :", df[col].max())
    print("Mean:", df[col].mean())