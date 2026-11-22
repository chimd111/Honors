import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import pandas as pd

from .prompts import COLUMNS, MEASUREMENTS, prepare_prompts, prepare_experiment
from .__main__ import main


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
            _, report = prepare_experiment(root, "123", "2020-01-01", 1)
            self.assertTrue(report["passed"])
            self.assertEqual(report["conditions"]["missing"]["removed_measurements"], 1)
            self.assertEqual(report["conditions"]["noisy"]["changed_dates"], 1)
            self.assertEqual(report["conditions"]["noisy"]["changes"][0]["reference_date"], "2020-01-01")
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

    def test_unchanged_conditions_block_send_and_save_reports(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = pd.DataFrame([
                {"Id": "123", "ActivityDate": "2020-01-01", **dict.fromkeys(MEASUREMENTS, 1.0)}])
            baseline.loc[0, "Calories"] = float("nan")
            baseline.to_csv(root / "baseline.csv", index=False)
            baseline.to_csv(root / "missing_10_percent.csv", index=False)
            noisy = baseline.copy()
            noisy["OriginalActivityDate"] = noisy["ActivityDate"]
            noisy["was_corrupted"] = True
            noisy.to_csv(root / "noisy_data_internal.csv", index=False)
            output = root / "runs"
            with patch("sys.argv", ["pipeline", "--participant", "123", "--start", "2020-01-01",
                                    "--days", "1", "--data-dir", str(root), "--output-dir", str(output), "--send"]), \
                    patch("llm_pipeline.__main__.generate") as generate:
                self.assertEqual(main(), 1)
                generate.assert_not_called()
            run = next(output.iterdir())
            report = json.loads((run / "validation.json").read_text())
            self.assertFalse(report["passed"])
            self.assertEqual(len(report["blocking_reasons"]), 2)
            self.assertEqual(report["conditions"]["missing"]["changed_cells"], 0)
            self.assertTrue((run / "validation.txt").exists())
            self.assertFalse(json.loads((run / "manifest.json").read_text())["sent"])


if __name__ == "__main__":
    unittest.main()
