/**
 * 答案之书 —— 心中默念问题，翻开启示之页
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import answerBookData from '../data/answer_book.json';

function AnswerBookPage() {
  const navigate = useNavigate();
  const [showAnswer, setShowAnswer] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [animating, setAnimating] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, []);

  const getAnswer = () => {
    if (animating) return;
    setAnimating(true);
    setShowAnswer(false);

    const delay = 800 + Math.random() * 1200;
    timerRef.current = setTimeout(() => {
      const idx = Math.floor(Math.random() * answerBookData.length);
      setAnswer(answerBookData[idx]);
      setShowAnswer(true);
      setAnimating(false);
    }, delay);
  };

  return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate('/games')}
        style={{ marginBottom: 16 }}>← 返回</button>

      <div className="card" style={{ cursor: 'default', textAlign: 'center', padding: '28px 24px' }}>
        <div style={{ fontSize: 48, marginBottom: 8 }}><Icon name="icon-book-open" size={16} /></div>
        <h2 style={{ fontSize: 20, marginBottom: 4 }}>答案之书</h2>
        <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 16 }}>
          心中默念你的问题，然后翻开属于你的答案
        </p>

        <button
          className="btn btn-primary"
          onClick={getAnswer}
          disabled={animating}
          style={{ padding: '10px 32px', fontSize: 15, borderRadius: 24 }}
        >
          {animating ? '🕯️ 正在寻找答案...' : '✨ 获取我的答案'}
        </button>

        {animating && (
          <div style={{
            marginTop: 20, padding: '24px 20px',
            background: 'var(--secondary)', borderRadius: 12, opacity: 0.5,
          }}>
            <div style={{ fontSize: 30, animation: 'pulse 1s infinite' }}><Icon name="icon-scroll" size={16} /></div>
          </div>
        )}

        {showAnswer && answer && (
          <div style={{
            marginTop: 20, padding: '24px 20px',
            background: 'var(--secondary)', borderRadius: 12,
            animation: 'fadeInUp 0.6s ease', textAlign: 'left',
          }}>
            <div style={{
              fontSize: 17, lineHeight: 1.8, color: 'var(--accent)',
              fontStyle: 'italic', marginBottom: 16,
              borderLeft: '3px solid var(--accent)', paddingLeft: 14,
            }}>
              「{answer.text}」
            </div>
            <div style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--text)', marginBottom: 12 }}>
              {answer.explanation}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-dim)', textAlign: 'right' }}>
              —— {answer.author}
            </div>
            <button
              className="btn btn-secondary"
              onClick={getAnswer}
              disabled={animating}
              style={{ marginTop: 16, padding: '6px 20px', fontSize: 12, borderRadius: 16, width: '100%' }}
            >
              <Icon name="icon-refresh" size={16} /> 再问一次
            </button>
          </div>
        )}
      </div>

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

export default AnswerBookPage;
