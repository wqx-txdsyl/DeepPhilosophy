import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AgentWorkspace from './pages/AgentPage';
import ErrorBoundary from './components/conversation/ErrorBoundary';
import { AuthProvider } from './auth';
import { LangProvider } from './utils/i18n';
import { initTheme } from './utils/theme';

/**
 * PhiAgent 工作区路由（conversation-first, §12）:
 *   /agent           → 临时 Draft（首条消息后才 persist）
 *   /agent/c/:id     → 稳定会话身份（刷新后可恢复）
 * 单条可选参数 route 复用同一组件实例, 会话切换不重挂载（流式可跨会话并行）。
 */
export default function App() {
  useEffect(() => { initTheme(); }, []);
  return (
    <AuthProvider>
      <LangProvider>
        <BrowserRouter>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<Navigate to="/agent" replace />} />
              {/* 单一 splat route: /agent 与 /agent/c/:id 命中同一组件实例（不重挂载, 流式跨会话并行） */}
              <Route path="/agent/*" element={<AgentWorkspace />} />
              <Route path="*" element={<Navigate to="/agent" replace />} />
            </Routes>
          </ErrorBoundary>
        </BrowserRouter>
      </LangProvider>
    </AuthProvider>
  );
}
