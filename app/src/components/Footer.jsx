/**
 * Footer — Apple 式多列布局
 */
import { useNavigate } from 'react-router-dom';

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
    title: '更多',
    links: [
      { label: '我的书房', path: '/profile' },
      { label: '设置', path: '/settings' },
      { label: '关于本站', path: '/about' },
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
          <p className="home-footer-brand-desc">一部横跨五千年的人类思想史长卷。111 个哲学流派，652 位哲学家与思想家，409 部著作。</p>
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
      <div className="home-footer-bottom" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <p className="home-footer-copy" style={{ margin: 0 }}>© {new Date().getFullYear()} DeepPhilosophy · @txdsyl_</p>
        <div style={{ display: 'flex', gap: 16 }}>
          <span className="home-footer-link" onClick={() => navigate('/privacy')}>隐私政策</span>
          <span className="home-footer-link" onClick={() => navigate('/terms')}>用户协议</span>
        </div>
      </div>
    </footer>
  );
}
