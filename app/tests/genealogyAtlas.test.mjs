import test, { mock } from 'node:test';
import { loadGenealogyCatalog } from '../src/data/genealogyCatalog.js';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { QUESTIONS, centuryYear, schoolPath, filterSchools, riverLayout, constellationLayout, schoolRelations, visibleEdges } from '../src/data/genealogyAtlas.js';

const publicRoot = new URL('../public/', import.meta.url);
const SCHOOLS = JSON.parse(fs.readFileSync(new URL('gene/atlas.json', publicRoot), 'utf8'));
const filterCatalog = options => filterSchools(SCHOOLS, options);
test('every existing school has its original artwork and a working detail mapping', () => {
  assert.equal(SCHOOLS.length, 111);
  assert.equal(new Set(SCHOOLS.map(school => school.id)).size, 111);
  const detailSource = fs.readFileSync(new URL('../src/pages/SchoolDetailPage.jsx', import.meta.url), 'utf8');
  for (const school of SCHOOLS) {
    assert.ok(fs.existsSync(new URL(school.image.slice(1), publicRoot)), school.name);
    assert.ok(fs.existsSync(new URL(`schools/data/${school.detailFile}`, publicRoot)), school.name);
    assert.ok(detailSource.includes(`'${school.name}':{_json:'${school.detailFile}'`), school.name);
    assert.equal(decodeURIComponent(schoolPath(school).slice('/school/'.length)), school.name);
    const detail = JSON.parse(fs.readFileSync(new URL(`schools/data/${school.detailFile}`, publicRoot), 'utf8'));
    assert.deepEqual(school.thinkers, (detail.thinkers || []).map(thinker => ({ name: thinker.name, key: thinker.key || '', influence: Number(thinker.influence) || 0 })).filter(thinker => thinker.name), school.name);
  }
});
test('28 questions have valid results and cover the complete catalog', () => {
  assert.equal(QUESTIONS.length, 28);
  for (const question of QUESTIONS) {
    assert.ok(filterCatalog({ question: question.id }).length > 0, question.title);
    assert.ok(question.schools.every(name => SCHOOLS.some(school => school.name === name)), question.title);
  }
  assert.ok(SCHOOLS.every(school => QUESTIONS.some(question => question.schools.includes(school.name))));
});
test('search includes thinkers and filters are combined without dropping matches', () => {
  assert.ok(filterCatalog({ query: '胡塞尔' }).some(school => school.name === '现象学'));
  assert.ok(filterCatalog({ query: '儒家', tradition: 'china' }).length >= 2);
  assert.equal(filterCatalog({ query: '不存在的流派名' }).length, 0);
  assert.ok(filterCatalog({ tradition: 'indigenous' }).every(school => school.tradition === 'indigenous'));
});
test('chronology orders BCE and early/mid/late centuries consistently', () => {
  assert.ok(centuryYear('公元前30世纪') < centuryYear('公元前6世纪'));
  assert.ok(centuryYear('公元前1世纪') < centuryYear('3世纪'));
  assert.ok(centuryYear('20世纪初') < centuryYear('20世纪中'));
  assert.ok(centuryYear('20世纪中') < centuryYear('20世纪末'));
  const layout = riverLayout(SCHOOLS, 1000);
  assert.ok(layout.nodes.every((node, index) => !index || centuryYear(node.school.century) >= centuryYear(layout.nodes[index - 1].school.century)));
  assert.equal((layout.path.match(/M /g) || []).length, 1, 'one continuous river');
});
function assertGeometry(layout) {
  assert.equal(layout.nodes.length, 111);
  for (const a of layout.nodes) {
    assert.ok(a.x - a.width / 2 >= 0, a.school.name);
    assert.ok(a.x + a.width / 2 <= layout.width, a.school.name);
    assert.ok(a.y >= 0 && a.y + a.height <= layout.height, a.school.name);
    for (const b of layout.nodes) {
      if (a === b) continue;
      const overlapX = Math.abs(a.x - b.x) < (a.width + b.width) / 2;
      const overlapY = Math.min(a.y + a.height, b.y + b.height) > Math.max(a.y, b.y);
      assert.ok(!(overlapX && overlapY), `${a.school.name} overlaps ${b.school.name}`);
    }
  }
}
test('all nodes stay within bounds and do not overlap at mobile and desktop widths', () => {
  for (const width of [240, 288, 360, 640, 900, 1200]) {
    assertGeometry(riverLayout(SCHOOLS, width));
    const layout = constellationLayout(SCHOOLS, width);
    assertGeometry(layout);
    assert.deepEqual(layout, constellationLayout(SCHOOLS, width));
  }
});
test('association labels distinguish shared thinkers from shared questions', () => {
  const school = SCHOOLS.find(school => school.name === '现象学');
  const relations = schoolRelations(school, SCHOOLS);
  assert.ok(relations.some(relation => relation.school.name === '存在主义' && relation.sharedThinkers.includes('海德格尔')));
  const layout = constellationLayout(SCHOOLS, 1000);
  const edges = visibleEdges(layout, school.id, null);
  assert.ok(edges.length > 0 && edges.length <= 7);
  assert.ok(edges.every(edge => edge.from === school.id || edge.to === school.id));
  assert.ok(edges.every(edge => edge.label && ['thinker', 'topic'].includes(edge.type)));
});


test('invalid CDN responses fall back to the canonical public JSON', async () => {
  const calls = [];
  const fetchMock = mock.method(globalThis, 'fetch', async url => {
    calls.push(url);
    return calls.length === 1 ? new Response('<html>fallback</html>', { status: 200 }) : new Response(JSON.stringify(SCHOOLS), { status: 200 });
  });
  try {
    assert.equal((await loadGenealogyCatalog()).length, 111);
    assert.equal(calls.length, 2);
    assert.equal(calls[1], '/gene/atlas.json');
  } finally { fetchMock.mock.restore(); }
});

test('aborted loads do not start another fallback request', async () => {
  const controller = new AbortController();
  controller.abort();
  const fetchMock = mock.method(globalThis, 'fetch', async () => { throw new DOMException('Aborted', 'AbortError'); });
  try {
    await assert.rejects(loadGenealogyCatalog(controller.signal), { name: 'AbortError' });
    assert.equal(fetchMock.mock.callCount(), 1);
  } finally { fetchMock.mock.restore(); }
});
