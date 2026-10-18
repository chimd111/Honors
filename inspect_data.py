import pandas as pd
from pathlib import Path

data_dir = Path("mturkfitbit_export_3.12.16-4.11.16")

for file in data_dir.glob("*.csv"):
    df = pd.read_csv(file)

    print(f"\n--- {file.name} ---")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print(df.head(3))
    print("Missing values:\n", df.isna().sum())