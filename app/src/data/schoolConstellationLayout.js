/** Deterministic, label-aware placement. No simulation, randomness, or discarded nodes. */
export function constellationNodes(thinkers = [], relations = []) {
  const byName = new Map();
  thinkers.filter(Boolean).forEach(person => {
    if (person.name && !byName.has(person.name)) byName.set(person.name, { ...person });
  });
  relations.filter(Boolean).forEach(relation => {
    [relation.from, relation.to].filter(Boolean).forEach(name => {
      if (!byName.has(name)) byName.set(name, { name, influence: 4, relatedOnly: true });
    });
  });
  return [...byName.values()];
}

const ANCHORS = [
  [.31, .20], [.57, .38], [.76, .65], [.51, .85], [.87, .19],
  [.14, .56], [.88, .44], [.84, .89], [.29, .85], [.10, .18],
  [.10, .88], [.49, .08], [.47, .64], [.71, .07], [.95, .69], [.29, .48],
];
const collides = (a, b) => Math.abs(a.x - b.x) < (a.width + b.width) / 2 + 16
  && a.top < b.top + b.height + 17 && a.top + a.height + 17 > b.top;

export function layoutConstellation(thinkers = [], relations = [], availableWidth = 700) {
  const width = Math.max(220, Math.round(availableWidth));
  const people = constellationNodes(thinkers, relations);
  const degrees = new Map(people.map(person => [person.name, 0]));
  relations.filter(Boolean).forEach(relation => {
    degrees.set(relation.from, (degrees.get(relation.from) || 0) + 1);
    degrees.set(relation.to, (degrees.get(relation.to) || 0) + 1);
  });
  const ranked = people.map((person, order) => ({ ...person, order,
    priority: (Number(person.influence) || 5) * 8 + (degrees.get(person.name) || 0) * 2,
  })).sort((a, b) => b.priority - a.priority || a.order - b.order);
  const mobile = width < 570;
  const initialHeight = Math.max(mobile ? 300 : 360,
    mobile ? Math.ceil(ranked.length / 2) * 125 + 65 : Math.ceil(ranked.length / Math.max(3, Math.floor(width / 165))) * 115 + 160);
  let height = initialHeight;
  const placed = [];
  ranked.forEach((person, rank) => {
    const markerSize = rank === 0 ? 72 : rank === 1 ? 58 : rank < 4 ? 50 : 12;
    const labelWidth = Math.min(mobile ? Math.max(90, width / 2 - 24) : 168,
      Math.max(mobile ? 104 : 118, [...person.name].length * 14 + 16));
    const lines = Math.max(1, Math.ceil([...person.name].length * 16 / labelWidth));
    const eraWidth = [...String(person.era || '')].reduce((sum, character) => sum + (character.codePointAt(0) > 255 ? 10 : 6), 0);
    const eraLines = Math.ceil(eraWidth / labelWidth);
    const boxHeight = markerSize + 10 + lines * 23 + eraLines * 19 + 4;
    const dimensions = { width: labelWidth, height: boxHeight };
    let ideal;
    if (ranked.length === 1) ideal = { x: width / 2, top: 85 };
    else if (mobile) {
      // Keep the founding figure above the branches; stagger the remaining rows.
      const row = Math.ceil(rank / 2);
      ideal = rank === 0 ? { x: width * .5, top: 32 } : {
        x: width * (rank % 2 ? .24 : .76), top: 38 + row * 130 + (rank % 2 ? 0 : 14),
      };
    } else {
      const anchor = ANCHORS[rank % ANCHORS.length];
      ideal = { x: anchor[0] * width, top: anchor[1] * (initialHeight - 120) + Math.floor(rank / ANCHORS.length) * 100 + 15 };
    }
    const fits = candidate => candidate.x >= labelWidth / 2 + 7
      && candidate.x <= width - labelWidth / 2 - 7 && candidate.top >= 14
      && !placed.some(other => collides(candidate, other));
    let chosen = { ...ideal, ...dimensions };
    if (!fits(chosen)) {
      let best = null;
      let bestScore = Infinity;
      // Search actual free rectangles, rather than relaxing a force-directed graph.
      for (let top = 16; top <= height - boxHeight + 48; top += 16) {
        for (let x = labelWidth / 2 + 8; x <= width - labelWidth / 2 - 8; x += 16) {
          const candidate = { x, top, ...dimensions };
          if (!fits(candidate)) continue;
          const score = Math.hypot((x - ideal.x) * 1.12, top - ideal.top);
          if (score < bestScore) { best = candidate; bestScore = score; }
        }
      }
      chosen = best || { x: Math.max(labelWidth / 2 + 8, Math.min(width - labelWidth / 2 - 8, ideal.x)), top: height + 20, ...dimensions };
    }
    const node = { ...person, ...chosen, markerSize, rank,
      y: chosen.top + markerSize / 2, radius: markerSize / 2 };
    placed.push(node);
    height = Math.max(height, chosen.top + boxHeight + 25);
  });
  return { nodes: placed, width, height };
}

export function constellationRelationKind(relation) {
  const label = `${relation.label || ''} ${relation.type || ''}`;
  if (/主题|比较|关联|参照|对照/.test(label)) return 'context';
  if (/批判|对立|争论|争鸣|分裂|之争|辩论/.test(label)) return 'criticism';
  if (/师|传承|继承|再传|创立|开创|父子/.test(label)) return 'lineage';
  if (/交流|合作|友谊|对话|同门|战友/.test(label)) return 'context';
  return 'influence';
}

export function constellationCurve(from, to, index = 0) {
  if (from.name === to.name) {
    const r = from.radius + 18;
    return `M ${from.x - r} ${from.y} C ${from.x - r * 2} ${from.y - r * 2}, ${from.x + r * 2} ${from.y - r * 2}, ${from.x + r} ${from.y}`;
  }
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const distance = Math.hypot(dx, dy) || 1;
  const x1 = from.x + dx / distance * (from.radius + 7);
  const y1 = from.y + dy / distance * (from.radius + 7);
  const x2 = to.x - dx / distance * (to.radius + 7);
  const y2 = to.y - dy / distance * (to.radius + 7);
  const bend = (index % 2 ? 1 : -1) * Math.min(34, distance * .1);
  return `M ${x1} ${y1} Q ${(x1 + x2) / 2 - dy / distance * bend} ${(y1 + y2) / 2 + dx / distance * bend}, ${x2} ${y2}`;
}
