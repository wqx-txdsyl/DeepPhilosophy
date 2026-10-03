import { formatBookTitle } from '../../data/bookTitles';
import { Link } from 'react-router-dom';
import { ossImg, ossFallback } from '../../data/ossUrls';

export default function WorksList({ works = [], references }) {
  if (!works.length) return null;
  return <section className="school-section" id="school-works" aria-labelledby="school-works-title">
    <header className="school-section-heading"><span className="school-kicker">PRIMARY TEXTS</span><h2 id="school-works-title">重要典籍</h2></header>
    <div className="school-works-grid">{works.map((work, index) => { const book = references?.findBook?.(work.title, work.author); return <article className="school-work" key={`${work.title}-${index}`}>
      {book?.cover && <Link to={book.href} aria-label={`阅读${work.title}`}><img src={ossImg(book.cover)} onError={ossFallback} alt={`${formatBookTitle(work.title)}封面`} loading="lazy" /></Link>}
      <div><h3>{formatBookTitle(work.title)}</h3><small>{work.author}{work.era ? ` · ${work.era}` : ''}</small><p>{work.desc}</p>{book && <Link className="school-text-link" to={book.href}>{book.chapterCount > 0 ? '阅读原典' : '查看书籍'} ↗</Link>}</div>
    </article>; })}</div>
  </section>;
}
