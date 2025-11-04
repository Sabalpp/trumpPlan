import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Dashboard from './pages/Dashboard';
import Signals from './pages/Signals';
import Backtest from './pages/Backtest';
import Waitlist from './pages/Waitlist';
import Pricing from './pages/Pricing';
import Disclaimer from './pages/Disclaimer';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-logo">
              📊 Political Alpha
            </Link>
            <ul className="nav-menu">
              <li className="nav-item">
                <Link to="/" className="nav-link">Dashboard</Link>
              </li>
              <li className="nav-item">
                <Link to="/signals" className="nav-link">Signals</Link>
              </li>
              <li className="nav-item">
                <Link to="/backtest" className="nav-link">Backtest</Link>
              </li>
              <li className="nav-item">
                <Link to="/pricing" className="nav-link">Pricing</Link>
              </li>
              <li className="nav-item">
                <Link to="/waitlist" className="nav-link cta-btn">Join Waitlist</Link>
              </li>
            </ul>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/signals" element={<Signals />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/waitlist" element={<Waitlist />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/disclaimer" element={<Disclaimer />} />
        </Routes>

        <footer className="footer">
          <div className="footer-content">
            <p>© 2025 Political Sentiment Alpha Platform</p>
            <p>
              <Link to="/disclaimer">Disclaimer</Link> | 
              <a href="/api/health" target="_blank" rel="noopener noreferrer"> API Status</a>
            </p>
            <p className="footer-warning">
              ⚠️ Not investment advice. See disclaimer for full terms.
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;

