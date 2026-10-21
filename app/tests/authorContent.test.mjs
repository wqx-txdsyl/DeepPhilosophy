import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { AUTHOR_KINDS, authorBooks, authorFile, authorSectionSources, bibliography, canonicalAuthor, loadAuthorPage, normalizeAuthor, readableBook } from '../src/data/authorContent.js';
import { OSS_BASE, staticImageSources } from '../src/data/ossUrls.js';
import { layoutConstellation } from '../src/data/schoolConstellationLayout.js';
import { buildSchoolReferences } from '../src/data/schoolContent.js';

const publicRoot = new URL('../public/', import.meta.url);
const read = path => JSON.parse(fs.readFileSync(new URL(path, publicRoot), 'utf8'));
const catalog = read('philosopher/catalog.json');
const roster = read('philosophers.json');
const schools = read('schools/catalog.json').schools;
const details = Object.keys(roster).map(name => normalizeAuthor(read(decodeURIComponent(authorFile(name).slice(1)))));

test('section citations honor declared sources instead of university-title guesses', () => {
  const person = details.find(item => item.name === '傅佩荣');
  assert.deepEqual(authorSectionSources(person, 'debate').map(source => source.id), ['ntu-nature']);
  assert.ok(!authorSectionSources(person, 'overview').some(source => source.accessScope === 'abstract-or-catalog'));
  assert.equal(person.profile.sources.length, 7);
});

test('catalogues, unread leads and missing declarations do not become body evidence', () => {
  const person = { profile: { editorial: { overviewSourceRefs: ['text', 'catalog', 'unread', 'missing'] }, sources: [
    { id: 'text', accessScope: 'partial-text' },
    { id: 'catalog', accessScope: 'abstract-or-catalog', title: '大学资料' },
    { id: 'unread', accessScope: 'unread' },
  ] } };
  assert.deepEqual(authorSectionSources(person, 'overview').map(source => source.id), ['text']);
  assert.deepEqual(authorSectionSources(person, 'debate'), []);
  assert.equal(person.profile.sources.length, 3);
});

test('detail and hero discovery are not blocked by a slow directory download, including old aliases', async () => {
  let finishCatalog;
  const calls = [], ready = [];
  const result = loadAuthorPage('奎因', undefined, {
    catalogLoader: () => new Promise(resolve => { finishCatalog = resolve; }),
    jsonLoader: async path => {
      calls.push(path);
      return path === authorFile('奎因') ? { aliasOf: '威拉德·范·奥曼·蒯因' } : { name: '威拉德·范·奥曼·蒯因' };
    },
    onDetail: author => ready.push(author.name),
  });
  await Promise.resolve(); await Promise.resolve();
  assert.deepEqual(calls, [authorFile('奎因'), authorFile('威拉德·范·奥曼·蒯因')]);
  assert.deepEqual(ready, ['威拉德·范·奥曼·蒯因']);
  finishCatalog(catalog);
  assert.equal((await result).raw.name, '威拉德·范·奥曼·蒯因');
});

test('portrait requests use sized CDN images with the unchanged original path as fallback', () => {
  for (const person of details.filter(person => person.portrait)) {
    const thumbnail = staticImageSources(person.portrait, 192);
    assert.ok(thumbnail.primary.startsWith(OSS_BASE + '/philosopher/'));
    assert.ok(thumbnail.primary.includes('image/resize,w_192/format,webp'));
    assert.equal(thumbnail.fallback, person.portrait);
  }
  assert.deepEqual(staticImageSources('https://example.com/photo.jpg'), { primary: 'https://example.com/photo.jpg', fallback: 'https://example.com/photo.jpg' });
});

