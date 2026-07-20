"""
ae_h1.py

H-1 : Acoustic Emission preprocessing and hit filtering.

Author: Sai Varun
Project: OX1 - Squad H
"""

from squad_h.models import AEHit, H1Result
from squad_h.config import NOISE_RISE_TIME_TO_DURATION_RATIO


def flag_noise(hit: AEHit) -> AEHit:
    """
    Flag an AE hit as noise per workplan H-1:

        rise_time / duration > 0.5  ->  mechanical/electrical noise

    Rules:
    - Hits are NEVER deleted.
    - Noise hits are flagged using the is_noise field, retained in the
      raw log, and excluded only from scoring (done downstream by
      split_hits / eligible_hits).
    - duration == 0 is treated as noise (can't compute the ratio, and a
      zero-duration "hit" is not physically meaningful) rather than
      silently dividing by zero.
    """

    if hit.duration == 0:
        hit.is_noise = True
        return hit

    ratio = hit.rise_time / hit.duration
    hit.is_noise = ratio > NOISE_RISE_TIME_TO_DURATION_RATIO

    return hit


def split_hits(hit_list: list[AEHit]) -> H1Result:
    """
    Split processed hits into:

    1. raw_hits
       - Contains every hit (including noise)

    2. eligible_hits
       - Contains only non-noise hits

    Also raises a flag if any noise was found, so downstream consumers
    don't have to scan raw_hits themselves to know noise was present.
    """

    raw_hits = hit_list

    eligible_hits = [
        hit
        for hit in hit_list
        if not hit.is_noise
    ]

    flags = []
    noise_count = len(raw_hits) - len(eligible_hits)
    if noise_count > 0:
        flags.append(f"noise_hits_excluded:{noise_count}")

    return H1Result(
        raw_hits=raw_hits,
        eligible_hits=eligible_hits,
        flags=flags,
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
