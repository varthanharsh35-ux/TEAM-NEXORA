import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import i18n from './i18n';
import './index.css';

class Boundary extends React.Component {
  state = { failed: false, error: null };

  static getDerivedStateFromError(error) {
    return { failed: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('GramSahayak Boundary caught an error:', error, errorInfo);
  }

  resetAndReload = () => {
    try {
      localStorage.removeItem('gs-report');
      localStorage.removeItem('gs-draft');
      localStorage.removeItem('gs-history');
    } catch {}
    window.location.reload();
  };

  render() {
    if (this.state.failed) {
      return (
        <main className="fatal" style={{ padding: '3rem 1.5rem', textAlign: 'center', maxWidth: '640px', margin: '4rem auto', background: '#ffffff', borderRadius: '12px', boxShadow: '0 8px 30px rgba(0,0,0,0.08)', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🌱</div>
          <h1 style={{ color: '#0f172a', fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.75rem' }}>
            {i18n.t('fatal') || 'Something went wrong. Reload to restore your saved plan.'}
          </h1>
          <p style={{ color: '#64748b', fontSize: '0.92rem', lineHeight: 1.6, marginBottom: '1.75rem' }}>
            A temporary display issue occurred while rendering. Click reload to try again, or reset your active draft if data became inconsistent.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="primary"
              onClick={() => window.location.reload()}
              style={{ padding: '10px 22px', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer' }}
            >
              {i18n.t('reload') || 'Reload Page'}
            </button>
            <button
              type="button"
              onClick={this.resetAndReload}
              style={{
                padding: '10px 22px',
                background: '#f8fafc',
                color: '#334155',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer'
              }}
            >
              Reset Saved Workspace
            </button>
          </div>
        </main>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Boundary>
      <App />
    </Boundary>
  </React.StrictMode>
);

if (import.meta.env.PROD && 'serviceWorker' in navigator)
  navigator.serviceWorker.register('/sw.js').catch(() => {});
