
from pathlib import Path
import numpy as np
import pandas as pd

# --------------------------------------------------
# SETUP
# --------------------------------------------------

data_dir = Path("data_files")
output_dir = Path("experimental_data/daily_activity")
output_dir.mkdir(parents=True, exist_ok=True)

original = pd.read_csv(
    data_dir / "dailyActivity_merged.csv"
)

original["ActivityDate"] = pd.to_datetime(
    original["ActivityDate"],
    format="%m/%d/%Y"
)

rng = np.random.default_rng(42)

# All measurement columns eligible for manipulation
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
    "Calories",
]

# Check that every column exists
missing_columns = [
    col for col in measurement_columns
    if col not in original.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns: {missing_columns}"
    )

# --------------------------------------------------
# BASELINE
# --------------------------------------------------

baseline = original.copy()

baseline.to_csv(
    output_dir / "baseline.csv",
    index=False
)

# --------------------------------------------------
# FILE 1: 10% MISSING MEASUREMENT CELLS
# --------------------------------------------------

missing = original.copy()

# Total number of eligible measurement cells
total_cells = len(missing) * len(measurement_columns)

missing_count = round(total_cells * 0.10)

# Randomly select unique cell positions
selected_cells = rng.choice(
    total_cells,
    size=missing_count,
    replace=False
)

# Convert cell positions into row and column positions
row_positions = selected_cells // len(measurement_columns)
column_positions = selected_cells % len(measurement_columns)

for row_pos, col_pos in zip(row_positions, column_positions):
    column = measurement_columns[col_pos]
    missing.at[missing.index[row_pos], column] = np.nan

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

count = round(len(shifted) * 0.10)

selected = rng.choice(
    shifted.index.to_numpy(),
    size=count,
    replace=False
)

shifted["OriginalActivityDate"] = shifted["ActivityDate"]

shifted.loc[selected, "ActivityDate"] += (
    pd.Timedelta(days=1)
)

shifted["corruption_type"] = "timestamp_shift"
shifted["was_corrupted"] = False
shifted.loc[selected, "was_corrupted"] = True
shifted["modified_column"] = pd.NA
shifted.loc[selected, "modified_column"] = "ActivityDate"

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

varied["corruption_type"] = "random_variation"
varied["was_corrupted"] = False
varied["modified_column"] = pd.NA

# Randomly select a measurement column for each row
for row_index in selected:

    column = rng.choice(measurement_columns)

    original_value = varied.at[row_index, column]

    # Calculate noise using the column's standard deviation
    noise_scale = original[column].std() * 0.10

    noise = rng.normal(0, noise_scale)

    new_value = max(0, original_value + noise)

    # Preserve whole-number measurements
    if column in [
        "TotalSteps",
        "VeryActiveMinutes",
        "FairlyActiveMinutes",
        "LightlyActiveMinutes",
        "SedentaryMinutes",
        "Calories",
    ]:
        new_value = round(new_value)

    else:
        new_value = round(new_value, 2)

    varied.at[row_index, column] = new_value
    varied.at[row_index, "was_corrupted"] = True
    varied.at[row_index, "modified_column"] = column

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

spikes["corruption_type"] = "unrealistic_spike"
spikes["was_corrupted"] = False
spikes["modified_column"] = pd.NA

for row_index in selected:

    column = rng.choice(measurement_columns)

    # Use an extreme value relative to the column
    column_max = original[column].max()

    # Make the value 5 times the original maximum
    spike_value = column_max * 5

    # Handle columns whose maximum is zero
    if spike_value == 0:
        spike_value = 100

    if column in [
        "TotalSteps",
        "VeryActiveMinutes",
        "FairlyActiveMinutes",
        "LightlyActiveMinutes",
        "SedentaryMinutes",
        "Calories",
    ]:
        spike_value = round(spike_value)
    else:
        spike_value = round(spike_value, 2)

    spikes.at[row_index, column] = spike_value
    spikes.at[row_index, "was_corrupted"] = True
    spikes.at[row_index, "modified_column"] = column

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
# VERIFICATION
# --------------------------------------------------

print("Daily activity experiments created!")

print("\nBaseline rows:", len(baseline))

print("\nMissing-data experiment:")
print("Missing cells introduced:", missing_count)

print("\nNoisy-data experiment:")
print("Total rows:", len(noisy_data))

print("\nRows assigned to each corruption type:")
print(noisy_data["corruption_type"].value_counts())

print("\nRows selected for corruption:")
print(
    noisy_data.groupby("corruption_type")[
        "was_corrupted"
    ].sum()
)

print("\nModified measurement columns:")
print(noisy_data["modified_column"].value_counts())

print("\nOutput folder:", output_dir.resolve())
