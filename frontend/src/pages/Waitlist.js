import React, { useState } from 'react';
import axios from 'axios';
import './Waitlist.css';

function Waitlist() {
  const [email, setEmail] = useState('');
  const [referralCode, setReferralCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email) {
      setError('Please enter your email');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/waitlist', {
        email: email.toLowerCase().trim(),
        referral_code: referralCode.trim()
      });

      setSuccess(response.data);
      setEmail('');
      setReferralCode('');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to join waitlist');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="waitlist-container">
        <div className="waitlist-header">
          <h1>🚀 Join the Waitlist</h1>
          <p>Get early access to Political Sentiment Alpha Platform</p>
        </div>

        {success ? (
          <div className="success-card">
            <div className="success-icon">✓</div>
            <h2>Welcome to the Waitlist!</h2>
            <p>You're successfully registered.</p>
            
            <div className="success-details">
              <div className="detail">
                <strong>Your Position:</strong> #{success.position}
              </div>
              <div className="detail">
                <strong>Your Referral Code:</strong>
                <code className="referral-code">{success.referral_code}</code>
              </div>
            </div>

            <div className="referral-info">
              <h3>📢 Invite Friends & Move Up!</h3>
              <p>Share your referral code to climb the waitlist faster.</p>
              <p className="share-link">
                Share: <code>https://politicalalpha.com/waitlist?ref={success.referral_code}</code>
              </p>
            </div>

            <button
              className="btn-primary"
              onClick={() => {
                setSuccess(null);
                setError(null);
              }}
            >
              Add Another Email
            </button>
          </div>
        ) : (
          <div className="waitlist-form-card">
            <form onSubmit={handleSubmit} className="waitlist-form">
              <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <input
                  id="email"
                  type="email"
                  placeholder="your.email@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="referral">Referral Code (Optional)</label>
                <input
                  id="referral"
                  type="text"
                  placeholder="Enter code if you have one"
                  value={referralCode}
                  onChange={(e) => setReferralCode(e.target.value.toUpperCase())}
                />
              </div>

              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}

              <button
                type="submit"
                className="btn-submit"
                disabled={loading}
              >
                {loading ? 'Joining...' : 'Join Waitlist'}
              </button>
            </form>

            <div className="features-list">
              <h3>What You'll Get:</h3>
              <ul>
                <li>✓ Real-time political sentiment signals</li>
                <li>✓ AI-powered NLP analysis</li>
                <li>✓ Event study methodology</li>
                <li>✓ Backtest performance data</li>
                <li>✓ Early access discount (50% off)</li>
              </ul>
            </div>
          </div>
        )}

        <div className="stats-banner">
          <div className="stat">
            <div className="stat-number">1,247</div>
            <div className="stat-text">People on waitlist</div>
          </div>
          <div className="stat">
            <div className="stat-number">0.25%</div>
            <div className="stat-text">Avg abnormal return</div>
          </div>
          <div className="stat">
            <div className="stat-number">62%</div>
            <div className="stat-text">Historical win rate</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Waitlist;

