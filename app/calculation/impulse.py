"""
Impulse Control Calculation Module

This module implements scientifically-based calculations for impulse control assessment
based on commission errors and response metrics from cognitive games.

Scientific Background:
- Commission errors are a primary measure of inhibitory control (Barkley, 1997)
- Response time variability indicates impulsive responding (Castellanos & Tannock, 2002)
- Error awareness and post-error adjustments reflect executive control (Ullsperger et al., 2014)
- Multiple metrics provide more reliable assessment than single measures (Nigg, 2017)

References:
1. Barkley, R. A. (1997). Behavioral inhibition, sustained attention, and executive functions: 
   Constructing a unifying theory of ADHD. Psychological Bulletin, 121(1), 65-94.
2. Castellanos, F. X., & Tannock, R. (2002). Neuroscience of attention-deficit/hyperactivity 
   disorder: The search for endophenotypes. Nature Reviews Neuroscience, 3(8), 617-628.
3. Ullsperger, M., Danielmeier, C., & Jocham, G. (2014). Neurophysiology of performance 
   monitoring and adaptive behavior. Physiological Reviews, 94(1), 35-79.
4. Nigg, J. T. (2017). Annual Research Review: On the relations among self‐regulation, 
   self‐control, executive functioning, effortful control, cognitive control, impulsivity, 
   risk‐taking, and inhibition for developmental psychopathology. Journal of Child Psychology 
   and Psychiatry, 58(4), 361-383.
"""

import statistics
from typing import List, Dict, Optional, Union
import math

