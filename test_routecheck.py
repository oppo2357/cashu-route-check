import json
from pathlib import Path
import subprocess
import sys
import unittest

from routecheck import verdict


ROOT = Path(__file__).resolve().parent


class RouteTests(unittest.TestCase):
    def test_demo(self):
        for snapshot, expected_code in [("before", 0), ("candidate", 1)]:
            with self.subTest(snapshot=snapshot):
                result = subprocess.run(
                    [sys.executable, "routecheck.py", "routes.json", f"examples/{snapshot}.json",
                     "--before", "examples/before.json"], cwd=ROOT, text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, expected_code, result.stderr)
                mint, melt = json.loads(result.stdout)
                self.assertEqual((mint["previous"], mint["status"]), ("advertised", "advertised"))
                self.assertEqual(melt["previous"], "advertised")
                self.assertEqual(melt["status"], "blocked" if expected_code else "advertised")

    def test_amount_boundaries(self):
        info = json.loads((ROOT / "examples/candidate.json").read_text())
        route = {"operation": "melt", "unit": "sat", "method": "bolt11"}
        for amount, expected in [(20, "blocked"), (21, "advertised"), (500000, "advertised"), (500001, "blocked")]:
            with self.subTest(amount=amount):
                self.assertEqual(verdict(info, dict(route, amount=amount))[0], expected)

    def test_invalid_mint_limits_preserve_melt_result(self):
        info = json.loads((ROOT / "examples/inverted.json").read_text())
        mint, melt = json.loads((ROOT / "routes.json").read_text())
        self.assertEqual(verdict(info, mint), ("unknown", "inverted limits"))
        self.assertEqual(verdict(info, melt)[0], "advertised")


if __name__ == "__main__":
    unittest.main()
