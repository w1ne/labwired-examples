"""Verify the deployed CAD record without running a service or flight model."""
import json
from pathlib import Path
import subprocess
import unittest


class QuadrotorDeployedCad(unittest.TestCase):
    def test_actual_corrected_mesh_preserves_pending_visual_and_flight_claims(self):
        root = Path(__file__).resolve().parents[1]
        auditor = root / (
            'examples/robotics/quadrotor-bldc/labwired/evidence/'
            '20261122-cad-correction/audit.mjs'
        )
        completed = subprocess.run(
            ['node', str(auditor)],
            check=True,
            capture_output=True,
            text=True,
            cwd=root,
            timeout=40,
        )
        result = json.loads(completed.stdout)
        self.assertTrue(result['recordIntegrityVerified'])
        self.assertTrue(result['cadGeometryAccepted'])
        self.assertEqual(result['assemblyParts'], 38)
        self.assertEqual(result['importedSourceTriangles'], 103850)
        self.assertEqual(result['wrongCorners'], 0)
        self.assertEqual(result['changedFcIndices'], 28)
        self.assertTrue(result['priorNegativePreserved'])
        self.assertFalse(result['inspectedLocalPlayerVideo'])
        self.assertTrue(result['visualRecordPending'])
        for claim in (
            'qualifiedDeployedEngine',
            'savedProjectUpdated',
            'browserFlightPerformed',
        ):
            self.assertFalse(result[claim], claim)


if __name__ == '__main__':
    unittest.main()
