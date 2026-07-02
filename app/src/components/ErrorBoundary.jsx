/**
 * Error Boundary — catches rendering crashes and shows fallback UI
 */
import { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', minHeight: '60vh', padding: 32,
          textAlign: 'center', fontFamily: 'var(--font-sans)',
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>😞</div>
          <h2 style={{ fontSize: 18, color: 'var(--ink)', marginBottom: 8 }}>
            页面加载出错
          </h2>
          <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 20, maxWidth: 400 }}>
            {this.state.error?.message || '发生了未知错误'}
          </p>
          <button className="btn btn-primary" onClick={() => {
            this.setState({ hasError: false, error: null });
            window.location.reload();
          }}>
            刷新页面
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