test('every canonical entry has its own matching detail, category and existing images', () => {
  assert.equal(details.length, 737);
  // 保留737入口；教材共同署名另作作者组，不把两个人合成一个思想者。
  assert.equal(details.filter(person => person.listingKind === 'thinker').length, 637);
  for (const person of details) {
    assert.ok(AUTHOR_KINDS[person.listingKind]);
    assert.equal(person.name, roster[person.name].name);
    assert.ok(person.profile.overview.length > 0, person.name);
    if (person.portrait) assert.ok(fs.existsSync(new URL(person.portrait.slice(1), publicRoot)), person.name);
    for (const school of person.profile.schoolLinks) assert.ok(fs.existsSync(new URL(`schools/data/${schools.find(item => item.name === school.name)?.detailFile}`, publicRoot)), school.name);
  }
});
test('Ani retains the ancient teaching attribution without a fabricated modern Indian biography or mythical dating', () => {
  const person = details.find(item => item.name === '安尼');
  assert.equal(person.listingKind, 'tradition');
  assert.equal(person.country, '古埃及');
  assert.equal(person.dateKind, 'text-tradition');
  assert.equal(person.portrait, null);
  assert.ok(person.bio.includes('传统署名'));
  assert.equal(person.profile.bibliography.length, 1);
  assert.match(person.profile.bibliography[0].originalTitle, /Instruction of Ani/);
  assert.ok(!person.bio.includes('瓦拉纳西'));
  const context = details.find(item => item.name === '阿肯那顿').profile.people.find(item => item.name === '安尼');
  assert.match(context.summary, /传统署名/);
  assert.ok(!context.summary.includes('死后审判'));
  assert.equal(details.filter(item => item.listingKind === 'review' && !['弗朗西斯·吉姆', '普阿·凯斯-达文波特', '罗克珊·维纳', '达格·奥斯特罗姆', '阿布·穆斯林·阿特-图尔基', '阿马菲乌斯'].includes(item.name)).length, 30);
});
test('Amorgen preserves the legacy route as an Irish literary tradition without the fabricated continental biography', () => {
  const person = details.find(item => item.name === '德鲁伊·阿莫尔根');
  assert.equal(person.listingKind, 'tradition');
  assert.equal(person.displayName, '阿莫尔根（爱尔兰传说）');
  assert.equal(person.portrait, null);
  assert.ok(person.bio.includes('Amorgen Glúingel'));
  assert.ok(!person.bio.includes('哈贝马斯'));
  assert.ok(!person.profile.bibliography.some(work => /欲望机器|数字幽灵/.test(work.title)));
  assert.equal(details.filter(item => item.listingKind === 'tradition').length, 26);
});
test('the legacy Poit entry resolves to Anne Poelina through the specific Nyikina and river-council identity', () => {
  const person = details.find(item => item.name === '安妮·波伊特');
  assert.equal(person.listingKind, 'thinker');
  assert.equal(person.displayName, 'Anne Poelina');
  assert.equal(person.country, '澳大利亚');
  assert.equal(person.portrait, null);
  assert.ok(person.bio.includes('Nyikina'));
  assert.ok(!person.bio.includes('1940-2021'));
  assert.ok(!person.profile.bibliography.some(work => /身体与差异|存在与性别|伦理与差异/.test(work.title)));
  assert.ok(person.profile.sources.some(source => new URL(source.url).hostname === 'www.notredame.edu.au'));
  assert.equal(details.filter(item => item.listingKind === 'review' && !['弗朗西斯·吉姆', '普阿·凯斯-达文波特', '罗克珊·维纳', '达格·奥斯特罗姆', '阿布·穆斯林·阿特-图尔基', '阿马菲乌斯'].includes(item.name)).length, 30);
});
test('Elaine Russell keeps her legacy route as an artist, without the fabricated US philosopher identity', () => {
  const person = details.find(item => item.name === '伊莲·拉塞尔');
  assert.equal(person.listingKind, 'context');
  assert.equal(person.country, '澳大利亚');
  assert.match(person.era, /1941/);
  assert.ok(person.bio.includes('艺术家'));
  assert.ok(person.profile.bibliography.some(work => work.originalTitle === 'The shack that Dad built'));
  assert.ok(!person.profile.bibliography.some(work => work.originalTitle === 'Consciousness and Representation'));
  assert.ok(person.profile.sources.some(source => new URL(source.url).hostname === 'digital.nga.gov.au'));
});
test('the Revel and Ricard legacy entry keeps the joint book and distinguishes both authors', () => {
  const name = '让-弗朗索瓦何维勒/马修理查德';
  const group = details.find(person => person.name === name);
  const raw = roster[name];
  assert.equal(raw.entityType, 'dialogue-author-group');
  assert.equal(raw.listingKind, 'context');
  assert.equal(raw.portrait, null);
  assert.ok(raw.bio.startsWith('本条是让-弗朗索瓦·何维勒与马修·理查德的共同对话专题'));
  assert.deepEqual(group.profile.people.map(person => person.name), ['让-弗朗索瓦·何维勒', '马修·理查德']);
  assert.ok(authorBooks(group, catalog).some(book => book.id === '077532e4515e'));
});
test('the Stumpf and Fieser legacy credit retains its readable book without becoming one person', () => {
  const name = '撒穆尔·伊诺克·斯通普夫/詹姆斯·菲泽';
  const group = details.find(person => person.name === name);
  assert.equal(roster[name].entityType, 'textbook-author-group');
  assert.equal(roster[name].listingKind, 'context');
  assert.equal(roster[name].portrait, null);
  assert.deepEqual(group.profile.people.map(person => person.name), ['Samuel Enoch Stumpf', 'James Fieser']);
  assert.ok(authorBooks(group, catalog).some(book => book.id === '4a4a200536bd'));
});
test('unresolved identities do not acquire near-name people or unverified university biographies', () => {
  const person = details.find(item => item.name === '普阿·凯斯-达文波特');
  assert.equal(person.listingKind, 'review');
  assert.equal(person.portrait, null);
  assert.ok(person.reviewReason);
  assert.equal(person.profile.concepts.length, 0);
  assert.ok(!person.bio.includes('斯坦福'));
  assert.ok(!person.bio.includes('Mauna Kea'));
  const amalfius = details.find(item => item.name === '阿马菲乌斯');
  assert.equal(amalfius.listingKind, 'review');
  assert.equal(amalfius.portrait, null);
  assert.ok(amalfius.reviewReason);
  assert.equal(amalfius.profile.concepts.length, 0);
  assert.doesNotMatch(amalfius.bio, /1220|巴黎大学|Amafinius|伊壁鸠鲁/);
  const turki = details.find(item => item.name === '阿布·穆斯林·阿特-图尔基');
  assert.equal(turki.listingKind, 'review');
  assert.equal(turki.portrait, null);
  assert.ok(turki.reviewReason);
  assert.equal(turki.profile.concepts.length, 0);
  assert.doesNotMatch(turki.bio, /开罗|欧美|1965|舒拉/);
  const dag = details.find(item => item.name === '达格·奥斯特罗姆');
  assert.equal(dag.listingKind, 'review');
  assert.equal(dag.portrait, null);
  assert.ok(dag.reviewReason);
  assert.equal(dag.profile.concepts.length, 0);
  assert.doesNotMatch(dag.bio, /印第安纳|Østerberg|妻子/);
  const viner = details.find(item => item.name === '罗克珊·维纳');
  assert.equal(viner.listingKind, 'review');
  assert.equal(viner.portrait, null);
  assert.ok(viner.reviewReason);
  assert.equal(viner.profile.concepts.length, 0);
  assert.ok(!viner.bio.includes('纽约大学'));
  assert.ok(!viner.bio.includes('Vandermause'));
});
test('recovering Narokobi does not turn an unverified school dialogue into historical evidence', () => {
  const recovered = details.find(person => person.name === '伯纳德·纳罗科比');
  assert.equal(recovered.country, '巴布亚新几内亚');
  assert.ok(recovered.bio.startsWith('伯纳德·纳罗科比是巴布亚新几内亚'));
  assert.ok(!recovered.profile.bibliography.some(work => work.originalTitle === 'De Universalibus'));
  const peer = details.find(person => person.name === '维利索尼·赫雷尼科');
  const shared = peer.profile.relations.filter(relation =>
    [relation.from, relation.to].includes('伯纳德·纳罗科比'));
  // Both biographies now have authored packets; a school graph cannot restore
  // a dialogue that neither packet has verified.
  assert.equal(shared.length, 0);
  assert.equal(peer.profile.englishName, 'Vilsoni Hereniko');
  assert.equal(peer.era, '1954—');
  assert.deepEqual(peer.centuries, ['20世纪', '21世纪']);
  assert.ok(!peer.bio.includes('对话性还原'));
});
test('all former aliases still resolve to an existing canonical detail', () => {
  for (const [old, target] of Object.entries(catalog.aliases)) {
    assert.equal(canonicalAuthor(old, catalog), target);
    assert.equal(read(decodeURIComponent(authorFile(old).slice(1))).aliasOf, target);
    assert.ok(roster[target], target);
    assert.ok(!roster[old], old);
  }
  const references = buildSchoolReferences(read('schools/catalog.json'));
  assert.equal(references.findPerson('奎因').name, '威拉德·范·奥曼·蒯因');
  assert.equal(references.findPerson('维特根斯坦').name, '路德维希·维特根斯坦');
});
test('corrected identities do not inherit unrelated portraits or fabricated biographies', () => {
  assert.equal(roster['丹尼斯·林德利'].era, '1923—2013');
  assert.equal(roster['理查德·杰弗里'].era, '1926—2002');
  for (const name of ['丹尼斯·林德利', '理查德·杰弗里']) {
    assert.equal(roster[name].portrait, null, `${name}: 错配图不得恢复`);
    assert.equal(roster[name].portraitReview.allowAsPortrait, false);
  }
  assert.match(roster['维雷杜·维雷杜'].era, /^1931[–—-]2022$/);
  assert.equal(roster['卡蒂尼'].era, '1879年4月21日—1904年9月17日（爪哇）');
  assert.equal(roster['玛丽·格雷厄姆（Mary Graham）'].country, '澳大利亚');
  const maffie = details.find(person => person.name === '詹姆斯·莫菲特');
  assert.equal(maffie.profile.englishName, 'James Maffie');
  assert.equal(maffie.era, '当代');
  assert.deepEqual(maffie.centuries, ['20世纪', '21世纪']);
  assert.doesNotMatch(maffie.bio, /1940|2019|4E认知/);
  assert.match(maffie.profile.life.find(event => event.year === '1988年').body, /Michigan Ann Arbor博士/);
  assert.ok(maffie.profile.bibliography.some(work => work.originalTitle === 'Aztec Philosophy: Understanding a World in Motion'));
  const dodson = details.find(person => person.name === '迈克尔·多德森');
  assert.equal(dodson.profile.englishName, 'Michael (Mick) Dodson');
  assert.equal(dodson.country, '澳大利亚');
  assert.match(dodson.era, /^1950/);
  assert.equal(dodson.portrait, null);
  assert.deepEqual(dodson.centuries, ['20世纪', '21世纪']);
  assert.ok(dodson.profile.life.some(event => event.year === '1993—1998年'));
  assert.ok(dodson.profile.bibliography.some(work => work.originalTitle === 'Bringing Them Home' && work.kind === 'collective-institutional-inquiry-report'));
  for (const person of details.filter(person => person.listingKind === 'review')) {
    assert.equal(person.bio, person.reviewReason);
    assert.equal(person.portrait, null);
    assert.equal(person.era, '身份待核实');
  }
});
test('only real readable books get reading routes; commentary and bibliographies stay separate', () => {
  const heidegger = details.find(person => person.name === '马丁·海德格尔');
  const books = authorBooks(heidegger, catalog);
  assert.deepEqual(books.map(book => book.id), ['c5013f33fe01']);
  assert.equal(bibliography(heidegger, catalog).length, 4);
  assert.equal(catalog.books.find(book => book.id === heidegger.profile.relatedBooks[0]).author, '张汝伦');
  assert.equal(readableBook({ chapterCount: 0, file_type: 'epub' }), false);
  assert.equal(readableBook({ chapterCount: 4, file_type: 'txt' }), false);
  for (const person of details) for (const book of authorBooks(person, catalog)) {
    assert.ok(fs.existsSync(new URL(`book_detail/${book.id}.json`, publicRoot)), book.id);
    if (book.cover) assert.ok(fs.existsSync(new URL(book.cover.replace(/^\//, ''), publicRoot)), book.id);
  }
});
test('every relationship endpoint is present, with context distinguished from historical relationships', () => {
  for (const person of details) {
    const names = new Set([person.name, ...person.profile.people.map(other => other.name)]);
    for (const relation of person.profile.relations) {
      assert.ok(names.has(relation.from), `${person.name}: ${relation.from}`);
      assert.ok(names.has(relation.to), `${person.name}: ${relation.to}`);
      if (relation.type === 'context') {
        if (['editorial-comparison', 'historical-contact'].includes(relation.evidenceKind)) {
          assert.ok(relation.detail);
          assert.doesNotMatch(relation.label, /师承|师生/);
        } else assert.equal(relation.label, '共同思想背景');
      }
    }
  }
});

test('reviewed bibliographies do not silently regain unsupported legacy titles', () => {
  const author = { name: '示例', books: ['旧资料中的待核实书名'], profile: { editorial: { schemaVersion: 1 }, bibliography: [{ title: '有出处的著述' }] } };
  assert.deepEqual(bibliography(author, { books: [] }).map(work => work.title), ['有出处的著述']);
});
test('all author graph groups fit six responsive widths without losing names or overlapping', () => {
  for (const person of details) {
    const others = person.profile.people.filter(other => other.name !== person.name && catalog.people[other.name]?.listingKind !== 'review');
    for (let page = 0; page < Math.ceil(others.length / 12); page++) for (const width of [220, 274, 320, 390, 620, 900]) {
      const people = [{ name: person.name, era: person.era, influence: 100 }, ...others.slice(page * 12, (page + 1) * 12)];
      const names = new Set(people.map(other => other.name));
      const relations = person.profile.relations.filter(relation => names.has(relation.from) && names.has(relation.to));
      const { nodes } = layoutConstellation(people, relations, width, { centerSubject: true });
      assert.equal(nodes.length, names.size);
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        assert.ok(a.x - a.width / 2 >= 0 && a.x + a.width / 2 <= width, `${person.name}: ${a.name}`);
        for (const b of nodes.slice(i + 1)) assert.ok(!(Math.abs(a.x - b.x) < (a.width + b.width) / 2 && a.top < b.top + b.height && a.top + a.height > b.top), `${person.name}: ${a.name}/${b.name}`);
      }
    }
  }
});
