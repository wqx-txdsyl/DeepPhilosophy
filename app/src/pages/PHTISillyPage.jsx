/**
 * PHTI 沙雕版 —— 50题 → 16种沙雕哲学家 → AI毒舌锐评
 * 人格称号严格按 PHTI.csv
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';
import sillyQuestions from '../data/phti_silly_questions.json';

// 16 哲学家在 4 维度空间中的坐标 (R/E, S/E, E/P, C/I) 归一化到 -10..10
const PHILOSOPHER_MAP = {
  'PLA': { name: '柏拉图的洞穴保安', title: '🔦 洞穴保安', desc: '天天盯着一墙影子做报表，坚信影子就是真理，偶尔回头看一眼太阳，又默默转回去——怕光，更怕换工作。', dims: [8, 2, 9, 5] },
  'DES': { name: '笛卡尔的冥想僵尸', title: '🧟 冥想僵尸', desc: '"我思故我在"……但我不想思，只想躺。每天醒来先怀疑自己是不是活在梦里，然后心安理得继续睡。', dims: [9, 1, 4, -6] },
  'HEG': { name: '黑格尔的螺旋滑梯', title: '🎢 螺旋滑梯', desc: '坚信万物都在上升，结果每次滑到底都告诉自己"这是螺旋的一部分"。被裁员了，他说"这是历史的扬弃"。', dims: [7, 5, 10, 3] },
  'NIE': { name: '尼采的锤子砸脚', title: '🔨 锤子砸脚', desc: '天天喊"重估一切价值"，结果一锤子下去砸到自己脚趾，疼得嗷嗷叫，还得硬撑说"这就是超人之路"。', dims: [-5, 3, -8, -9] },
  'KAN': { name: '康德的准点废柴', title: '⏰ 准点废柴', desc: '道德律令在心里，散步时刻在表上。下午四点必须出门，哪怕外面下刀子——不是为了健康，是为了让邻居对表。', dims: [10, 9, 8, 2] },
  'KIE': { name: '克尔凯郭尔的信仰跳楼', title: '🪂 信仰跳楼', desc: '闭着眼睛从悬崖跳下去，坚信下面有张弹簧床。跳了99次都没事，第100次摔成半身不遂，他说"这就是信仰的飞跃"。', dims: [-8, 4, -9, -3] },
  'BEN': { name: '边沁的快乐计算器', title: '🧮 快乐计算器', desc: '啥都算幸福值，吃饭算卡路里，谈恋爱算性价比。最后算出"活着收益为负"，但依然因为懒得死而继续活着。', dims: [9, -7, 3, 7] },
  'CAM': { name: '加缪的副驾驶', title: '🚗 副驾驶', desc: '反正明天可能被车创死，今天坚决不内耗。老板骂他，他想"他比我更荒诞"，然后哼着歌把咖啡洒在键盘上。', dims: [-6, -3, -7, -4] },
  'ARI': { name: '亚里士多德的掉书袋', title: '📚 掉书袋', desc: '兜里揣满数据，见人就掉书袋，"根据我的观察……"，结果观察了一辈子，发现观察本身也是经验，直接套娃死机。', dims: [8, 4, 7, 0] },
  'HUM': { name: '休谟的因果彩票', title: '🎰 因果彩票', desc: '坚信太阳每天升起，直到感恩节那天主人没来喂食，来了把刀。他中奖从不超过5块，但依然坚持"下次必然"。', dims: [-3, -5, -2, -1] },
  'HOB': { name: '霍布斯的办公室丛林', title: '🦁 办公室丛林', desc: '坚信社会就是人与人互撕，所以每天上班先吼三声"所有人对所有人的战争"，然后默默把同事的零食偷吃了。', dims: [-4, 2, 0, 8] },
  'DIO': { name: '第欧根尼的木桶VIP', title: '🪣 木桶VIP', desc: '公司让卷，他直接搬个纸箱子坐工位底下。亚历山大来视察，他说"别挡我晒太阳"。老板让他升职，他说"别挡我摸鱼"。', dims: [-9, -9, -6, -10] },
  'SPI': { name: '斯宾诺莎的猫', title: '🐱 斯宾诺莎的猫', desc: '相信一切是必然，包括猫把杯子推下桌。他从不生气，只说"这是几何学证明的一部分"，然后默默扫地。', dims: [10, 9, 5, -5] },
  'SAR': { name: '萨特的他人地狱', title: '👀 他人地狱', desc: '电梯里有人看他一眼，他内心OS："完了，我的本质被凝视没了"。外卖备注永远写"挂门上，别敲门，别呼吸"。', dims: [-7, -2, -10, -8] },
  'ROU': { name: '卢梭的逆行自然人', title: '🌿 逆行自然人', desc: '觉得文明全是糟粕，但手机没电会发疯。天天向往原始森林，结果在公园长椅上被蚊子咬醒，大骂"社会异化了我"。', dims: [-6, -8, -4, -7] },
  'WIT': { name: '维特根斯坦的已读不回', title: '🤐 已读不回', desc: '群里吵翻天，他只回一个"。"。对于不可言说的（比如老板的智商），他不仅沉默，还选择了"免打扰"。', dims: [10, 6, -5, -9] },
};

const TOTAL_Q = 50;

function PHTISillyPage() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState('intro');
  const [questions, setQuestions] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [result, setResult] = useState(null);
  const [roast, setRoast] = useState('');
  const [roasting, setRoasting] = useState(false);

  const start = () => {
    const shuffled = [...sillyQuestions].sort(() => Math.random() - 0.5);
    setQuestions(shuffled.slice(0, TOTAL_Q));
    setCurrentQ(0);
    setAnswers([]);
    setPhase('testing');
  };

  const answer = (score) => {
    const q = questions[currentQ];
    const newAnswers = [...answers, { dimension: q.dimension, direction: q.direction, score }];
    setAnswers(newAnswers);
    if (currentQ + 1 >= TOTAL_Q) finish(newAnswers);
    else setCurrentQ(currentQ + 1);
  };

  const finish = async (allAnswers) => {
    // 计算四维度原始总分（不做归一化，保持区分度）
    const dims = ['Rationalism', 'Stoicism', 'Essentialism', 'Communitarian'];
    const scores = {};
    for (const dim of dims) {
      const relevant = allAnswers.filter(a => a.dimension === dim);
      scores[dim] = relevant.reduce((s, a) => s + a.score * (a.direction === 'high' ? 1 : -1), 0);
    }

    // 缩放到与哲学家坐标匹配的范围（哲学家坐标在 -10..10）
    const perDim = TOTAL_Q / 4;
    const userVec = [
      Math.round(scores.Rationalism / perDim * 5),
      Math.round(scores.Stoicism / perDim * 5),
      Math.round(scores.Essentialism / perDim * 5),
      Math.round(scores.Communitarian / perDim * 5),
    ];

    // 概率匹配：距离转 softmax，得分越近概率越高，避免总是同一个
    const entries = Object.entries(PHILOSOPHER_MAP);
    const dists = entries.map(([, p]) =>
      p.dims.reduce((sum, v, i) => sum + (v - userVec[i]) ** 2, 0)
    );
    // 温度参数：越低越倾向最近的那个，越高越均匀
    const temperature = 80;
    const expDists = dists.map(d => Math.exp(-d / temperature));
    const totalExp = expDists.reduce((a, b) => a + b, 0);
    const probs = expDists.map(e => e / totalExp);

    // 加权随机选择
    let r = Math.random();
    let bestKey = entries[0][0];
    for (let i = 0; i < entries.length; i++) {
      r -= probs[i];
      if (r <= 0) { bestKey = entries[i][0]; break; }
    }

    setResult({ ...PHILOSOPHER_MAP[bestKey], scores: userVec, code: bestKey });
    setPhase('roasting');
    setRoasting(true);

    // AI Roast
    const phil = PHILOSOPHER_MAP[bestKey];
    const s = userVec;
    const dimLabel = [
      `理性${s[0] >= 0 ? '+' : ''}${s[0]} vs 感性${s[0] >= 0 ? '' : '+'}${-s[0]}`,
      `斯多葛${s[1] >= 0 ? '+' : ''}${s[1]} vs 伊壁鸠鲁${s[1] >= 0 ? '' : '+'}${-s[1]}`,
      `本质${s[2] >= 0 ? '+' : ''}${s[2]} vs 存在${s[2] >= 0 ? '' : '+'}${-s[2]}`,
      `社群${s[3] >= 0 ? '+' : ''}${s[3]} vs 个人${s[3] >= 0 ? '' : '+'}${-s[3]}`,
    ];
    const prompt = `你是一个毒舌脱口秀演员兼哲学教授。有人刚做了沙雕哲学人格测试，结果显示：

🏆 ${phil.title} —— ${phil.name}
📝 ${phil.desc}

各维度得分：${dimLabel.join('；')}

请用150-200字进行毒舌锐评，要求：
- 幽默刻薄但让人会心一笑
- 结合这个人格的特点精准吐槽
- 网络段子手风格，像微博热评
- 最后一定要有一句暴击金句收尾`;

    try {
      const resp = await fetch(`${getApiBase()}/api/ai/stream`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages: [
            { role: 'system', content: '你是一个犀利的脱口秀演员，吐槽精准幽默，像微博热评。' },
            { role: 'user', content: prompt },
          ],
          temperature: 0.95, max_tokens: 800,
        }),
      });
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let full = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of decoder.decode(value, { stream: true }).split('\n')) {
          if (line.startsWith('data: ') && line !== 'data: [DONE]') {
            try { const d = JSON.parse(line.slice(6)); if (d.choices?.[0]?.delta?.content) { full += d.choices[0].delta.content; setRoast(full); } } catch {}
          }
        }
      }
    } catch { setRoast('（毒舌评论家今天请假去晒太阳了🌞）'); }
    setRoasting(false);
  };

  const pct = questions.length > 0 ? ((currentQ + 1) / TOTAL_Q * 100) : 0;

  return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate('/games')} style={{ marginBottom: 16 }}>← 返回</button>

      {phase === 'intro' && (
        <div className="card" style={{ cursor: 'default', textAlign: 'center', padding: '24px 20px' }}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>🤪</div>
          <h2 style={{ fontSize: 20, marginBottom: 4 }}>PHTI 沙雕版</h2>
          <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 16 }}>
            测测你是哪个哲学家……的摆烂版本
          </p>
          <div style={{ background: 'var(--secondary)', borderRadius: 10, padding: '14px 18px', marginBottom: 16, textAlign: 'left', fontSize: 13, lineHeight: 1.8, color: 'var(--text-dim)' }}>
            <p style={{ margin: '0 0 4px' }}>📋 {TOTAL_Q}道轻松题 · 5秒一道</p>
            <p style={{ margin: '0 0 4px' }}>🎭 16种沙雕哲学家等你认领</p>
            <p style={{ margin: 0 }}>🔥 附带AI毒舌锐评（比亲妈还狠）</p>
          </div>
          <button className="btn btn-primary" onClick={start} style={{ padding: '12px 36px', fontSize: 15, borderRadius: 24 }}>
            🤪 开始测试
          </button>
        </div>
      )}

      {phase === 'testing' && questions.length > 0 && (
        <div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-dim)', marginBottom: 6 }}>
              <span>第 {currentQ + 1}/{TOTAL_Q} 题</span>
              <span>{Math.round(pct)}%</span>
            </div>
            <div style={{ height: 4, background: 'var(--secondary)', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${pct}%`, background: 'var(--accent)', borderRadius: 2, transition: 'width 0.3s' }} />
            </div>
          </div>
          <div className="card" style={{ cursor: 'default', padding: '24px 20px', textAlign: 'center' }}>
            <p style={{ fontSize: 17, lineHeight: 1.8, marginBottom: 24 }}>
              「{questions[currentQ].text}」
            </p>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 4, flexWrap: 'wrap' }}>
              {[
                { score: -2, label: '完全不', emoji: '👎' },
                { score: -1, label: '不太', emoji: '🤔' },
                { score: 0, label: '随便', emoji: '😐' },
                { score: 1, label: '有点', emoji: '👍' },
                { score: 2, label: '太对了', emoji: '💯' },
              ].map(o => (
                <button key={o.score} onClick={() => answer(o.score)} className="btn btn-secondary"
                  style={{ flex: '1 1 55px', minWidth: 50, padding: '10px 4px', fontSize: 11, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3, borderRadius: 10 }}>
                  <span style={{ fontSize: 18 }}>{o.emoji}</span><span>{o.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {phase === 'roasting' && result && (
        <div>
          <div className="card" style={{ cursor: 'default', textAlign: 'center', padding: '24px 20px', marginBottom: 12 }}>
            <div style={{ fontSize: 56, marginBottom: 8 }}>{result.title.slice(0, 2)}</div>
            <h2 style={{ fontSize: 20, marginBottom: 4 }}>{result.title}</h2>
            <p style={{ fontSize: 15, color: 'var(--accent)', fontWeight: 600, marginBottom: 12 }}>{result.name}</p>
            <p style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.7, fontStyle: 'italic' }}>
              {result.desc}
            </p>
          </div>

          <div className="card" style={{ cursor: 'default', padding: '16px 20px', background: '#fef9f0' }}>
            <h3 style={{ fontSize: 14, marginBottom: 8 }}>🔥 AI 毒舌锐评</h3>
            {roasting && !roast && <p style={{ fontSize: 13, color: 'var(--text-dim)' }}>🕯️ 评论家正在酝酿暴击...</p>}
            {roast && <p style={{ fontSize: 13, lineHeight: 1.9, whiteSpace: 'pre-line' }}>{roast}{roasting && <span style={{ color: 'var(--text-dim)' }}>▍</span>}</p>}
          </div>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <button className="btn btn-primary" onClick={start} style={{ padding: '10px 28px', fontSize: 14, borderRadius: 20 }}>🔄 再测一次</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default PHTISillyPage;
