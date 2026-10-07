import { ENTRY_PAGES } from '../data/entryPages';
import './EntryHeader.css';

export default function EntryHeader({ page, meta, secondary, action }) {
  const entry = ENTRY_PAGES[page];
  return <header className="entry-header">
    <div className="entry-heading">
      <p className="entry-eyebrow">DeepPhilosophy <span aria-hidden="true">·</span> {entry.en}</p>
      <h1 className="entry-title">{entry.title}</h1>
      <p className="entry-description">{entry.description}</p>
    </div>
    <div className="entry-aside">
      {meta && <p className="entry-meta">{meta}</p>}
      {secondary && <p className="entry-secondary">{secondary}</p>}
      {action && <div className="entry-actions">{action}</div>}
    </div>
  </header>;
}
