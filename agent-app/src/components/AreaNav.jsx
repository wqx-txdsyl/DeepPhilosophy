import { NavLink } from 'react-router-dom';
import './area-nav.css';

export default function AreaNav() {
  return <nav className="phi-area-nav" aria-label="工作分区">
    <NavLink to="/agent">Chat</NavLink><NavLink to="/projects">Project</NavLink>
  </nav>;
}
