import { DISCIPLINES } from './moreContent';

const metadata = {
  "philosophy": {
    "description": "从代表流派开始，沿着时间、思想关联与问题，继续探索哲学。",
    "ready": true,
    "color": "#B8956A"
  },
  "mythology": {
    "description": "神系、创世叙事与反复出现的文化母题。",
    "ready": true,
    "color": "#A86B3C"
  },
  "religion": {
    "description": "经典、实践与不同信仰传统的思想脉络。",
    "ready": true,
    "color": "#6B3FA0"
  },
  "literature": {
    "description": "诗歌、戏剧与小说中的经验和思想。",
    "ready": false,
    "color": "#8B6573"
  },
  "psychology": {
    "description": "意识、行为与理解心智的不同路径。",
    "ready": false,
    "color": "#3A5A7C"
  },
  "sociology": {
    "description": "个人、群体与社会秩序的形成。",
    "ready": false,
    "color": "#4A7A4A"
  },
  "history": {
    "description": "历史如何被记录、解释与重写。",
    "ready": false,
    "color": "#9B3A3A"
  },
  "politics": {
    "description": "权力、制度与共同生活的安排。",
    "ready": false,
    "color": "#3A7B8C"
  }
};
const philosophy = {
  "code": "Ph",
  "id": "philosophy",
  "name": "哲学",
  "en": "Philosophy",
  "color": "#B8956A",
  "description": "从代表流派开始，沿着时间、思想关联与问题，继续探索哲学。",
  "ready": true,
  "topics": [
    {
      "id": "儒家",
      "name": "儒家",
      "note": "仁、礼与日常伦理",
      "path": "/school/%E5%84%92%E5%AE%B6",
      "image": "/schools/儒家.webp"
    },
    {
      "id": "道家",
      "name": "道家",
      "note": "自然、变化与无为",
      "path": "/school/%E9%81%93%E5%AE%B6",
      "image": "/schools/道家.webp"
    },
    {
      "id": "古希腊哲学",
      "name": "古希腊哲学",
      "note": "理性、城邦与存在",
      "path": "/school/%E5%8F%A4%E5%B8%8C%E8%85%8A%E5%93%B2%E5%AD%A6",
      "image": "/schools/古希腊哲学.webp"
    },
    {
      "id": "德国古典哲学",
      "name": "德国古典哲学",
      "note": "批判、体系与辩证法",
      "path": "/school/%E5%BE%B7%E5%9B%BD%E5%8F%A4%E5%85%B8%E5%93%B2%E5%AD%A6",
      "image": "/schools/德国古典哲学.webp"
    },
    {
      "id": "现象学",
      "name": "现象学",
      "note": "回到经验与事物本身",
      "path": "/school/%E7%8E%B0%E8%B1%A1%E5%AD%A6",
      "image": "/schools/现象学.webp"
    },
    {
      "id": "存在主义",
      "name": "存在主义",
      "note": "自由、选择与责任",
      "path": "/school/%E5%AD%98%E5%9C%A8%E4%B8%BB%E4%B9%89",
      "image": "/schools/存在主义.webp"
    }
  ]
};

export const MORE_FIELDS = [philosophy, ...DISCIPLINES.map(d => ({
  ...d, ...metadata[d.id],
  topics: (d.topics?.filter(t => !t.hidden) || d.seeds.map((name, i) => ({ id: String(i), name })))
    .map(t => ({ ...t, image: t.heroImage, note: t.note?.replace('拉美 explosion', '拉美文学浪潮') })),
}))].map(f => ({ ...f, image: `/more/discipline-art-v1/${f.code}.webp` }));

export function moreAlbumPath(discipline, topic) {
  const params = new URLSearchParams({ discipline, album: 'open' });
  if (topic) params.set('topic', topic);
  return `/more?${params}`;
}
