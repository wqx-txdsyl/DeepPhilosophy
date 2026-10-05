"""Build the public author catalogue and detail profiles without changing existing paths.

Run after editing philosophers.json, school content, books.json or author-curation.
School concepts/events are attributed to their source school; shared membership is
never converted into a personal teacher/student relationship. Legacy generated
philosopher_network.json is deliberately not used as historical evidence.
"""
import argparse
import datetime
import json
import os
import re
from collections import Counter
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(BASE)
PUBLIC = ROOT / 'app/public'
CURATION = ROOT / 'scripts/author-curation'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def clean(value):
    return re.sub(r'[\s·•・.《》〈〉]', '', str(value or '')).lower()


def paragraphs(value):
    value = re.sub(r'(?m)^#{1,4}\s*', '', str(value or '').replace('\\n', '\n')).replace('**', '')
    result = []
    for block in re.split(r'\n\s*\n|\n', value):
        current = ''
        for sentence in re.findall(r'.+?(?:[。！？](?:[”」])?|$)', block):
            current += sentence
            if len(current) >= 240:
                result.append(current.strip())
                current = ''
        if current.strip():
            result.append(current.strip())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', default=datetime.date.today().isoformat(), help='目录整理报告日期（YYYY-MM-DD）；同参数重复运行输出幂等')
    args = parser.parse_args()
    people = read(PUBLIC / 'philosophers.json')
    roster = read(CURATION / 'roster.json')
    portrait_audit = read(PUBLIC / 'philosopher/portrait-audit.json').get('records', {})
    aliases = roster['aliases']
    merged = []
    for old, name in aliases.items():
        if old in people and name in people:
            # Preserve every bibliography entry from duplicate records.
            titles = {clean(item.get('title') if isinstance(item, dict) else item) for item in people[name]['books']}
            for item in people[old].get('books', []):
                title = clean(item.get('title') if isinstance(item, dict) else item)
                if title not in titles:
                    people[name]['books'].append(item)
                    titles.add(title)
            merged.append({'alias': old, 'canonical': name})
            del people[old]

    # Corrections replace identity-swapped prose rather than merely changing dates.
    corrections = read(CURATION / 'corrections.json')
    for name, correction in corrections.items():
        if name in people:
            people[name].update(correction)
    heidegger = read(CURATION / 'heidegger.json')
    people['马丁·海德格尔']['bio'] = '\n\n'.join(heidegger['overview'])
    people['马丁·海德格尔']['sources'] = heidegger['sources']
    people['马丁·海德格尔']['wiki_url'] = 'https://en.wikipedia.org/wiki/Martin_Heidegger'
    editorial = {record['name']: record for record in (read(path) for path in (PUBLIC / 'philosopher/editorial').glob('*.json'))}
    for name, record in editorial.items():
        if name not in people:
            raise ValueError(f'Editorial record has no canonical author: {name}')
        people[name].update(record.get('identity', {}))
        if record['profile'].get('englishName'):
            people[name]['englishName'] = record['profile']['englishName']
        people[name]['bio'] = '\n\n'.join(record['profile']['overview'])
        people[name]['sources'] = record['profile']['sources']

    for name, person in people.items():
        person['name'] = name
        person['listingKind'] = next((kind for kind in ['tradition', 'context', 'review'] if name in roster[kind]), 'thinker')
        person['book_count'] = len(person.get('books', []))
        if person['listingKind'] == 'review':
            person['reviewReason'] = roster['reviewReason']
            person.update(bio=roster['reviewReason'], era='身份待核实', country='', school='资料待核实', rank=0)
        if person['listingKind'] == 'tradition' and name not in ['相里氏之墨', '萨阿贡记录的匿名智者', '传道者', '约伯', '奇兰·巴兰']:
            person['dateKind'] = 'tradition'

    index = {clean(name): name for name in people}
    surnames = {}
    for name in people:
        surname = name.split('·')[-1]
        if surname != name and len(surname) >= 2:
            surnames.setdefault(clean(surname), []).append(name)
    variants = {'爱德蒙德·胡塞尔': '埃德蒙德·胡塞尔', '埃马纽埃尔·列维纳斯': '伊曼纽尔·列维纳斯'}

    def resolve(name, era=None):
        name = variants.get(name, aliases.get(name, name))
        matched = index.get(clean(name))
        if not matched and len(surnames.get(clean(name), [])) == 1:
            matched = surnames[clean(name)][0]
        # Wrong eras must not make Galen into Arnold Gehlen, or John Locke into Alain Locke.
        if matched and era:
            def year(value):
                match = re.search(r'\d{1,4}', str(value))
                if not match:
                    return None
                n = int(match[0])
                if '世纪' in str(value):
                    n *= 100
                return -n if '前' in str(value) else n
            a, b = year(era), year(people[matched].get('era'))
            if a is not None and b is not None and abs(a - b) > 200:
                return None
        return matched

    # Atlas names are the existing route keys; a display title inside a detail may differ.
    schools = sorted(({**read(PUBLIC / 'schools/data' / item['detailFile']), 'name': item['name']} for item in read(PUBLIC / 'gene/atlas.json')), key=lambda school: school['name'])
    books = read(PUBLIC / 'books.json')
    profiles = {name: {'overview': paragraphs(person.get('bio')), 'life': [], 'concepts': [], 'schoolLinks': [], 'people': [], 'relations': [], 'bibliography': [], 'sources': person.get('sources', [])} for name, person in people.items()}
    for school in schools:
        thinkers = school.get('thinkers', [])
        members = [(thinker, resolve(thinker.get('name'), thinker.get('era'))) for thinker in thinkers]
        members = [(thinker, name) for thinker, name in members if name and people[name]['listingKind'] != 'review']
        for thinker, name in members:
            profile = profiles[name]
            profile['schoolLinks'].append({'name': school['name'], 'image': f"/schools/{school['name']}.webp", 'question': school.get('subtitle', ''), 'key': thinker.get('key', '')})
            if not profile.get('question') and thinker.get('key'):
                profile['question'] = thinker['key']
            tokens = [thinker['name'], name]
            works = thinker.get('works', [])
            if isinstance(works, str):
                works = re.findall(r"['\"]([^'\"]+)['\"]", works) or re.split('[、；;]', works)
            works = [work for work in works if isinstance(work, str)]
            for title in works:
                if isinstance(title, str) and clean(title) not in {clean(item['title']) for item in profile['bibliography']}:
                    profile['bibliography'].append({'title': title, 'sourceSchool': school['name']})
            for event in school.get('timeline', []):
                title = event.get('event', '')
                if not isinstance(title, str):
                    continue
                explicit_person = any(token and token in title for token in tokens)
                work_event = any(f'《{work}》' in title and not re.search(rf'《{re.escape(work)}》\s*(?:释义|导读|研究|评注)', title) for work in works)
                another_person = any(other['name'] in title and other_name != name for other, other_name in members)
                if explicit_person or (work_event and not another_person):
                    item = {'year': event.get('year'), 'title': event['event'], 'body': event.get('detail', ''), 'sourceSchool': school['name']}
                    if not any(item['title'] == old['title'] for old in profile['life']):
                        profile['life'].append(item)
            for concept in school.get('cihai', []):
                def text_of(value):
                    return value if isinstance(value, str) else ''
                text = text_of(concept.get('def', '')) + text_of(concept.get('source', ''))
                if any(token and token in text for token in tokens) or any(title and title in concept.get('source', '') for title in works):
                    word = concept.get('word', '')
                    if word and not any(old['name'] == word for old in profile['concepts']):
                        profile['concepts'].append({'name': word, 'definition': concept.get('def', ''), 'source': concept.get('source', ''), 'sourceSchool': school['name']})
            # A shared school is an intellectual context, not evidence of a personal encounter.
            for other, other_name in members:
                if other_name != name and not any(item['name'] == other_name for item in profile['people']):
                    profile['people'].append({'name': other_name, 'era': people[other_name]['era'], 'influence': other.get('influence', 5), 'role': f"共同思想背景 · {school['name']}", 'summary': other.get('key', ''), 'sourceSchool': school['name']})
                    profile['relations'].append({'from': name, 'to': other_name, 'type': 'context', 'label': '共同思想背景', 'sourceSchool': school['name']})

            member_names = {other['name']: other_name for other, other_name in members}
            for relation in school.get('relations', []):
                source = member_names.get(relation.get('from'))
                target = member_names.get(relation.get('to'))
                if not source or not target or name not in [source, target] or source == target:
                    continue
                label = relation.get('label') or relation.get('type') or '思想关联'
                # Retain source direction and wording, including explicitly disputed traditions.
                kind = 'teacher' if '师承' in label else 'reading' if any(word in label for word in ['批判', '争论', '解读']) else 'influence'
                profile['relations'] = [old for old in profile['relations'] if not (old['type'] == 'context' and {old['from'], old['to']} == {source, target})]
                item = {'from': source, 'to': target, 'type': kind, 'label': label, 'detail': relation.get('detail', ''), 'sourceSchool': school['name']}
                if not any(old['from'] == source and old['to'] == target and old['label'] == label for old in profile['relations']):
                    profile['relations'].append(item)
                other_name = target if source == name else source
                other = next((old for old in profile['people'] if old['name'] == other_name), None)
                if other:
                    other.update(role=f"{label} · {school['name']}", summary=relation.get('detail') or other['summary'])

    for name, profile in profiles.items():
        if name == '马丁·海德格尔':
            profile.update(heidegger)
        if name in editorial:
            record = editorial[name]
            # Authored arrays replace derived context; legacy book links remain below.
            profile.update(record['profile'])
            profile['editorial'] = {key: record.get(key) for key in ['schemaVersion', 'reviewedAt', 'chronologyPolicy', 'worksPolicy', 'evidenceLimits', 'overviewSourceRefs', 'debateAssessment', 'regionCohort']}
        def event_year(item):
            raw = str(item['year'])
            number = int((re.search(r'\d{1,4}', raw) or ['9999'])[0])
            if '世纪' in raw:
                number = number * 100 if '前' in raw else (number - 1) * 100 + 1
            return -number if '前' in raw else number
        # Preserve reviewed ordering where dates are ranges, unknown, or text-history.
        if name not in editorial:
            profile['life'].sort(key=event_year)
        profile['schoolLinks'] = list({item['name']: item for item in profile['schoolLinks']}.values())
        profile['schoolLinks'].sort(key=lambda school: school['name'] not in re.split(r'[/、，;；]', people[name].get('school', '')))
        # Exact canonical author matching, including old book-author spellings.
        author_books = [book for book in books if resolve(book.get('author')) == name]
        for book in author_books:
            if not any(clean(item.get('title') if isinstance(item, dict) else item) == clean(book['title']) for item in people[name]['books']):
                people[name]['books'].append({'title': book['title'], 'id': book['id'], 'file_type': book.get('file_type')})
        people[name]['book_count'] = len(people[name]['books'])
        photo_names = [name] + [old for old, target in aliases.items() if target == name]
        portrait = next((f'/philosopher/{photo}.{ext}' for photo in photo_names for ext in ['webp', 'jpg', 'png'] if (PUBLIC / f'philosopher/{photo}.{ext}').exists()), None)
        # Corrected identities cannot inherit an unverified picture of a different person.
        if corrections.get(name, {}).get('portraitVerified') is False or people[name]['listingKind'] == 'review' or portrait_audit.get(name, {}).get('allowAsPortrait') is False:
            portrait = None
        if name in portrait_audit:
            people[name]['portraitReview'] = portrait_audit[name]
        people[name]['portrait'] = portrait
        detail = {**people[name], 'profile': profile}
        write(PUBLIC / 'philosopher/data' / (name.replace('/', '-').replace(':', '：') + '.json'), detail)
    # Alias files remain accessible to previous bookmarks; no public path is removed.
    for old, name in aliases.items():
        if name in people:
            write(PUBLIC / 'philosopher/data' / (old.replace('/', '-').replace(':', '：') + '.json'), {'name': name, 'aliasOf': name})
    write(PUBLIC / 'philosophers.json', people)
    counts = dict(Counter(person['listingKind'] for person in people.values()))
    catalog = {'version': 1, 'counts': counts, 'aliases': aliases, 'people': {name: {key: value for key, value in person.items() if key not in ['bio', 'books', 'wiki_url']} for name, person in people.items()}, 'books': [{key: book.get(key) for key in ['id', 'title', 'author', 'cover', 'chapterCount', 'file_type']} for book in books]}
    write(PUBLIC / 'philosopher/catalog.json', catalog)
    audit = {'date': args.date, 'policy': roster['policy'], 'counts': counts, 'canonicalRecords': len(people), 'originalRecords': 744, 'duplicateRecordsMerged': {old: aliases[old] for old in list(aliases)[:7]}, 'legacyAliases': aliases, 'identityCorrections': list(corrections), 'classified': {kind: roster[kind] for kind in ['tradition', 'context', 'review']}, 'scope': '全目录查重与分类、全部详情结构及链接检查、重点身份错配纠正。普通旧简介未逐句完成学术核验；来源薄弱条目仍需持续审读。', 'relationshipPolicy': '不采用旧 AI 星丛作为历史证据；采用已整理的流派关系并保留语境，共同流派关系明确标作思想背景，海德格尔使用核验的人物关系。'}
    write(ROOT / 'docs/author-content-audit.json', audit)
    print(json.dumps({'records': len(people), 'counts': counts, 'detailProfiles': len(profiles), 'aliases': len(aliases)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
