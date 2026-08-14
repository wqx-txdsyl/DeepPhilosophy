import { useState, useEffect } from 'react';
import AgentPage from './pages/AgentPage';
import AgentSidebar from './components/AgentSidebar';
import { AuthProvider } from './auth';
import { LangProvider } from './utils/i18n';
import { initTheme } from './utils/theme';

export default function App() {
  useEffect(() => { initTheme(); }, []);
  const [agent, setAgent] = useState('general');
  const [chatKey, setChatKey] = useState(0);   // 切换智能体时重置对话

  const handleSelect = (key) => {
    if (key !== agent) {
      setAgent(key);
      setChatKey(k => k + 1);   // 每个智能体独立对话
    }
  };

  return (
    <AuthProvider>
      <LangProvider>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <AgentSidebar current={agent} onSelect={handleSelect} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <AgentPage key={chatKey} agent={agent} />
        </div>
      </div>
      </LangProvider>
    </AuthProvider>
  );
}
