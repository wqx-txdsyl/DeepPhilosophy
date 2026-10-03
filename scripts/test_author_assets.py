"""Semantic guards for authored packets and the complete legacy review queue."""
import copy
import json
import os
import unittest
from collections import Counter
from pathlib import Path
from audit_author_assets import assess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = Path(BASE) / 'app/public'


class AuthorAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packets = [json.loads(path.read_text()) for path in (PUBLIC / 'philosopher/editorial').glob('*.json')]

    def test_balanced_regions_and_retained_benchmark(self):
        cohorts = Counter(packet['regionCohort'] for packet in self.packets if packet.get('batch') == '2026-10-03-balanced-01')
        self.assertEqual(cohorts, {'古希腊与欧洲思想': 10, '东亚思想': 10, '南亚、伊斯兰、非洲、拉美与原住民传统': 10})
        self.assertTrue(any(packet['name'] == '马丁·海德格尔' for packet in self.packets))

    def test_every_packet_survives_compilation_with_references(self):
        for packet in self.packets:
            name = packet['name']
            path = PUBLIC / 'philosopher/data' / (name.replace('/', '-').replace(':', '：') + '.json')
            compiled = json.loads(path.read_text())['profile']
            for field, value in packet['profile'].items():
                self.assertEqual(compiled[field], value, f'{name}: {field}')
            assessment = assess(compiled, packet)
            self.assertEqual(assessment['level'], 'source-backed', f'{name}: {assessment}')

    def test_full_fields_without_editorial_review_do_not_pass(self):
        self.assertEqual(assess(self.packets[0]['profile'])['level'], 'needs-review')

    def test_unresolved_citations_cannot_pass(self):
        packet = copy.deepcopy(self.packets[0])
        packet['profile']['concepts'][0]['sourceRefs'] = ['missing-source']
        self.assertEqual(assess(packet['profile'], packet)['level'], 'needs-review')

    def test_limited_evidence_requires_an_explicit_explanation(self):
        packet = copy.deepcopy(next(packet for packet in self.packets if packet['name'] == '老子'))
        packet['evidenceLimits'] = ''
        self.assertIn('missing-chronology-explanation', assess(packet['profile'], packet)['errors'])

    def test_no_autographs_are_not_invented_to_fill_the_bibliography(self):
        for name in ['苏格拉底', '孔子', '释迦牟尼']:
            packet = next(packet for packet in self.packets if packet['name'] == name)
            self.assertEqual(packet['worksPolicy'], 'no-autographs')
            self.assertTrue(all(work['kind'] == 'testimony' for work in packet['profile']['bibliography']))

    def test_political_controversy_is_not_a_required_quota(self):
        packet = copy.deepcopy(self.packets[0])
        packet['profile'].pop('debate', None)
        packet['debateAssessment'] = {'status': 'not-required', 'scope': 'No relevant sourced controversy to add.'}
        self.assertEqual(assess(packet['profile'], packet)['level'], 'source-backed')


if __name__ == '__main__':
    unittest.main()
