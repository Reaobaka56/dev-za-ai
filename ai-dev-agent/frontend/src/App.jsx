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
          <li><a href="#product">Product</a></li>
          <li><a href="#testimonials">Testimonials</a></li>
          <li><a href="#how-it-works">How it works</a></li>
        </ul>
        <button className="nav-button">Join Beta</button>
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
          <button className="btn-primary">Apply for Beta</button>
          <button className="btn-secondary">Learn More</button>
        </div>

        <div className="logo-circle">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        </div>
      </main>
    </>
  );
}

export default App;
