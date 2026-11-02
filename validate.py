
from pathlib import Path
import pandas as pd

datasets = {
    "Sleep": {
        "folder": "sleep",
        "timestamp": "date",
        "original_timestamp": "OriginalDate",
        "keys": ["Id", "logId", "reference_time"],
    },
    "Weight": {
        "folder": "weight",
        "timestamp": "Date",
        "original_timestamp": "OriginalDate",
        "keys": ["Id", "LogId"],
    },
}

for name, config in datasets.items():
    path = Path("experimental_data") / config["folder"]

    baseline = pd.read_csv(path / "baseline.csv")
    noisy = pd.read_csv(
        path / "noisy_data_internal.csv",
        low_memory=False
    )

    time_col = config["timestamp"]
    original_col = config["original_timestamp"]

    baseline["reference_time"] = pd.to_datetime(
        baseline[time_col], errors="raise"
    )

    noisy["reference_time"] = pd.to_datetime(
        noisy[original_col].fillna(noisy[time_col]),
        errors="raise"
    )

    baseline_keys = pd.MultiIndex.from_frame(
        baseline[config["keys"]]
    )

    noisy_keys = pd.MultiIndex.from_frame(
        noisy[config["keys"]]
    )

    shifted = (
        pd.to_datetime(noisy[time_col], errors="raise")
        != noisy["reference_time"]
    ).sum()

    print(f"\n=== {name} ===")
    print("Baseline rows:", len(baseline))
    print("Noisy rows:", len(noisy))
    print("Baseline unique keys:", baseline_keys.nunique())
    print("Noisy reference unique keys:", noisy_keys.nunique())
    print(
        "All reference keys match:",
        baseline_keys.difference(noisy_keys).empty
        and noisy_keys.difference(baseline_keys).empty
    )
    print(
        "Duplicate baseline keys:",
        baseline_keys.duplicated().sum()
    )
    print(
        "Duplicate reference keys:",
        noisy_keys.duplicated().sum()
    )
    print("Timestamp-shifted rows:", int(shifted))
