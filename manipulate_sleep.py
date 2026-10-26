from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------
# SETUP
# --------------------------------------------------

data_dir = Path("data_files")
output_dir = Path("experimental_data/sleep")
output_dir.mkdir(parents=True, exist_ok=True)

# Load the original dataset
original = pd.read_csv(data_dir / "minuteSleep_merged.csv")

# Make timestamps usable for time manipulation
original["date"] = pd.to_datetime(
    original["date"],
    format="%m/%d/%Y %I:%M:%S %p",
)

# Keep an untouched baseline copy
baseline = original.copy()
baseline.to_csv(output_dir / "baseline.csv", index=False)

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

# Remove 10% of sleep-stage values, not entire rows
missing.loc[missing_rows, "value"] = np.nan

missing.to_csv(
    output_dir / "missing_10_percent.csv",
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
shifted["OriginalDate"] = shifted["date"]

count = round(len(shifted) * 0.10)

selected = rng.choice(
    shifted.index.to_numpy(),
    size=count,
    replace=False,
)

shifted.loc[selected, "date"] += pd.Timedelta(hours=1)
shifted["corruption_type"] = "timestamp_shift"
shifted["was_corrupted"] = False
shifted.loc[selected, "was_corrupted"] = True

corrupted_groups.append(shifted)

# Group 2: Add random variation to 10% of sleep-stage values
varied = original.loc[groups[1]].copy()

count = round(len(varied) * 0.10)

selected = rng.choice(
    varied.index.to_numpy(),
    size=count,
    replace=False,
)

noise_scale = varied["value"].std() * 0.10
noise = rng.normal(0, noise_scale, size=count)

varied.loc[selected, "value"] = np.clip(
    np.round(varied.loc[selected, "value"].to_numpy() + noise),
    1,
    3,
).astype(int)

varied["corruption_type"] = "random_variation"
varied["was_corrupted"] = False
varied.loc[selected, "was_corrupted"] = True

corrupted_groups.append(varied)

# Group 3: Insert unrealistic spikes in 10% of sleep-stage values
spikes = original.loc[groups[2]].copy()

count = round(len(spikes) * 0.10)

selected = rng.choice(
    spikes.index.to_numpy(),
    size=count,
    replace=False,
)

spikes.loc[selected, "value"] = 5
spikes["corruption_type"] = "unrealistic_spike"
spikes["was_corrupted"] = False
spikes.loc[selected, "was_corrupted"] = True

corrupted_groups.append(spikes)

# Combine the three groups into one file
noisy_data = pd.concat(
    corrupted_groups,
    ignore_index=True,
)

noisy_data.to_csv(
    output_dir / "noisy_data.csv",
    index=False,
)

# --------------------------------------------------
# VERIFY OUTPUTS
# --------------------------------------------------

print("Sleep-data experiments created successfully!")
print("\nBaseline:")
print("Rows:", len(baseline))

print("\nMissing-data experiment:")
print("Rows:", len(missing))
print("Missing values:", missing["value"].isna().sum())

print("\nCorrupted-data experiment:")
print("Rows:", len(noisy_data))
print(noisy_data["corruption_type"].value_counts())
print("Rows selected for corruption:")
print(noisy_data.groupby("corruption_type")["was_corrupted"].sum())

print("\nFiles saved in:", output_dir.resolve())
