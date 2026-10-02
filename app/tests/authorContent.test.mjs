import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { AUTHOR_KINDS, authorBooks, authorFile, bibliography, canonicalAuthor, loadAuthorPage, normalizeAuthor, readableBook } from '../src/data/authorContent.js';
import { OSS_BASE, staticImageSources } from '../src/data/ossUrls.js';
import { layoutConstellation } from '../src/data/schoolConstellationLayout.js';
import { buildSchoolReferences } from '../src/data/schoolContent.js';

const publicRoot = new URL('../public/', import.meta.url);
const read = path => JSON.parse(fs.readFileSync(new URL(path, publicRoot), 'utf8'));
const catalog = read('philosopher/catalog.json');
const roster = read('philosophers.json');
const schools = read('schools/catalog.json').schools;
const details = Object.keys(roster).map(name => normalizeAuthor(read(decodeURIComponent(authorFile(name).slice(1)))));

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
  assert.equal(details.filter(person => person.listingKind === 'thinker').length, 652);
  for (const person of details) {
    assert.ok(AUTHOR_KINDS[person.listingKind]);
    assert.equal(person.name, roster[person.name].name);
    assert.ok(person.profile.overview.length > 0, person.name);
    if (person.portrait) assert.ok(fs.existsSync(new URL(person.portrait.slice(1), publicRoot)), person.name);
    for (const school of person.profile.schoolLinks) assert.ok(fs.existsSync(new URL(`schools/data/${schools.find(item => item.name === school.name)?.detailFile}`, publicRoot)), school.name);
  }
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
  assert.equal(roster['维雷杜·维雷杜'].era, '1931–2022');
  assert.equal(roster['卡蒂尼'].era, '1879–1904');
  assert.equal(roster['玛丽·格雷厄姆（Mary Graham）'].country, '澳大利亚');
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
      if (relation.type === 'context') assert.equal(relation.label, '共同思想背景');
    }
  }
});
test('all author graph groups fit six responsive widths without losing names or overlapping', () => {
  for (const person of details) {
    const others = person.profile.people.filter(other => other.name !== person.name && catalog.people[other.name] && catalog.people[other.name].listingKind !== 'review');
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
