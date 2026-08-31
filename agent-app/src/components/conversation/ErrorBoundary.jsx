import { Component } from 'react';

/**
 * TopLevel ErrorBoundary — 局部错误不白屏（spec §37 错误 UX）
 * 不显示 stack trace; 开发环境附带 error.message 便于定位。
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('[PhiAgent] 渲染错误', error, info);
  }

  render() {
    if (this.state.error) {
      const msg = import.meta.env.DEV ? String(this.state.error.message || this.state.error) : null;
      return (
        <div style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--text-dim)', fontSize: 14 }}>
          <div>出错了 — {msg || '请刷新页面重试'}</div>
          <button onClick={() => { this.setState({ error: null }); this.props.onRetry?.(); }}
            style={{ marginTop: 12, padding: '8px 18px', borderRadius: 8, cursor: 'pointer',
                     border: '1px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}>
            重试
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
