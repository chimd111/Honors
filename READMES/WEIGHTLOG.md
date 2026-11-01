## Weight Logs Data Processing and Validation

### Dataset and Extracted Variables

Source: `data_files/weightLogInfo_merged.csv`. Each condition contains 33 records from 11 participants.

| Variable | Description |
|---|---|
| Id | Participant identifier |
| Date | Timestamp of the weight log |
| WeightKg | Weight in kilograms |
| WeightPounds | Weight in pounds |
| Fat | Source body-fat field, preserved as supplied |
| BMI | Source body mass index |
| IsManualReport | Source manual-entry indicator |
| LogId | Source weight log identifier |

### Experimental Conditions

1. **Baseline:** Source measurements with standardized timestamps.
2. **Missing data:** Approximately 10% of the targeted measurement values replaced with blanks, without removing rows.
3. **Noisy data:** Rows randomly divided into three groups; approximately 10% of each group selected for timestamp shifts, random variation, or spikes.

Only `WeightKg` is manipulated. Timestamp shifts add one day; random variation is rounded to two decimal places and clipped at zero; spikes set weight to 300 kg.

The manipulation script `manipulate_weightlog.py` uses NumPy seed `42`.

### Processing and Outputs

`process_weightlog.py` reads the three existing conditions from `experimental_data/weight/`, checks required columns, retains only original wearable columns, standardizes timestamps to `YYYY-MM-DD HH:MM:SS`, and validates numeric measurements.

It preserves row order, missing values, duplicate records, and manipulated measurements. It does not aggregate, impute, remove outliers, or repair values.

- LLM-facing files: `llm_inputs/weight/baseline.csv`, `missing_10_percent.csv`, and `noisy_data.csv`.
- Internal validation: `evaluation/weight/validation_report.csv`.
- Internal corruption records: `experimental_data/weight/noisy_data_internal.csv`.

Original timestamps and experimental labels remain in the internal noisy file and are excluded from LLM-facing columns. Internal and LLM-facing noisy files retain the same row order. The processor does not independently verify reference matching.

### Validation Results

Values below are taken from the current validation report. Missing and negative counts refer to measurement cells. Duplicate counts use participant and timestamp, counting occurrences after the first.

| Metric | Baseline | Missing 10% | Noisy |
|---|---:|---:|---:|
| Records | 33 | 33 | 33 |
| Participants | 11 | 11 | 11 |
| Missing measurement cells | 31 | 34 | 31 |
| Duplicate participant-timestamp records | 0 | 0 | 0 |
| Negative measurement cells | 0 | 0 | 0 |

The baseline already has 31 missing measurement cells; the missing-data condition adds three missing `WeightKg` values, giving 34 in total. `WeightPounds` and `BMI` remain unchanged when `WeightKg` changes. These related fields may reveal inconsistencies or provide information about missing weights; the processor does not reconcile them.

These checks report structural issues; they do not establish clinical validity or detect every implausible value. Condition names in filenames should be hidden or replaced with neutral identifiers before presenting files to a model.

### Run

From the `Honors` folder, process the existing experimental files:

```powershell
python process_weightlog.py
```

Dependencies: pandas. Running the processor does not rerun data manipulation.

