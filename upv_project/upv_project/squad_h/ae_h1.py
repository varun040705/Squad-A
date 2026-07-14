"""
ae_h1.py

H-1 : Acoustic Emission preprocessing and hit filtering.

Author: Sai Varun
Project: OX1 - Squad H
"""

from squad_h.models import AEHit, H1Result
from squad_h.config import (
    MIN_AMPLITUDE,
    MIN_ENERGY,
    MIN_COUNTS,
)


def flag_noise(hit: AEHit) -> AEHit:
    """
    Flag an AE hit as noise based on threshold values.

    Rules:
    - Hits are NEVER deleted.
    - Noise hits are flagged using the is_noise field.
    """

    if (
        hit.amplitude < MIN_AMPLITUDE
        or hit.energy < MIN_ENERGY
        or hit.counts < MIN_COUNTS
    ):
        hit.is_noise = True
    else:
        hit.is_noise = False

    return hit


def split_hits(hit_list: list[AEHit]) -> H1Result:
    """
    Split processed hits into:

    1. raw_hits
       - Contains every hit (including noise)

    2. eligible_hits
       - Contains only non-noise hits
    """

    raw_hits = hit_list

    eligible_hits = [
        hit
        for hit in hit_list
        if not hit.is_noise
    ]

    return H1Result(
        raw_hits=raw_hits,
        eligible_hits=eligible_hits,
    )


def preprocess_and_detect_hits(hit_list: list[AEHit]) -> H1Result:
    """
    Complete H-1 preprocessing pipeline.

    Steps
    -----
    1. Flag noise
    2. Preserve every hit
    3. Create eligible scoring list

    Returns
    -------
    H1Result
    """

    processed_hits = []

    for hit in hit_list:
        processed_hits.append(flag_noise(hit))

    return split_hits(processed_hits)