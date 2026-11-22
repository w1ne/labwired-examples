"""Integrity of staged release evidence; no product or firmware execution."""
import json
from pathlib import Path
import subprocess
import unittest


class QuadrotorDeploymentPreflight(unittest.TestCase):
    def test_record_integrity_preserves_negative_and_pending_claims(self):
        root = Path(__file__).resolve().parents[1]
        auditor = root / (
            'examples/robotics/quadrotor-bldc/labwired/evidence/'
            '20261122-deployment-preflight/audit_preflight.mjs'
        )
        completed = subprocess.run(
            ['node', str(auditor)],
            check=True,
            capture_output=True,
            text=True,
            cwd=root,
        )
        result = json.loads(completed.stdout)
        self.assertTrue(result['recordIntegrityVerified'])
        self.assertEqual(result['reviewedFilesPreserved'], 19)
        self.assertEqual(result['originalPayloadsVerified'], 4)
        self.assertEqual(
            [part['wrongCorners'] for part in result['importedPopulations']],
            [0, 28],
        )
        for claim in (
            'cadGeometryAccepted',
            'qualifiedDeployedEngine',
            'savedProjectUpdated',
            'browserFlightPerformed',
        ):
            self.assertFalse(result[claim], claim)


if __name__ == '__main__':
    unittest.main()
