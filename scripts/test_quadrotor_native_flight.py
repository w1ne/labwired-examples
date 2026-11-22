"""Source-bound five-controller native flight and fault evidence integrity."""
import importlib.util
from pathlib import Path
import unittest

class NativeFlightAcceptance(unittest.TestCase):
    def test_archived_bytes_and_independent_body_fault_oracles(self):
        root = Path(__file__).resolve().parents[1]
        path = root / 'examples/robotics/quadrotor-bldc/labwired/evidence/20261122-native-flight/audit.py'
        spec = importlib.util.spec_from_file_location('quadrotor_native_audit', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.audit_bundle()
        self.assertEqual(result['passingScenarios'], 7)
        self.assertEqual(result['preservedNegativeScenarios'], 4)
        self.assertTrue(result['inverterObserverEquivalent'])

if __name__ == '__main__':
    unittest.main()
