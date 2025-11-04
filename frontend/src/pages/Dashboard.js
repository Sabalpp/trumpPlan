import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Dashboard.css';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentSignals, setRecentSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsRes, signalsRes] = await Promise.all([
        axios.get('/api/stats'),
        axios.get('/api/signals?limit=5')
      ]);
      
      setStats(statsRes.data);
      setRecentSignals(signalsRes.data.signals || []);
      setError(null);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📊 Dashboard</h1>
        <p>Real-time political sentiment trading signals</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats?.total_signals || 0}</div>
          <div className="stat-label">Total Signals</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.recent_signals_7d || 0}</div>
          <div className="stat-label">Signals (7 Days)</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{(stats?.average_confidence * 100 || 0).toFixed(1)}%</div>
          <div className="stat-label">Avg Confidence</div>
        </div>
        <div className="stat-card">
          <div className="stat-value status-operational">✓</div>
          <div className="stat-label">System Status</div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-header">Recent Signals</h2>
        {recentSignals.length === 0 ? (
          <p className="no-data">No recent signals available</p>
        ) : (
          <div className="signals-list">
            {recentSignals.map((signal, index) => (
              <div key={index} className="signal-item">
                <div className="signal-ticker">{signal.ticker}</div>
                <div className={`signal-direction ${signal.direction}`}>
                  {signal.direction === 'long' ? '📈' : '📉'} {signal.direction.toUpperCase()}
                </div>
                <div className="signal-confidence">
                  Confidence: {(signal.confidence * 100).toFixed(0)}%
                </div>
                <div className="signal-time">
                  {new Date(signal.generated_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="disclaimer-box">
        <p>
          ⚠️ <strong>Important:</strong> This platform provides general research information only. 
          Not investment advice. See <a href="/disclaimer">full disclaimer</a>.
        </p>
      </div>
    </div>
  );
}

export default Dashboard;

