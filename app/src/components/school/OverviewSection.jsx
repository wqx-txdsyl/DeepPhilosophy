export default function OverviewSection({ overview }) {
  return <section className="school-section school-overview" id="school-overview" aria-labelledby="school-overview-title">
    <header className="school-section-heading centered"><span className="school-kicker">INTRODUCTION</span><h2 id="school-overview-title">简介与核心思想</h2></header>
    <div className="school-prose">{(overview || '').split(/\n\s*\n/).filter(Boolean).map((paragraph, index) => <p key={index}>{paragraph.trim()}</p>)}</div>
  </section>;
}
