import { Link } from 'react-router-dom';
import { ossImg, ossFallback } from '../../data/ossUrls';

export default function HeroSection({ name, quote, quoteAuthor, quoteKind, heroImage, englishName, subtitle }) {
  const image = heroImage?.replace(/^url\(['"]?|['"]?\)$/g, '') || '/schools/default.webp';
  return <section className="school-hero-section school-hero" aria-label={`${name}封面`}>
    <img className="school-hero-art" src={image.startsWith('/') ? ossImg(image, { w: 1600 }) : image} onError={ossFallback} alt="" fetchPriority="high" />
    <header className="school-masthead"><Link className="school-brand" to="/">DeepPhilosophy</Link><Link className="school-back" to="/genealogy">← 返回谱系</Link></header>
    <div className="school-hero-copy"><p className="school-kicker">{englishName || 'PHILOSOPHY & TRADITION'}</p><h1 className={name.length > 10 ? 'school-title-long' : name.length > 6 ? 'school-title-medium' : ''}>{name}</h1>
      {quote && <p className="school-hero-quote">{quoteKind === 'quote' ? `“${quote}”` : quote}</p>}
      {quoteAuthor && <p className="school-hero-author">{quoteKind === 'paraphrase' && <span>思想概述 · </span>}{quoteAuthor}</p>}
    </div>
    <div className="school-hero-foot"><span>{subtitle}</span><a href="#school-overview" className="school-start" aria-label="开始阅读简介">↓</a><span>思想 · 人物 · 原典</span></div>
  </section>;
}
