import React from 'react';
import './index.css';

function App() {
  return (
    <>
      <div className="bg-effects">
        <div className="aurora-blur"></div>
      </div>

      <nav className="navbar">
        <div className="nav-brand">Agent.ai</div>
        <ul className="nav-links">
          <li><a href="#features">Features</a></li>
          <li><a href="#install">Installation</a></li>
          <li><a href="#testimonials">Testimonials</a></li>
          <li><a href="#how-it-works">How it works</a></li>
        </ul>
        <a href="https://github.com/Reaobaka56/dev-za-ai" target="_blank" rel="noreferrer" className="nav-button" style={{textDecoration: 'none'}}>Join Beta</a>
      </nav>

      <main className="hero">
        <div className="nodes-container">
          <div className="glass-node right-dot" style={{ top: '30%', left: '15%', animationDelay: '0s' }}>
            Enhancement
          </div>
          <div className="glass-node left-dot" style={{ top: '25%', right: '20%', animationDelay: '1s' }}>
            Research
          </div>
          <div className="glass-node bottom-dot" style={{ top: '45%', left: '25%', animationDelay: '2s' }}>
            Automation
          </div>
          <div className="glass-node right-dot" style={{ bottom: '25%', left: '18%', animationDelay: '3s' }}>
            Scalability
          </div>
          <div className="glass-node top-dot" style={{ bottom: '30%', right: '25%', animationDelay: '4s' }}>
            Connection
          </div>
          <div className="glass-node left-dot" style={{ bottom: '15%', right: '40%', animationDelay: '1.5s' }}>
            Generation
          </div>
        </div>

        <div className="badge">Beta 2.1</div>
        
        <h1>
          Meet Agent!<br />
          Built By AI. For Developers.
        </h1>
        
        <p>
          Agent uses cutting-edge AI built with empathy at its core. Whether you're scaffolding a new app, finding a complex bug, or optimizing your ML models, it's like having an expert by your side.
        </p>

        <div className="hero-buttons">
          <a href="https://github.com/Reaobaka56/dev-za-ai" target="_blank" rel="noreferrer" className="btn-primary" style={{textDecoration: 'none'}}>View Repository</a>
          <a href="#install" className="btn-secondary" style={{textDecoration: 'none'}}>How to Install</a>
        </div>

        <div className="logo-circle">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        </div>
      </main>

      <section id="install" style={{ padding: '6rem 2rem', textAlign: 'center', zIndex: 10, position: 'relative' }}>
        <h2 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>Get Started Locally</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '3rem', maxWidth: '600px', margin: '0 auto 3rem auto' }}>
          Follow these simple steps to clone the repository and run the AI Dev Agent environment on your own machine.
        </p>
        <div style={{ background: 'var(--glass-bg)', padding: '2rem', borderRadius: '16px', border: '1px solid var(--glass-border)', display: 'inline-block', textAlign: 'left', backdropFilter: 'blur(10px)', boxShadow: 'var(--glass-shadow)', maxWidth: '600px', width: '100%' }}>
          <pre style={{ color: 'var(--accent-light)', marginBottom: '1rem', whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '1rem', lineHeight: '1.6' }}>
            <code>git clone https://github.com/Reaobaka56/dev-za-ai.git</code><br/>
            <code>cd dev-za-ai</code><br/>
            <code># Run backend model:</code><br/>
            <code>pip install -r requirements.txt</code><br/>
            <code>uvicorn app:app --port 8000</code><br/><br/>
            <code># Or run via Docker:</code><br/>
            <code>docker build -t ml-model .</code><br/>
            <code>docker run -p 8000:8000 ml-model</code>
          </pre>
        </div>
      </section>
    </>
  );
}

export default App;
