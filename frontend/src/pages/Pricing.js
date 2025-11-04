import React from 'react';
import { Link } from 'react-router-dom';
import './Pricing.css';

function Pricing() {
  const tiers = [
    {
      name: 'Free',
      price: 0,
      period: 'forever',
      features: [
        'Delayed signals (30-min)',
        'Limited to 10 signals/day',
        'Email notifications',
        'Basic dashboard',
        'Community access'
      ],
      cta: 'Sign Up',
      link: '/waitlist',
      highlight: false
    },
    {
      name: 'Pro',
      price: 29,
      period: 'month',
      features: [
        'Real-time signals',
        'Unlimited signals',
        'Event study analysis',
        'Advanced dashboard',
        'Priority support',
        'Export to ThinkorSwim',
        'Historical backtest data',
        'Custom alerts'
      ],
      cta: 'Start Free Trial',
      link: '/waitlist',
      highlight: true,
      badge: 'Most Popular'
    },
    {
      name: 'Institutional',
      price: 500,
      period: 'month',
      features: [
        'Everything in Pro',
        'API access (1000 req/day)',
        'Custom integrations',
        'Dedicated support',
        'White-label options',
        'SLA guarantee',
        'Custom models',
        'Team collaboration'
      ],
      cta: 'Contact Sales',
      link: '/waitlist',
      highlight: false
    }
  ];

  return (
    <div className="page-container">
      <div className="pricing-header">
        <h1>💰 Pricing Plans</h1>
        <p>Choose the plan that fits your trading needs</p>
        <div className="pricing-badge">
          🎉 Early Access: Get 50% off by joining the waitlist!
        </div>
      </div>

      <div className="pricing-grid">
        {tiers.map((tier, index) => (
          <div
            key={index}
            className={`pricing-card ${tier.highlight ? 'highlight' : ''}`}
          >
            {tier.badge && <div className="pricing-badge-card">{tier.badge}</div>}
            
            <div className="pricing-card-header">
              <h2>{tier.name}</h2>
              <div className="price">
                <span className="currency">$</span>
                <span className="amount">{tier.price}</span>
                <span className="period">/{tier.period}</span>
              </div>
            </div>

            <div className="features">
              {tier.features.map((feature, idx) => (
                <div key={idx} className="feature-item">
                  <span className="check">✓</span> {feature}
                </div>
              ))}
            </div>

            <Link to={tier.link} className="pricing-cta">
              {tier.cta}
            </Link>
          </div>
        ))}
      </div>

      <div className="faq-section">
        <h2>Frequently Asked Questions</h2>
        
        <div className="faq-grid">
          <div className="faq-item">
            <h3>What's included in the free trial?</h3>
            <p>
              All Pro features for 14 days, no credit card required. Cancel anytime.
            </p>
          </div>

          <div className="faq-item">
            <h3>How are signals generated?</h3>
            <p>
              Using NLP analysis of political communications combined with event study
              methodology to identify potential market-moving events.
            </p>
          </div>

          <div className="faq-item">
            <h3>Can I cancel anytime?</h3>
            <p>
              Yes, all subscriptions are month-to-month with no long-term commitment.
            </p>
          </div>

          <div className="faq-item">
            <h3>Is this investment advice?</h3>
            <p>
              No. This is a research tool providing general information only. Always
              consult a licensed financial advisor before trading.
            </p>
          </div>
        </div>
      </div>

      <div className="cta-section">
        <h2>Ready to Get Started?</h2>
        <p>Join the waitlist for early access and exclusive discounts</p>
        <Link to="/waitlist" className="cta-button">
          Join Waitlist Now
        </Link>
      </div>
    </div>
  );
}

export default Pricing;

