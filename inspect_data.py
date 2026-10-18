
import pandas as pd
from pathlib import Path

print("Script started!")

data_dir = Path("data_files")

print("Looking inside:", data_dir.resolve())
print("Folder exists:", data_dir.exists())

csv_files = list(data_dir.rglob("*.csv"))
print("CSV files found:", len(csv_files))

for file in csv_files:
    df = pd.read_csv(file)

    print(f"\n--- {file.name} ---")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print(df.head(3))
    print("Missing values:\n", df.isna().sum())
