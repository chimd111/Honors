# Fitbit Data Quality Manipulation

## 1. Project Overview

This project investigates how data-quality problems in wearable health data may affect AI-generated health summaries.

The dataset used is the Fitbit Fitness Tracker dataset obtained from [Zenodo](https://zenodo.org/records/53894). It contains activity, heart-rate, sleep, calorie and other fitness measurements collected from Fitbit users.

The purpose of this project is to introduce controlled data-quality problems into the original dataset and later compare AI-generated health summaries produced from the original and manipulated data.

The experiments focus on two main categories:

1. **Missing data:** Removing selected measurement values while preserving the records.
2. **Corrupted data:** Introducing inaccurate timestamps, random variations in measurements and unrealistic spikes.

The original dataset is preserved so that the manipulated data can be compared against an unchanged reference.

## 2. Project Structure

The project is organized into the following folders and files:

```text
Honors/
├── data_files/
│   ├── hourlySteps_merged.csv
│   ├── hourlyCalories_merged.csv
│   └── other Fitbit CSV files
├── experimental_data/
│   ├── steps/
│   │   ├── baseline.csv
│   │   ├── missing_10_percent.csv
│   │   └── noisy_data.csv
│   ├── heart_rate/
│   │   ├── baseline.csv
│   │   ├── missing_10_percent.csv
│   │   └── noisy_data.csv
│   ├── calories/
│   │   ├── baseline.csv
│   │   ├── missing_10_percent.csv
│   │   └── noisy_data.csv
│   ├── intensities/
│   │   ├── baseline.csv
│   │   ├── missing_10_percent.csv
│   │   └── noisy_data.csv
│   └── sleep/
│       ├── baseline.csv
│       ├── missing_10_percent.csv
│       └── noisy_data.csv
├── manipulate_data.py
├── manipulate_h_calories.py
└── README.md
```

**Note:** The output filenames depend on which script is executed and how its output paths are configured.

### Folder descriptions

- `data_files/`: Contains the original Fitbit CSV files. These files should remain unchanged.
- `experimental_data/`: Stores the baseline and manipulated datasets in separate folders for steps, heart rate, calories, intensities and sleep.
- `manipulate_data.py`: Processes the hourly step-count data.
- `manipulate_h_calories.py`: Adapts the manipulation process to hourly calorie data.
- `README.md`: Documents the experiment and explains how to run the scripts.

## 3. Technologies Used

The experiments are implemented in Python using the following libraries:

- **pandas:** Loads, organizes, modifies and exports CSV data using DataFrames.
- **NumPy:** Randomly selects records and generates numerical variations for the corruption experiments.
- **pathlib:** Creates and manages file and folder paths.

Install the required libraries if they are not already installed:

```bash
pip install pandas numpy
```

## 4. Step-by-Step Data Preparation

### Step 1: Load the original dataset

The script reads the selected CSV file using pandas.

For the step-count experiment:

```python
original = pd.read_csv(
    data_dir / "hourlySteps_merged.csv"
)
```

For the calorie experiment:

```python
original = pd.read_csv(
    data_dir / "hourlyCalories_merged.csv"
)
```

The step-count file contains the `StepTotal` measurement column, while the calorie file contains the `Calories` measurement column.

### Step 2: Prepare the timestamps

The timestamp column is converted into a datetime format.

```python
original["ActivityHour"] = pd.to_datetime(
    original["ActivityHour"],
    format="%m/%d/%Y %I:%M:%S %p",
)
```

This allows Python to perform operations on timestamps, such as shifting a recorded time forward by one hour.

### Step 3: Create a baseline

An unchanged copy of the loaded dataset is saved for comparison.

```python
baseline = original.copy()

baseline.to_csv(
    output_dir / "baseline.csv",
    index=False,
)
```

The baseline provides a reference for evaluating the effects of the manipulated data.

The original downloaded CSV remains unchanged. The baseline has the same measurements, although its timestamps have been converted to datetime values.

### Step 4: Set a random seed

The scripts use a fixed random seed:

```python
rng = np.random.default_rng(42)
```

This makes the random selection reproducible when the same script, input data and execution sequence are used.

## 5. Experiment A: Missing Data

The missing-data experiment introduces missing values into 10% of the measurement records.

### Procedure

1. Create a copy of the original dataset.
2. Calculate 10% of the total number of rows.
3. Randomly select that number of row positions without replacement.
4. Replace the selected measurement values with `NaN`.
5. Save the manipulated data as a new CSV file.

Example:

```python
missing = original.copy()

count = round(len(missing) * 0.10)

selected = rng.choice(
    missing.index.to_numpy(),
    size=count,
    replace=False,
)

missing.loc[selected, "StepTotal"] = np.nan

missing.to_csv(
    output_dir / "missing_10_percent.csv",
    index=False,
)
```

For the calorie dataset, the measurement column is changed from `StepTotal` to `Calories`.

### Expected result

Approximately 10% of the measurement values become missing, while the original number of rows is preserved.

The participant IDs and timestamps remain available for the affected records.

**Purpose:** To investigate whether missing wearable measurements affect the completeness, accuracy and uncertainty of AI-generated health summaries.

## 6. Experiment B: Corrupted Data

The corrupted-data experiment divides the original dataset into three randomly assigned groups. Each group receives a different type of corruption.

The rows are shuffled before being divided so that the groups are not simply based on the order in which the records appear in the CSV.

```python
shuffled_indices = rng.permutation(
    original.index.to_numpy()
)

groups = np.array_split(shuffled_indices, 3)
```

Each group contains approximately one-third of the original records.

Within each group, 10% of the records are randomly selected for manipulation.

### 6.1 Timestamp Shifts

**Objective:** Simulate errors in the recorded time of a measurement.

Procedure:

1. Select the first group.
2. Calculate 10% of the group's rows.
3. Preserve the original timestamp in an additional column.
4. Randomly select the rows to modify.
5. Add one hour to the selected timestamps.

```python
shifted = original.loc[groups[0]].copy()

shifted["OriginalActivityHour"] = (
    shifted["ActivityHour"]
)

count = round(len(shifted) * 0.10)

selected = rng.choice(
    shifted.index.to_numpy(),
    size=count,
    replace=False,
)

shifted.loc[selected, "ActivityHour"] += (
    pd.Timedelta(hours=1)
)

shifted["corruption_type"] = "timestamp_shift"
```

The step counts remain unchanged, but some measurements appear to have occurred at a different time.

The `OriginalActivityHour` column allows the modified timestamps to be compared with their original values.

### 6.2 Random Variation

**Objective:** Simulate inaccurate or noisy measurement values.

Procedure:

1. Select the second group.
2. Calculate 10% of the group's rows.
3. Randomly select the measurements to modify.
4. Generate random numerical variations using a normal distribution.
5. Add the variations to the selected measurement values.
6. Prevent negative values and round the results to whole numbers where appropriate.

For the step-count experiment, the noise is generated using a scale based on 10% of the standard deviation of the group's step counts.

```python
noise_scale = varied["StepTotal"].std() * 0.10

noise = rng.normal(
    0,
    noise_scale,
    size=count,
)
```

The selected values are then updated using the generated noise.

For the calorie experiment, the `Calories` column is used instead of `StepTotal`.

The resulting values may be higher or lower than their original measurements.

**Purpose:** To investigate whether inaccurate measurements cause AI-generated summaries to misrepresent activity or calorie expenditure.

### 6.3 Unrealistic Spikes

**Objective:** Simulate extreme or implausible measurement values.

Procedure:

1. Select the third group.
2. Calculate 10% of the group's rows.
3. Randomly select the rows to modify.
4. Replace the selected measurement values with an intentionally extreme value.
5. Label the records as containing unrealistic spikes.

For the step-count experiment:

```python
spikes.loc[selected, "StepTotal"] = 5000

spikes["corruption_type"] = (
    "unrealistic_spike"
)
```

For the calorie experiment, the corresponding measurement column is `Calories`, with an appropriately chosen extreme test value.

The value of 5,000 steps per hour is an experimental choice intended to introduce an extreme reading. The chosen threshold should be justified in the research methodology.

**Purpose:** To determine whether extreme measurements cause AI-generated summaries to make unsupported or misleading claims.

## 7. Combining the Corrupted Groups

After the three groups have been manipulated, they are combined into one DataFrame.

```python
noisy_data = pd.concat(
    corrupted_groups,
    ignore_index=True,
)
```

The resulting dataset is saved as:

```python
noisy_data.to_csv(
    output_dir / "noisy_data.csv",
    index=False,
)
```

The `corruption_type` column identifies the manipulation assigned to each group:

- `timestamp_shift`
- `random_variation`
- `unrealistic_spike`

The combined file contains approximately the same number of rows as the original dataset. The records are distributed among the three corruption conditions, rather than having all three types of corruption applied to every record.

## 8. Running the Scripts

Open a terminal in the project directory.

Run the step-count experiment:

```bash
python manipulate_data.py
```

Run the calorie experiment:

```bash
python manipulate_h_calories.py
```

The scripts read the original files from `data_files/` and write their outputs to `experimental_data/`.

After execution, inspect the terminal output and the generated CSV files to verify that the experiments completed successfully.

## 9. Verification and Reproducibility

Before using the manipulated data for AI-generated summaries, verify the following:

- The original dataset has not been overwritten.
- The baseline contains the original measurement values.
- The missing-data file contains the intended proportion of missing measurement values.
- The corrupted-data file contains the expected number of rows for each corruption type.
- The timestamp changes are recorded correctly.
- The random variation and spikes affect only the intended records.
- The experiment settings and random seed are documented.

The corruption rates should be verified using the actual output rather than assuming that the script ran correctly.

## 10. Research Application

The manipulated datasets will be used to investigate how different wearable data-quality problems affect AI-generated health summaries.

The original baseline and the manipulated versions can be used to compare:

1. **Accuracy:** Whether the summary is supported by the available measurements.
2. **Completeness:** Whether important information is omitted.
3. **Unsupported claims:** Whether the AI makes claims that cannot be justified by the data.
4. **Uncertainty awareness:** Whether the AI acknowledges missing, noisy or unreliable information.

The same summary prompt and model settings should be used for comparable experiments. The results should be evaluated using a predefined assessment rubric.

## 11. Methodological Considerations

This implementation is an initial experimental pipeline.

The corrupted-data experiment assigns different corruption types to different groups of rows. Consequently, the groups may contain different participants or activity patterns. Differences in generated summaries may therefore reflect both the corruption type and differences between the groups.

For stronger comparisons, future experiments may apply each corruption type to a full copy of the same baseline dataset, or use participant-aware grouping and balanced experimental conditions.

The timestamp shifts, random variations and spike thresholds are controlled manipulations created for this research. They should not be interpreted as evidence that the original Fitbit dataset contains those particular errors.

The findings will describe the behaviour of the evaluated AI system under the experimental conditions and should not be treated as clinical validation.
