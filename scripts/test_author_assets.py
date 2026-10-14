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
            expected = 'needs-review' if (assessment['gaps'] or assessment['errors']) else 'source-backed'
            self.assertEqual(assessment['level'], expected, f'{name}: {assessment}')
            if assessment['level'] == 'needs-review':
                # 待审必须给出可定位的原因（结构缺口或门禁错误），不允许无因降级。
                self.assertTrue(assessment['gaps'] or assessment['errors'], f'{name}: 待审缺少可定位原因: {assessment}')

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

    @staticmethod
    def frozen_lock(name, content):
        import hashlib
        from check_author_source_evidence import editorial_relpath
        rel = editorial_relpath(name)
        return {'frozenEditorialHashes': {rel: hashlib.sha256(content).hexdigest()}, 'roundAuthorization': {'additionalRepairNames': [], 'nameSetSha256': ''}}

    def legacy_profile(self):
        legacy = source('leads', 'https://example.org/legacy', accessScope='full-text')
        legacy.pop('accessScope')
        return self.packet(legacy)

    def test_unchanged_frozen_baseline_stays_historically_compatible(self):
        import json as _json
        profile, editorial = self.legacy_profile()
        content = (_json.dumps({'profile': profile}, ensure_ascii=False, sort_keys=True) + '\n').encode()
        lock = self.frozen_lock('门禁测试人物', content)
        from check_author_source_evidence import packet_is_gated
        self.assertFalse(packet_is_gated(profile, '门禁测试人物', lock=lock, content=content))
        self.assertEqual(evaluate_source_evidence(profile, editorial, '门禁测试人物', lock=lock, content=content), [])

    def test_new_packets_without_any_access_scope_fail(self):
        profile, editorial = self.legacy_profile()
        errors = evaluate_source_evidence(profile, editorial, '门禁测试人物')
        self.assertIn('sources[0]:missing-required-field:accessScope', errors)

    def test_revised_frozen_packet_does_not_inherit_exemption(self):
        import json as _json
        profile, editorial = self.legacy_profile()
        stale = (_json.dumps({'profile': {'sources': []}}, ensure_ascii=False, sort_keys=True) + '\n').encode()
        lock = self.frozen_lock('门禁测试人物', stale)
        from check_author_source_evidence import packet_is_gated
        self.assertTrue(packet_is_gated(profile, '门禁测试人物', lock=lock))
        errors = evaluate_source_evidence(profile, editorial, '门禁测试人物', lock=lock)
        self.assertIn('sources[0]:missing-required-field:accessScope', errors)

    def test_round_listed_packets_are_gated_even_if_frozen(self):
        import hashlib
        import json as _json
        from check_author_source_evidence import packet_is_gated
        profile, editorial = self.legacy_profile()
        content = (_json.dumps({'profile': profile}, ensure_ascii=False, sort_keys=True) + '\n').encode()
        lock = self.frozen_lock('齐格蒙特·鲍曼', content)
        lock['roundAuthorization'] = {
            'additionalRepairNames': ['齐格蒙特·鲍曼'],
            'nameSetSha256': hashlib.sha256(_json.dumps(['齐格蒙特·鲍曼'], ensure_ascii=False, separators=(',', ':')).encode()).hexdigest(),
        }
        self.assertTrue(packet_is_gated(profile, '齐格蒙特·鲍曼', lock=lock, content=content))
        errors = evaluate_source_evidence(profile, editorial, '齐格蒙特·鲍曼', lock=lock)
        self.assertIn('sources[0]:missing-required-field:accessScope', errors)

    def test_missing_lock_baseline_is_an_error_not_an_exemption(self):
        import copy
        import check_author_source_evidence as gate
        lock = copy.deepcopy(gate.load_lock())
        # 模拟锁文件只覆盖别人：目标包不在冻结表 → 新包必须门禁，而非自动豁免
        lock['frozenEditorialHashes'] = {}
        profile, editorial = self.legacy_profile()
        self.assertTrue(gate.packet_is_gated(profile, '门禁测试人物', lock=lock))
        self.assertIn('sources[0]:missing-required-field:accessScope',
                      evaluate_source_evidence(profile, editorial, '门禁测试人物', lock=lock))

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

    def test_catalog_metadata_supports_only_bibliography_facts(self):
        catalog = source('oclc', 'https://search.example.org/record', accessScope='abstract-or-catalog', readScope='仅编目著录')
        profile, editorial = self.packet(catalog, referencing='oclc')
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertIn('life[0]:abstract-catalog-supports-bibliography-only:oclc', errors)
        self.assertNotIn('life[0]:clue-source-referenced:oclc', errors)
        editorial_bib = {'name': '门禁测试人物', 'overviewSourceRefs': []}
        bib_profile = {
            'name': '门禁测试人物',
            'sources': [catalog],
            'bibliography': [{'title': '书', 'year': '1900', 'kind': 'authored', 'description': '描述', 'sourceRefs': ['oclc']}],
        }
        errors = evaluate_source_evidence(bib_profile, editorial_bib, '不存在于研究目录的名字')
        self.assertNotIn('bibliography[0]:abstract-catalog-supports-bibliography-only:oclc', errors)
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
        self.assertIn('sources[0]:missing-required-field:accessScope', errors)
        undeclared['accessScope'] = 'full-text'
        undeclared.pop('readScope')
        undeclared.pop('coverage')
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertIn('sources[0]:missing-read-scope-note', errors)
        partial = source('sep', 'https://plato.stanford.edu/entries/renxue/')
        partial.pop('accessedAt')
        profile, editorial = self.packet(readable, partial, referencing='sep')
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertIn('sources[1]:missing-required-field:accessedAt', errors)
        not_read = source('book', 'https://press.example.org/book', accessScope='maybe-scanned')
        profile, editorial = self.packet(not_read, referencing='book')
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字')
        self.assertIn('sources[0]:invalid-access-scope', errors)

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

    def test_fact_verdicts_cannot_rest_on_unread_or_snippet_sources(self):
        snippet = source('leads', 'https://example.org/x', accessScope='search-summary', readScope='仅检索摘要')
        unread = source('paywall', 'https://press.example.org/paywalled', accessScope='unread', readScope='403 未读')
        profile, editorial = self.packet(snippet, unread, referencing='leads')
        evidence = {'sources': [{'id': 'leads'}, {'id': 'paywall'}], 'checks': [
            {'field': 'profile.life[0].year', 'claim': '生年', 'sourceId': 'leads', 'locator': '摘要第1行', 'verdict': 'confirmed'},
            {'field': 'profile.bibliography[0].year', 'claim': '出版年', 'sourceId': 'paywall', 'locator': '版权页', 'verdict': 'corrected'},
        ]}
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字', evidence)
        self.assertIn('evidence-checks[0]:verdict-source-not-readable:leads', errors)
        self.assertIn('evidence-checks[1]:verdict-source-not-readable:paywall', errors)

    def test_catalog_records_back_verdicts_on_bibliography_fields_only(self):
        catalog = source('authority', 'https://authority.example.org/gros', accessScope='abstract-or-catalog', readScope='仅著录层')
        profile, editorial = self.packet(catalog, referencing='authority')
        evidence = {'sources': [{'id': 'authority'}], 'checks': [
            {'field': 'profile.bibliography[2].year', 'claim': '出版年2005', 'sourceId': 'authority', 'locator': '著录行', 'verdict': 'corrected'},
            {'field': 'profile.life[2].body', 'claim': '生平事件', 'sourceId': 'authority', 'locator': '著录行', 'verdict': 'confirmed'},
        ]}
        errors = evaluate_source_evidence(profile, editorial, '不存在于研究目录的名字', evidence)
        self.assertNotIn('evidence-checks[0]:verdict-source-not-readable:authority', errors)
        self.assertIn('evidence-checks[1]:verdict-source-not-readable:authority', errors)

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


