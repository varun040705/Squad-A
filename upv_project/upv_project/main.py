from squad_h.models import AEHit
from squad_h.engine import run_ae_engine


hits = [

    AEHit(
        sensor_id="S1",
        timestamp=0.1,
        amplitude=45,
        duration=1,
        energy=50,
        rise_time=0.4,
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
        rise_time=0.3,
        counts=2,
        peak_frequency=180,
        quality_score=90,
    ),
]


context = run_ae_engine(
    inspection_id="AE-001",
    hits=hits,
)

print(context)