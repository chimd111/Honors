# Fitbit Data Quality Manipulation

## 1. Project Overview

This project explores how data-quality problems in wearable health data can affect AI-generated health summaries. The repository uses Fitbit data streams and creates controlled versions of the original CSV files with missing values, timestamp shifts, random noise, and unrealistic spikes.

The main purpose is to compare clean baseline data against manipulated datasets and assess how those quality issues change downstream interpretation and summary generation.

The repository currently covers the following Fitbit sources:

- daily activity
- heart rate
- hourly calories
- hourly intensities
- hourly steps
- minute sleep
- weight logs

## 2. Repository Structure

```text
Honors/
├── README.md
├── starter.py
├── inspect_data.py
├── inject_missing.py
├── manipulate_h_steps.py
├── manipulate_h_calories.py
├── manipulate_heartrate.py
├── manipulate_dailyactivity.py
├── manipulate_intensities.py
├── manipulate_sleep.py
├── manipulate_weightlog.py
├── data_files/
│   ├── dailyActivity_merged.csv
│   ├── heartrate_seconds_merged.csv
│   ├── hourlyCalories_merged.csv
│   ├── hourlyIntensities_merged.csv
│   ├── hourlySteps_merged.csv
│   ├── minuteCaloriesNarrow_merged.csv
│   ├── minuteIntensitiesNarrow_merged.csv
│   ├── minuteMETsNarrow_merged.csv
│   ├── minuteSleep_merged.csv
│   ├── minuteStepsNarrow_merged.csv
│   └── weightLogInfo_merged.csv
├── experimental_data/
│   ├── calories/
│   │   ├── baseline.csv
│   │   ├── missing_10_percent.csv
│   │   └── noisy_data.csv
│   ├── daily_activity/
│   │   ├── baseline.csv
│   │   ├── missing_10_percent.csv
│   │   └── noisy_data.csv
│   ├── heart_rate/
│   │   ├── baseline.csv
│   │   ├── missing_10_percent.csv
│   │   └── noisy_data.csv
│   ├── intensities/
│   │   ├── baseline.csv
│   │   ├── missing_10_percent.csv
│   │   └── noisy_data.csv
│   ├── sleep/
│   │   ├── baseline.csv
│   │   ├── missing_10_percent.csv
│   │   └── noisy_data.csv
│   ├── steps/
│   │   ├── baseline.csv
│   │   ├── missing_10_percent.csv
│   │   └── noisy_data.csv
│   └── weight/
│       ├── baseline.csv
│       ├── missing_10_percent.csv
│       └── noisy_data.csv
└── .git
```

## 3. What Has Been Implemented

The project currently includes:

- a general-purpose missing-data injector in `inject_missing.py`
- dataset-specific manipulation scripts for each Fitbit data source
- output folders under `experimental_data/` containing baseline and manipulated data
- reproducible corruption with a fixed random seed
- CSV exports for three corruption categories:
  - timestamp shifts
  - random variation
  - unrealistic spikes

## 4. Data Manipulation Workflow

Each dataset script follows the same general pipeline:

1. Load the original Fitbit CSV file.
2. Convert timestamps to pandas datetime objects.
3. Save a clean baseline copy.
4. Create a missing-value version by setting approximately 10% of measurement values to `NaN`.
5. Split the dataset into three random groups.
6. Apply one corruption pattern to each group:
   - timestamp shift
   - random numerical variation
   - unrealistic spike
7. Combine the corrupted groups into one `noisy_data.csv` file.

## 5. Scripts in the Repository

### `inspect_data.py`

This script scans all CSV files in `data_files/` and prints:

- file shape
- column names
- first few rows
- missing values per column

Run it with:

```bash
python inspect_data.py
```

### `inject_missing.py`

This script provides a more flexible missing-data generation workflow. It can:

- inject missing values at different proportions
- use random or block-based missingness patterns
- support value-level masking or row removal
- work with subject IDs and time columns
- create a flags file and manifest.json for traceability

Example:

```bash
python inject_missing.py data_files/heartrate_seconds_merged.csv \
  --value-cols Value \
  --id-col Id \
  --time-col Time \
  --levels 0.10 0.25 0.50 \
  --pattern random \
  --seed 42 \
  --out-dir missing_out
```

### Dataset-specific scripts

The following scripts generate manipulated copies for each data stream:

```bash
python manipulate_h_steps.py
python manipulate_h_calories.py
python manipulate_heartrate.py
python manipulate_dailyactivity.py
python manipulate_intensities.py
python manipulate_sleep.py
python manipulate_weightlog.py
```

These scripts save outputs into the corresponding folder under `experimental_data/`.

## 6. Experimental Data Outputs

Each dataset folder contains an untouched baseline and a corrupted version:

- `baseline.csv`: clean dataset copy
- `missing_10_percent.csv`: approximately 10% missing values
- `noisy_data.csv`: combined corrupted dataset with timestamp shifts, random variation, and unrealistic spikes

Current folders:

- `experimental_data/steps`
- `experimental_data/calories`
- `experimental_data/heart_rate`
- `experimental_data/daily_activity`
- `experimental_data/intensities`
- `experimental_data/sleep`
- `experimental_data/weight`

## 7. Corruption Types

### Missing data

A subset of measurement values is replaced with `NaN` while the rest of the record remains intact.

### Timestamp shifts

Some rows are copied and their timestamp is moved forward by a fixed amount, such as 1 hour or 1 day.

### Random variation

Selected measurements are adjusted by random noise based on the column's variability.

### Unrealistic spikes

Selected values are replaced with extreme readings to represent sensor malfunction or outlier behavior.

## 8. Technologies Used

This project is implemented in Python using:

- pandas
- numpy
- pathlib

Install dependencies with:

```bash
pip install pandas numpy
```

## 9. Verification and Reproducibility

The scripts are designed to be reproducible through a fixed random seed (`np.random.default_rng(42)`). This allows consistent generation of manipulated datasets across repeated runs.

Before using the data for comparison or AI analysis, confirm that:

- the original files in `data_files/` remain unchanged
- the baseline data match the original measurements
- the missing-data files contain the expected proportion of missing values
- the noisy data includes all three corruption categories
- the timestamp, variation, and spike manipulations were applied only to the intended rows

## 10. Research Purpose

This repository supports an experiment on how degraded wearable health data affects AI-generated summaries. The idea is to test whether missingness, noise, and unrealistic values lead to inaccurate or misleading conclusions in health analysis.

The manipulated datasets are useful for evaluating:

- how incomplete measurements affect summary quality
- whether timestamp errors distort trend interpretation
- how noisy values influence health conclusions
- whether extreme outliers trigger unsupported claims

## 11. Notes

- `starter.py` is a minimal example script and not part of the main experiment workflow.
- The original Fitbit CSV files are treated as source data and should not be overwritten.
- All generated experimental datasets are stored under `experimental_data/` for comparison.

This README reflects the current state of the repository: the data-processing scripts, generated experimental datasets, and the missing-data utility are all in place and working as part of the project workflow.
