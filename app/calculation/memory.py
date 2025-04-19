"""
Enhanced Memory Score Calculation Module

This module implements scientifically-based calculations for memory assessment
based on both sequence memory metrics and matching card metrics.

Scientific Background:
- Working memory capacity is commonly assessed using span tasks (Conway et al., 2005)
- Visual recognition memory is assessed through matching paradigms (Luck & Hollingworth, 2008)
- Multiple memory systems contribute to overall memory function (Baddeley, 2000)
- Age-appropriate expectations are essential for valid assessment (Gathercole et al., 2004)

References:
1. Conway, A. R., Kane, M. J., Bunting, M. F., Hambrick, D. Z., Wilhelm, O., & Engle, R. W. (2005). 
   Working memory span tasks: A methodological review and user's guide. Psychonomic bulletin & review, 12(5), 769-786.
2. Luck, S. J., & Hollingworth, A. (Eds.). (2008). Visual memory. Oxford University Press.
3. Baddeley, A. (2000). The episodic buffer: a new component of working memory?
   Trends in cognitive sciences, 4(11), 417-423.
4. Gathercole, S. E., Pickering, S. J., Ambridge, B., & Wearing, H. (2004). The structure of
   working memory from 4 to 15 years of age. Developmental psychology, 40(2), 177-190.
"""

import statistics
from typing import List, Dict, Optional, Union
import math


