import json
import tempfile
import unittest
from pathlib import Path


class IterLocalCallFilesTests(unittest.TestCase):
    def test_discovers_json_files_across_month_and_day_folders(self):
        from dashboard_sync.backfill_calls import iter_local_call_files

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "junio" / "2026-06-01").mkdir(parents=True)
            (base / "julio" / "2026-07-08").mkdir(parents=True)
            call_a = base / "junio" / "2026-06-01" / "call_a.json"
            call_b = base / "julio" / "2026-07-08" / "call_b.json"
            call_a.write_text(json.dumps({"call_id": "call_a"}), encoding="utf-8")
            call_b.write_text(json.dumps({"call_id": "call_b"}), encoding="utf-8")

            found = list(iter_local_call_files(base))

            self.assertEqual(sorted(f.name for f in found), ["call_a.json", "call_b.json"])

    def test_ignores_non_json_files(self):
        from dashboard_sync.backfill_calls import iter_local_call_files

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            day_dir = base / "julio" / "2026-07-08"
            day_dir.mkdir(parents=True)
            (day_dir / "call_a.json").write_text("{}", encoding="utf-8")
            (day_dir / "notes.txt").write_text("no procesar esto", encoding="utf-8")

            found = list(iter_local_call_files(base))

            self.assertEqual([f.name for f in found], ["call_a.json"])

    def test_empty_base_dir_yields_nothing(self):
        from dashboard_sync.backfill_calls import iter_local_call_files

        with tempfile.TemporaryDirectory() as tmp:
            found = list(iter_local_call_files(Path(tmp)))
            self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
