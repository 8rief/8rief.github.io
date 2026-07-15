from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HardwareReportTests(unittest.TestCase):
    def test_report_has_required_experiments(self) -> None:
        report = json.loads((ROOT / 'reports' / 'report.json').read_text(encoding='utf-8'))
        rows = report['cpu']['raw_rows']
        experiments = {row['experiment'] for row in rows}
        self.assertIn('matrix_locality', experiments)
        self.assertIn('stride_scan', experiments)
        self.assertIn('branch_predictability', experiments)
        self.assertGreater(report['cpu']['matrix_column_to_row_seconds_ratio'], 0)
        self.assertGreater(report['cpu']['branch_unpredictable_to_predictable_seconds_ratio'], 0)

    def test_stride_rows_are_positive(self) -> None:
        report = json.loads((ROOT / 'reports' / 'report.json').read_text(encoding='utf-8'))
        stride_rows = report['cpu']['stride_scan']
        self.assertGreaterEqual(len(stride_rows), 5)
        for row in stride_rows:
            self.assertGreater(row['work_items'], 0)
            self.assertGreater(row['useful_bytes'], 0)
            self.assertGreater(row['seconds'], 0)
            self.assertGreater(row['mib_per_s'], 0)

    def test_cuda_status_is_explicit(self) -> None:
        report = json.loads((ROOT / 'reports' / 'report.json').read_text(encoding='utf-8'))
        self.assertIn(report['cuda']['status'], {'ok', 'skipped', 'compile_failed', 'run_failed', 'missing'})

    def test_cuda_ok_rows_are_timed(self) -> None:
        report = json.loads((ROOT / 'reports' / 'report.json').read_text(encoding='utf-8'))
        cuda = report['cuda']
        if cuda['status'] != 'ok':
            self.skipTest('CUDA probe was not available in this run')
        self.assertIn('timing_note', cuda)
        rows = cuda.get('rows', [])
        self.assertGreaterEqual(len(rows), 1)
        for row in rows:
            self.assertGreater(row['bytes'], 0)
            for key in ['pageable_h2d_ms', 'pageable_d2h_ms', 'pinned_h2d_ms', 'pinned_d2h_ms', 'kernel_ms']:
                self.assertIn(key, row)
                self.assertGreaterEqual(row[key], 0)


if __name__ == '__main__':
    unittest.main()
