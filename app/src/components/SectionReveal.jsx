/**
 * SectionReveal — 滚动触发揭示动画包装器
 * 元素进入视口时淡入上滑
 */
import { useRef, useState, useEffect } from 'react';

export default function SectionReveal({ children, className = '', style, delay = 0 }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setVisible(true); },
      { threshold: 0.08, rootMargin: '-30px 0px' }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`section-reveal ${visible ? 'visible' : ''} ${className}`}
      style={{ transitionDelay: `${delay}ms`, ...style }}
    >
      {children}
    </div>
  );
}
