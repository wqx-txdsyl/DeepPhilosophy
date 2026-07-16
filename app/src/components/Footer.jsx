/**
 * Footer — Apple 式多列布局
 */
import { useNavigate } from 'react-router-dom';
import Icon from './Icon';

const columns = [
  {
    title: '知识库',
    links: [
      { label: '哲学著作', path: '/books' },
      { label: '哲学家', path: '/authors' },
      { label: '哲学谱系', path: '/genealogy' },
      { label: '世界哲学地图', path: '/world-philosophies' },
    ],
  },
  {
    title: '互动',
    links: [
      { label: 'AI 问答', path: '/qa' },
      { label: '答案之书', path: '/games/answer-book' },
      { label: 'PHTI 人格测试', path: '/games/phti' },
      { label: 'PHTI 沙雕版', path: '/games/phti-silly' },
    ],
  },
  {
    title: '更多',
    links: [
      { label: '个人中心', path: '/profile' },
      { label: '设置', path: '/settings' },
      { label: '开发者', path: '/DEVELOPER_IS_TXDSYL' },
    ],
  },
];

export default function Footer() {
  const navigate = useNavigate();

  return (
    <footer className="home-footer">
      <div className="home-footer-inner">
        {/* 品牌区 */}
        <div className="home-footer-brand">
          <p className="home-footer-logo" onClick={() => navigate('/')}>DeepPhilosophy</p>
          <p className="home-footer-brand-desc">一部横跨五千年的人类思想史长卷。111 个哲学流派，759 位哲学家，305 部经典著作。</p>
        </div>

        {/* 链接列 */}
        <div className="home-footer-columns">
          {columns.map(col => (
            <div key={col.title} className="home-footer-col">
              <h4 className="home-footer-col-title">{col.title}</h4>
              {col.links.map(l => (
                <span key={l.path} className="home-footer-link" onClick={() => navigate(l.path)}>
                  {l.label}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* 底部版权 */}
      <div className="home-footer-bottom">
        <p className="home-footer-copy">© {new Date().getFullYear()} DeepPhilosophy · @txdsyl_</p>
      </div>
    </footer>
  );
}
