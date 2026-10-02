import { Link } from 'react-router-dom';
import { ossImg, ossFallback } from '../../data/ossUrls';

export default function EpilogueSection({ conclusion, closingQuote, closingQuoteAuthor, closingQuoteKind, image }) {
  const parts = String(closingQuote || '').split(/\s+[—–]\s*/);
  const author = closingQuoteAuthor || parts.slice(1).join(' · ');
  return <section className="school-section school-ending" id="school-conclusion" aria-labelledby="school-conclusion-title">
    {image && <img className="school-ending-art" src={ossImg(image, { w: 1000 })} onError={ossFallback} alt="" loading="lazy" />}
    <header className="school-section-heading centered"><span className="school-kicker">EPILOGUE</span><h2 id="school-conclusion-title">结语</h2></header>
    <div className="school-prose">{String(conclusion || '').split(/\n\s*\n/).filter(Boolean).map((paragraph, i) => <p key={i}>{paragraph}</p>)}</div>
    {closingQuote && <p className="school-closing-quote">{closingQuoteKind === 'quote' ? `“${parts[0]}”` : parts[0]}</p>}
    {author && <p className="school-closing-author">{closingQuoteKind === 'paraphrase' ? '思想概述 · ' : ''}{author}</p>}
    <div className="school-ending-links"><a href="#school-overview">回到简介 ↑</a><Link to="/genealogy">返回谱系 →</Link></div>
  </section>;
}
