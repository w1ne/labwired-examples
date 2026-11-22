"""Check the exact AXIOM mesh refresh and keep its acceptance boundaries explicit."""
import gzip
import hashlib
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples/robotics/axiom-h1'
MECHANICAL = EXAMPLE / 'mechanical'
REFRESH = MECHANICAL / 'artifact-refresh-20261122'
IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def raw(path):
    data = path.read_bytes()
    return gzip.decompress(data) if path.suffix == '.gz' else data


def read(path):
    return json.loads(raw(path))


def sha(data):
    return hashlib.sha256(data).hexdigest()


class AxiomMeshRefresh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qualification = read(REFRESH / 'qualification.json')
        cls.model = read(REFRESH / 'model.json')
        cls.mesh = read(REFRESH / 'mesh.json.gz')
        cls.source = read(REFRESH / 'joint-transform.json.gz')
        cls.actual = read(REFRESH / 'mesh-transform.json.gz')

    def test_all_artifacts_and_replay_script_are_hash_bound(self):
        q = self.qualification
        for name, record in q['files'].items():
            path = REFRESH / name
            self.assertEqual(sha(path.read_bytes()), record['sha256'], name)
            self.assertEqual(path.stat().st_size, record['bytes'], name)
            if 'uncompressedSha256' in record:
                self.assertEqual(sha(raw(path)), record['uncompressedSha256'], name)
                self.assertEqual(len(raw(path)), record['uncompressedBytes'], name)
        script = (REFRESH / q['runtimeReplay']['script']).resolve()
        self.assertEqual(script, ROOT / 'scripts/check-axiom-joint-transforms.mjs')
        self.assertEqual(sha(script.read_bytes()), q['runtimeReplay']['scriptSha256'])

    def test_only_the_artifact_pin_changes(self):
        prior = read(MECHANICAL / 'compact-frame-model.json')
        candidate = dict(self.model)
        self.assertNotEqual(candidate['meshProvenance'], prior['meshProvenance'])
        candidate['meshProvenance'] = prior['meshProvenance']
        self.assertEqual(candidate, prior)
        self.assertEqual(self.qualification['changedModelFields'], ['meshProvenance'])
        digest = sha((MECHANICAL / 'axiom-compact-frame.kcad.ts').read_bytes())
        self.assertEqual(digest, self.qualification['unchangedSourceSha256'])
        self.assertEqual(digest, self.mesh['provenance']['source']['sha256'])
        self.assertEqual(digest, self.actual['cadSourceSha256'])
        self.assertEqual(self.model['electronics'], read(MECHANICAL / 'source-derived-electronics.json'))

    def test_pose_manifest_retains_every_source_endpoint(self):
        coverage = read(REFRESH / 'pose-coverage.json')
        source = read(EXAMPLE / 'current-project.input.json')['source']
        names = re.findall(r'"([^"]+)"', re.search(r'joint_name\[NUM_JOINTS\] = \{([\s\S]*?)\};', source)[1])
        def values(name):
            return [int(x) for x in re.search(name + r'\[NUM_JOINTS\]=\{([^}]+)\}', source)[1].split(',')]
        expected = {name: sorted({lo, 0 if lo <= 0 <= hi else (lo + hi) / 2, hi})
                    for name, lo, hi in zip(names, values('jmin'), values('jmax'))}
        actual = {}
        self.assertEqual(coverage['poses'][0], {'name': 'rest', 'poses': {}})
        for pose in coverage['poses'][1:]:
            self.assertEqual(len(pose['poses']), 1)
            self.assertEqual(list(pose['poses']), [pose['mateName']])
            actual.setdefault(pose['mateName'], []).append(pose['poses'][pose['mateName']])
        self.assertEqual({name: sorted(v) for name, v in actual.items()}, expected)
        self.assertEqual(len(coverage['poses']), 59)
        evaluation = read(REFRESH / 'evaluation.json')
        self.assertTrue(evaluation['ok'])
        self.assertEqual(evaluation['mechanism'], 'real')
        self.assertEqual(evaluation['mechanismSummary']['failures'], [])
        self.assertIn('59 poses across 20 joints', evaluation['mechanismSummary']['statement'])

    def test_actual_mesh_identity_and_complete_part_roster(self):
        mesh = self.mesh
        canonical = json.dumps(mesh['provenance'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        self.assertEqual(sha(canonical), self.model['meshProvenance'])
        self.assertEqual(mesh['revision'], self.model['version'])
        self.assertEqual(mesh['bounds'], self.qualification['boundsMm'])
        self.assertEqual(sorted(g['assemblyPartName'] for g in mesh['features']), sorted(self.qualification['parts']))
        self.assertEqual(len(mesh['features']), 27)
        self.assertEqual(len({g['featureId'] for g in mesh['features']}), 27)
        self.assertEqual(self.actual['mesh']['sha256'], sha(raw(REFRESH / 'mesh.json.gz')))
        self.assertEqual(self.actual['mesh']['vertices'], 38604)
        self.assertEqual(self.actual['mesh']['triangles'], 43356)
        self.assertTrue(all(g['transform'] == IDENTITY for g in mesh['features']))

    def test_all46_runtime_samples_match_with_explicit_rest_semantics(self):
        self.assertEqual(len(self.source['samples']), 46)
        self.assertEqual(len(self.actual['samples']), 46)
        names = [part for motion in self.model['electronics']['motions'] for part in motion['parts']]
        self.assertEqual(len(names), 23)
        for i, (source, actual) in enumerate(zip(self.source['samples'], self.actual['samples'])):
            self.assertEqual({k:v for k,v in source.items() if k != 'transforms'},
                             {k:v for k,v in actual.items() if k != 'transforms'}, i)
            self.assertEqual({k:source['transforms'].get(k, IDENTITY) for k in names},
                             {k:actual['transforms'].get(k, IDENTITY) for k in names}, i)
            if i >= 2:
                self.assertEqual(source, actual)
        self.assertEqual(len(self.source['changedParts']), 10)
        self.assertEqual(len(self.actual['changedParts']), 23)
        self.assertEqual(self.actual['bindingCount'], 20)
        self.assertLess(self.actual['maximumMatrixMarkerErrorMm'], 1e-8)
        disabled = [s for s in self.actual['samples'] if s['phase'].startswith('estop') and s['allDisabled']]
        self.assertGreaterEqual(len(disabled), 2)
        self.assertTrue(all(s['transforms'] == disabled[0]['transforms'] for s in disabled))

    def test_old_pin_failure_and_physical_failure_remain_explicit(self):
        q = self.qualification
        self.assertEqual(q['priorArtifact']['storedOnlyApiStatus'], 404)
        self.assertEqual(q['priorArtifact']['oldPinCdnBodyProvenance'], self.model['meshProvenance'])
        self.assertEqual(q['priorArtifact']['oldAndNewByteOrTriangulationEquivalence'], 'not_claimed')
        self.assertEqual(q['physicalAcceptance']['status'], 'failed')
        self.assertFalse(q['savedLabWiredProject']['mechanicalCasPerformed'])
        self.assertFalse(q['viewerPainted'])
        timeout = read(REFRESH / 'additional-dense-sweep-time-limit.json')
        self.assertEqual(timeout['result']['structuredContent']['kernelcadError']['code'], 'job.time-limit')
        for case in read(REFRESH / 'negative-replay.json')['cases']:
            self.assertNotEqual(case['exitCode'], 0)
            self.assertFalse(case['wroteSuccessReceipt'])
            self.assertEqual(sha((REFRESH / case['logFile']).read_bytes()), case['logSha256'])


if __name__ == '__main__':
    unittest.main()
