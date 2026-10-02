import { QUESTIONS, TRADITIONS } from './genealogyTopics.js';

export { QUESTIONS, TRADITIONS };
const TOPICS_BY_SCHOOL = new Map();
for (const question of QUESTIONS) {
  for (const name of question.schools) {
    if (!TOPICS_BY_SCHOOL.has(name)) TOPICS_BY_SCHOOL.set(name, []);
    TOPICS_BY_SCHOOL.get(name).push(question);
  }
}
export const schoolTopics = school => TOPICS_BY_SCHOOL.get(typeof school === 'string' ? school : school.id) || [];

export function centuryYear(century) {
  const match = century.match(/(\d+)世纪/);
  if (!match) return 2000;
  const number = Number(match[1]);
  if (century.startsWith('公元前')) return -number * 100;
  return (number - 1) * 100 + (century.includes('末') ? 75 : century.includes('中') ? 40 : 0);
}

export function schoolPath(school) {
  return `/school/${encodeURIComponent(typeof school === 'string' ? school : school.name)}`;
}

export function filterSchools(schools, { query = '', tradition = 'all', question = null } = {}) {
  const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const topic = QUESTIONS.find(item => item.id === question);
  return schools.filter(school => {
    if (tradition !== 'all' && school.tradition !== tradition) return false;
    if (topic && !topic.schools.includes(school.name)) return false;
    const haystack = [school.name, school.century, school.traditionLabel, school.desc, ...school.thinkers.flatMap(thinker => [thinker.name, thinker.key])].join(' ').toLocaleLowerCase();
    return terms.every(term => haystack.includes(term));
  });
}

export function schoolRelations(school, candidates = []) {
  const thinkers = new Set(school.thinkers.filter(thinker => thinker.influence >= 8).map(thinker => thinker.name));
  const topics = new Set((TOPICS_BY_SCHOOL.get(school.id) || []).map(topic => topic.id));
  return candidates.filter(other => other.id !== school.id).map(other => {
    const sharedThinkers = other.thinkers.filter(thinker => thinker.influence >= 8 && thinkers.has(thinker.name)).map(thinker => thinker.name);
    const sharedTopics = (TOPICS_BY_SCHOOL.get(other.id) || []).filter(topic => topics.has(topic.id));
    return { school: other, sharedThinkers, sharedTopics, score: sharedThinkers.length * 5 + sharedTopics.length };
  }).filter(relation => relation.score > 0).sort((a, b) => b.score - a.score || a.school.order - b.school.order);
}

const CARD_HEIGHT = 210;
function geometry(width) {
  const mobile = width < 560;
  const columns = mobile ? 2 : width < 820 ? 3 : width < 1080 ? 4 : 5;
  const cell = width / columns;
  return { mobile, columns, cell, cardWidth: Math.min(mobile ? 140 : 190, cell - (mobile ? 12 : 32)) };
}

export function riverLayout(schools, width) {
  const { mobile, cell, cardWidth } = geometry(width);
  const columns = mobile ? 2 : width < 760 ? 3 : 4;
  const spacing = width / columns;
  const ordered = [...schools].sort((a, b) => centuryYear(a.century) - centuryYear(b.century) || a.order - b.order);
  const nodes = ordered.map((school, index) => {
    const row = Math.floor(index / columns), offset = index % columns;
    const column = row % 2 ? columns - 1 - offset : offset;
    return { school, x: spacing * (column + .5), y: 48 + row * 304 + (column % 2 ? 35 : 0), width: Math.min(cardWidth, spacing - (mobile ? 12 : 24)), height: CARD_HEIGHT };
  });
  const labels = nodes.filter((node, index) => index === 0 || ordered[index - 1].century !== node.school.century)
    .map(node => ({ text: node.school.century, x: Math.max(0, node.x - node.width / 2), y: node.y - 22 }));
  const points = nodes.map(node => ({ x: node.x, y: node.y + CARD_HEIGHT + 16 }));
  let path = points.length ? `M 0 ${points[0].y + 12}` : '';
  points.forEach((point, index) => {
    const previous = index ? points[index - 1] : { x: 0, y: point.y + 12 };
    const sameRow = index && Math.floor(index / columns) === Math.floor((index - 1) / columns);
    const middle = (point.x + previous.x) / 2;
    path += sameRow || index === 0
      ? ` C ${middle} ${previous.y + 10}, ${middle} ${point.y - 10}, ${point.x} ${point.y}`
      : ` C ${previous.x} ${previous.y + 34}, ${point.x} ${point.y - 42}, ${point.x} ${point.y}`;
  });
  const height = nodes.length ? Math.max(...nodes.map(node => node.y + node.height)) + 70 : 180;
  return { nodes, labels, groups: [], path, width, height, cell };
}

