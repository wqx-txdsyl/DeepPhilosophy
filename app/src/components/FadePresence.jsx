import { cloneElement, isValidElement, useEffect, useState } from 'react';

// Keep only the departing panel for its short exit; it is immediately inert.
export default function FadePresence({ children }) {
  const incoming = isValidElement(children) ? children : null;
  const [stored, setStored] = useState(incoming);
  if (incoming && incoming !== stored) setStored(incoming);
  const open = Boolean(incoming);
  useEffect(() => {
    if (open || !stored) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const timer = setTimeout(() => setStored(null), reduced ? 0 : 150);
    return () => clearTimeout(timer);
  }, [open, stored]);
  const element = incoming || stored;
  if (!element) return null;
  return cloneElement(element, {
    className: `${element.props.className || ''} dp-presence${open ? '' : ' is-leaving'}`,
    inert: open ? element.props.inert : true,
    'aria-hidden': open ? element.props['aria-hidden'] : true,
  });
}
