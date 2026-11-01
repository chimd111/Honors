## Heart Rate Data Processing and Validation

### Dataset

The `heartrate_seconds_merged.csv` dataset contains 1,154,681 heart rate measurements from 14 participants.

Three experimental conditions were prepared:

1. **Baseline:** Original heart rate measurements.
2. **Missing data:** 10% of heart rate values replaced with missing values.
3. **Noisy data:** Heart rate measurements and/or timestamps manipulated to introduce data-quality problems.

### Extracted Variables

| Variable | Description |
|---|---|
| Id | Participant identifier |
| Time | Timestamp of the heart rate measurement |
| Value | Heart rate measurement in beats per minute (BPM) |

### Processing

The `process_heartrate.py` script standardizes timestamps, verifies numeric heart rate values, and checks for missing measurements, duplicate participant-timestamp records, and negative values.

The processed datasets are saved in `llm_inputs/heart_rate/` without experimental metadata.

Corruption metadata is preserved separately in `experimental_data/heart_rate/noisy_data_internal.csv`.

### Validation Results

| Metric | Baseline | Missing 10% | Noisy |
|---|---:|---:|---:|
| Records | 1,154,681 | 1,154,681 | 1,154,681 |
| Participants | 14 | 14 | 14 |
| Missing values | 0 | 115,468 | 0 |
| Duplicate timestamps | 0 | 0 | 17,465 |
| Negative values | 0 | 0 | 0 |

A separate reference-mapping check identified 38,489 records with shifted timestamps.

All 1,154,681 original participant-timestamp keys were successfully matched to their noisy counterparts, with no duplicate reference keys.

### LLM Input Preparation

Only the original wearable-data columns (`Id`, `Time`, `Value`) are retained in LLM-facing files.

Experimental metadata, including original timestamps and corruption labels, is excluded so that models are not explicitly informed of the manipulated data.

The raw measurements are preserved for later aggregation into participant-level or daily summaries.