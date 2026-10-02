import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ossImg, ossFallback } from '../../data/ossUrls';

const termName = value => String(value || '').split(/[（(]/)[0].trim();

export default function SubSchoolsSection({ schoolName, subSchools = [], thinkers = [], cihai = [], references, initialBranch, onSelectPerson, onSelectConcept }) {
  const [opened, setOpened] = useState(initialBranch || null);
  if (!subSchools.length) return null;
  return <section className="school-section school-branches" id="school-branches" aria-labelledby="school-branches-title">
    <header className="school-section-heading centered"><span className="school-kicker">BRANCHES OF THOUGHT</span><h2 id="school-branches-title">子流派与思想分支</h2></header>
    <div className="school-branch-parent">{schoolName}</div>
    <div className="school-branch-grid">{subSchools.map((sub, index) => {
      const people = thinkers.filter(person => person.sub?.includes(sub.name) || sub.desc?.includes(person.name));
      const terms = [...new Map(cihai.filter(term => termName(term.word).length > 1 && `${sub.name} ${sub.desc}`.includes(termName(term.word))).map(term => [termName(term.word), term])).values()].slice(0, 4);
      const focus = terms[0] ? termName(terms[0].word) : sub.name.replace(/现象学|哲学|主义|学派|学说/g, '').slice(0, 4);
      const target = references?.findSchool?.(sub.name), open = opened === sub.name;
      return <article className={`school-branch ${open ? 'is-open' : ''}`} key={`${sub.name}-${index}`}>
        <button type="button" className="school-branch-trigger" aria-expanded={open} aria-controls={`school-branch-${index}`} onClick={() => setOpened(open ? null : sub.name)}>
          <span className="school-branch-focus" aria-hidden="true">{focus}</span><small>{sub.era}{sub.kind ? ` · ${sub.kind}` : ''}</small><h3>{sub.name}</h3><p>{sub.desc}</p><span className="school-branch-hint"><span>{people.map(person => person.name).join(' · ') || '阅读分支脉络'}</span><span aria-hidden="true">{open ? '−' : '＋'}</span></span>
        </button>
        <div id={`school-branch-${index}`} className="school-branch-detail" hidden={!open}>
          {people.length > 0 && <div className="school-branch-people">{people.map(person => { const ref = references?.findPerson?.(person.name, person.era); return <button key={person.name} type="button" onClick={() => onSelectPerson?.(person.name)}>{ref?.portrait && <img src={ossImg(ref.portrait, { w: 100 })} onError={ossFallback} alt="" loading="lazy" />}<span>{person.name} ↗</span></button>; })}</div>}
          {terms.length > 0 && <div className="school-branch-terms">{terms.map((term, i) => <button type="button" key={`${term.word}-${i}`} onClick={() => onSelectConcept?.(term.word)}>{termName(term.word)} ↗</button>)}</div>}
          {target && target.name !== schoolName && <Link className="school-text-link" to={`/school/${encodeURIComponent(target.name)}`}>进入{target.name} →</Link>}
          {!people.length && !terms.length && !target && <p className="school-branch-note">本页简介、时间轴与原典共同呈现这一分支的背景。</p>}
        </div>
      </article>;
    })}</div>
  </section>;
}
