
from pathlib import Path
import numpy as np
import pandas as pd

# --------------------------------------------------
# SETUP
# --------------------------------------------------

data_dir = Path("data_files")
output_dir = Path("experimental_data/weight")
output_dir.mkdir(parents=True, exist_ok=True)

# Load original dataset
original = pd.read_csv(
    data_dir / "weightLogInfo_merged.csv"
)

# Convert date column
original["Date"] = pd.to_datetime(
    original["Date"],
    format="%m/%d/%Y %I:%M:%S %p"
)

# Fixed random seed
rng = np.random.default_rng(42)

# --------------------------------------------------
# BASELINE
# --------------------------------------------------

baseline = original.copy()

baseline.to_csv(
    output_dir / "baseline.csv",
    index=False
)

# --------------------------------------------------
# FILE 1: 10% MISSING WEIGHT VALUES
# --------------------------------------------------

missing = original.copy()

missing_count = round(len(missing) * 0.10)

missing_rows = rng.choice(
    missing.index.to_numpy(),
    size=missing_count,
    replace=False
)

missing.loc[missing_rows, "WeightKg"] = np.nan

missing.to_csv(
    output_dir / "missing_10_percent.csv",
    index=False
)

# --------------------------------------------------
# FILE 2: CORRUPTED / NOISY DATA
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

shifted["OriginalDate"] = shifted["Date"]

count = round(len(shifted) * 0.10)

selected = rng.choice(
    shifted.index.to_numpy(),
    size=count,
    replace=False
)

# Shift dates forward by one day
shifted.loc[selected, "Date"] += pd.Timedelta(days=1)

shifted["corruption_type"] = "timestamp_shift"
shifted["was_corrupted"] = False
shifted.loc[selected, "was_corrupted"] = True

corrupted_groups.append(shifted)

# --------------------------------------------------
# GROUP 2: RANDOM WEIGHT VARIATION
# --------------------------------------------------

varied = original.loc[groups[1]].copy()

count = round(len(varied) * 0.10)

selected = rng.choice(
    varied.index.to_numpy(),
    size=count,
    replace=False
)

# Noise based on 10% of standard deviation
noise_scale = varied["WeightKg"].std() * 0.10

noise = rng.normal(
    0,
    noise_scale,
    size=count
)

varied.loc[selected, "WeightKg"] = np.maximum(
    0,
    np.round(
        varied.loc[selected, "WeightKg"].to_numpy()
        + noise,
        2
    )
)

varied["corruption_type"] = "random_variation"
varied["was_corrupted"] = False
varied.loc[selected, "was_corrupted"] = True

corrupted_groups.append(varied)

# --------------------------------------------------
# GROUP 3: UNREALISTIC WEIGHT SPIKES
# --------------------------------------------------

spikes = original.loc[groups[2]].copy()

count = round(len(spikes) * 0.10)

selected = rng.choice(
    spikes.index.to_numpy(),
    size=count,
    replace=False
)

# Artificially extreme weight reading
spikes.loc[selected, "WeightKg"] = 300

spikes["corruption_type"] = "unrealistic_spike"
spikes["was_corrupted"] = False
spikes.loc[selected, "was_corrupted"] = True

corrupted_groups.append(spikes)

# --------------------------------------------------
# COMBINE ALL CORRUPTED GROUPS
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

print("Weight-log experiments created!")

print("\nBaseline rows:", len(baseline))

print(
    "Missing WeightKg values:",
    missing["WeightKg"].isna().sum()
)

print("\nNoisy-data rows:", len(noisy_data))

print("\nCorruption groups:")
print(noisy_data["corruption_type"].value_counts())

print("\nRows selected for corruption:")
print(
    noisy_data.groupby("corruption_type")[
        "was_corrupted"
    ].sum()
)

print("\nFiles saved in:", output_dir.resolve())
