
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------
# SETUP
# --------------------------------------------------

data_dir = Path("data_files")
output_dir = Path("experimental_data")
output_dir.mkdir(exist_ok=True)

# Load the original dataset
original = pd.read_csv(data_dir / "hourlyCalories_merged.csv")

# Make timestamps usable for time manipulation
original["ActivityHour"] = pd.to_datetime(
    original["ActivityHour"],
    format="%m/%d/%Y %I:%M:%S %p",
)

# Keep an untouched baseline copy
baseline = original.copy()
baseline.to_csv(output_dir / "hourly_calories_baseline.csv", index=False)

# Reproducible random selection
rng = np.random.default_rng(42)

# --------------------------------------------------
# FILE 1: 10% MISSING DATA
# --------------------------------------------------

missing = original.copy()

missing_count = round(len(missing) * 0.10)

missing_rows = rng.choice(
    missing.index.to_numpy(),
    size=missing_count,
    replace=False,
)

# Remove 10% of Calories values, not entire rows
missing.loc[missing_rows, "Calories"] = np.nan

missing.to_csv(
    output_dir / "hourly_calories_missing_10_percent.csv",
    index=False,
)

# --------------------------------------------------
# FILE 2: CORRUPTED / NOISY DATA
# Divide rows into three random groups
# --------------------------------------------------

shuffled_indices = rng.permutation(original.index.to_numpy())
groups = np.array_split(shuffled_indices, 3)

corrupted_groups = []

# Group 1: Shift 10% of timestamps by one hour
shifted = original.loc[groups[0]].copy()
shifted["OriginalActivityHour"] = shifted["ActivityHour"]

count = round(len(shifted) * 0.10)

selected = rng.choice(
    shifted.index.to_numpy(),
    size=count,
    replace=False,
)

shifted.loc[selected, "ActivityHour"] += pd.Timedelta(hours=1)
shifted["corruption_type"] = "timestamp_shift"

corrupted_groups.append(shifted)

# Group 2: Add random variation to 10% of step counts
varied = original.loc[groups[1]].copy()

count = round(len(varied) * 0.10)

selected = rng.choice(
    varied.index.to_numpy(),
    size=count,
    replace=False,
)

noise_scale = varied["Calories"].std() * 0.10
noise = rng.normal(0, noise_scale, size=count)

varied.loc[selected, "Calories"] = np.maximum(
    0,
    np.round(
        varied.loc[selected, "Calories"].to_numpy() + noise
    ),
).astype(int)

varied["corruption_type"] = "random_variation"

corrupted_groups.append(varied)

# Group 3: Insert unrealistic spikes in 10% of step counts
spikes = original.loc[groups[2]].copy()

count = round(len(spikes) * 0.10)

selected = rng.choice(
    spikes.index.to_numpy(),
    size=count,
    replace=False,
)

spikes.loc[selected, "Calories"] = 5000
spikes["corruption_type"] = "unrealistic_spike"

corrupted_groups.append(spikes)

# Combine the three groups into one file
noisy_data = pd.concat(
    corrupted_groups,
    ignore_index=True,
)

noisy_data.to_csv(
    output_dir / "hourly_calories_noisy.csv",
    index=False,
)

# --------------------------------------------------
# VERIFY OUTPUTS
# --------------------------------------------------

print("Experiments created successfully!")
print("\nMissing-data experiment:")
print("Original rows:", len(original))
print("Missing Calories values:", missing["Calories"].isna().sum())

print("\nCorrupted-data experiment:")
print("Total rows:", len(noisy_data))
print(noisy_data["corruption_type"].value_counts())

print("\nFiles saved in:", output_dir.resolve())
