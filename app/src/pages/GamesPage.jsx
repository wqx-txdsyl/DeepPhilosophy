/**
 * 游戏 —— 答案之书 / PHTI
 */
import { useState } from 'react';
import answerBookData from '../data/answer_book.json';

function GamesPage() {
  const [showAnswer, setShowAnswer] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [animating, setAnimating] = useState(false);

  const getAnswer = () => {
    if (animating) return;
    setAnimating(true);
    setShowAnswer(false);

    // 随机延迟后显示答案（模拟翻书感）
    const delay = 800 + Math.random() * 1200;
    setTimeout(() => {
      const idx = Math.floor(Math.random() * answerBookData.length);
      setAnswer(answerBookData[idx]);
      setShowAnswer(true);
      setAnimating(false);
    }, delay);
  };

  return (
    <div className="page-container">
      {/* 答案之书 */}
      <div className="card" style={{ cursor: 'default', textAlign: 'center', padding: '28px 24px' }}>
        <div style={{ fontSize: 48, marginBottom: 8 }}>📖</div>
        <h2 style={{ fontSize: 20, marginBottom: 4 }}>答案之书</h2>
        <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 16 }}>
          心中默念你的问题，然后翻开属于你的答案
        </p>

        <button
          className="btn btn-primary"
          onClick={getAnswer}
          disabled={animating}
          style={{
            padding: '10px 32px',
            fontSize: 15,
            borderRadius: 24,
            transition: 'all 0.3s',
          }}
        >
          {animating ? '🕯️ 正在寻找答案...' : '✨ 获取我的答案'}
        </button>

        {/* 答案卡片 */}
        {animating && (
          <div style={{
            marginTop: 20,
            padding: '24px 20px',
            background: 'var(--secondary)',
            borderRadius: 12,
            opacity: 0.5,
            transition: 'opacity 0.3s',
          }}>
            <div style={{ fontSize: 30, animation: 'pulse 1s infinite' }}>📜</div>
          </div>
        )}

        {showAnswer && answer && (
          <div style={{
            marginTop: 20,
            padding: '24px 20px',
            background: 'var(--secondary)',
            borderRadius: 12,
            animation: 'fadeInUp 0.6s ease',
            textAlign: 'left',
          }}>
            <div style={{
              fontSize: 17,
              lineHeight: 1.8,
              color: 'var(--accent)',
              fontStyle: 'italic',
              marginBottom: 16,
              padding: '0 4px',
              borderLeft: '3px solid var(--accent)',
              paddingLeft: 14,
            }}>
              「{answer.text}」
            </div>
            <div style={{
              fontSize: 14,
              lineHeight: 1.7,
              color: 'var(--text)',
              marginBottom: 12,
            }}>
              {answer.explanation}
            </div>
            <div style={{
              fontSize: 12,
              color: 'var(--text-dim)',
              textAlign: 'right',
            }}>
              —— {answer.author}
            </div>

            <button
              className="btn btn-secondary"
              onClick={getAnswer}
              disabled={animating}
              style={{
                marginTop: 16,
                padding: '6px 20px',
                fontSize: 12,
                borderRadius: 16,
                width: '100%',
              }}
            >
              🔄 再问一次
            </button>
          </div>
        )}
      </div>

      {/* PHTI */}
      <div
        className="card"
        style={{
          cursor: 'default',
          opacity: 0.5,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px 20px',
          marginTop: 12,
        }}
      >
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
            🧠 PHTI
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>
            Philosophical Turing Intelligence — 哲学图灵测试
          </div>
        </div>
        <span style={{ fontSize: 13, color: 'var(--text-dim)' }}>🚧 即将上线</span>
      </div>

      {/* 动画定义 */}
      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 1; }
        }
      `}</style>
    </div>
  );
}

export default GamesPage;
