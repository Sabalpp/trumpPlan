import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Signals.css';

function Signals() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    limit: 20,
    min_confidence: 0.6,
    ticker: '',
    days: 7
  });

  useEffect(() => {
    fetchSignals();
  }, [filters]);

  const fetchSignals = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append('limit', filters.limit);
      params.append('min_confidence', filters.min_confidence);
      params.append('days', filters.days);
      if (filters.ticker) params.append('ticker', filters.ticker);

      const response = await axios.get(`/api/signals?${params.toString()}`);
      setSignals(response.data.signals || []);
    } catch (err) {
      console.error('Failed to fetch signals:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📈 Trading Signals</h1>
        <p>Historical trading signals generated from political communications</p>
      </div>

      <div className="card filters-card">
        <h3>Filters</h3>
        <div className="filters-grid">
          <div className="filter-group">
            <label>Ticker Symbol</label>
            <input
              type="text"
              placeholder="e.g., AAPL"
              value={filters.ticker}
              onChange={(e) => handleFilterChange('ticker', e.target.value.toUpperCase())}
            />
          </div>
          <div className="filter-group">
            <label>Min Confidence</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={filters.min_confidence}
              onChange={(e) => handleFilterChange('min_confidence', parseFloat(e.target.value))}
            />
            <span>{(filters.min_confidence * 100).toFixed(0)}%</span>
          </div>
          <div className="filter-group">
            <label>Time Period</label>
            <select
              value={filters.days}
              onChange={(e) => handleFilterChange('days', parseInt(e.target.value))}
            >
              <option value="1">Last 24 hours</option>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-header">
          {signals.length} Signal{signals.length !== 1 ? 's' : ''} Found
        </h2>
        
        {loading ? (
          <div className="loading">Loading signals...</div>
        ) : signals.length === 0 ? (
          <p className="no-data">No signals match your filters</p>
        ) : (
          <div className="signals-table">
            <div className="table-header">
              <div>Ticker</div>
              <div>Direction</div>
              <div>Confidence</div>
              <div>Sentiment</div>
              <div>Timestamp</div>
              <div>Explanation</div>
            </div>
            {signals.map((signal, index) => (
              <div key={index} className="table-row">
                <div className="cell-ticker">{signal.ticker}</div>
                <div className={`cell-direction ${signal.direction}`}>
                  {signal.direction === 'long' ? '↗ LONG' : '↘ SHORT'}
                </div>
                <div className="cell-confidence">
                  <div className="confidence-bar">
                    <div
                      className="confidence-fill"
                      style={{ width: `${signal.confidence * 100}%` }}
                    />
                  </div>
                  {(signal.confidence * 100).toFixed(0)}%
                </div>
                <div className="cell-sentiment">
                  {signal.sentiment_polarity > 0 ? '😊' : signal.sentiment_polarity < 0 ? '😟' : '😐'}
                  {' '}
                  {signal.sentiment_polarity?.toFixed(2)}
                </div>
                <div className="cell-time">
                  {new Date(signal.generated_at).toLocaleDateString()}<br />
                  <small>{new Date(signal.generated_at).toLocaleTimeString()}</small>
                </div>
                <div className="cell-explanation">
                  {signal.explanation || 'No explanation provided'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Signals;

