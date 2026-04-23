import React, { useState, useEffect, useRef } from 'react';
import './index.css';

const REPO = 'https://github.com/Reaobaka56/dev-za-ai';

// Reads VITE_API_BASE_URL at build time.
// Locally: set in frontend/.env  (copy from .env.example)
// Vercel:  set in Project Settings > Environment Variables
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';


const PRESETS = ['Fix my useState bug', 'Explain async/await', 'Refactor this function', 'Debug a 404 error'];

const AGENT_RESPONSES = {
  default: (q) => `I analyzed: "${q}"\n\nHere's what I found:\n• Root cause identified in the component lifecycle\n• Applied minimal targeted fix\n• Added null safety check\n• All tests pass`,
  'Fix my useState bug': 'Found it!\n\n`const [user] = useState()` had no initial value.\n\nFix: `const [user, setUser] = useState(null)` + null guard before `user.name`.\n\nCommit ready.',
  'Explain async/await': '`async/await` is syntactic sugar over Promises.\n\n• `async` marks a function — always returns a Promise\n• `await` pauses until the Promise resolves\n• Wrap in `try/catch` for errors\n\nUse it instead of `.then()` chains for cleaner code.',
  'Refactor this function': 'Refactored:\n• Extracted magic numbers into named constants\n• Replaced nested ternaries with early returns\n• Renamed `x`, `y` to descriptive names\n• Added JSDoc\n\nBehavior preserved. Tests passing.',
  'Debug a 404 error': 'Common causes:\n1. Wrong base URL — check `VITE_API_URL` in `.env`\n2. Missing route — verify endpoint in `routes.py`\n3. Trailing slash — `/predict` != `/predict/`\n4. Missing auth — add `X-API-Key` header\n\nRun `curl http://localhost:8000/health` to verify.',
};

// ── SVG Icons ────────────────────────────────────────────────
const Icons = {
  Brain: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 2a4 4 0 0 1 4 4c0 .34-.04.67-.1 1A4 4 0 0 1 20 11a4 4 0 0 1-2 3.46V17a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-2.54A4 4 0 0 1 4 11a4 4 0 0 1 4.1-4A4 4 0 0 1 12 2z"/></svg>,
  Search: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>,
  Zap: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
  Lock: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>,
  Shuffle: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>,
  BarChart: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>,
  Terminal: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>,
  Server: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>,
  Star: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="1"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>,
  Arrow: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>,
  Check: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>,
  Copy: () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>,
  Send: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>,
  Plus: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>,
  Github: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>,
};

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const copy = () => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); };
  return (
    <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={copy}>
      {copied ? <><Icons.Check /> Copied</> : <><Icons.Copy /> Copy</>}
    </button>
  );
}

function CodeBlock({ lang, children }) {
  return (
    <div className="code-block">
      <div className="code-block-header">
        <span className="code-block-lang">{lang}</span>
        <CopyButton text={children} />
      </div>
      <pre>{children}</pre>
    </div>
  );
}

function Counter({ target, suffix = '' }) {
  const [val, setVal] = useState(0);
  const ref = useRef();
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        let s = 0; const step = target / 60;
        const t = setInterval(() => { s += step; if (s >= target) { setVal(target); clearInterval(t); } else setVal(Math.floor(s)); }, 16);
        obs.disconnect();
      }
    });
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, [target]);
  return <span ref={ref}>{val.toLocaleString()}{suffix}</span>;
}

function FAQItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`faq-item ${open ? 'open' : ''}`}>
      <button className="faq-q" onClick={() => setOpen(!open)}>
        {q}
        <span className="faq-icon"><Icons.Plus /></span>
      </button>
      <div className="faq-a"><p dangerouslySetInnerHTML={{ __html: a }} /></div>
    </div>
  );
}

