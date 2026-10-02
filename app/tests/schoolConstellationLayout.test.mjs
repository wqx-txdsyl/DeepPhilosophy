import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { layoutConstellation, constellationNodes, constellationRelationKind } from '../src/data/schoolConstellationLayout.js';

function checkLayout(layout, expectedCount) {
  assert.equal(layout.nodes.length, expectedCount, 'every thinker and relationship endpoint must remain visible');
  for (let i = 0; i < layout.nodes.length; i++) {
    const a = layout.nodes[i];
    assert.ok(a.x - a.width / 2 >= 0 && a.x + a.width / 2 <= layout.width, `horizontal bounds: ${a.name}`);
    assert.ok(a.top >= 0 && a.top + a.height <= layout.height, `vertical bounds: ${a.name}`);
    for (const b of layout.nodes.slice(i + 1)) {
      const overlaps = Math.abs(a.x - b.x) < (a.width + b.width) / 2 && a.top < b.top + b.height && a.top + a.height > b.top;
      assert.equal(overlaps, false, `label collision: ${a.name} / ${b.name}`);
    }
  }
}

test('every school stays complete and collision-free from narrow phones to desktops', () => {
  const directory = new URL('../public/schools/data/', import.meta.url);
  const files = fs.readdirSync(directory).filter(name => /^school_.+\.json$/.test(name));
  assert.ok(files.length >= 100);
  for (const file of files) {
    const data = JSON.parse(fs.readFileSync(new URL(file, directory), 'utf8'));
    const expected = constellationNodes(data.thinkers, data.relations).length;
    for (const width of [280, 320, 390, 540, 680, 850]) checkLayout(layoutConstellation(data.thinkers, data.relations, width), expected);
  }
});

test('a single thinker and future dense schools both remain readable', () => {
  checkLayout(layoutConstellation([{ name: '单一节点', era: '公元前1300—前1200年', influence: 10 }], [], 280), 1);
  const thinkers = Array.from({ length: 48 }, (_, index) => ({ name: `长姓名的思想家·${index}`, era: '约公元前3000年至公元前2500年', influence: 10 - index / 10 }));
  const relations = thinkers.slice(1).map(thinker => ({ from: thinkers[0].name, to: thinker.name, type: '影响' }));
  checkLayout(layoutConstellation(thinkers, relations, 320), 48);
  checkLayout(layoutConstellation(thinkers, relations, 780), 48);
});

test('placement is deterministic and never mutates source data', () => {
  const thinkers = [{ name: '师', influence: 10 }, { name: '学生', influence: 8 }];
  const relations = [{ from: '师', to: '学生', type: '师生' }, { from: '学生', to: '相关流派', label: '批判' }];
  const before = JSON.stringify({ thinkers, relations });
  assert.deepEqual(layoutConstellation(thinkers, relations, 700), layoutConstellation(thinkers, relations, 700));
  assert.equal(JSON.stringify({ thinkers, relations }), before);
  assert.equal(constellationNodes(thinkers, relations).find(node => node.name === '相关流派').relatedOnly, true);
  assert.equal(constellationRelationKind({ type: '影响', label: '批判' }), 'criticism');
  assert.equal(constellationRelationKind({ type: '主题关联', label: '主题比较' }), 'context');
});
