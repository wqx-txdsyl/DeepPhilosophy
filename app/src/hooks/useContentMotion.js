import { useLayoutEffect } from 'react';

// Animate reading blocks, never graph canvases, sticky shells, or the reader text.
const READING_BLOCKS = [
  '.school-section-heading', '.school-prose > p', '.school-branch', '.school-work',
  '.school-star-heading', '.school-river-heading', '.school-river-trigger',
  '.school-glossary-heading', '.school-quotes-heading', '.school-sources > h2',
  '.mtd-overview-sec > h3', '.mtd-dialogue', '.mtd-cross-card',
  '.hp-section-heading', '.hp-prose > p', '.hp-life-trigger', '.hp-related-work',
  '.hp-source-grid > a', '.dp-section-caption', '.dp-prose > p', '.dp-concept-heading',
  '.dp-reading-books > a', '.dp-feature-copy', '.dp-library-intro', '.dp-book', '.ap-card',
  '.s-page-heading', '.s-about-essay > p', '.s-principles > article', '.s-reading-row', '.s-notecard',
].join(',');

export default function useContentMotion(rootRef, routeKey, enabled) {
  useLayoutEffect(() => {
    const root = rootRef.current;
    if (!enabled || !root || !('IntersectionObserver' in window)) return;
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (preference.matches) return;
    const seen = new WeakSet(), pending = new Set(), animations = new Set();
    const observer = new IntersectionObserver(entries => {
      let order = 0;
      for (const entry of entries) if (entry.isIntersecting) reveal(entry.target, (order++ % 4) * 45);
    }, { threshold: 0, rootMargin: '0px 0px -24px 0px' });

    function reveal(element, delay = 0, immediate = false) {
      pending.delete(element);
      observer.unobserve(element);
      element.classList.remove('dp-motion-pending');
      if (immediate || preference.matches || typeof element.animate !== 'function') return;
      const animation = element.animate([
        { opacity: 0, transform: 'translateY(14px)' },
        { opacity: 1, transform: 'translateY(0)' },
      ], { duration: 620, delay, easing: 'cubic-bezier(.22,1,.36,1)', fill: 'backwards' });
      animations.add(animation);
      animation.finished.then(() => animations.delete(animation), () => animations.delete(animation));
    }
    function register(element, order) {
      if (preference.matches || seen.has(element) || element.closest('[hidden],[inert],[aria-hidden="true"]')) return;
      // Avoid nested opacity and transform effects on the same content.
      if (element.parentElement?.closest(READING_BLOCKS)) return;
      seen.add(element);
      const box = element.getBoundingClientRect();
      if (!box.width || !box.height) return;
      if (box.top < window.innerHeight - 24 && box.bottom > 0) reveal(element, (order % 4) * 45);
      else {
        pending.add(element);
        element.classList.add('dp-motion-pending');
        observer.observe(element);
      }
    }
    function scan(node) {
      if (!(node instanceof Element)) return;
      if (node.matches(READING_BLOCKS)) register(node, 0);
      node.querySelectorAll(READING_BLOCKS).forEach(register);
    }
    const mutations = new MutationObserver(records => {
      for (const record of records) {
        if (record.type === 'attributes') scan(record.target);
        else record.addedNodes.forEach(scan);
      }
    });
    scan(root);
    mutations.observe(root, { childList: true, subtree: true, attributes: true, attributeFilter: ['hidden', 'inert'] });
    const focus = event => {
      for (let node = event.target; node && node !== root; node = node.parentElement) {
        if (pending.has(node)) reveal(node, 0, true);
      }
    };
    const reduce = () => {
      if (!preference.matches) { scan(root); return; }
      for (const element of [...pending]) reveal(element, 0, true);
      for (const animation of animations) animation.cancel();
      animations.clear();
    };
    root.addEventListener('focusin', focus);
    preference.addEventListener('change', reduce);
    return () => {
      observer.disconnect(); mutations.disconnect();
      root.removeEventListener('focusin', focus);
      preference.removeEventListener('change', reduce);
      for (const element of pending) element.classList.remove('dp-motion-pending');
      for (const animation of animations) animation.cancel();
    };
  }, [rootRef, routeKey, enabled]);
}