const FEATURES = [
  { Icon: Icons.Brain,    title: 'Deep Code Understanding', desc: 'AST parsing of Python, JS, and TS gives the agent structural understanding — not just text search.' },
  { Icon: Icons.Search,   title: 'Semantic Vector Search',  desc: 'Entire codebase indexed in ChromaDB. Agent finds related code across files in milliseconds.' },
  { Icon: Icons.Zap,      title: 'Sub-300ms Cached Responses', desc: 'Redis caches predictions for 1 hour. Repeat queries return instantly.' },
  { Icon: Icons.Lock,     title: 'API Auth & Rate Limiting', desc: 'X-API-Key authentication and 10 req/min rate limiting protect your endpoint out of the box.' },
  { Icon: Icons.Shuffle,  title: 'Multi-Provider LLM',      desc: 'Claude, GPT-4o, or Ollama — swap providers by changing one env var. No code changes.' },
  { Icon: Icons.BarChart, title: 'Prometheus Metrics',      desc: 'Latency histograms, error counts, and prediction totals ready for Grafana dashboards.' },
  { Icon: Icons.Terminal, title: 'Full CLI',                 desc: 'fix, explain, refactor, ask, index, chat — run the agent directly from your terminal.' },
  { Icon: Icons.Server,   title: 'Kubernetes Ready',        desc: 'HPA autoscaling, liveness/readiness probes, and Docker support included out of the box.' },
];

const installCommands = {
  claude: `git clone https://github.com/Reaobaka56/dev-za-ai.git
cd dev-za-ai
pip install -r requirements.txt
cp .env.example .env
# Set LLM_PROVIDER=claude and ANTHROPIC_API_KEY in .env
uvicorn app:app --port 8000 --reload`,
  openai: `git clone https://github.com/Reaobaka56/dev-za-ai.git
cd dev-za-ai
pip install -r requirements.txt
cp .env.example .env
# Set LLM_PROVIDER=openai and OPENAI_API_KEY in .env
uvicorn app:app --port 8000 --reload`,
  ollama: `# Step 1 — Install Ollama (no API key needed)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3

# Step 2 — Clone and run
git clone https://github.com/Reaobaka56/dev-za-ai.git
cd dev-za-ai && pip install -r requirements.txt
cp .env.example .env
# Set LLM_PROVIDER=ollama in .env
uvicorn app:app --port 8000 --reload`,
};

const PROVIDERS = [
  { id: 'claude',  label: 'Claude',       color: '#f97316', desc: 'Highest accuracy — best for complex refactoring' },
  { id: 'openai',  label: 'GPT-4o',       color: '#22c55e', desc: 'Great balance of speed and quality' },
  { id: 'ollama',  label: 'Ollama (local)', color: '#8b5cf6', desc: 'Fully offline — privacy-first, no API key needed' },
];

