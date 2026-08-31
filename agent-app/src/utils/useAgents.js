import { useEffect, useState } from 'react';
import { getApiBase } from './api';

/**
 * useAgents — 智能体列表（/api/agents: general + 后端注册表哲学家）
 * 带超时 + 自动重试（服务器启动期后端未就绪时自动等待, 沿用旧 Sidebar 行为）。
 */
export default function useAgents() {
  const [agents, setAgents] = useState([
    { key: 'general', name: '深哲', subtitle: '通用哲学智能体', tagline: '检索/思辨/辩论/生图/写作/疏导', portrait: null },
  ]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let retries = 0;
    const load = () => {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 5000);
      fetch(`${getApiBase()}/api/agents`, { signal: ctrl.signal })
        .then(r => r.json())
        .then(d => {
          clearTimeout(timer);
          if (!cancelled && d.agents?.length) {
            setAgents(d.agents);
            setLoading(false);
          } else if (!cancelled) {
            setLoading(false);
          }
        })
        .catch(() => {
          clearTimeout(timer);
          if (!cancelled && retries < 10) {
            retries += 1;
            setTimeout(load, 2000);   // 2s 后重试（最多 10 次, 覆盖后端启动窗口）
          } else if (!cancelled) {
            setLoading(false);
          }
        });
    };
    load();
    return () => { cancelled = true; };
  }, []);

  return { agents, agentsLoading: loading };
}
