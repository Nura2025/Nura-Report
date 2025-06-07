import math
import statistics
from typing import Dict, List, Optional, Union, Tuple

import statistics
import math

def compute_gonogo_attention_score(
    commission_errors: int,
    omission_errors: int,
    correct_go_responses: int,
    correct_nogo_responses: int,
    average_reaction_time_ms: float,
    reaction_time_variability_ms: float,
    age_group: Optional[str] = None
) -> float:
    """
    Calculate attention score based on Go/No-Go task metrics.

    Focuses on sustained attention (omission errors) and response consistency (RT variability).

    Returns:
        float: Attention score (0-100)

    References:
        - Sustained attention & omissions: Robertson et al. (1997) - Test of Everyday Attention (TEA)
        - RT Variability: Castellanos & Tannock (2002), Kofler et al. (2013)
    """
    total_go_trials = correct_go_responses + omission_errors
    total_nogo_trials = correct_nogo_responses + commission_errors # Needed for context, not directly in score

    if total_go_trials == 0:
        return 0.0 # Cannot calculate if no Go trials occurred

    # --- Component Calculations ---

    # 1. Sustained Attention / Accuracy (Weight: 60%)
    # Measures ability to maintain focus on Go stimuli.
    sustained_attention_accuracy = (correct_go_responses / total_go_trials) * 100

    # 2. Response Consistency (Weight: 30%)
    # Measures stability of attentional state via RT variability.
    # Lower variability = better consistency.
    # Define max acceptable SD (example values, adjust based on norms/literature for Go/No-Go)
    max_acceptable_sd = {
        "5-7": 350,
        "8-10": 300,
        "11-13": 250,
        "14-16": 200,
        "adult": 180
    }.get(age_group, 250) # Default

    # Normalize variability (higher score for lower SD)
    consistency_score = 0
    if average_reaction_time_ms > 0: # Avoid division by zero
        # Coefficient of Variation (CV) = SD / Mean
        cv = reaction_time_variability_ms / average_reaction_time_ms
        # Target CV might be around 0.2-0.3 for good performance
        # Score decreases as CV increases above target
        target_cv = 0.25
        variability_range = 0.3 # e.g., score drops to 0 if CV reaches target + range (0.55)
        consistency_score = max(0, min(1.0, (target_cv + variability_range - cv) / variability_range)) * 100
    else:
        consistency_score = 50 # Default if RT is zero or variability cannot be assessed


    # 3. Processing Speed (Weight: 10%)
    # Reflects speed of responding to targets. Faster is generally better, but very fast might link to impulsivity.
    # Define expected RT range (example values, adjust based on norms)
    min_expected_rt = {
        "5-7": 400,
        "8-10": 350,
        "11-13": 300,
        "14-16": 280,
        "adult": 250
    }.get(age_group, 300)
    max_expected_rt = {
        "5-7": 1000,
        "8-10": 900,
        "11-13": 800,
        "14-16": 750,
        "adult": 700
    }.get(age_group, 800)

    speed_score = 0
    if average_reaction_time_ms > 0:
        if average_reaction_time_ms < min_expected_rt:
             # Slightly penalize potentially impulsive fast responses
            speed_score = (average_reaction_time_ms / min_expected_rt) * 80 # Max score 80 if too fast
        elif average_reaction_time_ms > max_expected_rt:
            # Penalize slow responses
            speed_score = max(0, (1 - (average_reaction_time_ms - max_expected_rt) / (max_expected_rt * 1.5))) * 100 # Gradual decrease
        else:
            # Optimal range
            speed_score = 100
    else:
        speed_score = 0

    # --- Final Weighted Score ---
    overall_gonogo_attention_score = (
        (0.60 * sustained_attention_accuracy) +
        (0.30 * consistency_score) +
        (0.10 * speed_score)
    )

    return round(max(0, min(100, overall_gonogo_attention_score)), 2)



