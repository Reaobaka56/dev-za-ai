import React, { useState, useEffect } from 'react';
import { Terminal, Send, CheckCircle2, ChevronRight } from 'lucide-react';
import './index.css';

function App() {
  const [demoInput, setDemoInput] = useState('');
  const [messages, setMessages] = useState([
    { type: 'agent', text: 'Hi! I am Agent.ai. Paste some code or describe a bug, and I will fix it for you.' }
  ]);
  const [isTyping, setIsTyping] = useState(false);

  // Counter logic
  const [stats, setStats] = useState({ devs: 0, accuracy: 0, time: 0 });
  
  useEffect(() => {
    // Simple animation for counters on load
    let currentDevs = 0;
    const interval = setInterval(() => {
      currentDevs += 500;
      if (currentDevs <= 50000) {
        setStats({ devs: currentDevs, accuracy: 99.2, time: 0.3 });
      } else {
        clearInterval(interval);
      }
    }, 20);
    return () => clearInterval(interval);
  }, []);

  const handleDemoSubmit = (e) => {
    e.preventDefault();
    if (!demoInput.trim()) return;
    
    setMessages(prev => [...prev, { type: 'user', text: demoInput }]);
    setDemoInput('');
    setIsTyping(true);
    
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        type: 'agent', 
        text: `Found the issue! On line 47, you're trying to access a property on an undefined object. I've initialized the state and added a null check. The code diff is ready to copy.` 
      }]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <>
      <div className="bg-effects">
        <div className="aurora-blur"></div>
      </div>

      <nav className="navbar">
        <div className="nav-brand">Agent.ai</div>
        <ul className="nav-links">
          <li><a href="#demo">Demo</a></li>
          <li><a href="#diff">Features</a></li>
          <li><a href="#install">Install</a></li>
        </ul>
        <a href="https://github.com/Reaobaka56/dev-za-ai" target="_blank" rel="noreferrer" className="nav-button" style={{textDecoration: 'none'}}>Join Beta</a>
      </nav>

      <main className="hero">
        <div className="nodes-container">
          <div className="glass-node right-dot" style={{ top: '30%', left: '15%', animationDelay: '0s' }}>Enhancement</div>
          <div className="glass-node left-dot" style={{ top: '25%', right: '20%', animationDelay: '1s' }}>Research</div>
          <div className="glass-node bottom-dot" style={{ top: '45%', left: '25%', animationDelay: '2s' }}>Automation</div>
          <div className="glass-node right-dot" style={{ bottom: '25%', left: '18%', animationDelay: '3s' }}>Scalability</div>
          <div className="glass-node top-dot" style={{ bottom: '30%', right: '25%', animationDelay: '4s' }}>Connection</div>
          <div className="glass-node left-dot" style={{ bottom: '15%', right: '40%', animationDelay: '1.5s' }}>Generation</div>
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
      </main>

      {/* Stats Counters */}
      <section className="stats-container">
        <div className="stat-item">
          <div className="stat-number">{stats.devs >= 50000 ? '50K+' : stats.devs}</div>
          <div className="stat-label">Devs Worldwide</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">{stats.accuracy}%</div>
          <div className="stat-label">Bug Fix Accuracy</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">{stats.time}s</div>
          <div className="stat-label">Avg Fix Time</div>
        </div>
      </section>

      {/* Interactive Demo Playground */}
      <section id="demo" className="demo-section">
        <h2 style={{ textAlign: 'center', fontSize: '2.5rem', marginBottom: '2rem' }}>Experience the Magic</h2>
        <div className="demo-container">
          <div className="demo-header">
            <div className="demo-dots">
              <div className="demo-dot"></div><div className="demo-dot"></div><div className="demo-dot"></div>
            </div>
            <span style={{color: 'var(--text-secondary)', fontSize: '0.9rem', fontFamily: 'monospace'}}><Terminal size={14} style={{display:'inline', verticalAlign:'middle', marginRight:'5px'}}/> agent-cli --interactive</span>
          </div>
          
          <div className="demo-chat">
            {messages.map((m, i) => (
              <div key={i} className={`message ${m.type}`}>
                {m.text}
                {m.type === 'agent' && i > 0 && (
                  <button className="nav-button" style={{marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '5px', padding: '0.4rem 0.8rem', fontSize: '0.8rem'}}>
                    <CheckCircle2 size={14} /> Copy Fix
                  </button>
                )}
              </div>
            ))}
            {isTyping && <div className="message agent">Analyzing context...</div>}
          </div>

          <form onSubmit={handleDemoSubmit} className="demo-input-area">
            <input 
              type="text" 
              className="demo-input" 
              placeholder="e.g. Debug this useState error in my React component..."
              value={demoInput}
              onChange={(e) => setDemoInput(e.target.value)}
            />
            <button type="submit" className="btn-primary" style={{padding: '0.8rem 1.5rem'}} disabled={isTyping}>
              <Send size={18} />
            </button>
          </form>
        </div>
      </section>

      {/* Live Code Editor Diff */}
      <section id="diff" className="diff-section">
        <h2 style={{ textAlign: 'center', fontSize: '2.5rem', marginBottom: '1rem' }}>Instant Context-Aware Fixes</h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '3rem' }}>Agent understands your entire repository to provide perfect drop-in replacements.</p>
        
        <div className="diff-container">
          {/* Before */}
          <div className="diff-card">
            <div className="diff-header error">BEFORE (Buggy)</div>
            <div className="diff-body">
{`function FetchUser() {
  const [user] = useState()
  
`}
<span className="diff-line removed">{`  // ERROR HERE! Cannot read property 'name' of undefined`}</span>
<span className="diff-line removed">{`  return user.name `}</span>
{`
}`}
            </div>
          </div>
          
          {/* After */}
          <div className="diff-card">
            <div className="diff-header success">AFTER (Fixed by Agent.ai)</div>
            <div className="diff-body">
{`function FetchUser() {
`}
<span className="diff-line added">{`  const [user, setUser] = useState(null)`}</span>
{`  
`}
<span className="diff-line added">{`  if (!user) return null`}</span>
<span className="diff-line added">{`  return user.name`}</span>
{`
}`}
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Carousel */}
      <section id="testimonials" className="testimonials-section">
        <h2 style={{ textAlign: 'center', fontSize: '2.5rem', marginBottom: '3rem' }}>Loved by Engineers</h2>
        <div className="testimonial-carousel">
          <div className="testimonial-card">
            <div className="testimonial-text">"Agent saved me 6 hours debugging complex Redux state issues. It instantly understood my store context."</div>
            <div className="testimonial-author">
              <div className="testimonial-avatar"></div>
              <div>
                <div style={{fontWeight: '600'}}>Sarah Chen</div>
                <div style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>Senior Engineer @ Stripe</div>
              </div>
            </div>
          </div>
          <div className="testimonial-card">
            <div className="testimonial-text">"The only AI tool I've used that actually proposes working, production-ready code with tests included."</div>
            <div className="testimonial-author">
              <div className="testimonial-avatar"></div>
              <div>
                <div style={{fontWeight: '600'}}>Markus L.</div>
                <div style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>Lead Dev @ Vercel</div>
              </div>
            </div>
          </div>
          <div className="testimonial-card">
            <div className="testimonial-text">"It's like having a senior engineer constantly pair-programming with me. Phenomenal product."</div>
            <div className="testimonial-author">
              <div className="testimonial-avatar"></div>
              <div>
                <div style={{fontWeight: '600'}}>Elena Rust</div>
                <div style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>CTO @ StartupX</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="install" style={{ padding: '6rem 2rem', textAlign: 'center', zIndex: 10, position: 'relative' }}>
        <h2 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>Get Started Locally</h2>
        <div style={{ background: 'var(--glass-bg)', padding: '2rem', borderRadius: '16px', border: '1px solid var(--glass-border)', display: 'inline-block', textAlign: 'left', backdropFilter: 'blur(10px)', boxShadow: 'var(--glass-shadow)', maxWidth: '600px', width: '100%' }}>
          <pre style={{ color: 'var(--accent-light)', whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '1rem', lineHeight: '1.6' }}>
            <code>git clone https://github.com/Reaobaka56/dev-za-ai.git</code><br/>
            <code>cd dev-za-ai</code><br/>
            <code>pip install -r requirements.txt</code><br/>
            <code>uvicorn app:app --port 8000</code><br/>
          </pre>
        </div>
      </section>
    </>
  );
}

export default App;
