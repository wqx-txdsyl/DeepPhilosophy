/**
 * SEO utilities — dynamic <title> and meta tags per route
 */
import { useEffect } from 'react';

const DEFAULT_TITLE = 'DeepPhilosophy — 哲学爱好者移动应用';
const DEFAULT_DESC = '从公元前三十世纪至二十一世纪，一部横跨五千年的思想史长卷。探索世界哲学流派、哲学家与经典著作。';

/**
 * Set page title and meta description.
 * Restores defaults on unmount.
 */
export function useSEO(title, description) {
  useEffect(() => {
    const prevTitle = document.title;
    const prevDesc = document.querySelector('meta[name="description"]')?.getAttribute('content') || '';

    if (title) {
      document.title = `${title} - DeepPhilosophy`;
    }
    if (description) {
      let meta = document.querySelector('meta[name="description"]');
      if (!meta) {
        meta = document.createElement('meta');
        meta.name = 'description';
        document.head.appendChild(meta);
      }
      meta.setAttribute('content', description);
    }

    return () => {
      document.title = prevTitle;
      const meta = document.querySelector('meta[name="description"]');
      if (meta) meta.setAttribute('content', prevDesc || DEFAULT_DESC);
    };
  }, [title, description]);
}

export { DEFAULT_TITLE, DEFAULT_DESC };
