"""
loader.py

Loads the bridge digital twin dataset.

Author: Sai Varun
Project: OX1 - Defect Engine
"""

import pandas as pd

from defect_engine.models import BridgeRecord


def load_bridge_dataset(csv_path: str) -> list[BridgeRecord]:
    """
    Load the bridge dataset and convert each row into
    a validated BridgeRecord.
    """

    df = pd.read_csv(csv_path)

    records = []

    for _, row in df.iterrows():

        record = BridgeRecord(

            timestamp=row["Timestamp"],

            acoustic_emission=row["Acoustic_Emissions_levels"],

            crack_propagation=row["Crack_Propagation_mm"],

            corrosion_level=row["Corrosion_Level_percent"],

            fatigue_accumulation=row["Fatigue_Accumulation_au"],

            structural_health_index=row["Structural_Health_Index_SHI"],

            anomaly_score=row["Anomaly_Detection_Score"],

            probability_of_failure=row["Probability_of_Failure_PoF"],

            maintenance_alert=bool(row["Maintenance_Alert"]),

        )

        records.append(record)

    return records
