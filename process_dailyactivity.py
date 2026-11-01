
from pathlib import Path
import pandas as pd

# -----------------------------------
# SETUP
# -----------------------------------

input_dir = Path("experimental_data/daily_activity")
llm_dir = Path("llm_inputs/daily_activity")
evaluation_dir = Path("evaluation/daily_activity")

llm_dir.mkdir(parents=True, exist_ok=True)
evaluation_dir.mkdir(parents=True, exist_ok=True)

files = {
    "baseline": "baseline.csv",
    "missing_10_percent": "missing_10_percent.csv",
    "noisy": "noisy_data.csv"
}

# Columns allowed in LLM-facing files
measurement_columns = [
    "TotalSteps",
    "TotalDistance",
    "TrackerDistance",
    "LoggedActivitiesDistance",
    "VeryActiveDistance",
    "ModeratelyActiveDistance",
    "LightActiveDistance",
    "SedentaryActiveDistance",
    "VeryActiveMinutes",
    "FairlyActiveMinutes",
    "LightlyActiveMinutes",
    "SedentaryMinutes",
    "Calories"
]

columns = ["Id", "ActivityDate"] + measurement_columns

# -----------------------------------
# PROCESS DATASETS
# -----------------------------------

reports = []

for condition, filename in files.items():

    df = pd.read_csv(input_dir / filename)

    # Validate required columns
    missing_columns = set(columns) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{filename} missing columns: {missing_columns}"
        )

    # Keep only wearable data columns
    df = df[columns].copy()

    # Standardize date format
    df["ActivityDate"] = pd.to_datetime(
        df["ActivityDate"], errors="raise"
    ).dt.strftime("%Y-%m-%d")

    # Validate measurement types without filling missing values
    for col in measurement_columns:
        df[col] = pd.to_numeric(df[col], errors="raise")

    # Check participant/date duplicates
    duplicate_count = df.duplicated(
        subset=["Id", "ActivityDate"]
    ).sum()

    # Check negative measurement values
    negative_count = (df[measurement_columns] < 0).sum().sum()

    # Count missing measurement cells
    missing_count = df[measurement_columns].isna().sum().sum()

    # Export cleanly structured LLM input
    output_path = llm_dir / filename
    df.to_csv(output_path, index=False)

    reports.append({
        "condition": condition,
        "rows": len(df),
        "participants": df["Id"].nunique(),
        "missing_measurements": int(missing_count),
        "duplicate_participant_dates": int(duplicate_count),
        "negative_measurements": int(negative_count)
    })

    print(f"Processed {filename}: {len(df)} rows")

# -----------------------------------
# SAVE INTERNAL VALIDATION REPORT
# -----------------------------------

report = pd.DataFrame(reports)

report.to_csv(
    evaluation_dir / "validation_report.csv",
    index=False
)

print("\nValidation report:")
print(report.to_string(index=False))

print("\nProcessing complete!")
