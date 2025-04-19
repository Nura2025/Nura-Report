def get_age_group(age: int) -> str:
    """
    Convert numeric age to a predefined age group label.
    
    Args:
        age: Age in years
    
    Returns:
        Age group label as string
    """
    if 5 <= age <= 7:
        return "5-7"
    elif 8 <= age <= 10:
        return "8-10"
    elif 11 <= age <= 13:
        return "11-13"
    elif 14 <= age <= 16:
        return "14-16"
    else:
        return "adult"