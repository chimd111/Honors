## Minute Sleep Data Processing and Validation

### Dataset and Extracted Variables

Source: `data_files/minuteSleep_merged.csv`. Each condition contains 198,559 records from 23 participants.

| Variable | Description |
|---|---|
| Id | Participant identifier |
| date | Timestamp of the minute sleep record |
| value | Source coded sleep-state value; retained without assigning clinical stage meanings |
| logId | Source sleep log identifier |

### Experimental Conditions

1. **Baseline:** Source measurements with standardized timestamps.
2. **Missing data:** Approximately 10% of the targeted measurement values replaced with blanks, without removing rows.
3. **Noisy data:** Rows randomly divided into three groups; approximately 10% of each group selected for timestamp shifts, random variation, or spikes.

`value` is the manipulated measurement. Timestamp shifts add one hour; random variation is rounded and clipped to codes 1 through 3; spikes set the code to 5.

The manipulation script `manipulate_sleep.py` uses NumPy seed `42`.

### Processing and Outputs

`process_sleep.py` reads the three existing conditions from `experimental_data/sleep/`, checks required columns, retains only original wearable columns, standardizes timestamps to `YYYY-MM-DD HH:MM:SS`, and validates numeric measurements.

It preserves row order, missing values, duplicate records, and manipulated measurements. It does not aggregate, impute, remove outliers, or repair values.

- LLM-facing files: `llm_inputs/sleep/baseline.csv`, `missing_10_percent.csv`, and `noisy_data.csv`.
- Internal validation: `evaluation/sleep/validation_report.csv`.
- Internal corruption records: `experimental_data/sleep/noisy_data_internal.csv`.

Original timestamps and experimental labels remain in the internal noisy file and are excluded from LLM-facing columns. Internal and LLM-facing noisy files retain the same row order. The processor does not independently verify reference matching.

### Validation Results

Values below are taken from the current validation report. Missing and negative counts refer to measurement cells. Duplicate counts use participant and timestamp, counting occurrences after the first.

| Metric | Baseline | Missing 10% | Noisy |
|---|---:|---:|---:|
| Records | 198559 | 198559 | 198559 |
| Participants | 23 | 23 | 23 |
| Missing measurement cells | 0 | 19856 | 0 |
| Duplicate participant-timestamp records | 525 | 525 | 5948 |
| Negative measurement cells | 0 | 0 | 0 |

The baseline already contains 525 duplicate participant-timestamp records. Duplicate counts ignore `logId` and count rows after the first occurrence. The processor does not validate sleep-code membership: the injected code 5 is preserved. Selection for random variation does not guarantee an actual change after rounding.

These checks report structural issues; they do not establish clinical validity or detect every implausible value. Condition names in filenames should be hidden or replaced with neutral identifiers before presenting files to a model.

### Run

From the `Honors` folder, process the existing experimental files:

```powershell
python process_sleep.py
```

Dependencies: pandas. Running the processor does not rerun data manipulation.