def compute_impulse_control_score(
    commission_errors: int = 0,
    total_sequence_elements: int = 0,
    retention_times: Optional[List[int]] = None,
    gonogo_commission_errors: int = 0,
    correct_nogo_responses: int = 0,
    average_reaction_time_ms: Optional[float] = None,
    reaction_time_variability_ms: Optional[float] = None,  # Add this parameter
    incorrect_matches: int = 0,
    matches_attempted: int = 0,
    time_per_match: Optional[List[int]] = None,
    age_group: Optional[str] = None
) -> Dict[str, Union[float, str]]:
    """
    Calculate a comprehensive impulse control score based on game metrics.
    
    Args:
        commission_errors: Number of incorrect responses in sequence task
        total_sequence_elements: Total elements presented in sequence task
        retention_times: List of response times in sequence task (milliseconds)
        
        distractions: Number of distractor responses in crop task
        total_crops_presented: Total crops presented in crop task
        crop_response_times: Dictionary of response times in crop task
        
        incorrect_matches: Number of incorrect matches in card matching task
        matches_attempted: Total number of match attempts
        time_per_match: List of times taken per match attempt (milliseconds)
        
        age_group: Optional age group for normative comparison
        
    Returns:
        Dictionary containing impulse control score components and overall score
    """
    # Track which game data is available
    available_games = []
    
    # 1. Calculate inhibitory control component (40% of total score)
    # Based on commission errors and distractor responses
    # Scientific basis: Commission errors directly measure inhibitory control (Barkley, 1997)
    inhibitory_control_scores = []
    
    # Sequence task inhibitory control
    if total_sequence_elements > 0:
        sequence_error_rate = commission_errors / total_sequence_elements
        sequence_inhibitory_score = max(0, (1 - sequence_error_rate)) * 100
        inhibitory_control_scores.append(sequence_inhibitory_score)
        available_games.append("sequence")
    
    # gonogo task inhibitory control
    total_nogo_trials = correct_nogo_responses + gonogo_commission_errors
    if total_nogo_trials > 0:
        gonogo_error_rate = gonogo_commission_errors / total_nogo_trials
        gonogo_inhibitory_score = max(0, (1 - gonogo_error_rate)) * 100
        inhibitory_control_scores.append(gonogo_inhibitory_score)
        if "gonogo" not in available_games: available_games.append("gonogo")
    
    # Card matching inhibitory control
    if matches_attempted > 0:
        incorrect_rate = incorrect_matches / matches_attempted
        matching_inhibitory_score = max(0, (1 - incorrect_rate)) * 100
        inhibitory_control_scores.append(matching_inhibitory_score)
        available_games.append("matching")
    
    # Calculate overall inhibitory control score
    if inhibitory_control_scores:
        inhibitory_control = statistics.mean(inhibitory_control_scores)
    else:
        inhibitory_control = 0
    
    # 2. Calculate response control component (30% of total score)
    # Based on response time variability
    # Scientific basis: Response variability indicates impulsive responding (Castellanos & Tannock, 2002)
    response_control_scores = []
    
    # Sequence task response control
    if retention_times and len(retention_times) > 1:
        mean_rt = statistics.mean(retention_times)
        if mean_rt > 0:
            cv = statistics.stdev(retention_times) / mean_rt
            # Convert to score (0-100), where lower CV = higher score
            # CV of 0.2 or less is considered good consistency
            sequence_response_score = max(0, min(1.0, (0.5 - cv) / 0.3)) * 100
            response_control_scores.append(sequence_response_score)
    
   
    
    # Card matching response control
    if time_per_match and len(time_per_match) > 1:
        mean_rt = statistics.mean(time_per_match)
        if mean_rt > 0:
            cv = statistics.stdev(time_per_match) / mean_rt
            matching_response_score = max(0, min(1.0, (0.5 - cv) / 0.3)) * 100
            response_control_scores.append(matching_response_score)
    
    # Calculate overall response control score
    if response_control_scores:
        response_control = statistics.mean(response_control_scores)
    else:
        response_control = 50  # Default middle value if insufficient data
    
    # 3. Calculate decision speed component (20% of total score)
    # Based on average response times
    # Scientific basis: Impulsivity often manifests as faster, less considered responses (Nigg, 2017)
    decision_speed_scores = []
    
    # Define optimal response time ranges by age group (milliseconds)
    # Too fast = impulsive, too slow = inattentive
    optimal_ranges = {
        "5-7": (800, 2000),
        "8-10": (700, 1800),
        "11-13": (600, 1600),
        "14-16": (500, 1400),
        "adult": (400, 1200)
    }
    
    # Get optimal range for age group
    optimal_range = optimal_ranges.get(age_group, (600, 1600))
    optimal_min, optimal_max = optimal_range
    
    # Sequence task decision speed
    if retention_times and len(retention_times) > 0:
        mean_rt = statistics.mean(retention_times)
        # Score is highest when in optimal range, lower when too fast or too slow
        if mean_rt < optimal_min:
            # Too fast (impulsive)
            sequence_speed_score = (mean_rt / optimal_min) * 100
        elif mean_rt > optimal_max:
            # Too slow (inattentive)
            sequence_speed_score = max(0, (1 - (mean_rt - optimal_max) / optimal_max)) * 100
        else:
            # Optimal range
            sequence_speed_score = 100
        decision_speed_scores.append(sequence_speed_score)
    
    # Crop task decision speed
    if average_reaction_time_ms is not None and average_reaction_time_ms > 0:
        # Use same optimal range logic as before
        optimal_range = optimal_ranges.get(age_group, (600, 1600))
        optimal_min, optimal_max = optimal_range
        if average_reaction_time_ms < optimal_min:
            gonogo_speed_score = (average_reaction_time_ms / optimal_min) * 100
        elif average_reaction_time_ms > optimal_max:
            gonogo_speed_score = max(0, (1 - (average_reaction_time_ms - optimal_max) / optimal_max)) * 100
        else:
            gonogo_speed_score = 100
        decision_speed_scores.append(gonogo_speed_score)
        if "gonogo" not in available_games: available_games.append("gonogo")

    
    # Card matching decision speed
    if time_per_match and len(time_per_match) > 0:
        mean_rt = statistics.mean(time_per_match)
        if mean_rt < optimal_min:
            matching_speed_score = (mean_rt / optimal_min) * 100
        elif mean_rt > optimal_max:
            matching_speed_score = max(0, (1 - (mean_rt - optimal_max) / optimal_max)) * 100
        else:
            matching_speed_score = 100
        decision_speed_scores.append(matching_speed_score)
    
    # Calculate overall decision speed score
    if decision_speed_scores:
        decision_speed = statistics.mean(decision_speed_scores)
    else:
        decision_speed = 50  # Default middle value if insufficient data
    
    # 4. Calculate error adaptation component (10% of total score)
    # Based on post-error slowing and recovery
    # Scientific basis: Error awareness and adaptation reflect executive control (Ullsperger et al., 2014)
    # This is a simplified implementation - a full implementation would analyze trial-by-trial adjustments
    error_adaptation = 50  # Default middle value
    
    # For a complete implementation, we would need trial-by-trial data to calculate:
    # - Post-error slowing (response time after errors compared to baseline)
    # - Error recovery (performance on trials following errors)
    # - Error awareness (self-corrections or reported awareness)
    
    # 5. Calculate overall impulse control score with weighted components
    # Adjust weights based on available data
    if available_games:
        overall_score = (
            (0.40 * inhibitory_control) +
            (0.30 * response_control) +
            (0.20 * decision_speed) +
            (0.10 * error_adaptation)
        )
    else:
        overall_score = 0
    
    # Round scores for readability
    return {
        "overall_impulse_control_score": round(overall_score, 1),
        "inhibitory_control": round(inhibitory_control, 1),
        "response_control": round(response_control, 1),
        "decision_speed": round(decision_speed, 1),
        "error_adaptation": round(error_adaptation, 1),
        "data_completeness": len(available_games) / 3 if available_games else 0,
        "games_used": available_games,
        "components": {
            "commission_error_rate": round(commission_errors / max(total_sequence_elements, 1), 3) if total_sequence_elements > 0 else None,
            "gonogo_commission_error_rate": round(gonogo_commission_errors / max(total_nogo_trials, 1), 3) if total_nogo_trials > 0 else None,
            "incorrect_match_rate": round(incorrect_matches / max(matches_attempted, 1), 3) if matches_attempted > 0 else None
        }
    }