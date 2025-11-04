import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Backtest.css';

function Backtest() {
  const [backtest, setBacktest] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBacktest();
  }, []);

  const fetchBacktest = async () => {
    try {
      const response = await axios.get('/api/backtest');
      setBacktest(response.data.backtest);
    } catch (err) {
      console.error('Failed to fetch backtest:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading">Loading backtest results...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📊 Backtest Results</h1>
        <p>Historical performance analysis of trading signals</p>
      </div>

      {!backtest ? (
        <div className="card">
          <p className="no-data">No backtest results available yet</p>
        </div>
      ) : (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-icon">📈</div>
              <div className="metric-value">{backtest.total_signals}</div>
              <div className="metric-label">Total Signals</div>
            </div>
            <div className="metric-card">
              <div className="metric-icon">✓</div>
              <div className="metric-value">{backtest.profitable_signals}</div>
              <div className="metric-label">Profitable Signals</div>
            </div>
            <div className="metric-card">
              <div className="metric-icon">🎯</div>
              <div className="metric-value">{backtest.win_rate}%</div>
              <div className="metric-label">Win Rate</div>
            </div>
            <div className="metric-card">
              <div className="metric-icon">💰</div>
              <div className="metric-value">{(backtest.average_return * 100).toFixed(2)}%</div>
              <div className="metric-label">Avg Return</div>
            </div>
            <div className="metric-card">
              <div className="metric-icon">📊</div>
              <div className="metric-value">{backtest.sharpe_ratio}</div>
              <div className="metric-label">Sharpe Ratio</div>
            </div>
            <div className="metric-card">
              <div className="metric-icon">⚠️</div>
              <div className="metric-value">{(backtest.max_drawdown * 100).toFixed(2)}%</div>
              <div className="metric-label">Max Drawdown</div>
            </div>
          </div>

          <div className="card">
            <h2 className="card-header">Backtest Details</h2>
            <div className="details-grid">
              <div className="detail-item">
                <span className="detail-label">Strategy:</span>
                <span className="detail-value">{backtest.strategy}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Start Date:</span>
                <span className="detail-value">
                  {new Date(backtest.start_date).toLocaleDateString()}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">End Date:</span>
                <span className="detail-value">
                  {new Date(backtest.end_date).toLocaleDateString()}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Run At:</span>
                <span className="detail-value">
                  {new Date(backtest.run_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="card-header">About This Backtest</h2>
            <div className="info-content">
              <p>
                This backtest simulates trading based on historical political sentiment signals
                from {new Date(backtest.start_date).getFullYear()} to {new Date(backtest.end_date).getFullYear()}.
              </p>
              <p>
                <strong>Methodology:</strong> Event study analysis with CAPM-based abnormal return
                calculation. Signals generated from Trump-era social media communications.
              </p>
              <p className="warning-text">
                ⚠️ <strong>Important:</strong> Past performance does not guarantee future results.
                This is for research purposes only.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Backtest;

