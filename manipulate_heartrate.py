
from pathlib import Path
import numpy as np
import pandas as pd

# --------------------------------------------------
# SETUP
# --------------------------------------------------

data_dir = Path("data_files")
output_dir = Path("experimental_data/heart_rate")
output_dir.mkdir(parents=True, exist_ok=True)

# Load original heart-rate dataset
original = pd.read_csv(
    data_dir / "heartrate_seconds_merged.csv"
)

# Convert timestamps to datetime
original["Time"] = pd.to_datetime(
    original["Time"],
    format="%m/%d/%Y %I:%M:%S %p"
)

# Fixed seed for reproducibility
rng = np.random.default_rng(42)

# --------------------------------------------------
# BASELINE: SAVE ORIGINAL MEASUREMENTS
# --------------------------------------------------

baseline = original.copy()

baseline.to_csv(
    output_dir / "baseline.csv",
    index=False
)

# --------------------------------------------------
# FILE 1: 10% MISSING HEART-RATE VALUES
# --------------------------------------------------

missing = original.copy()

missing_count = round(len(missing) * 0.10)

missing_rows = rng.choice(
    missing.index.to_numpy(),
    size=missing_count,
    replace=False
)

missing.loc[missing_rows, "Value"] = np.nan

missing.to_csv(
    output_dir / "missing_10_percent.csv",
    index=False
)

# --------------------------------------------------
# FILE 2: CORRUPTED / NOISY DATA
# Divide rows into three random groups
# --------------------------------------------------

shuffled_indices = rng.permutation(
    original.index.to_numpy()
)

groups = np.array_split(shuffled_indices, 3)

corrupted_groups = []

# --------------------------------------------------
# GROUP 1: TIMESTAMP SHIFTS
# --------------------------------------------------

shifted = original.loc[groups[0]].copy()

shifted["OriginalTime"] = shifted["Time"]

count = round(len(shifted) * 0.10)

selected = rng.choice(
    shifted.index.to_numpy(),
    size=count,
    replace=False
)

# Shift timestamps forward by one hour
shifted.loc[selected, "Time"] += pd.Timedelta(hours=1)

shifted["corruption_type"] = "timestamp_shift"
shifted["was_corrupted"] = False
shifted.loc[selected, "was_corrupted"] = True

corrupted_groups.append(shifted)

# --------------------------------------------------
# GROUP 2: RANDOM HEART-RATE VARIATION
# --------------------------------------------------

varied = original.loc[groups[1]].copy()

count = round(len(varied) * 0.10)

selected = rng.choice(
    varied.index.to_numpy(),
    size=count,
    replace=False
)

# Random noise scaled to the group's variability
noise_scale = varied["Value"].std() * 0.10

noise = rng.normal(
    0,
    noise_scale,
    size=count
)

varied.loc[selected, "Value"] = np.maximum(
    0,
    np.round(
        varied.loc[selected, "Value"].to_numpy() + noise
    )
).astype(int)

varied["corruption_type"] = "random_variation"
varied["was_corrupted"] = False
varied.loc[selected, "was_corrupted"] = True

corrupted_groups.append(varied)

# --------------------------------------------------
# GROUP 3: UNREALISTIC HEART-RATE SPIKES
# --------------------------------------------------

spikes = original.loc[groups[2]].copy()

count = round(len(spikes) * 0.10)

selected = rng.choice(
    spikes.index.to_numpy(),
    size=count,
    replace=False
)

# Intentionally extreme heart-rate readings
spikes.loc[selected, "Value"] = 300

spikes["corruption_type"] = "unrealistic_spike"
spikes["was_corrupted"] = False
spikes.loc[selected, "was_corrupted"] = True

corrupted_groups.append(spikes)

# --------------------------------------------------
# COMBINE CORRUPTED GROUPS
# --------------------------------------------------

noisy_data = pd.concat(
    corrupted_groups,
    ignore_index=True
)

noisy_data.to_csv(
    output_dir / "noisy_data.csv",
    index=False
)

# --------------------------------------------------
# VERIFY OUTPUTS
# --------------------------------------------------

print("Heart-rate experiments created successfully!")

print("\nBaseline:")
print("Rows:", len(baseline))

print("\nMissing-data experiment:")
print("Rows:", len(missing))
print("Missing values:", missing["Value"].isna().sum())

print("\nCorrupted-data experiment:")
print("Rows:", len(noisy_data))

print("\nRows assigned to each corruption type:")
print(noisy_data["corruption_type"].value_counts())

print("\nRows selected for actual corruption:")
print(
    noisy_data.groupby("corruption_type")["was_corrupted"].sum()
)

print("\nFiles saved in:", output_dir.resolve())
