from pathlib import Path
import pandas as pd

# -----------------------------------
# SETUP
# -----------------------------------

input_dir = Path("experimental_data/intensities")
llm_dir = Path("llm_inputs/intensities")
evaluation_dir = Path("evaluation/intensities")

llm_dir.mkdir(parents=True, exist_ok=True)
evaluation_dir.mkdir(parents=True, exist_ok=True)

files = {
    "baseline": "baseline.csv",
    "missing_10_percent": "missing_10_percent.csv",
    "noisy": "noisy_data.csv"
}

# Only original wearable columns are allowed in LLM-facing files.
expected_columns = ["Id","ActivityHour","TotalIntensity","AverageIntensity"]
measurement_columns = ["TotalIntensity","AverageIntensity"]
reports = []

# -----------------------------------
# PROCESS DATASETS
# -----------------------------------

for condition, filename in files.items():

    df = pd.read_csv(input_dir / filename)

    # Check required columns.
    missing_columns = set(expected_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{filename} missing columns: {missing_columns}"
        )

    # Exclude experimental metadata and preserve existing row order.
    df = df[expected_columns].copy()

    # Standardize timestamps without changing the recorded times.
    df["ActivityHour"] = pd.to_datetime(
        df["ActivityHour"], errors="raise"
    ).dt.strftime("%Y-%m-%d %H:%M:%S")

    # Validate numeric measurements without filling missing values.
    for col in measurement_columns:
        df[col] = pd.to_numeric(df[col], errors="raise")

    # Flag issues without dropping or repairing experimental records.
    missing_values = df[measurement_columns].isna().sum().sum()

    duplicate_timestamps = df.duplicated(
        subset=["Id", "ActivityHour"]
    ).sum()

    negative_values = (df[measurement_columns] < 0).sum().sum()

    # Export LLM-facing data.
    df.to_csv(llm_dir / filename, index=False)

    reports.append({
        "condition": condition,
        "rows": len(df),
        "participants": df["Id"].nunique(),
        "missing_values": int(missing_values),
        "duplicate_timestamps": int(duplicate_timestamps),
        "negative_values": int(negative_values)
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

print("\nIntensities processing complete!")

