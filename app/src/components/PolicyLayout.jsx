import { Link } from 'react-router-dom';
import { useSEO } from '../utils/seo';
import { SiteFooter } from './SitePageParts';
import '../pages/SitePages.css';
import './PolicyLayout.css';
export default function PolicyLayout({title,english,intro,sections,current}){
  useSEO(title,`${title} · DeepPhilosophy 的服务与数据处理说明。`);
  return <article className="site-pages policy-page"><header className="policy-header"><p className="s-kicker">{english}</p><h1>{title}</h1><p>{intro}</p><div className="policy-meta"><span>更新于 2026年10月4日</span><nav aria-label="网站说明"><Link to="/about">关于本站</Link><Link to="/privacy" aria-current={current==='privacy'?'page':undefined}>隐私政策</Link><Link to="/terms" aria-current={current==='terms'?'page':undefined}>用户协议</Link></nav></div></header><div className="policy-body"><aside><nav aria-label={`${title}目录`}>{sections.map((s,i)=><a key={s.id} href={`#${s.id}`}><span>{String(i+1).padStart(2,'0')}</span>{s.title}</a>)}</nav></aside><div>{sections.map((s,i)=><section id={s.id} className="policy-section" key={s.id}><p className="s-kicker">{String(i+1).padStart(2,'0')}</p><h2>{s.title}</h2>{s.content}</section>)}</div></div><SiteFooter/></article>;
}
export function FeedbackLink(){return <a href="https://github.com/wqx-txdsyl/DeepPhilosophy/issues" target="_blank" rel="noopener noreferrer">项目反馈入口 ↗</a>;}
