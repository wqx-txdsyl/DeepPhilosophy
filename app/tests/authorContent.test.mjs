import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { AUTHOR_KINDS, authorBooks, authorFile, authorPortraitImage, authorSectionSources, bibliography, canonicalAuthor, loadAuthorPage, normalizeAuthor, readableBook } from '../src/data/authorContent.js';
import { OSS_BASE, staticImageSources } from '../src/data/ossUrls.js';
import { layoutConstellation } from '../src/data/schoolConstellationLayout.js';
import { buildSchoolReferences, normalizeSchool } from '../src/data/schoolContent.js';
import { bookAuthors } from '../src/data/bookDetail.js';
import { isRetiredAuthor } from '../src/data/retiredAuthors.js';

const publicRoot = new URL('../public/', import.meta.url);
const read = path => JSON.parse(fs.readFileSync(new URL(path, publicRoot), 'utf8'));
const catalog = read('philosopher/catalog.json');
const roster = read('philosophers.json');
const schools = read('schools/catalog.json').schools;
const retirement = JSON.parse(fs.readFileSync(new URL('../../scripts/author-curation/retirement-2026-10-21.json', import.meta.url), 'utf8'));
const details = Object.keys(roster).map(name => normalizeAuthor(read(decodeURIComponent(authorFile(name).slice(1)))));

test('verified replacement photos refresh both CDN and fallback without changing the stored public path', () => {
  const person = roster['大卫·艾布拉姆'];
  const image = authorPortraitImage(person);
  const revision = person.portraitReview.observedSha256.slice(0, 12);
  assert.equal(person.portrait, '/philosopher/大卫·艾布拉姆.webp');
  assert.equal(image, `${person.portrait}?v=${revision}`);
  const sources = staticImageSources(image, 192);
  assert.equal(new URL(sources.primary).searchParams.get('v'), revision);
  assert.equal(sources.fallback, image);
  assert.equal(authorPortraitImage(roster['亨佩尔']), null);
  assert.equal(authorPortraitImage({ portrait: person.portrait }), person.portrait);
});

test('school references honor withdrawn portraits and all shared image routes keep the current revision', () => {
  const references = buildSchoolReferences({ philosophers: read('schools/catalog.json').philosophers });
  assert.equal(references.findPerson('亨佩尔').portrait, null);
  const person = references.findPerson('大卫·艾布拉姆');
  const revision = roster[person.name].portraitReview.observedSha256.slice(0, 12);
  assert.equal(new URL(staticImageSources(person.portrait).primary).searchParams.get('v'), revision);
  const future = `${person.portrait}?v=next-reviewed-image`;
  assert.equal(new URL(staticImageSources(future).primary).searchParams.get('v'), 'next-reviewed-image');
  const absolute = `${OSS_BASE}${future}&x-oss-process=image/resize,w_50`;
  const resized = new URL(staticImageSources(absolute, 192).primary);
  assert.equal(resized.searchParams.get('v'), 'next-reviewed-image');
  assert.equal(resized.searchParams.getAll('x-oss-process').length, 1);
  assert.ok(resized.searchParams.get('x-oss-process').includes('w_192'));
});

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
    assert.equal(decodeURIComponent(new URL(thumbnail.fallback, 'https://deepphilosophy.top').pathname), person.portrait);
  }
  assert.deepEqual(staticImageSources('https://example.com/photo.jpg'), { primary: 'https://example.com/photo.jpg', fallback: 'https://example.com/photo.jpg' });
});

test('every canonical entry has its own matching detail, category and existing images', () => {
  assert.equal(details.length, 644);
  assert.deepEqual(Object.keys(catalog.people).sort(), Object.keys(roster).sort());
  assert.equal(details.filter(person => person.listingKind === 'thinker').length, details.length);
  for (const person of details) {
    assert.ok(AUTHOR_KINDS[person.listingKind]);
    assert.equal(person.name, roster[person.name].name);
    assert.ok(person.profile.overview.length > 0, person.name);
    if (person.portrait) assert.ok(fs.existsSync(new URL(person.portrait.slice(1), publicRoot)), person.name);
    for (const school of person.profile.schoolLinks) assert.ok(fs.existsSync(new URL(`schools/data/${schools.find(item => item.name === school.name)?.detailFile}`, publicRoot)), school.name);
  }
});
test('non-individual texts and mythological names are retired instead of relabelled as philosophers', () => {
  const names = Object.entries(retirement.retired).filter(([, item]) => item.previousKind === 'tradition').map(([name]) => name);
  assert.equal(names.length, 26);
  for (const name of names) {
    assert.ok(!roster[name]);
    assert.ok(!catalog.people[name]);
    assert.ok(!fs.existsSync(new URL(decodeURIComponent(authorFile(name).slice(1)), publicRoot)), name);
  }
});

