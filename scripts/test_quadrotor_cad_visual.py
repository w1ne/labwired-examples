"""Integrity of the inspected stored-artifact visual comparison."""
import json
from pathlib import Path
import subprocess
import unittest


class QuadrotorCadVisual(unittest.TestCase):
    def test_actual_capture_retains_the_separate_flight_gates(self):
        root = Path(__file__).resolve().parents[1]
        auditor = root / (
            'examples/robotics/quadrotor-bldc/labwired/evidence/'
            '20261122-cad-visual/audit.mjs'
        )
        completed = subprocess.run(
            ['node', str(auditor)],
            check=True,
            capture_output=True,
            text=True,
            cwd=root,
            timeout=20,
        )
        result = json.loads(completed.stdout)
        self.assertTrue(result['recordIntegrityVerified'])
        self.assertTrue(result['storedArtifactsBound'])
        self.assertEqual(result['renderedPart'], 'fc-population-native-mesh')
        self.assertEqual(result['renderedTriangles'], 47778)
        self.assertEqual(result['correctedIndices'], 28)
        self.assertEqual(result['capturedFrames'], 4)
        self.assertEqual(result['decodedVideoFrames'], 192)
        self.assertEqual(result['videoDurationSeconds'], 8)
        self.assertTrue(result['priorEncodingPreserved'])
        self.assertTrue(result['localPlayerVideoInspected'])
        self.assertTrue(result['allOwnedProcessesExited'])
        for claim in (
            'qualifiedDeployedEngine',
            'savedProjectUpdated',
            'browserFlightPerformed',
            'interactiveHostedViewerPainted',
        ):
            self.assertFalse(result[claim], claim)


if __name__ == '__main__':
    unittest.main()
