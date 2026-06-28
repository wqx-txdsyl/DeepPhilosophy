/**
 * PHTI — Philosophical Turing Intelligence
 * 哲学人格测试：50题 → 维度计分 → 16型匹配 → AI毒舌锐评
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';
import phtiTypes from '../data/phti_original_types.json';
import allQuestions from '../data/phti_questions.json';

const TOTAL_QUESTIONS = 50;

// 4 dimensions: Rationalism, Stoicism, Essentialism, Communitarian
const DIMS = ['Rationalism', 'Stoicism', 'Essentialism', 'Communitarian'];

function PHTIPage() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState('intro'); // intro | testing | roasting | result
  const [questions, setQuestions] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState([]); // array of {dimension, direction, score(-2..2)}
  const [result, setResult] = useState(null); // matched personality
  const [roast, setRoast] = useState('');
  const [roasting, setRoasting] = useState(false);
  const roastRef = useRef('');

  // Start test
  const startTest = () => {
    const shuffled = [...allQuestions].sort(() => Math.random() - 0.5);
    setQuestions(shuffled.slice(0, TOTAL_QUESTIONS));
    setCurrentQ(0);
    setAnswers([]);
    setPhase('testing');
  };

  // Answer a question
  const answer = (score) => {
    const q = questions[currentQ];
    const newAnswers = [...answers, {
      dimension: q.dimension,
      direction: q.direction,
      score: score,
    }];
    setAnswers(newAnswers);

    if (currentQ + 1 >= TOTAL_QUESTIONS) {
      finishTest(newAnswers);
    } else {
      setCurrentQ(currentQ + 1);
    }
  };

  // Calculate personality and request roast
  const finishTest = async (allAnswers) => {
    // Score each dimension
    const scores = {};
    for (const dim of DIMS) {
      let total = 0;
      let count = 0;
      for (const a of allAnswers) {
        if (a.dimension === dim) {
          const multiplier = a.direction === 'high' ? 1 : -1;
          total += a.score * multiplier;
          count++;
        }
      }
      // Normalize to roughly -10 to +10 range
      scores[dim] = count > 0 ? Math.round((total / count) * 5) : 0;
    }

    // 概率性匹配：得分越极端越确定，越接近0越随机
    // 每个维度的 R/E 概率由得分决定（sigmoid）
    const sigmoid = (x) => 1 / (1 + Math.exp(-x / 2)); // 温度=2，得分±5时概率≈0.92/0.08
    const probs = [
      sigmoid(scores.Rationalism), // >0.5 means R, <0.5 means E
      sigmoid(scores.Stoicism),
      sigmoid(scores.Essentialism),
      sigmoid(scores.Communitarian),
    ];

    // 按概率生成4-letter code (多次采样取最常见？不，就一次采样)
    const genLetter = (dimIdx, highLetter, lowLetter) =>
      Math.random() < probs[dimIdx] ? highLetter : lowLetter;

    const personalityCode =
      genLetter(0, 'R', 'E') +
      genLetter(1, 'R', 'E') +
      genLetter(2, 'R', 'E') +
      genLetter(3, 'R', 'E');

    const matched = phtiTypes.find(t => t.code === personalityCode) || phtiTypes[0];

    setResult({ ...matched, scores, personalityCode });
    setPhase('roasting');
    setRoasting(true);

    // Build answer summary for AI roast
    const dimSummaries = DIMS.map(dim => {
      const dimAnswers = allAnswers.filter(a => a.dimension === dim);
      const avg = dimAnswers.reduce((s, a) => s + a.score, 0) / dimAnswers.length;
      const strongAgrees = dimAnswers.filter(a => Math.abs(a.score) === 2).length;
      return `${dim}: 均分=${avg.toFixed(1)}, 极端回答=${strongAgrees}/${dimAnswers.length}`;
    }).join('; ');

    const roastPrompt = `你是一个毒舌脱口秀演员兼哲学教授。有人刚做完哲学人格测试：

人格类型：${matched.title}（${matched.name}）
性格简述：${matched.short_desc}
维度得分：${JSON.stringify(scores)}
- 理性主义(${scores.Rationalism >= 0 ? '+' : ''}${scores.Rationalism}) vs 经验主义
- 斯多葛(${scores.Stoicism >= 0 ? '+' : ''}${scores.Stoicism}) vs 伊壁鸠鲁
- 本质主义(${scores.Essentialism >= 0 ? '+' : ''}${scores.Essentialism}) vs 存在主义
- 社群主义(${scores.Communitarian >= 0 ? '+' : ''}${scores.Communitarian}) vs 个人主义

请写一段300-400字的毒舌锐评，要求：
- 开头直接暴击，戳穿这个人格最自欺欺人的地方
- 中间用2-3个具体生活场景精准吐槽
- 语气像微博热评、脱口秀段子，哲学梗+网络梗混用
- 最后一句必须是致命暴击金句，让人看完沉默三秒然后转发
- 字数一定要够300字以上！不要敷衍！`;

    try {
      const apiBase = getApiBase();
      const resp = await fetch(`${apiBase}/api/ai/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages: [
            { role: 'system', content: '你是一个毒舌脱口秀演员兼哲学教授。吐槽犀利长篇不留情面，像微博热评第一+脱口秀开场段子。每句话都要有杀伤力，绝不说教，绝不温和。字数不少于300。' },
            { role: 'user', content: roastPrompt },
          ],
          temperature: 1.0,
          max_tokens: 1200,
        }),
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ') && line !== 'data: [DONE]') {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.choices?.[0]?.delta?.content) {
                fullText += data.choices[0].delta.content;
                roastRef.current = fullText;
                setRoast(fullText);
              }
            } catch {}
          }
        }
      }
    } catch (e) {
      setRoast('（毒舌评论家暂时不在，请稍后再试）');
    }
    setRoasting(false);
  };

  // Progress bar
  const progress = questions.length > 0 ? ((currentQ + 1) / TOTAL_QUESTIONS * 100) : 0;

  return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate('/games')}
        style={{ marginBottom: 16 }}>← 返回</button>

      {/* Intro */}
      {phase === 'intro' && (
        <div className="card" style={{ cursor: 'default', textAlign: 'center', padding: '28px 24px' }}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>🧠</div>
          <h2 style={{ fontSize: 20, marginBottom: 4 }}>PHTI 哲学人格测试</h2>
          <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 8 }}>
            Philosophical Turing Intelligence
          </p>
          <div style={{
            background: 'var(--secondary)', borderRadius: 10, padding: '16px 20px',
            margin: '16px 0', textAlign: 'left', fontSize: 13, lineHeight: 1.8, color: 'var(--text-dim)',
          }}>
            <p style={{ margin: '0 0 8px' }}>📋 <strong>测试说明</strong></p>
            <p style={{ margin: '0 0 4px' }}>• 共 {TOTAL_QUESTIONS} 道哲学情境题</p>
            <p style={{ margin: '0 0 4px' }}>• 每题用 1-5 分表示你的同意程度</p>
            <p style={{ margin: '0 0 4px' }}>• 四个维度：理性/感性 · 斯多葛/伊壁鸠鲁 · 本质/存在 · 公民/个人</p>
            <p style={{ margin: 0 }}>• 完成后显示你的哲学人格 + AI 毒舌锐评 🔥</p>
          </div>
          <button className="btn btn-primary" onClick={startTest}
            style={{ padding: '12px 36px', fontSize: 15, borderRadius: 24, marginTop: 8 }}>
            🚀 开始测试
          </button>
        </div>
      )}

      {/* Testing */}
      {phase === 'testing' && questions.length > 0 && (
        <div>
          {/* Progress */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-dim)', marginBottom: 6 }}>
              <span>第 {currentQ + 1}/{TOTAL_QUESTIONS} 题</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div style={{ height: 4, background: 'var(--secondary)', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${progress}%`, background: 'var(--accent)', borderRadius: 2, transition: 'width 0.3s' }} />
            </div>
          </div>

          {/* Question */}
          <div className="card" style={{ cursor: 'default', padding: '24px 20px', textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 12, letterSpacing: '0.05em' }}>
              请选择你对以下陈述的同意程度
            </div>
            <p style={{ fontSize: 17, lineHeight: 1.8, marginBottom: 24, color: 'var(--text)' }}>
              「{questions[currentQ].text}」
            </p>

            {/* Likert scale */}
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 4, flexWrap: 'wrap' }}>
              {[
                { score: -2, label: '完全不同意', emoji: '👎' },
                { score: -1, label: '不太同意', emoji: '🤔' },
                { score: 0, label: '中立', emoji: '😐' },
                { score: 1, label: '比较同意', emoji: '👍' },
                { score: 2, label: '完全同意', emoji: '💯' },
              ].map(opt => (
                <button key={opt.score} onClick={() => answer(opt.score)}
                  className="btn btn-secondary"
                  style={{
                    flex: '1 1 60px', minWidth: 55, padding: '10px 6px', fontSize: 11,
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
                    borderRadius: 10, border: '1px solid var(--border)',
                  }}>
                  <span style={{ fontSize: 18 }}>{opt.emoji}</span>
                  <span>{opt.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Roasting */}
      {phase === 'roasting' && result && (
        <div>
          {/* Result card */}
          <div className="card" style={{ cursor: 'default', textAlign: 'center', padding: '24px 20px', marginBottom: 12 }}>
            <div style={{ fontSize: 48, marginBottom: 4 }}>{result.title.slice(0, 2)}</div>
            <h2 style={{ fontSize: 18, marginBottom: 2 }}>{result.title}</h2>
            <p style={{ fontSize: 14, color: 'var(--accent)', fontWeight: 600, marginBottom: 12 }}>
              {result.name}
            </p>
            <p style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.6, marginBottom: 16 }}>
              {result.short_desc}
            </p>

            {/* Dimension bars */}
            <div style={{ textAlign: 'left', padding: '0 8px' }}>
              {[
                { dim: 'Rationalism', left: '理性主义', right: '经验主义', score: result.scores.Rationalism },
                { dim: 'Stoicism', left: '斯多葛', right: '伊壁鸠鲁', score: result.scores.Stoicism },
                { dim: 'Essentialism', left: '本质主义', right: '存在主义', score: result.scores.Essentialism },
                { dim: 'Communitarian', left: '社群主义', right: '个人主义', score: result.scores.Communitarian },
              ].map(d => {
                const pct = Math.max(-10, Math.min(10, d.score));
                const barLeft = 50 + pct * 5; // maps -10..10 to 0..100
                return (
                  <div key={d.dim} style={{ marginBottom: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-dim)', marginBottom: 2 }}>
                      <span>{d.left}</span>
                      <span>{d.right}</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--secondary)', borderRadius: 3, position: 'relative', overflow: 'hidden' }}>
                      <div style={{
                        position: 'absolute', left: 0, width: `${barLeft}%`, height: '100%',
                        background: 'var(--accent)', borderRadius: 3, transition: 'width 0.5s',
                      }} />
                      <div style={{
                        position: 'absolute', left: '50%', top: -2, width: 2, height: 10,
                        background: 'var(--ink)', opacity: 0.3,
                      }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Detailed description */}
          <div className="card" style={{ cursor: 'default', padding: '16px 20px', marginBottom: 12 }}>
            <p style={{ fontSize: 13, lineHeight: 1.8, color: 'var(--text)', whiteSpace: 'pre-line' }}>
              {result.full_desc}
            </p>
          </div>

          {/* AI Roast */}
          <div className="card" style={{ cursor: 'default', padding: '16px 20px', background: 'var(--accent-light, #faf3e8)' }}>
            <h3 style={{ fontSize: 14, marginBottom: 8 }}>🔥 AI 毒舌锐评</h3>
            {roasting && !roast && (
              <p style={{ fontSize: 13, color: 'var(--text-dim)', fontStyle: 'italic' }}>
                🕯️ 评论家正在酝酿犀利的点评...
              </p>
            )}
            {roast && (
              <p style={{ fontSize: 13, lineHeight: 1.8, color: 'var(--text)', whiteSpace: 'pre-line' }}>
                {roast}
              </p>
            )}
            {roasting && roast && (
              <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>▍</span>
            )}
          </div>

          {/* Retry button */}
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <button className="btn btn-primary" onClick={startTest}
              style={{ padding: '10px 28px', fontSize: 14, borderRadius: 20 }}>
              🔄 重新测试
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default PHTIPage;
