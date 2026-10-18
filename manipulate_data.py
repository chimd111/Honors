
from pathlib import Path
import pandas as pd
import numpy as np

# Folders
data_dir = Path("data_files")
output_dir = Path("experimental_data")
output_dir.mkdir(exist_ok=True)

# Load the original dataset
df = pd.read_csv(data_dir / "hourlySteps_merged.csv")

# Parse timestamps
df["ActivityHour"] = pd.to_datetime(
    df["ActivityHour"],
    format="%m/%d/%Y %I:%M:%S %p"
)

# Keep an untouched baseline copy
baseline = df.copy()
baseline.to_csv(output_dir / "baseline.csv", index=False)

# Use a fixed seed so experiments are reproducible
rng = np.random.default_rng(42)
n = len(df)
count = round(n * 0.10)

# Experiment A: 10% missing step counts
missing = df.copy()
missing_rows = rng.choice(n, size=count, replace=False)
missing.loc[missing_rows, "StepTotal"] = np.nan
missing.to_csv(output_dir / "missing_10_percent.csv", index=False)

# Experiment B: Noise on 10% of step counts
noisy = df.copy()
noise_rows = rng.choice(n, size=count, replace=False)

original_steps = noisy.loc[noise_rows, "StepTotal"]
noise = rng.normal(loc=0, scale=original_steps.std(), size=count)

noisy.loc[noise_rows, "StepTotal"] = np.maximum(
    0, np.round(original_steps.to_numpy() + noise)
).astype(int)

noisy.to_csv(output_dir / "noisy_10_percent.csv", index=False)

# Experiment C: Shift 10% of timestamps by one hour
shifted = df.copy()
shift_rows = rng.choice(n, size=count, replace=False)

shifted.loc[shift_rows, "ActivityHour"] += pd.Timedelta(hours=1)
shifted.to_csv(output_dir / "timestamp_shift_10_percent.csv",
               index=False)

print("Experiments created successfully!")
print("Original rows:", len(baseline))
print("Missing values introduced:", missing["StepTotal"].isna().sum())
print("Noisy readings changed:", count)
print("Timestamps shifted:", count)
print("Output folder:", output_dir.resolve())
