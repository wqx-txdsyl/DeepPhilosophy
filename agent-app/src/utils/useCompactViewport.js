import { useEffect, useState } from 'react';
export default function useCompactViewport() {
  const [compact,setCompact] = useState(()=>typeof window !== 'undefined' && !!window.matchMedia?.('(max-width: 600px)').matches);
  useEffect(()=>{
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const media=window.matchMedia('(max-width: 600px)');
    const update=()=>setCompact(media.matches);
    if (media.addEventListener) media.addEventListener('change',update); else media.addListener(update);
    return ()=>{ if (media.removeEventListener) media.removeEventListener('change',update); else media.removeListener(update); };
  },[]);
  return compact;
}
