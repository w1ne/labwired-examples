"""Validate immutable 2026-11-22 GUI evidence (not simulation acceptance)."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'examples/flagship-ui-readbacks-20261122.json'


class TestFlagshipUiReadback(unittest.TestCase):
    def test_pinned_readbacks_have_current_jpeg_bytes_and_no_claimed_sim_run(self):
        manifest = json.loads(MANIFEST.read_text())
        self.assertEqual(manifest['schema'], 'labwired-flagship-ui-readback-v1')
        self.assertEqual(manifest['new_live_world_run_ids'], [])
        self.assertEqual(len(manifest['captures']), 6)
        for item in manifest['captures']:
            with self.subTest(item=item['id']):
                p = ROOT / item['image']
                self.assertTrue(p.is_relative_to(ROOT / 'examples'))
                raw = p.read_bytes()
                self.assertTrue(raw.startswith(b'\xff\xd8\xff'))
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item['sha256'])
                self.assertTrue(item['captured_utc'].startswith('2026-11-22T'))
                self.assertIn(item['project_id'], item['project_url'])
        self.assertTrue(any('not firmware execution' in line for line in manifest['limitations']))
        self.assertEqual({item['project_id'] for item in manifest['captures']}, {
            '7c92d38a4f2ac205aa91502291fde0d8',
            'c9ede30a619b12d7c97056a2da040cc1',
            'e6b30d45ba55e64aa450a2aa292edd4b',
            'dab8622b41adbf3b9e2175909146b207',
        })
