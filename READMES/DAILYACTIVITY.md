## Daily Activity Data Processing and Validation

### Dataset

The `dailyActivity_merged.csv` file from the Zenodo Fitbit dataset was used to create three experimental conditions:

1. **Baseline:** Original, unmodified measurements.
2. **Missing data:** 10% of eligible measurement cells randomly replaced with missing values.
3. **Noisy data:** Records divided into three groups, with timestamp shifts, random variation, or unrealistic spikes introduced into selected records.

### Extracted Variables

The pipeline preserves the participant identifier (`Id`), activity date (`ActivityDate`), and 13 activity measurements:

- **Activity and distance:** TotalSteps, TotalDistance, TrackerDistance, LoggedActivitiesDistance, VeryActiveDistance, ModeratelyActiveDistance, LightActiveDistance, SedentaryActiveDistance.
- **Activity duration:** VeryActiveMinutes, FairlyActiveMinutes, LightlyActiveMinutes, SedentaryMinutes.
- **Energy expenditure:** Calories.

### Processing

The `process_dailyactivity.py` script reads the three experimental CSV files, verifies the required columns, standardizes dates to `YYYY-MM-DD`, and converts measurement columns to numeric types.

Missing values and corrupted measurements are preserved rather than corrected or replaced.

The processed datasets are saved under `llm_inputs/daily_activity/` without experimental labels. Corruption metadata is retained separately for internal evaluation.

### Validation Results

| Metric | Baseline | Missing data | Noisy data |
|---|---:|---:|---:|
| Records | 457 | 457 | 457 |
| Participants | 35 | 35 | 35 |
| Missing measurement cells | 0 | 594 | 0 |
| Duplicate participant-date records | 0 | 0 | 11 |
| Negative measurements | 0 | 0 | 0 |

The noisy-data condition included 15 timestamp shifts of one day. Comparison using the internally preserved original dates confirmed that all 457 original records could be matched to their noisy counterparts, with no duplicate reference keys.

### Separation of Experimental Metadata

The LLM-facing datasets contain only the original Fitbit columns. Experimental condition labels, original timestamps for shifted records, corruption types, and modification indicators are excluded.

This ensures that the LLM is not explicitly informed whether a dataset has been manipulated.

### Reproducibility

The manipulation script uses NumPy's random generator with seed `42` to support reproducible corruption. The processing script performs deterministic standardization and validation.

These processed files will be used as inputs to the standardized LLM interaction pipeline in the next stage of the project.

### Output Files and Running the Processor

- LLM-facing files: `llm_inputs/daily_activity/baseline.csv`, `missing_10_percent.csv`, and `noisy_data.csv`.
- Internal validation report: `evaluation/daily_activity/validation_report.csv`.
- Full noisy dataset with corruption metadata: `experimental_data/daily_activity/noisy_data_internal.csv`.

Run from the `Honors` folder with pandas installed:

```powershell
python process_dailyactivity.py
```

The processor reads existing experimental files; it does not rerun manipulation. It preserves row order, missingness, duplicates, and manipulated values.

### Validation Scope

The table above agrees with the current saved validation report. Duplicate counts represent records after the first occurrence of each participant-date or participant-timestamp key. Missing and negative counts apply to measurement cells.

The processor checks required columns, parses dates and numeric measurements, and reports missingness, duplicates, and negative values. It does not establish clinical validity, flag every implausible measurement, or automatically verify the separate reference-mapping results described above.

Internal and LLM-facing noisy files retain the same row order. Original timestamps and corruption labels are excluded from LLM-facing columns. Condition names in filenames should also be hidden or replaced with neutral identifiers before presenting files to a model.