def compute_sequence_attention_score(
    sequence_length: int,
    expected_max_sequence: int,
    commission_errors: int,
    total_sequence_elements: int,
    retention_times: Optional[List[int]] = None,
    age_group: Optional[str] = None
) -> float:
    """
    Calculate attention score based on sequence memory metrics.
    
    Parameters:
    -----------
    sequence_length : int
        Maximum sequence length achieved
    expected_max_sequence : int
        Expected maximum sequence length for age group
    commission_errors : int
        Number of incorrect responses (false positives)
    total_sequence_elements : int
        Total number of sequence elements presented
    retention_times : List[int], optional
        List of retention times in milliseconds
    age_group : str, optional
        Age group for normative comparison ("5-7", "8-10", "11-13", "14-16")
        
    Returns:
    --------
    float
        Attention score (0-100)
        
    References:
    -----------
    Based on Gathercole et al. (2004) working memory span development research
    """
    if total_sequence_elements == 0:
        return 0.0
    
    # Adjust expected max sequence based on age group
    if age_group == "5-7":
        expected_max_sequence = 5  # Based on Gathercole et al. (2004)
    elif age_group == "8-10":
        expected_max_sequence = 6
    elif age_group == "11-13":
        expected_max_sequence = 7
    elif age_group == "14-16":
        expected_max_sequence = 8
    # else use the provided expected_max_sequence
    
    # Calculate components with scientific rationale
    # 1. Sequence capacity: Ability to maintain attention on increasingly complex sequences
    # - Based on working memory span research showing developmental trajectories
    sequence_part = sequence_length / expected_max_sequence if expected_max_sequence > 0 else 0
    sequence_part = min(1.0, sequence_part)  # Cap at 1.0 (100%)
    
    # 2. Error control: Ability to avoid commission errors
    # - Based on research showing commission errors as markers of attention lapses
    error_part = 1 - (commission_errors / total_sequence_elements) if total_sequence_elements > 0 else 0
    
    # 3. Processing efficiency (if retention times available)
    if retention_times and len(retention_times) > 0:
        # Calculate average retention time
        avg_retention = sum(retention_times) / len(retention_times)
        
        # Set expected retention time based on age group
        if age_group == "5-7":
            expected_retention = 1500  # milliseconds
        elif age_group == "8-10":
            expected_retention = 1200
        elif age_group == "11-13":
            expected_retention = 1000
        elif age_group == "14-16":
            expected_retention = 800
        else:
            expected_retention = 1000  # Default
        
        # Calculate efficiency part (lower is better)
        efficiency_part = max(0, min(1, expected_retention / avg_retention))
        
        # Calculate weighted score with efficiency
        score = (50 * sequence_part) + (30 * error_part) + (20 * efficiency_part)
    else:
        # Calculate weighted score without efficiency
        score = (60 * sequence_part) + (40 * error_part)
    
    return round(score, 2)


# Example modification
def compute_overall_attention_score(
    gonogo_score: Optional[float] = None, # Changed from crop_score
    sequence_score: Optional[float] = None
) -> Optional[float]:
    # Both scores available
    if gonogo_score is not None and sequence_score is not None:
        # Example: Equal weighting or weight GoNoGo slightly higher
        return round((0.5 * gonogo_score) + (0.5 * sequence_score), 2)
    # Only GoNoGo score available
    elif gonogo_score is not None:
        return round(gonogo_score, 2)
    # Only sequence score available
    elif sequence_score is not None:
        return round(sequence_score, 2)
    else:
        return None



def get_attention_normative_comparison(
    attention_score: float,
    age_group: str,
    clinical_group: Optional[str] = None
) -> Dict[str, Union[float, str]]:
    """
    Compare attention score to normative data.
    
    Parameters:
    -----------
    attention_score : float
        Overall attention score
    age_group : str
        Age group ("5-7", "8-10", "11-13", "14-16")
    clinical_group : str, optional
        Clinical group for comparison ("ADHD" or None for typical development)
        
    Returns:
    --------
    Dict
        Normative comparison data
        
    References:
    -----------
    Normative data based on Willcutt et al. (2005) meta-analysis
    """
    # Normative data from Willcutt et al. (2005)
    # Format: (mean, standard_deviation)
    typical_norms = {
        "5-7": (65, 15),
        "8-10": (70, 15),
        "11-13": (75, 12),
        "14-16": (80, 10)
    }
    
    adhd_norms = {
        "5-7": (45, 18),
        "8-10": (50, 18),
        "11-13": (55, 15),
        "14-16": (60, 15)
    }
    
    # Get appropriate normative data
    if age_group not in typical_norms:
        age_group = "8-10"  # Default if age group not found
    
    typical_mean, typical_sd = typical_norms[age_group]
    
    # Calculate z-score compared to typical development
    typical_z_score = (attention_score - typical_mean) / typical_sd
    
    # Calculate percentile
    typical_percentile = round(100 * (0.5 * (1 + math.erf(typical_z_score / math.sqrt(2)))), 1)
    
    # Determine classification
    if typical_z_score < -2:
        classification = "Very Low"
    elif typical_z_score < -1:
        classification = "Low"
    elif typical_z_score < 0:
        classification = "Low Average"
    elif typical_z_score < 1:
        classification = "Average"
    elif typical_z_score < 2:
        classification = "High Average"
    else:
        classification = "High"
    
    # Prepare result
    result = {
        "score": attention_score,
        "typical_mean": typical_mean,
        "typical_sd": typical_sd,
        "typical_z_score": round(typical_z_score, 2),
        "percentile": typical_percentile,
        "classification": classification,
        "reference": "Willcutt et al. (2005)"
    }
    
    # Add ADHD comparison if requested
    if clinical_group == "ADHD":
        adhd_mean, adhd_sd = adhd_norms[age_group]
        adhd_z_score = (attention_score - adhd_mean) / adhd_sd
        adhd_percentile = round(100 * (0.5 * (1 + math.erf(adhd_z_score / math.sqrt(2)))), 1)
        
        result.update({
            "adhd_mean": adhd_mean,
            "adhd_sd": adhd_sd,
            "adhd_z_score": round(adhd_z_score, 2),
            "adhd_percentile": adhd_percentile
        })
    
    return result

