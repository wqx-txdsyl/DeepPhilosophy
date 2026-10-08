"""Semantic guards for authored packets and the complete legacy review queue."""
import copy
import json
import os
import unittest
from collections import Counter
from pathlib import Path
from audit_author_assets import assess
from check_author_source_evidence import evaluate as evaluate_source_evidence

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


def source(id, url, type='scholarly-encyclopedia', accessScope='full-text', readScope='读了相关章节'):
    return {'id': id, 'title': '来源', 'url': url, 'type': type, 'accessedAt': '2026-10-09',
            'accessScope': accessScope, 'readScope': readScope, 'coverage': '覆盖范围'}


class SourceEvidenceGateTests(unittest.TestCase):
    @staticmethod
    def packet(*sources, referencing='sep'):
        editorial = {'name': '门禁测试人物', 'overviewSourceRefs': [referencing]}
        profile = {
            'name': '门禁测试人物',
            'sources': list(sources),
            'life': [{'year': '1900', 'title': '节点', 'body': '内容', 'sourceRefs': [referencing]}],
            'bibliography': [{'title': '书', 'year': '1900', 'kind': 'authored', 'description': '描述', 'sourceRefs': [referencing]}],
        }
        return profile, editorial

    def test_packets_without_access_scope_stay_exempt(self):
        legacy = source('leads', 'https://zh.wikipedia.org/wiki/%E8%B0%AD%E5%97%A3%E5%90%8C')
        legacy.pop('accessScope')
        profile, editorial = self.packet(legacy)
        self.assertEqual(evaluate_source_evidence(profile, editorial, '门禁测试人物'), [])

    def test_search_summaries_and_wikipedia_never_support_body_claims(self):
        snippet = source('leads', 'https://example.org/x', accessScope='search-summary', readScope='仅检索摘要')
        profile, editorial = self.packet(snippet, referencing='leads')
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertIn('life[0]:clue-source-referenced:leads', errors)
        wiki = source('wiki', 'https://zh.wikipedia.org/wiki/%E8%B0%AD%E5%97%A3%E5%90%8C')
        profile, editorial = self.packet(wiki, referencing='wiki')
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertIn('life[0]:clue-source-referenced:wiki', errors)
        self.assertIn('overviewSourceRefs:clue-source-referenced:wiki', errors)

    def test_authoritative_domains_do_not_turn_unread_excerpts_into_full_text(self):
        mislabeled = source('gov', 'https://www.gov.uk/', type='encyclopedia-clue', accessScope='full-text')
        profile, editorial = self.packet(mislabeled, referencing='gov')
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertIn('sources[0]:clue-source-marked-readable', errors)
        self.assertIn('life[0]:clue-source-referenced:gov', errors)

    def test_primary_text_transcriptions_are_not_plain_wikipedia(self):
        transcription = source('ws', 'https://zh.wikisource.org/wiki/%E4%BB%81%E5%AD%B8', type='primary-text-transcription')
        evidence = {'sources': [{'id': 'ws'}],
                    'checks': [{'field': 'profile.life[0]', 'claim': '断言', 'sourceId': 'ws', 'locator': '§1', 'verdict': 'confirmed'}]}
        profile, editorial = self.packet(transcription)
        self.assertEqual(evaluate_source_evidence(profile, editorial, '门禁测试人物', evidence), [])

    def test_catalog_metadata_supports_title_facts_but_search_summaries_support_nothing(self):
        catalog = source('oclc', 'https://search.example.org/record', accessScope='abstract-or-catalog', readScope='仅编目著录')
        profile, editorial = self.packet(catalog, referencing='oclc')
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertNotIn('life[0]:clue-source-referenced:oclc', errors)
        snippet = source('leads', 'https://search.example.org/hit', accessScope='search-summary', readScope='仅检索摘要')
        profile, editorial = self.packet(snippet, referencing='leads')
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertIn('bibliography[0]:clue-source-referenced:leads', errors)
        self.assertIn('life[0]:clue-source-referenced:leads', errors)

    def test_access_scope_must_be_declared_for_every_source(self):
        undeclared = source('ws', 'https://zh.wikisource.org/wiki/%E4%BB%81%E5%AD%B8', type='primary-text-transcription')
        undeclared.pop('accessScope')
        readable = source('sep', 'https://plato.stanford.edu/entries/renxue/')
        profile, editorial = self.packet(undeclared, readable, referencing='sep')
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertIn('sources[0]:invalid-access-scope', errors)
        undeclared['accessScope'] = 'full-text'
        undeclared.pop('readScope')
        undeclared.pop('coverage')
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertIn('sources[0]:missing-read-scope-note', errors)

    def test_read_sources_need_an_evidence_record_with_locators(self):
        readable = source('sep', 'https://plato.stanford.edu/entries/renxue/')
        profile, editorial = self.packet(readable)
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertIn('missing-source-evidence-record', errors)
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字', {'sources': [], 'checks': []})
        self.assertIn('evidence-record-missing-source:sep', errors)
        self.assertIn('evidence-record-without-checks', errors)
        thin = {'sources': [{'id': 'sep'}], 'checks': [{'field': 'life[0]', 'claim': '断言', 'sourceId': 'sep', 'locator': '', 'verdict': 'confirmed'}]}
        errors = evaluate_source_evidence(profile, editorial, '门禁测试人物', thin)
        self.assertIn('evidence-checks[0]:missing-locator', errors)
        bad = {'sources': [{'id': 'sep'}], 'checks': [{'field': 'life[0]', 'claim': '断言', 'sourceId': 'sep', 'locator': '§2', 'verdict': 'surely-fine'}]}
        errors = evaluate_source_evidence(profile, editorial, '门禁测试人物', bad)
        self.assertIn('evidence-checks[0]:invalid-verdict', errors)

    def test_uncertain_checks_do_not_require_a_locator(self):
        readable = source('sep', 'https://plato.stanford.edu/entries/renxue/')
        evidence = {'sources': [{'id': 'sep'}],
                    'checks': [{'field': 'profile.life[0].year', 'claim': '生年', 'sourceId': 'sep', 'locator': '', 'verdict': 'uncertain'}]}
        profile, editorial = self.packet(readable)
        self.assertEqual(evaluate_source_evidence(profile, editorial, '门禁测试人物', evidence), [])

    def test_gated_packets_fail_the_asset_audit_through_the_same_path(self):
        readable = source('sep', 'https://plato.stanford.edu/entries/renxue/')
        profile, editorial = self.packet(readable)
        editorial.update({'schemaVersion': 1, 'reviewedAt': '2026-10-09', 'reviewMethod': 'per-source review',
                          'overviewSourceRefs': ['sep'], 'debateAssessment': {'status': 'not-required', 'scope': '无'}})
        assessment = assess(profile, editorial)
        self.assertIn('missing-source-evidence-record', assessment['errors'])
        self.assertEqual(assessment['level'], 'needs-review')


if __name__ == '__main__':
    unittest.main()