test('Hipparchia and Hypatia resolve to distinct independently restored people', async () => {
  assert.ok(roster['希帕提娅']);
  assert.ok(roster['希帕基娅']);
  assert.equal(catalog.aliases['希帕基娅'], undefined);
  assert.notEqual(roster['希帕提娅'].era, roster['希帕基娅'].era);
  assert.ok(details.find(person => person.name === '希帕基娅').profile.sources.some(source => source.url.includes('iep.utm.edu/hipparch/')));
  const result = await loadAuthorPage('希帕基娅', undefined, { catalogLoader: async () => catalog, jsonLoader: async () => read(decodeURIComponent(authorFile('希帕基娅').slice(1))) });
  assert.equal(result.raw.name, '希帕基娅');
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
  assert.equal(details.filter(item => item.listingKind === 'review').length, 0);
});
test('background artists are no longer philosopher records and retained philosophical authors have explicit sources', () => {
  assert.ok(!roster['伊莲·拉塞尔']);
  assert.equal(retirement.retired['伊莲·拉塞尔'].previousKind, 'context');
  for (const name of ['李斯', '老普林尼']) {
    assert.equal(roster[name].listingKind, 'thinker');
    assert.ok(roster[name].sources.some(source => source.accessScope === 'partial-text'));
    assert.equal(roster[name].eligibilityReview.completeInformationReview, false);
  }
});

test('removing a joint-person node preserves the Revel and Ricard book without a dead author link', () => {
  const name = '让-弗朗索瓦何维勒/马修理查德';
  assert.ok(!roster[name]);
  const book = catalog.books.find(book => book.id === '077532e4515e');
  assert.ok(book);
  assert.ok(bookAuthors(book.author, catalog).every(author => !author.path || catalog.people[author.canonical]));
  assert.ok(fs.existsSync(new URL(`book_detail/${book.id}.json`, publicRoot)));
});

test('removing a textbook author group preserves its readable book and records both distinct author gaps', () => {
  assert.ok(!roster['撒穆尔·伊诺克·斯通普夫/詹姆斯·菲泽']);
  const book = catalog.books.find(book => book.id === '4a4a200536bd');
  assert.ok(readableBook(book));
  assert.ok(bookAuthors(book.author, catalog).every(author => !author.path || catalog.people[author.canonical]));
  assert.ok(retirement.missingDistinctProfiles.some(name => name.includes('Stumpf')));
  assert.ok(retirement.missingDistinctProfiles.some(name => name.includes('Fieser')));
});

test('retired identities cannot reappear through stale details, school graphs or aliases', async () => {
  const names = Object.entries(retirement.retired).filter(([, item]) => item.previousKind === 'review').map(([name]) => name);
  assert.equal(names.length, 36);
  for (const name of names) {
    assert.ok(!roster[name]);
    assert.ok(isRetiredAuthor(name));
    await assert.rejects(loadAuthorPage(name, undefined, { jsonLoader: () => { throw new Error('stale detail fetched'); } }), { code: 'AUTHOR_RETIRED' });
    const school = normalizeSchool({ thinkers: [{ name }, { name: '孔子' }], relations: [{ from: name, to: '孔子' }] });
    assert.deepEqual(school.thinkers.map(item => item.name), ['孔子']);
    assert.deepEqual(school.relations, []);
  }
  for (const target of Object.values(catalog.aliases)) assert.ok(roster[target]);
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
test('only reference-checked authorized paper portraits replace withdrawn AI fillers', () => {
  const audit = read('philosopher/portrait-audit.json').records;
  for (const person of Object.values(roster)) {
    const review = person.portraitReview;
    if (review?.imageType !== 'ai-generated-illustration') continue;
    if (review.allowAsPortrait !== true) {
      assert.equal(person.portrait, null, person.name);
      continue;
    }
    assert.equal(review.style, 'graphite-pencil-paper-v1', person.name);
    assert.equal(review.authorizedRound, 'pencil-20261024', person.name);
    assert.equal(review.referenceVerified, true, person.name);
    assert.equal(review.background, 'opaque-warm-paper', person.name);
    if (review.identityBasis === 'traditional-depiction') assert.equal(review.faceTreatment, 'lifelike-human-reconstruction', person.name);
    assert.match(review.referenceSha256, /^[a-f0-9]{64}$/, person.name);
    assert.equal(review.sourcePage, undefined);
    const digest = createHash('sha256').update(fs.readFileSync(new URL(person.portrait.slice(1), publicRoot))).digest('hex');
    assert.equal(digest, review.observedSha256, person.name);
    assert.deepEqual(audit[person.name], review);
    assert.deepEqual(catalog.people[person.name].portraitReview, review);
    assert.deepEqual(details.find(item => item.name === person.name).portraitReview, review);
    assert.equal(read('schools/catalog.json').philosophers.find(item => item.name === person.name).portrait, person.portrait);
  }
  const person = roster['孔子'];
  assert.equal(person.portraitReview.identityBasis, 'traditional-depiction');
  assert.equal(person.portraitReview.style, 'graphite-pencil-paper-v1');
  assert.notEqual(person.portraitReview.observedSha256, '9a403bc4fce3f09a4809eb6ce5e97656b379ddb76a43d552b148a7897bfdbe88');
});
test('corrected identities do not inherit unrelated portraits or fabricated biographies', () => {
  assert.equal(roster['丹尼斯·林德利'].era, '1923—2013');
  assert.equal(roster['理查德·杰弗里'].era, '1926—2002');
  assert.equal(roster['理查德·杰弗里'].portrait, null, '错配图不得恢复');
  assert.equal(roster['理查德·杰弗里'].portraitReview.allowAsPortrait, false);
  const lindley = roster['丹尼斯·林德利'];
  assert.equal(lindley.portraitReview.authorizedRound, 'pencil-20261024');
  assert.equal(lindley.portraitReview.referenceSha256, '72e9002b6526a85403ed544d667855e8c9bb0319072b97bbfc0bce95e6784f21'); // Named Washington course photograph, not his namesake or Kendall.
  assert.equal(lindley.portrait, '/philosopher/丹尼斯·林德利.webp');
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