export function constellationLayout(schools, width, question = null) {
  const { mobile, columns, cell, cardWidth } = geometry(width);
  const nodes = [], groups = [];
  let top = 50;
  const partitions = question ? [{ id: 'question', label: question.title, schools }]
    : TRADITIONS.filter(tradition => tradition.id !== 'all').map(tradition => ({ ...tradition, schools: schools.filter(school => school.tradition === tradition.id) })).filter(group => group.schools.length);
  for (const group of partitions) {
    groups.push({ label: group.label, x: 0, y: top - 46 });
    let index = 0, row = 0;
    while (index < group.schools.length) {
      const capacity = mobile ? columns : Math.max(2, columns - (row % 3 === 1 ? 1 : 0));
      const count = Math.min(capacity, group.schools.length - index);
      const start = (width - count * cell) / 2;
      for (let column = 0; column < count; column++) {
        const school = group.schools[index++];
        const jitter = Math.sin((school.order + 1) * 2.37) * (mobile ? 3 : 9);
        nodes.push({ school, x: start + (column + .5) * cell + jitter, y: top + row * 252 + Math.cos((school.order + 1) * 1.31) * 12, width: cardWidth * (school.tier === 'A' ? 1 : school.tier === 'B' ? .9 : .82), height: CARD_HEIGHT });
      }
      row++;
    }
    top += row * 252 + 62;
  }
  return { nodes, groups, labels: [], path: '', width, height: nodes.length ? Math.max(...nodes.map(node => node.y + node.height)) + 52 : 180 };
}

export function visibleEdges(layout, focusId, question) {
  const byId = new Map(layout.nodes.map(node => [node.school.id, node]));
  const seen = new Set(), edges = [];
  const sources = focusId && byId.has(focusId) ? [byId.get(focusId)] : layout.nodes;
  for (const node of sources) {
    const candidates = layout.nodes.filter(other => other.school.id !== node.school.id && (focusId || question || other.school.tradition === node.school.tradition)).map(other => other.school);
    for (const relation of schoolRelations(node.school, candidates).slice(0, focusId ? 7 : 1)) {
      const other = byId.get(relation.school.id);
      const id = [node.school.id, other.school.id].sort().join('::');
      if (seen.has(id)) continue;
      seen.add(id);
      const direction = other.x > node.x ? 1 : -1;
      const start = { x: node.x + direction * (node.width / 2 + 5), y: node.y + 70 };
      const end = { x: other.x - direction * (other.width / 2 + 5), y: other.y + 70 };
      const bend = Math.min(70, Math.abs(end.y - start.y) / 5 + 18);
      const path = `M ${start.x} ${start.y} C ${start.x + direction * bend} ${start.y}, ${end.x - direction * bend} ${end.y}, ${end.x} ${end.y}`;
      edges.push({ id, from: node.school.id, to: other.school.id, path, label: relation.sharedThinkers.length ? relation.sharedThinkers.join('、') : relation.sharedTopics[0]?.title, type: relation.sharedThinkers.length ? 'thinker' : 'topic' });
    }
  }
  return edges;
}
