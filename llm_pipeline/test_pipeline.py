import tempfile
import unittest
from pathlib import Path

import pandas as pd

from .prompts import COLUMNS, MEASUREMENTS, prepare_prompts


class PromptTests(unittest.TestCase):
    def test_reference_window_blinding_and_missing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = pd.DataFrame([
                {"Id": "123", "ActivityDate": "2020-01-01", **dict.fromkeys(MEASUREMENTS, 1.0)},
                {"Id": "123", "ActivityDate": "2020-01-02", **dict.fromkeys(MEASUREMENTS, 2.0)},
            ])
            baseline.to_csv(root / "baseline.csv", index=False)
            missing = baseline.copy()
            missing.loc[0, "TotalSteps"] = float("nan")
            missing.to_csv(root / "missing_10_percent.csv", index=False)
            noisy = baseline.iloc[::-1].copy()
            noisy["OriginalActivityDate"] = noisy["ActivityDate"]
            noisy.loc[0, "ActivityDate"] = "2019-12-31"
            noisy["corruption_type"] = "secret"
            noisy.to_csv(root / "noisy_data_internal.csv", index=False)
            prompts = prepare_prompts(root, "123", "2020-01-01", 1)
            self.assertIn("2019-12-31", prompts["noisy"])
            self.assertNotIn("2020-01-02", prompts["noisy"])
            self.assertIn(",NA,", prompts["missing"])
            for prompt in prompts.values():
                for secret in ("123", "OriginalActivityDate", "corruption_type", "secret"):
                    self.assertNotIn(secret, prompt)
                self.assertIn(",".join(COLUMNS), prompt)
            noisy.loc[0, "OriginalActivityDate"] = "2020-02-01"
            noisy.to_csv(root / "noisy_data_internal.csv", index=False)
            with self.assertRaisesRegex(ValueError, "no records"):
                prepare_prompts(root, "123", "2020-01-01", 1)


if __name__ == "__main__":
    unittest.main()
