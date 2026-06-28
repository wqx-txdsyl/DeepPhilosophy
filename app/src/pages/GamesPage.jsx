/**
 * 游戏 —— 哲学小游戏入口
 * 答案之书 / PHTI
 */
import { useNavigate } from 'react-router-dom';

const games = [
  {
    key: 'answer-book',
    title: '📖 答案之书',
    desc: '心中默念问题，翻开启示之页',
    status: '🚧 即将上线',
    disabled: true,
  },
  {
    key: 'phti',
    title: '🧠 PHTI',
    desc: 'Philosophical Turing Intelligence — 哲学图灵测试',
    status: '🚧 即将上线',
    disabled: true,
  },
];

function GamesPage() {
  const navigate = useNavigate();

  return (
    <div className="page-container">
      <h2 className="section-title" style={{ fontSize: 20, marginBottom: 16 }}>
        🎮 哲学游戏
      </h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {games.map((game) => (
          <div
            key={game.key}
            className="card"
            style={{
              cursor: game.disabled ? 'default' : 'pointer',
              opacity: game.disabled ? 0.6 : 1,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '16px 20px',
            }}
          >
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
                {game.title}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                {game.desc}
              </div>
            </div>
            <span style={{ fontSize: 13, color: 'var(--text-dim)' }}>
              {game.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default GamesPage;
