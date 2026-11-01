## Hourly Steps Data Processing and Validation

### Dataset and Extracted Variables

Source: `data_files/hourlySteps_merged.csv`. Each condition contains 24,084 records from 34 participants.

| Variable | Description |
|---|---|
| Id | Participant identifier |
| ActivityHour | Hour of the measurement |
| StepTotal | Steps recorded during the hour |

### Experimental Conditions

1. **Baseline:** Source measurements with standardized timestamps.
2. **Missing data:** Approximately 10% of the targeted measurement values replaced with blanks, without removing rows.
3. **Noisy data:** Rows randomly divided into three groups; approximately 10% of each group selected for timestamp shifts, random variation, or spikes.

`StepTotal` is the manipulated measurement. Timestamp shifts add one hour; spikes set steps to 5,000. Random variation is rounded and clipped at zero.

The manipulation script `manipulate_h_steps.py` uses NumPy seed `42`.

### Processing and Outputs

`process_h_steps.py` reads the three existing conditions from `experimental_data/steps/`, checks required columns, retains only original wearable columns, standardizes timestamps to `YYYY-MM-DD HH:MM:SS`, and validates numeric measurements.

It preserves row order, missing values, duplicate records, and manipulated measurements. It does not aggregate, impute, remove outliers, or repair values.

- LLM-facing files: `llm_inputs/steps/baseline.csv`, `missing_10_percent.csv`, and `noisy_data.csv`.
- Internal validation: `evaluation/steps/validation_report.csv`.
- Internal corruption records: `experimental_data/steps/noisy_data_internal.csv`.

Original timestamps and experimental labels remain in the internal noisy file and are excluded from LLM-facing columns. Internal and LLM-facing noisy files retain the same row order. The processor does not independently verify reference matching.

### Validation Results

Values below are taken from the current validation report. Missing and negative counts refer to measurement cells. Duplicate counts use participant and timestamp, counting occurrences after the first.

| Metric | Baseline | Missing 10% | Noisy |
|---|---:|---:|---:|
| Records | 24084 | 24084 | 24084 |
| Participants | 34 | 34 | 34 |
| Missing measurement cells | 0 | 2408 | 0 |
| Duplicate participant-timestamp records | 0 | 0 | 777 |
| Negative measurement cells | 0 | 0 | 0 |

Steps and calories do not currently record `was_corrupted`; their `corruption_type` labels describe group assignment, not proof that every row was modified.

These checks report structural issues; they do not establish clinical validity or detect every implausible value. Condition names in filenames should be hidden or replaced with neutral identifiers before presenting files to a model.

### Run

From the `Honors` folder, process the existing experimental files:

```powershell
python process_h_steps.py
```

Dependencies: pandas. Running the processor does not rerun data manipulation.

