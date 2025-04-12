from typing import List


def compute_crop_attention_score(
    crops_identified: int,
    omission_errors: int,
    distractions: int,
    total_crops: int,
    response_times: List[float],
    max_acceptable_sd: float = 0.8  # or based on age
) -> float:
    total_attempts = crops_identified + omission_errors
    attention_part = crops_identified / total_attempts if total_attempts > 0 else 0
    distraction_part = 1 - (distractions / total_crops) if total_crops > 0 else 0

    if len(response_times) > 1:
        sd_response_time = np.std(response_times)
    else:
        sd_response_time = 0  # stable but not reliable

    consistency_part = 1 - (sd_response_time / max_acceptable_sd)
    consistency_part = max(0, min(1, consistency_part))

    score = (70 * attention_part) + (20 * distraction_part) + (10 * consistency_part)
    return round(score, 2)


def compute_sequence_attention_score(
    sequence_length: int,
    expected_max_sequence: int,
    commission_errors: int,
    total_elements: int
) -> float:
    sequence_part = sequence_length / expected_max_sequence if expected_max_sequence > 0 else 0
    error_part = 1 - (commission_errors / total_elements) if total_elements > 0 else 0

    score = (60 * sequence_part) + (40 * error_part)
    return round(score, 2)


def compute_overall_attention_score(crop_score: float, sequence_score: float) -> float:
    return round((0.6 * crop_score) + (0.4 * sequence_score), 2)