class GuardRoundAuthorizationTests(unittest.TestCase):
    """The lock may narrow but never widen what the authorization queues file grants."""

    @classmethod
    def setUpClass(cls):
        import guard_author_quality_worktree as guard
        cls.guard = guard
        cls.lock = guard.read(guard.LOCK)

    def test_registered_authorization_matches_the_queues_file(self):
        repair, context = self.guard.round_authorization(self.lock)
        self.assertEqual(len(repair), 73)
        self.assertEqual(context, {'汉谟拉比'})
        self.assertTrue('齐格蒙特·鲍曼' in repair and '弗里德里克·格鲁' in repair)

    def test_original_repair_list_is_preserved(self):
        import json as _json
        queues = self.guard.read(self.guard.ROOT / self.lock['roundAuthorization']['authorizationQueues'])
        protected = queues['originalLockProtection']['existingRepairNames']
        self.assertEqual(set(self.lock['repairExistingPackets']), set(protected))
        self.assertEqual(len(protected), 11)

    def test_tampered_lists_fail_closed(self):
        import copy
        cases = []
        wider = copy.deepcopy(self.lock)
        wider['roundAuthorization']['additionalRepairNames'].append('孔子')
        cases.append(('widen-repair', wider))
        shrink = copy.deepcopy(self.lock)
        shrink['repairExistingPackets'] = shrink['repairExistingPackets'][:10]
        cases.append(('drop-original', shrink))
        widen_ctx = copy.deepcopy(self.lock)
        widen_ctx['roundAuthorization']['contextApplicationNames'] = ['汉谟拉比', '老子']
        cases.append(('widen-context', widen_ctx))
        for label, tampered in cases:
            with self.subTest(label=label):
                with self.assertRaises(SystemExit):
                    self.guard.round_authorization(tampered)


if __name__ == '__main__':
    unittest.main()
