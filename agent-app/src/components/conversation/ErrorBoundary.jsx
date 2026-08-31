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
    if (import.meta.env.DEV && info?.componentStack) this.setState({ info: info.componentStack });
  }

  render() {
    if (this.state.error) {
      const msg = import.meta.env.DEV ? String(this.state.error.message || this.state.error) : null;
      const stack = import.meta.env.DEV ? this.state.info : null;
      return (
        <div style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--text-dim)', fontSize: 14 }}>
          <div>出错了 — {msg || '请刷新页面重试'}</div>
          {stack && <pre style={{ margin: '14px auto 0', maxWidth: 720, textAlign: 'left', fontSize: 10.5,
            whiteSpace: 'pre-wrap', color: 'var(--text-dim)', background: 'var(--soft)', padding: 10, borderRadius: 8 }}>{stack}</pre>}
          <button onClick={() => { this.setState({ error: null, info: null }); this.props.onRetry?.(); }}
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