def compute_memory_score(
    # Sequence memory metrics
    sequence_length: int = 0,
    commission_errors: int = 0,
    num_of_trials: int = 0,
    retention_times: Optional[List[int]] = None,
    total_sequence_elements: int = 0,
    
    # Matching card metrics
    correct_matches: int = 0,
    incorrect_matches: int = 0,
    matches_attempted: int = 0,
    time_per_match: Optional[List[int]] = None,
    
    age_group: Optional[str] = None
) -> Dict[str, Union[float, str]]:
    """
    Calculate a comprehensive memory score based on sequence and matching card metrics.
    
    Args:
        sequence_length: Maximum sequence length successfully achieved
        commission_errors: Number of incorrect responses in sequence task
        num_of_trials: Number of attempts made in sequence task
        retention_times: List of response times in sequence task (milliseconds)
        total_sequence_elements: Total number of elements presented across all trials
        
        correct_matches: Number of correct matches in card matching task
        incorrect_matches: Number of incorrect matches in card matching task
        matches_attempted: Total number of match attempts
        time_per_match: List of times taken per match attempt (milliseconds)
        
        age_group: Optional age group for normative comparison
        
    Returns:
        Dictionary containing memory score components and overall score
    """
    # Initialize empty lists to track available tasks and their scores
    available_tasks = []
    memory_scores = []
    
    # Set retention_times and time_per_match to empty lists if None
    if retention_times is None:
        retention_times = []
    if time_per_match is None:
        time_per_match = []
    
    # 1. Calculate working memory component from sequence task (if available)
    if sequence_length > 0 or total_sequence_elements > 0:
        # 1.1 Calculate span capacity component (40% of working memory score)
        # Normalize sequence length against expected maximum
        # Scientific basis: Sequence span directly measures working memory capacity (Conway et al., 2005)
        expected_max_sequence = 9  # Based on average adult capacity of 7±2 items
        if age_group:
            # Adjust expected maximum based on age group
            age_adjustments = {
                "5-7": 5,    # Young children have lower capacity
                "8-10": 6,   # Older children
                "11-13": 7,  # Adolescents
                "14-16": 8,  # Teenagers
                "adult": 9   # Adults
            }
            expected_max_sequence = age_adjustments.get(age_group, 9)
        
        # Calculate normalized span score (0-100)
        span_capacity = min(sequence_length / expected_max_sequence, 1.0) * 100
        
        # 1.2 Calculate accuracy component (30% of working memory score)
        # Based on commission errors relative to total elements
        # Scientific basis: Error rates reflect memory precision (Richardson, 2007)
        if total_sequence_elements > 0:
            error_rate = commission_errors / total_sequence_elements
            accuracy = max(0, (1 - error_rate)) * 100
        else:
            accuracy = 0
        
        # 1.3 Calculate efficiency component (20% of working memory score)
        # Based on trials needed to reach maximum sequence length
        # Scientific basis: Learning efficiency reflects memory consolidation (Kessels et al., 2000)
        if sequence_length > 0:
            # Ideal: 1 trial per sequence length achieved
            ideal_trials = sequence_length
            efficiency_ratio = ideal_trials / max(num_of_trials, 1)
            efficiency = min(efficiency_ratio, 1.0) * 100
        else:
            efficiency = 0
        
        # 1.4 Calculate processing speed component (10% of working memory score)
        # Based on consistency and speed of retention times
        # Scientific basis: Response variability indicates attentional fluctuation (Klingberg, 2010)
        if retention_times and len(retention_times) > 1:
            # Calculate coefficient of variation (lower is better)
            mean_rt = statistics.mean(retention_times)
            if mean_rt > 0:
                cv = statistics.stdev(retention_times) / mean_rt
                # Convert to score (0-100), where lower CV = higher score
                # CV of 0.2 or less is considered good consistency
                processing_speed = max(0, min(1.0, (0.5 - cv) / 0.3)) * 100
            else:
                processing_speed = 0
        else:
            processing_speed = 50  # Default middle value if insufficient data
        
        # 1.5 Calculate working memory score with weighted components
        working_memory_score = (
            (0.40 * span_capacity) +
            (0.30 * accuracy) +
            (0.20 * efficiency) +
            (0.10 * processing_speed)
        )
        
        # Add to memory scores list
        memory_scores.append(("working_memory", working_memory_score))
        available_tasks.append("sequence")
        
        # Store component scores for detailed reporting
        working_memory_components = {
            "span_capacity": round(span_capacity, 1),
            "accuracy": round(accuracy, 1),
            "efficiency": round(efficiency, 1),
            "processing_speed": round(processing_speed, 1)
        }
    else:
        working_memory_components = {}
    
    # 2. Calculate visual recognition memory from matching card task (if available)
    if matches_attempted > 0:
        # 2.1 Calculate recognition accuracy (50% of visual memory score)
        # Scientific basis: Accuracy in visual recognition tasks reflects memory fidelity (Luck & Hollingworth, 2008)
        recognition_accuracy = (correct_matches / matches_attempted) * 100
        
        # 2.2 Calculate recognition efficiency (30% of visual memory score)
        # Based on time taken per match
        # Scientific basis: Processing speed reflects memory access efficiency (Cowan, 2010)
        if time_per_match and len(time_per_match) > 0:
            avg_time = statistics.mean(time_per_match)
            # Faster times = better efficiency (within reasonable limits)
            # Optimal time range depends on age group
            optimal_ranges = {
                "5-7": (2000, 5000),  # 2-5 seconds
                "8-10": (1500, 4000),
                "11-13": (1200, 3500),
                "14-16": (1000, 3000),
                "adult": (800, 2500)
            }
            optimal_range = optimal_ranges.get(age_group, (1200, 3500))
            optimal_min, optimal_max = optimal_range
            
            if avg_time < optimal_min:
                # Too fast might indicate guessing
                efficiency_ratio = avg_time / optimal_min
            elif avg_time > optimal_max:
                # Too slow indicates inefficient processing
                efficiency_ratio = max(0, 1 - ((avg_time - optimal_max) / optimal_max))
            else:
                # Within optimal range
                efficiency_ratio = 1.0
                
            recognition_efficiency = efficiency_ratio * 100
        else:
            recognition_efficiency = 50  # Default if no timing data
            
        # 2.3 Calculate memory load handling (20% of visual memory score)
        # Based on total number of matches attempted relative to expected
        # Scientific basis: Memory load capacity reflects visual working memory limits (Cowan, 2001)
        expected_matches = 15  # Typical number in a memory card game
        if age_group:
            age_adjustments = {
                "5-7": 10,
                "8-10": 12,
                "11-13": 15,
                "14-16": 18,
                "adult": 20
            }
            expected_matches = age_adjustments.get(age_group, 15)
            
        memory_load = min(matches_attempted / expected_matches, 1.0) * 100
        
        # 2.4 Calculate visual memory score with weighted components
        visual_memory_score = (
            (0.50 * recognition_accuracy) +
            (0.30 * recognition_efficiency) +
            (0.20 * memory_load)
        )
        
        # Add to memory scores list
        memory_scores.append(("visual_memory", visual_memory_score))
        available_tasks.append("matching")
        
        # Store component scores for detailed reporting
        visual_memory_components = {
            "recognition_accuracy": round(recognition_accuracy, 1),
            "recognition_efficiency": round(recognition_efficiency, 1),
            "memory_load": round(memory_load, 1)
        }
    else:
        visual_memory_components = {}
    
    # 3. Calculate overall memory score
    # Scientific basis: Multiple memory systems contribute to overall memory function (Baddeley, 2000)
    if len(memory_scores) == 2:
        # If both tasks available, weight working memory 60%, visual memory 40%
        # This weighting reflects the relative contribution of each system to general memory function
        overall_memory_score = (0.60 * memory_scores[0][1]) + (0.40 * memory_scores[1][1])
        components = {
            "working_memory": round(memory_scores[0][1], 1),
            "visual_memory": round(memory_scores[1][1], 1),
            "working_memory_components": working_memory_components,
            "visual_memory_components": visual_memory_components
        }
    elif len(memory_scores) == 1:
        # If only one task available, use that score
        overall_memory_score = memory_scores[0][1]
        if memory_scores[0][0] == "working_memory":
            components = {
                "working_memory": round(memory_scores[0][1], 1),
                "working_memory_components": working_memory_components
            }
        else:
            components = {
                "visual_memory": round(memory_scores[0][1], 1),
                "visual_memory_components": visual_memory_components
            }
    else:
        # No valid memory data
        overall_memory_score = 0
        components = {}
    
    # 4. Return comprehensive results
    return {
        "overall_memory_score": round(overall_memory_score, 1),
        "components": components,
        "tasks_used": available_tasks,
        "data_completeness": len(available_tasks) / 2 if available_tasks else 0
    }


