import { Link } from 'react-router-dom';
import CdnImage from '../CdnImage';
import { heroArtworkLayout } from '../../data/heroArtworkLayout';

export default function HeroSection({ name, quote, quoteAuthor, quoteKind, heroImage, englishName, subtitle,
  backTo = '/genealogy', backLabel = '返回谱系', startId = 'school-overview', startLabel = '开始阅读简介',
  footerMeta = '思想 · 人物 · 原典', chapters = [], onChapterSelect }) {
  const image = heroImage?.replace(/^url\(['"]?|['"]?\)$/g, '') || '/schools/default.webp';
  const artwork = heroArtworkLayout(image);
  const jump = (event, id) => {
    if (onChapterSelect) { event.preventDefault(); onChapterSelect(id); }
  };
  return <section className={`school-hero-section school-hero hero-tone-${artwork.tone} hero-copy-${artwork.placement}`} aria-label={`${name}封面`}
    style={{ '--hero-height-factor': artwork.heightFactor, '--hero-position': artwork.position }}>
    <CdnImage className="school-hero-art" src={image} imageWidth={1920} width={artwork.width} height={artwork.height}
      alt="" fetchPriority="high" decoding="async" />
    <header className="school-masthead"><Link className="school-brand" to="/">DeepPhilosophy</Link><Link className="school-back" to={backTo}>← {backLabel}</Link></header>
    <div className="school-hero-copy"><p className="school-kicker">{englishName || 'PHILOSOPHY & TRADITION'}</p><h1 className={name.length > 10 ? 'school-title-long' : name.length > 6 ? 'school-title-medium' : ''}>{name}</h1>
      {quote && <p className="school-hero-quote">{quoteKind === 'quote' ? `“${quote}”` : quote}</p>}
      {quoteAuthor && <p className="school-hero-author">{quoteKind === 'paraphrase' && <span>思想概述 · </span>}{quoteAuthor}</p>}
    </div>
    <div className="school-hero-bottom">
      <div className="school-hero-foot"><span>{subtitle}</span><a href={`#${startId}`} className="school-start" aria-label={startLabel} onClick={event => jump(event, startId)}>↓</a><span>{footerMeta}</span></div>
      {chapters.length > 0 && <nav className="school-chapter-nav" aria-label="章节导航">{chapters.map(chapter => <a key={chapter.id} href={`#${chapter.id}`} onClick={event => jump(event, chapter.id)}><small>{chapter.num}</small>{chapter.name}</a>)}</nav>}
    </div>
  </section>;
}
