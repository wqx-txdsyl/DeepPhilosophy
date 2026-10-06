/**
 * 神祇图片抓取 — zh.wikipedia pageimages API，en.wikipedia 兜底
 * 输出: public/more/deities/{id}.jpg + deityIcons.js 映射
 */
import { mkdirSync, writeFileSync, existsSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..'); // app 根目录
const OUT = join(ROOT, 'public/more/deities');
mkdirSync(OUT, { recursive: true });

const TITLES = {
  pangu: ['盘古'], nuwa: ['女娲'], fuxi: ['伏羲'], zhulong: ['烛龙'], dijiang: ['帝江'],
  dijun: ['帝俊'], huangdi: ['黄帝'], yandi: ['炎帝'], zhuanxu: ['颛顼'], diku: ['帝喾'],
  yao: ['尧'], shun: ['舜'], shaohao: ['少昊'],
  xihe: ['羲和'], changxi: ['常羲'], wangshu: ['望舒'], feilian: ['飞廉'], pingyi: ['屏翳'],
  fenglong: ['丰隆'], leigong: ['雷公'], dianmu: ['电母'], zhinv: ['织女'], qianniu: ['牛郎'], change: ['嫦娥'],
  xiwangmu: ['西王母'], luwu: ['陆吾'], kaiming: ['开明兽'], yingzhao: ['英招'], shenshu: ['神荼'], yulei: ['郁垒'],
  bingyi: ['河伯', '冯夷'], mifei: ['洛神'], xiangjun: ['湘君'], xiangfuren: ['湘夫人'], yaoji: ['巫山神女'], yuhao: ['禺猇'],
  goumang: ['句芒'], zhurong: ['祝融'], rushou: ['蓐收'], gonggong: ['共工'], houtu: ['后土'], xuanming: ['玄冥'],
  suirens: ['燧人氏'], yuchaos: ['有巢氏'], shennong: ['神农'], cangjie: ['仓颉'], leizu: ['嫘祖'],
  houji: ['后稷'], gaoyao: ['皋陶'], boyi: ['伯益'], pengzu: ['彭祖'], wuxian: ['巫咸'], linjun: ['廪君'], nvxiu: ['女修'],
  houyi: ['后羿'], gun: ['鲧'], dayu: ['大禹', '禹'], kuafu: ['夸父'], xingtian: ['刑天'], jingwei: ['精卫'],
  chiyou: ['蚩尤'], shangtang: ['商汤', '成汤'], nuba: ['女魃', '旱魃'],
  taotie: ['饕餮'], qiongqi: ['穷奇'], taowu: ['梼杌'], xiangliu: ['相柳'], jiuying: ['九婴'], zaochi: ['凿齿'],
  yayu: ['猰貐', '窫窳'], xiushe: ['巴蛇'], dafeng: ['大风'], fengxi: ['封豨'],
  yinglong: ['应龙'], jiuweihu: ['九尾狐'], baize: ['白泽'], bifang: ['毕方'], kunpeng: ['鲲鹏'],
  fenghuang: ['凤凰'], sixiang: ['四象'], chongming: ['重明鸟'], xiezhi: ['獬豸'], xuangui: ['旋龟'],
  xingxing: ['狌狌'], tianwu: ['天吴'],
  taishanjun: ['泰山府君'], tubo: ['土伯'], fengdu: ['酆都大帝'], yanluo: ['阎罗'], mengpo: ['孟婆'],
  yuhuang: ['玉皇大帝'], nezha: ['哪吒'], erlangshen: ['二郎神'], jiangziya: ['姜子牙'], sunwukong: ['孙悟空'],
  zhongkui: ['钟馗'], magu: ['麻姑'], baxian: ['八仙'], mazu: ['妈祖'],
};

const EN_FALLBACK = {
  nuwa: 'Nüwa', fuxi: 'Fuxi', huangdi: 'Yellow Emperor', yandi: 'Yan Emperor', zhuanxu: 'Zhuanxu',
  diku: 'Emperor Ku', yao: 'Emperor Yao', shun: 'Emperor Shun', change: "Chang'e", xiwangmu: 'Queen Mother of the West',
  mifei: 'Xi Shi', houyi: 'Houyi', dayu: 'Yu the Great', jingwei: 'Jingwei', chiyou: 'Chiyou',
  kuafu: 'Kuafu', xingtian: 'Xingtian', nuba: 'Nuba', taotie: 'Taotie', yinglong: 'Yinglong',
  jiuweihu: 'Nine-tailed fox', fenghuang: 'Fenghuang', sixiang: 'Four Symbols', xiezhi: 'Xiezhi',
  yuhuang: 'Jade Emperor', nezha: 'Nezha', erlangshen: 'Erlang Shen', jiangziya: 'Jiang Ziya',
  sunwukong: 'Sun Wukong', zhongkui: 'Zhong Kui', magu: 'Magu', baxian: 'Eight Immortals', mazu: 'Mazu',
  zhinv: 'Weaver Girl', qianniu: 'Niulang', shennong: 'Shennong', cangjie: 'Cangjie', leizu: 'Leizu',
  houji: 'Houji', gonggong: 'Gonggong', zhurong: 'Zhurong', kunpeng: 'Peng (mythology)',
  baize: 'Bai Ze', mengpo: 'Meng Po', yanluo: 'Yama',
  zhulong: 'Zhulong', dijun: 'Emperor Jun', changxi: 'Changxi', wangshu: 'Wangshu', feilian: 'Feilian',
  gun: 'Gun (Chinese mythology)', bifang: 'Bifang', xingxing: 'Xingxing', xiangliu: 'Xiangliu',
};

/* Commons 站内文件搜索兜底（冷门神祇） */
const COMMONS_FALLBACK = {
  zhulong: ['Zhulong', '烛龙'], dijun: ['Dijun', 'Di Jun'], changxi: ['Changxi'], wangshu: ['Wangshu moon'],
  pingyi: ['Pingyi rain', '雨师'], fenglong: ['Fenglong'], luwu: ['Luwu', '陆吾'], kaiming: ['Kaiming beast', '开明兽'],
  yingzhao: ['Yingzhao', '英招'], yulei: ['Yulei', '神荼郁垒'], yuhao: ['Yuhai', '禺号'],
  xuanming: ['Xuanming', '玄冥'], wuxian: ['Wu Xian', '巫咸'], linjun: ['Linjun', '廪君'], nvxiu: ['Nvxiu'],
  gun: ['Gun Yu the Great', '鲧'], jiuying: ['Jiuying', '九婴'], zaochi: ['Zaochi', '凿齿'],
  yayu: ['Yayu', '窫窳'], xiushe: ['Bashe', '巴蛇'], dafeng: ['Dafeng bird'], fengxi: ['Fengxi', '封豨'],
  bifang: ['Bifang', '毕方'], chongming: ['Chongming bird', '重明鸟'], xuangui: ['Xuangui', '旋龟'],
  xingxing: ['Xingxing', '狌狌'], tubo: ['Tubo', '土伯'],
};

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function fetchRetry(url, tries = 5) {
  for (let i = 0; i < tries; i++) {
    const resp = await fetch(url, { headers: { 'User-Agent': 'DeepPhilosophy-dev/1.0 (local dev; contact: txdsyl)' } });
    if (resp.ok) return resp;
    if (resp.status === 429 || resp.status === 503) {
      const wait = Number(resp.headers.get('retry-after')) * 1000 || 45000;
      process.stdout.write(`  [限流 ${resp.status}，等待 ${Math.round(wait / 1000)}s]\n`);
      await sleep(wait);
      continue;
    }
    return resp;
  }
  return null;
}

async function thumb(lang, title) {
  const url = `https://${lang}.wikipedia.org/w/api.php?action=query&format=json&redirects=1&prop=pageimages&piprop=thumbnail&pithumbsize=640&titles=${encodeURIComponent(title)}`;
  const resp = await fetchRetry(url);
  if (!resp || !resp.ok) return null;
  const json = await resp.json();
  const pages = json.query?.pages || {};
  for (const p of Object.values(pages)) {
    if (p.thumbnail?.source) return p.thumbnail.source;
  }
  return null;
}

async function download(url, file) {
  const resp = await fetchRetry(url);
  if (!resp || !resp.ok) return false;
  const buf = Buffer.from(await resp.arrayBuffer());
  if (buf.length < 3000) return false; // 过小视为无效
  writeFileSync(file, buf);
  return true;
}

async function commonsThumb(term) {
  const url = `https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=3&gsrsearch=${encodeURIComponent(term)}&prop=imageinfo&iiprop=url&iiurlwidth=640`;
  const resp = await fetchRetry(url);
  if (!resp || !resp.ok) return null;
  const json = await resp.json();
  const pages = Object.values(json.query?.pages || {});
  for (const p of pages) {
    const info = p.imageinfo?.[0];
    if (!info) continue;
    const ext = (info.url || '').split('.').pop().toLowerCase();
    if (!['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) continue;
    if (info.thumburl) return info.thumburl;
  }
  return null;
}

const found = {}, failed = [];
for (const [id, titles] of Object.entries(TITLES)) {
  const file = `${OUT}/${id}.jpg`;
  if (existsSync(file) && statSync(file).size > 3000) { found[id] = `/more/deities/${id}.jpg`; continue; }
  let done = false;
  for (const t of titles) {
    const src = await thumb('zh', t).catch(() => null);
    if (src && await download(src, file)) { done = true; break; }
    await sleep(120);
  }
  if (!done && EN_FALLBACK[id]) {
    const url = await thumb('en', EN_FALLBACK[id]).catch(() => null);
    if (url && await download(url, file)) done = true;
  }
  if (!done && COMMONS_FALLBACK[id]) {
    for (const term of COMMONS_FALLBACK[id]) {
      const url = await commonsThumb(term).catch(() => null);
      if (url && await download(url, file)) { done = true; break; }
      await sleep(300);
    }
  }
  if (done) found[id] = `/more/deities/${id}.jpg`; else failed.push(id);
  process.stdout.write(`${done ? '✓' : '✗'} ${id}\n`);
  await sleep(400);
}

writeFileSync(join(ROOT, 'src/data/moreTopics/chineseMythology/deityIcons.js'),
  `/**
 * 神祇图片映射 — 自动爬取（zh/en Wikipedia pageimages，公共领域艺术品/塑像为主）
 * 生产环境上线前需转存 OSS 并替换路径
 */
export const DEITY_ICONS = ${JSON.stringify(found, null, 2)};
`);
console.log(`\n完成: ${Object.keys(found).length} 成功, ${failed.length} 失败`);
if (failed.length) console.log('失败:', failed.join(', '));