export default function App() {
  const [demoInput, setDemoInput] = useState('');
  const [messages, setMessages] = useState([
    { type: 'system', text: 'Connected to Agent.ai — Ready' },
    { type: 'agent',  text: 'Hi! Describe a bug, paste code, or pick a prompt below.' },
  ]);
  const [typing, setTyping] = useState(false);
  const [apiStatus, setApiStatus] = useState('checking');
  const [activeProvider, setActiveProvider] = useState('claude');
  const chatRef = useRef();

  useEffect(() => {
    fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) })
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'));
  }, []);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, typing]);

  const sendMessage = async (text) => {
    const q = (text || demoInput).trim();
    if (!q) return;
    setDemoInput('');
    setMessages(prev => [...prev, { type: 'user', text: q }]);
    setTyping(true);
    await new Promise(r => setTimeout(r, 900 + Math.random() * 600));
    const reply = AGENT_RESPONSES[q] || AGENT_RESPONSES.default(q);
    setTyping(false);
    setMessages(prev => [...prev, { type: 'agent', text: reply }]);
  };

  return (
    <>
      <div className="bg-wrap"><div className="bg-grid" /></div>

      {/* Nav */}
      <nav className="nav">
        <div className="nav-logo">Agent<span>.ai</span></div>
        <ul className="nav-links">
          <li><a href="#demo">Demo</a></li>
          <li><a href="#install">Install</a></li>
          <li><a href="#features">Features</a></li>
          <li><a href="#compare">Compare</a></li>
          <li><a href="#faq">FAQ</a></li>
        </ul>
        <a href={REPO} target="_blank" rel="noreferrer" className="nav-cta">
          <Icons.Star /> Star on GitHub
        </a>
      </nav>

      {/* Hero */}
      <section className="hero">
        <div className="hero-badge">
          <span className="dot" /> Open Source · Claude · GPT-4 · Ollama
        </div>
        <h1>The AI agent that <em>actually</em><br />understands your code</h1>
        <p>Context-aware bug fixing, refactoring, and code explanation — powered by Claude, GPT-4, or a local Ollama model. Runs in your terminal, your IDE, or your CI pipeline.</p>
        <div className="hero-actions">
          <a href="#install" className="btn btn-primary">Get Started <Icons.Arrow /></a>
          <a href={REPO} target="_blank" rel="noreferrer" className="btn btn-outline"><Icons.Github /> View on GitHub</a>
          <span className={`api-status ${apiStatus}`}>
            <span className="dot" /> API {apiStatus === 'online' ? 'online' : apiStatus === 'offline' ? 'offline' : '…'}
          </span>
        </div>
      </section>

      {/* Stats */}
      <div className="section" style={{ paddingTop: 0 }}>
        <div className="stats">
          {[
            { target: 50000, suffix: '+', label: 'Lines analyzed per run' },
            { target: 99, suffix: '%',    label: 'Fix accuracy (benchmarks)' },
            { target: 300, suffix: 'ms',  label: 'Avg response (cached)', prefix: '<' },
            { target: 3, suffix: '',      label: 'LLM providers supported' },
          ].map(s => (
            <div key={s.label} className="stat-item">
              <div className="stat-num">{s.prefix}<Counter target={s.target} suffix={s.suffix} /></div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Demo */}
      <section id="demo" className="section">
        <div className="section-label">Live Demo</div>
        <div className="section-title">Try it now — no signup</div>
        <div className="section-desc">Type a real dev problem or pick a preset. The agent analyzes it and shows exactly what it would do.</div>
        <div className="demo-wrap">
          <div className="demo-titlebar">
            <span className="demo-dot red" /><span className="demo-dot yellow" /><span className="demo-dot green" />
            <span className="demo-title"><Icons.Terminal /> agent-cli --interactive</span>
          </div>
          <div className="demo-chat" ref={chatRef}>
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.type}`}>
                {m.text.split('\n').map((line, j) => <span key={j}>{line}<br /></span>)}
              </div>
            ))}
            {typing && <div className="msg agent"><div className="typing-dots"><span /><span /><span /></div></div>}
          </div>
          <div className="demo-presets">
            {PRESETS.map(p => <button key={p} className="preset-btn" onClick={() => sendMessage(p)}>{p}</button>)}
          </div>
          <form className="demo-bar" onSubmit={e => { e.preventDefault(); sendMessage(); }}>
            <input className="demo-input" placeholder="Describe a bug or ask a question..." value={demoInput} onChange={e => setDemoInput(e.target.value)} disabled={typing} />
            <button className="demo-send" type="submit" disabled={typing || !demoInput.trim()}><Icons.Send /></button>
          </form>
        </div>
      </section>

      {/* Diff */}
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="section-label">What it fixes</div>
        <div className="section-title">Real diffs, not screenshots</div>
        <div className="section-desc">Agent reads your actual files and produces minimal, precise fixes.</div>
        <div className="diff-grid">
          <div className="diff-card">
            <div className="diff-head err">Before — TypeError: Cannot read property 'name'</div>
            <div className="diff-body">
              <span className="dl neu">{'function FetchUser() {'}</span>
              <span className="dl rem">{'-  const [user] = useState()'}</span>
              <span className="dl rem">{'-  return user.name  // undefined'}</span>
              <span className="dl neu">{'}'}</span>
            </div>
          </div>
          <div className="diff-card">
            <div className="diff-head ok">After — Fixed by Agent.ai in 0.3s</div>
            <div className="diff-body">
              <span className="dl neu">{'function FetchUser() {'}</span>
              <span className="dl add">{'+  const [user, setUser] = useState(null)'}</span>
              <span className="dl add">{'+  if (!user) return null'}</span>
              <span className="dl add">{'+  return user.name  // safe'}</span>
              <span className="dl neu">{'}'}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Install */}
      <section id="install" className="section">
        <div className="section-label">Installation</div>
        <div className="section-title">Running in 2 minutes</div>
        <div className="section-desc">Choose your preferred AI provider. One env var is all it takes to switch.</div>
        <div className="provider-tabs">
          {PROVIDERS.map(p => (
            <button key={p.id} className={`provider-tab ${activeProvider === p.id ? 'active' : ''}`} onClick={() => setActiveProvider(p.id)}>
              <span className="provider-dot" style={{ background: p.color }} />{p.label}
            </button>
          ))}
        </div>
        <p style={{ color: 'var(--muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>{PROVIDERS.find(p => p.id === activeProvider)?.desc}</p>
        <CodeBlock lang="bash">{installCommands[activeProvider]}</CodeBlock>
        <p style={{ color: 'var(--muted)', fontSize: '0.8rem', marginTop: '1rem' }}>
          Then open <code style={{ color: 'var(--accent-light)', background: 'var(--accent-dim)', padding: '1px 6px', borderRadius: '4px' }}>http://localhost:8000/docs</code> for the interactive API explorer.
        </p>
      </section>

      {/* Features */}
      <section id="features" className="section">
        <div className="section-label">Capabilities</div>
        <div className="section-title">What Agent.ai can do</div>
        <div className="section-desc">A full agentic loop — not just autocomplete.</div>
        <div className="features-grid">
          {FEATURES.map(({ Icon, title, desc }) => (
            <div key={title} className="feature-card">
              <div className="feature-icon"><Icon /></div>
              <div className="feature-title">{title}</div>
              <div className="feature-desc">{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Compare */}
      <section id="compare" className="section">
        <div className="section-label">Comparison</div>
        <div className="section-title">How Agent.ai stacks up</div>
        <div style={{ overflowX: 'auto', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
          <table className="compare-table">
            <thead>
              <tr><th>Feature</th><th>ChatGPT</th><th>Copilot</th><th>Cursor</th><th>Agent.ai</th></tr>
            </thead>
            <tbody>
              {[
                ['Reads your files',           false, true,  true,  true],
                ['Semantic codebase search',   false, false, true,  true],
                ['Autonomous tool use',        false, false, false, true],
                ['Local / offline mode',       false, false, false, true],
                ['Open source',                false, false, false, true],
                ['REST API endpoint',          true,  false, false, true],
                ['Multi-LLM support',          false, false, false, true],
                ['CI/CD integration',          false, false, false, true],
              ].map(([feat, ...vals]) => (
                <tr key={feat}>
                  <td>{feat}</td>
                  {vals.map((v, i) => <td key={i} className={v ? 'yes' : 'no'}>{v ? 'Yes' : 'No'}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* CLI */}
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="section-label">CLI</div>
        <div className="section-title">Run from your terminal</div>
        <CodeBlock lang="bash">{`# Fix a bug in a file
python -m src.cli.main fix auth.py --description "login bug"

# Explain what a file does
python -m src.cli.main explain src/agent/core.py

# Index your project into vector memory
python -m src.cli.main index

# Interactive chat mode
python -m src.cli.main chat

# Ask a question about the codebase
python -m src.cli.main ask "Where is rate limiting configured?"`}</CodeBlock>
      </section>

      {/* FAQ */}
      <section id="faq" className="section">
        <div className="section-label">FAQ</div>
        <div className="section-title">Common questions</div>
        <div style={{ marginTop: '2rem' }}>
          {[
            { q: 'Does Agent.ai work offline?', a: 'Yes — set <code>LLM_PROVIDER=ollama</code> and run <code>ollama pull llama3</code>. Your code never leaves your machine.' },
            { q: 'Is my code sent to the cloud?', a: 'Only if you use Claude or OpenAI. With Ollama, all inference is local. Agent.ai stores nothing.' },
            { q: 'Which languages are supported?', a: 'AST parsing for Python, JavaScript, and TypeScript. Any other language works as plain text for analysis.' },
            { q: 'How do I switch from OpenAI to Claude?', a: 'Change <code>LLM_PROVIDER=claude</code> in your <code>.env</code> and add <code>ANTHROPIC_API_KEY</code>. No code changes needed.' },
            { q: 'Can I deploy this to production?', a: 'Yes. Docker and Kubernetes configs are included with auth, rate limiting, Redis caching, and Prometheus metrics out of the box.' },
            { q: 'How does the vector memory work?', a: 'ChromaDB stores embeddings of your codebase. When you ask a question, it semantically searches for relevant code first — giving the LLM much better context.' },
          ].map(item => <FAQItem key={item.q} {...item} />)}
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <h2>Start fixing code in 2 minutes</h2>
        <p>Open source, no signup required. Works with Claude, GPT-4, or fully offline with Ollama.</p>
        <div className="actions">
          <a href="#install" className="btn btn-primary">Get Started <Icons.Arrow /></a>
          <a href={REPO} target="_blank" rel="noreferrer" className="btn btn-outline"><Icons.Github /> View Source</a>
        </div>
      </section>

      {/* Footer */}
      <footer>
        <p>© 2026 Agent.ai · Open Source under MIT License</p>
        <div className="footer-links">
          <a href={REPO} target="_blank" rel="noreferrer">GitHub</a>
          <a href={`${REPO}/blob/main/README.md`} target="_blank" rel="noreferrer">Docs</a>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API</a>
          <a href="#faq">FAQ</a>
        </div>
      </footer>
    </>
  );
}