def interpret_memory_score(score: float) -> str:
    """
    Provide clinical interpretation of memory score.
    
    Args:
        score: Overall memory score (0-100)
        
    Returns:
        String with interpretation of score level
    """
    if score >= 90:
        return "Superior memory capacity"
    elif score >= 80:
        return "Above average memory capacity"
    elif score >= 70:
        return "Average memory capacity"
    elif score >= 60:
        return "Low average memory capacity"
    elif score >= 50:
        return "Below average memory capacity"
    else:
        return "Impaired memory capacity"


def compare_to_normative_data(
    memory_score: float,
    age_group: str,
    normative_data: Optional[Dict] = None
) -> Dict[str, Union[float, str]]:
    """
    Compare memory score to age-appropriate normative data.
    
    Args:
        memory_score: Overall memory score (0-100)
        age_group: Age group for comparison
        normative_data: Optional dictionary with normative data
        
    Returns:
        Dictionary with percentile and interpretation
    """
    # Default normative data if none provided
    # Based on simplified approximation of population distribution
    # In a real implementation, this would come from empirical studies
    if normative_data is None:
        normative_data = {
            "5-7": {"mean": 65, "std": 12},
            "8-10": {"mean": 70, "std": 12},
            "11-13": {"mean": 75, "std": 12},
            "14-16": {"mean": 78, "std": 12},
            "adult": {"mean": 80, "std": 12}
        }
    
    # Get normative values for age group
    norm = normative_data.get(age_group, {"mean": 75, "std": 12})
    
    # Calculate z-score
    z_score = (memory_score - norm["mean"]) / norm["std"]
    
    # Convert to percentile
    # Using error function approximation for normal distribution CDF
    percentile = round(100 * (0.5 * (1 + math.erf(z_score / math.sqrt(2)))), 1)
    
    # Determine classification
    if percentile >= 98:
        classification = "Very Superior"
    elif percentile >= 91:
        classification = "Superior"
    elif percentile >= 75:
        classification = "High Average"
    elif percentile >= 25:
        classification = "Average"
    elif percentile >= 9:
        classification = "Low Average"
    elif percentile >= 2:
        classification = "Borderline"
    else:
        classification = "Extremely Low"
    
    return {
        "percentile": percentile,
        "z_score": round(z_score, 2),
        "classification": classification,
        "comparison_group": age_group
    }


# Example usage:
if __name__ == "__main__":
    # Example data with both sequence and matching card metrics
    sample_metrics = {
        # Sequence metrics
        "sequence_length": 6,
        "commission_errors": 3,
        "num_of_trials": 8,
        "retention_times": [850, 920, 780, 850, 900, 830],
        "total_sequence_elements": 30,
        
        # Matching card metrics
        "correct_matches": 12,
        "incorrect_matches": 3,
        "matches_attempted": 15,
        "time_per_match": [1200, 1300, 1100, 1250, 1150],
        
        "age_group": "11-13"
    }
    
    # Calculate memory score
    memory_results = compute_memory_score(**sample_metrics)
    
    # Get interpretation
    interpretation = interpret_memory_score(memory_results["overall_memory_score"])
    
    # Compare to normative data
    normative_comparison = compare_to_normative_data(
        memory_results["overall_memory_score"],
        sample_metrics["age_group"]
    )
    
    # Print results
    print(f"Memory Score: {memory_results['overall_memory_score']}")
    print(f"Tasks Used: {memory_results['tasks_used']}")
    print(f"Data Completeness: {memory_results['data_completeness'] * 100}%")
    print(f"Interpretation: {interpretation}")
    print(f"Percentile: {normative_comparison['percentile']}")
    print(f"Classification: {normative_comparison['classification']}")
    
    # Print component scores
    print("\nComponent Scores:")
    for component, score in memory_results['components'].items():
        if isinstance(score, dict):
            print(f"\n{component}:")
            for subcomponent, subscore in score.items():
                print(f"  {subcomponent}: {subscore}")
        else:
            print(f"{component}: {score}")
