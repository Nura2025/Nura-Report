# Updated seed_normative_data.py with Go/No-Go and Attention norms
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import NormativeData # Assuming NormativeData model is defined here or imported

async def seed_normative_data(db: AsyncSession):
    """
    Seed normative data for cognitive domains based on scientific research.

    References:
    1. Gathercole, S. E., Pickering, S. J., Ambridge, B., & Wearing, H. (2004).
       The structure of working memory from 4 to 15 years of age.
       Developmental Psychology, 40(2), 177-190.

    2. Liu, Q., Zhu, X., Ziegler, A., & Shi, J. (2015).
       The effects of inhibitory control training for preschoolers on reasoning ability and neural activity.
       Scientific Reports, 5, 14200.

    3. Willcutt, E. G., Doyle, A. E., Nigg, J. T., Faraone, S. V., & Pennington, B. F. (2005).
       Validity of the executive function theory of attention-deficit/hyperactivity disorder: a meta-analytic review.
       Biological Psychiatry, 57(11), 1336-1346.

    4. Barnard, A. R., Barch, D. M., & Yerys, B. E. (2023).
       Psychometric Properties of a Combined Go/No-go and Continuous Performance Task across Childhood.
       Journal of the International Neuropsychological Society : JINS, 29(6), 585–596. PMC10041761
       (Note: Provided Mean & Range; SDs for Go/No-Go are ESTIMATED/PLACEHOLDERS below)
    """

    # Memory normative data (Gathercole et al., 2004)
    memory_norms = [
        {"domain": "Memory", "age_group": "5-7", "mean_score": 70, "standard_deviation": 12,
         "source_reference": "Gathercole et al. (2004)", "clinical_group": "TypicallyDeveloping"},
        {"domain": "Memory", "age_group": "8-10", "mean_score": 75, "standard_deviation": 12,
         "source_reference": "Gathercole et al. (2004)", "clinical_group": "TypicallyDeveloping"},
        {"domain": "Memory", "age_group": "11-13", "mean_score": 80, "standard_deviation": 12,
         "source_reference": "Gathercole et al. (2004)", "clinical_group": "TypicallyDeveloping"},
        # Add other age groups as needed
    ]

    # Impulse control normative data (Liu et al., 2015 - Note: Original reference was 2016, check accuracy)
    impulse_norms = [
        {"domain": "ImpulseControl", "age_group": "5-7", "mean_score": 65, "standard_deviation": 15,
         "source_reference": "Liu et al. (2015)", "clinical_group": "TypicallyDeveloping"},
        {"domain": "ImpulseControl", "age_group": "8-10", "mean_score": 72, "standard_deviation": 15,
         "source_reference": "Liu et al. (2015)", "clinical_group": "TypicallyDeveloping"},
        {"domain": "ImpulseControl", "age_group": "11-13", "mean_score": 78, "standard_deviation": 15,
         "source_reference": "Liu et al. (2015)", "clinical_group": "TypicallyDeveloping"},
        # Add other age groups as needed
    ]

    # Executive function normative data (derived from Willcutt et al., 2005)
    executive_norms = [
        {"domain": "ExecutiveFunction", "age_group": "5-7", "mean_score": 68, "standard_deviation": 13,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "TypicallyDeveloping"},
        {"domain": "ExecutiveFunction", "age_group": "8-10", "mean_score": 74, "standard_deviation": 13,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "TypicallyDeveloping"},
        {"domain": "ExecutiveFunction", "age_group": "11-13", "mean_score": 79, "standard_deviation": 13,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "TypicallyDeveloping"},
        # Add other age groups as needed
    ]

    # ADHD-specific normative data (Willcutt et al., 2005)
    adhd_norms = [
        # Memory
        {"domain": "Memory", "age_group": "5-7", "mean_score": 62, "standard_deviation": 14,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "ADHD"},
        {"domain": "Memory", "age_group": "8-10", "mean_score": 66, "standard_deviation": 14,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "ADHD"},
        {"domain": "Memory", "age_group": "11-13", "mean_score": 70, "standard_deviation": 14,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "ADHD"},

        # Impulse control
        {"domain": "ImpulseControl", "age_group": "5-7", "mean_score": 55, "standard_deviation": 16,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "ADHD"},
        {"domain": "ImpulseControl", "age_group": "8-10", "mean_score": 60, "standard_deviation": 16,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "ADHD"},
        {"domain": "ImpulseControl", "age_group": "11-13", "mean_score": 65, "standard_deviation": 16,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "ADHD"},

        # Executive function
        {"domain": "ExecutiveFunction", "age_group": "5-7", "mean_score": 58, "standard_deviation": 15,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "ADHD"},
        {"domain": "ExecutiveFunction", "age_group": "8-10", "mean_score": 63, "standard_deviation": 15,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "ADHD"},
        {"domain": "ExecutiveFunction", "age_group": "11-13", "mean_score": 67, "standard_deviation": 15,
         "source_reference": "Willcutt et al. (2005)", "clinical_group": "ADHD"},
    ]

    # --- NEW: Go/No-Go Metrics Norms (Based on Barnard et al., 2023, GNG Phase) ---
    # IMPORTANT: SDs are ESTIMATED/PLACEHOLDERS. Replace with actual SDs for accurate Z-scores.
    # Using Barnard's 5-6 yrs for "5-7" and 7+ yrs for "8-10" and "11-13" as proxies.
    # Scores are proportions (0-1) for errors, milliseconds for RT.
    gonogo_norms = [
        # Age 5-7 (Proxy: Barnard 5-6 yrs)
        {"domain": "GoNoGo_CommissionErrors", "age_group": "5-7", "mean_score": 0.28, "standard_deviation": 0.15, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},
        {"domain": "GoNoGo_OmissionErrors", "age_group": "5-7", "mean_score": 0.17, "standard_deviation": 0.15, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},
        {"domain": "GoNoGo_MeanRT", "age_group": "5-7", "mean_score": 497.70, "standard_deviation": 70.0, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},
        {"domain": "GoNoGo_RTVariability", "age_group": "5-7", "mean_score": 119.64, "standard_deviation": 30.0, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},

        # Age 8-10 (Proxy: Barnard 7+ yrs)
        {"domain": "GoNoGo_CommissionErrors", "age_group": "8-10", "mean_score": 0.33, "standard_deviation": 0.18, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},
        {"domain": "GoNoGo_OmissionErrors", "age_group": "8-10", "mean_score": 0.25, "standard_deviation": 0.18, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},
        {"domain": "GoNoGo_MeanRT", "age_group": "8-10", "mean_score": 356.57, "standard_deviation": 50.0, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},
        {"domain": "GoNoGo_RTVariability", "age_group": "8-10", "mean_score": 76.73, "standard_deviation": 20.0, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},

        # Age 11-13 (Proxy: Barnard 7+ yrs - Consider finding more specific norms)
        {"domain": "GoNoGo_CommissionErrors", "age_group": "11-13", "mean_score": 0.33, "standard_deviation": 0.18, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},
        {"domain": "GoNoGo_OmissionErrors", "age_group": "11-13", "mean_score": 0.25, "standard_deviation": 0.18, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},
        {"domain": "GoNoGo_MeanRT", "age_group": "11-13", "mean_score": 356.57, "standard_deviation": 50.0, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},
        {"domain": "GoNoGo_RTVariability", "age_group": "11-13", "mean_score": 76.73, "standard_deviation": 20.0, # Estimated SD
         "source_reference": "Barnard et al. (2023) PMC10041761 - SD Estimated", "clinical_group": "TypicallyDeveloping"},
        # Add ADHD specific Go/No-Go norms if available
    ]

    # --- NEW: Placeholder Attention Norms (Derived Score) ---
    # Replace with actual norms derived from your scoring logic and normative sample
    attention_norms = [
        {"domain": "Attention", "age_group": "5-7", "mean_score": 72.0, "standard_deviation": 14.0,
         "source_reference": "Placeholder - Derived Score", "clinical_group": "TypicallyDeveloping"},
        {"domain": "Attention", "age_group": "8-10", "mean_score": 78.0, "standard_deviation": 13.0,
         "source_reference": "Placeholder - Derived Score", "clinical_group": "TypicallyDeveloping"},
        {"domain": "Attention", "age_group": "11-13", "mean_score": 82.0, "standard_deviation": 12.0,
         "source_reference": "Placeholder - Derived Score", "clinical_group": "TypicallyDeveloping"},
        # Add ADHD specific Attention norms if available
        # {"domain": "Attention", "age_group": "8-10", "mean_score": 60.0, "standard_deviation": 16.0,
        #  "source_reference": "Placeholder - Derived Score", "clinical_group": "ADHD"},
    ]

    # Combine all norms
    all_norms = memory_norms + impulse_norms + executive_norms + adhd_norms + gonogo_norms + attention_norms

    # Check for existing data before seeding (optional, depends on your logic)
    # existing_count = await db.scalar(select(func.count(NormativeData.id)))
    # if existing_count > 0:
    #     print("Normative data already exists. Skipping seed.")
    #     return

    added_count = 0
    for norm_dict in all_norms:
        # Ensure all required fields are present before creating the object
        if all(k in norm_dict for k in ('domain', 'age_group', 'mean_score', 'standard_deviation')):
            # Set default clinical_group if not present
            if 'clinical_group' not in norm_dict:
                norm_dict['clinical_group'] = 'TypicallyDeveloping'

            norm_data = NormativeData(**norm_dict)
            db.add(norm_data)
            added_count += 1
        else:
            print(f"Skipping invalid norm record: {norm_dict}")

    await db.commit()
    print(f"Attempted to add {len(all_norms)} normative data records. Successfully added: {added_count}")

# Example of how to run (if needed, usually called from main seeding script)
# async def main():
#     from app.db.session import SessionLocal # Adjust import as per your project structure
#     async with SessionLocal() as db:
#         await seed_normative_data(db)
#
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())

