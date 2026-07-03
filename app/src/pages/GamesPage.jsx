/**
 * 游戏 —— 哲学小游戏入口
 * 答案之书 / PHTI
 */
import { useNavigate } from 'react-router-dom';
import Icon from '../components/Icon';

const games = [
  {
    key: 'answer-book',
    icon: 'icon-book-open',
    title: '答案之书',
    desc: '心中默念问题，翻开启示之页',
    path: '/games/answer-book',
    disabled: false,
  },
  {
    key: 'phti',
    icon: 'icon-brain',
    title: 'PHTI',
    desc: 'Philosophical Turing Intelligence — 哲学人格测试',
    path: '/games/phti',
    disabled: false,
  },
  {
    key: 'phti-silly',
    icon: 'icon-crazy',
    title: 'PHTI 沙雕版',
    desc: '测测你是哪个哲学家的摆烂版本',
    path: '/games/phti-silly',
    disabled: false,
  },
];

function GamesPage() {
  const navigate = useNavigate();

  return (
    <div className="page-container">
      <h2 className="section-title" style={{ fontSize: 20, marginBottom: 16 }}>
        <Icon name="nav-games" size={20} /> 哲学游戏
      </h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {games.map((game) => (
          <div
            key={game.key}
            className="card"
            onClick={() => !game.disabled && game.path && navigate(game.path)}
            style={{
              cursor: game.disabled ? 'default' : 'pointer',
              opacity: game.disabled ? 0.5 : 1,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '16px 20px',
              transition: 'transform 0.15s',
            }}
          >
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
                <Icon name={game.icon} size={22} /> {game.title}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                {game.desc}
              </div>
            </div>
            <span style={{ fontSize: 13, color: 'var(--text-dim)' }}>
              {game.disabled ? '即将上线' : '→'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default GamesPage;
