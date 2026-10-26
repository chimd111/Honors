
from pathlib import Path
import numpy as np
import pandas as pd

# --------------------------------------------------
# SETUP
# --------------------------------------------------

data_dir = Path("data_files")
output_dir = Path("experimental_data/intensities")
output_dir.mkdir(parents=True, exist_ok=True)

# Load original dataset
original = pd.read_csv(
    data_dir / "hourlyIntensities_merged.csv"
)

# Convert timestamp
original["ActivityHour"] = pd.to_datetime(
    original["ActivityHour"],
    format="%m/%d/%Y %I:%M:%S %p"
)

# Fixed seed for reproducibility
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
# FILE 1: 10% MISSING DATA
# --------------------------------------------------

missing = original.copy()

missing_count = round(len(missing) * 0.10)

missing_rows = rng.choice(
    missing.index.to_numpy(),
    size=missing_count,
    replace=False
)

# Remove selected TotalIntensity values
missing.loc[missing_rows, "TotalIntensity"] = np.nan

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

shifted["OriginalActivityHour"] = shifted["ActivityHour"]

count = round(len(shifted) * 0.10)

selected = rng.choice(
    shifted.index.to_numpy(),
    size=count,
    replace=False
)

shifted.loc[selected, "ActivityHour"] += (
    pd.Timedelta(hours=1)
)

shifted["corruption_type"] = "timestamp_shift"
shifted["was_corrupted"] = False
shifted.loc[selected, "was_corrupted"] = True

corrupted_groups.append(shifted)

# --------------------------------------------------
# GROUP 2: RANDOM VARIATION
# --------------------------------------------------

varied = original.loc[groups[1]].copy()

count = round(len(varied) * 0.10)

selected = rng.choice(
    varied.index.to_numpy(),
    size=count,
    replace=False
)

noise_scale = varied["TotalIntensity"].std() * 0.10

noise = rng.normal(
    0,
    noise_scale,
    size=count
)

varied.loc[selected, "TotalIntensity"] = np.maximum(
    0,
    np.round(
        varied.loc[selected, "TotalIntensity"].to_numpy()
        + noise
    )
).astype(int)

varied["corruption_type"] = "random_variation"
varied["was_corrupted"] = False
varied.loc[selected, "was_corrupted"] = True

corrupted_groups.append(varied)

# --------------------------------------------------
# GROUP 3: UNREALISTIC SPIKES
# --------------------------------------------------

spikes = original.loc[groups[2]].copy()

count = round(len(spikes) * 0.10)

selected = rng.choice(
    spikes.index.to_numpy(),
    size=count,
    replace=False
)

# Extreme synthetic intensity value
spikes.loc[selected, "TotalIntensity"] = 500

spikes["corruption_type"] = "unrealistic_spike"
spikes["was_corrupted"] = False
spikes.loc[selected, "was_corrupted"] = True

corrupted_groups.append(spikes)

# --------------------------------------------------
# COMBINE ALL THREE GROUPS
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

print("Hourly intensity experiments created!")

print("\nBaseline rows:", len(baseline))

print(
    "Missing TotalIntensity values:",
    missing["TotalIntensity"].isna().sum()
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
