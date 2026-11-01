
from pathlib import Path
import pandas as pd

# -----------------------------------
# SETUP
# -----------------------------------

input_dir = Path("experimental_data/heart_rate")
llm_dir = Path("llm_inputs/heart_rate")
evaluation_dir = Path("evaluation/heart_rate")

llm_dir.mkdir(parents=True, exist_ok=True)
evaluation_dir.mkdir(parents=True, exist_ok=True)

files = {
    "baseline": "baseline.csv",
    "missing_10_percent": "missing_10_percent.csv",
    "noisy": "noisy_data.csv"
}

expected_columns = ["Id", "Time", "Value"]
reports = []

# -----------------------------------
# PROCESS DATASETS
# -----------------------------------

for condition, filename in files.items():

    df = pd.read_csv(input_dir / filename)

    # Check required columns
    missing_columns = set(expected_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{filename} missing columns: {missing_columns}"
        )

    # Keep only original wearable columns
    df = df[expected_columns].copy()

    # Standardize timestamps
    df["Time"] = pd.to_datetime(
        df["Time"], errors="raise"
    ).dt.strftime("%Y-%m-%d %H:%M:%S")

    # Ensure heart rate is numeric
    df["Value"] = pd.to_numeric(
        df["Value"], errors="raise"
    )

    # Validation checks
    missing_values = df["Value"].isna().sum()

    duplicate_timestamps = df.duplicated(
        subset=["Id", "Time"]
    ).sum()

    negative_values = (df["Value"] < 0).sum()

    # Export LLM-facing data
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

print("\nHeart rate processing complete!")
