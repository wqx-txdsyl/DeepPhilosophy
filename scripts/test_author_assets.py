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
        cls.people = json.loads((PUBLIC / 'philosophers.json').read_text())
        cls.books = json.loads((PUBLIC / 'books.json').read_text())

    def test_balanced_regions_and_retained_benchmark(self):
        cohorts = Counter(packet['regionCohort'] for packet in self.packets if packet.get('batch') == '2026-10-03-balanced-01')
        self.assertEqual(cohorts, {'古希腊与欧洲思想': 10, '东亚思想': 10, '南亚、伊斯兰、非洲、拉美与原住民传统': 10})
        self.assertTrue(any(packet['name'] == '马丁·海德格尔' for packet in self.packets))

    def test_new_batches_stay_separate_from_the_frozen_baseline_batch(self):
        for packet in self.packets:
            if packet.get('batch') == '2026-10-03-balanced-01':
                continue
            self.assertNotEqual(packet.get('batch'), '2026-10-03-balanced-01', packet['name'])
            self.assertTrue(packet.get('batch'), packet['name'])

    def test_relation_endpoints_are_resolvable(self):
        for packet in self.packets:
            known = {packet['name']} | {person['name'] for person in packet['profile'].get('people', [])} | set(self.people)
            for relation in packet['profile'].get('relations', []):
                for endpoint in (relation['from'], relation['to']):
                    self.assertIn(endpoint, known, f"{packet['name']}: {endpoint}")
                    self.assertNotEqual(self.people.get(endpoint, {}).get('listingKind'), 'review', f"{packet['name']}: {endpoint}")

    def test_alias_targets_resolve_without_chains(self):
        aliases = json.loads((Path(BASE) / 'scripts/author-curation/roster.json').read_text())['aliases']
        for old, canonical in aliases.items():
            self.assertIn(canonical, self.people, old)
            self.assertNotIn(canonical, aliases, f'{canonical} 既是别名目标又是别名，形成链')

    def test_linked_book_ids_exist_in_the_catalog(self):
        book_ids = {book['id'] for book in self.books}
        for name, person in self.people.items():
            for item in person.get('books', []):
                if isinstance(item, dict) and item.get('id'):
                    self.assertIn(item['id'], book_ids, f'{name}: {item["id"]} {item.get("title", "")}')

    def test_no_autographs_are_not_invented_to_fill_the_bibliography(self):
        for packet in self.packets:
            if packet.get('worksPolicy') != 'no-autographs':
                continue
            for work in packet['profile']['bibliography']:
                self.assertNotIn(work['kind'], ['authored', 'coauthored', 'edited'], f"{packet['name']}: {work['title']}")
        for name in ['苏格拉底', '孔子', '释迦牟尼']:
            packet = next(packet for packet in self.packets if packet['name'] == name)
            self.assertEqual(packet['worksPolicy'], 'no-autographs')
            self.assertTrue(all(work['kind'] == 'testimony' for work in packet['profile']['bibliography']))

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

    def test_empty_content_cannot_pass_with_valid_reference_ids(self):
        packet = copy.deepcopy(self.packets[0])
        packet['profile']['concepts'][0]['definition'] = ''
        self.assertEqual(assess(packet['profile'], packet)['level'], 'needs-review')

    def test_limited_evidence_requires_an_explicit_explanation(self):
        packet = copy.deepcopy(next(packet for packet in self.packets if packet['name'] == '老子'))
        packet['evidenceLimits'] = ''
        self.assertIn('missing-chronology-explanation', assess(packet['profile'], packet)['errors'])

    def test_debate_assessment_must_match_the_debate_body(self):
        packet = copy.deepcopy(self.packets[0])
        packet['debateAssessment']['status'] = 'included'
        packet['profile'].pop('debate', None)
        self.assertIn('debate-assessment-without-body', assess(packet['profile'], packet)['errors'])
        packet['debateAssessment']['status'] = 'not-required'
        packet['profile']['debate'] = {'title': 'x', 'year': 'y', 'paragraphs': ['z'], 'sourceRefs': [packet['profile']['sources'][0]['id']]}
        self.assertIn('debate-body-without-included-assessment', assess(packet['profile'], packet)['errors'])

    def test_political_controversy_is_not_a_required_quota(self):
        packet = copy.deepcopy(self.packets[0])
        packet['profile'].pop('debate', None)
        packet['debateAssessment'] = {'status': 'not-required', 'scope': 'No relevant sourced controversy to add.'}
        self.assertEqual(assess(packet['profile'], packet)['level'], 'source-backed')


if __name__ == '__main__':
    unittest.main()
