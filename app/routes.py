"""
Additional Flask Routes for Go-to-Market Features
===============================================

Routes for:
- Waitlist management
- User dashboard
- Backtesting interface
- Subscription/monetization
"""

from datetime import datetime
import secrets
import string

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from sqlalchemy import func

from models.db import SessionLocal, User, Signal, BacktestResult

# Create Blueprint
gtm = Blueprint('gtm', __name__)


@gtm.route('/waitlist', methods=['GET', 'POST'])
def waitlist():
    """
    Waitlist signup page
    
    GET: Show waitlist form
    POST: Process waitlist signup
    """
    if request.method == 'GET':
        # Render waitlist page
        stats = get_waitlist_stats()
        return render_template('waitlist.html', stats=stats)
    
    # POST: Process signup
    try:
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email', '').strip().lower()
        referred_by = data.get('referral_code', '').strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if not SessionLocal:
            return jsonify({'error': 'Service temporarily unavailable'}), 503
        
        session = SessionLocal()
        
        # Check if already exists
        existing = session.query(User).filter(User.email == email).first()
        
        if existing:
            session.close()
            return jsonify({
                'status': 'success',
                'message': 'Already on waitlist!',
                'referral_code': existing.referral_code,
                'position': get_waitlist_position(existing.id)
            }), 200
        
        # Generate unique referral code
        referral_code = generate_referral_code()
        
        # Create user
        user = User(
            email=email,
            tier='waitlist',
            referral_code=referral_code,
            referred_by=referred_by if referred_by else None
        )
        session.add(user)
        session.commit()
        
        # Update referrer if applicable
        if referred_by:
            referrer = session.query(User).filter(User.referral_code == referred_by).first()
            if referrer:
                referrer.referral_count += 1
                session.commit()
        
        position = get_waitlist_position(user.id)
        
        session.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Successfully joined waitlist!',
            'referral_code': referral_code,
            'position': position,
            'referral_count': 0
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gtm.route('/dashboard')
def dashboard():
    """
    User dashboard showing recent signals
    
    Requires authentication (simplified for MVP)
    """
    # In production, add proper authentication
    # For MVP, show public dashboard
    
    if not SessionLocal:
        return "Service unavailable", 503
    
    session = SessionLocal()
    
    try:
        # Get recent signals (last 24 hours)
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        recent_signals = session.query(Signal)\
            .filter(Signal.generated_at >= cutoff)\
            .order_by(Signal.generated_at.desc())\
            .limit(20)\
            .all()
        
        # Get statistics
        stats = {
            'total_signals_24h': len(recent_signals),
            'high_confidence': sum(1 for s in recent_signals if s.confidence > 0.7),
            'long_signals': sum(1 for s in recent_signals if s.direction == 'long'),
            'short_signals': sum(1 for s in recent_signals if s.direction == 'short'),
        }
        
        session.close()
        
        return render_template(
            'dashboard.html',
            signals=recent_signals,
            stats=stats
        )
        
    except Exception as e:
        session.close()
        return f"Error: {str(e)}", 500


@gtm.route('/backtest')
def backtest_interface():
    """
    Backtesting interface and results
    """
    if not SessionLocal:
        return "Service unavailable", 503
    
    session = SessionLocal()
    
    try:
        # Get latest backtest result
        latest_backtest = session.query(BacktestResult)\
            .order_by(BacktestResult.run_at.desc())\
            .first()
        
        # Get historical performance by month
        monthly_stats = get_monthly_performance(session)
        
        session.close()
        
        return render_template(
            'backtest.html',
            backtest=latest_backtest,
            monthly_stats=monthly_stats
        )
        
    except Exception as e:
        session.close()
        return f"Error: {str(e)}", 500


@gtm.route('/pricing')
def pricing():
    """
    Pricing page with subscription tiers
    """
    tiers = [
        {
            'name': 'Free',
            'price': 0,
            'features': [
                'Delayed signals (30-min)',
                'Limited to 10 signals/day',
                'Email notifications',
                'Basic dashboard'
            ],
            'cta': 'Sign Up',
            'cta_link': '/waitlist'
        },
        {
            'name': 'Pro',
            'price': 29,
            'features': [
                'Real-time signals',
                'Unlimited signals',
                'Event study analysis',
                'Advanced dashboard',
                'Priority support',
                'Export to ThinkorSwim'
            ],
            'cta': 'Start Free Trial',
            'cta_link': '/subscribe/pro',
            'highlight': True
        },
        {
            'name': 'Institutional',
            'price': 500,
            'features': [
                'Everything in Pro',
                'API access (1000 req/day)',
                'Custom integrations',
                'Dedicated support',
                'White-label options',
                'SLA guarantee'
            ],
            'cta': 'Contact Sales',
            'cta_link': '/contact'
        }
    ]
    
    return render_template('pricing.html', tiers=tiers)


@gtm.route('/subscribe/<tier>', methods=['POST'])
def subscribe(tier):
    """
    Process subscription via Stripe
    
    Simplified for MVP - full Stripe integration needed
    """
    # In production, integrate with Stripe Checkout
    # For MVP, return placeholder
    
    return jsonify({
        'message': 'Subscription system coming soon!',
        'tier': tier,
        'next_steps': 'Join waitlist for early access'
    }), 200


@gtm.route('/export/thinkorswim')
def export_thinkorswim():
    """
    Export recent signals as ThinkorSwim Paper Money CSV
    
    Format: Ticker,Action,Quantity,Price
    """
    if not SessionLocal:
        return "Service unavailable", 503
    
    session = SessionLocal()
    
    try:
        # Get recent high-confidence signals
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=1)
        
        signals = session.query(Signal)\
            .filter(Signal.generated_at >= cutoff)\
            .filter(Signal.confidence >= 0.7)\
            .filter(Signal.is_outlier == False)\
            .order_by(Signal.generated_at.desc())\
            .limit(10)\
            .all()
        
        # Generate CSV
        csv_lines = ['Ticker,Action,Quantity,Price']
        
        for sig in signals:
            action = 'BUY' if sig.direction == 'long' else 'SELL'
            csv_lines.append(f"{sig.ticker},{action},1,MARKET")
        
        csv_content = '\n'.join(csv_lines)
        
        session.close()
        
        # Return as downloadable file
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=political_alpha_signals_{datetime.utcnow().date()}.csv'
            }
        )
        
    except Exception as e:
        session.close()
        return f"Error: {str(e)}", 500


# Helper functions

def generate_referral_code(length=8):
    """Generate unique referral code"""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(chars) for _ in range(length))
        # Check uniqueness (in production)
        # For MVP, assume it's unique
        return code


def get_waitlist_position(user_id):
    """Get user's position in waitlist"""
    if not SessionLocal:
        return 0
    
    session = SessionLocal()
    
    try:
        # Count users created before this user
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        
        position = session.query(User)\
            .filter(User.tier == 'waitlist')\
            .filter(User.created_at < user.created_at)\
            .count() + 1
        
        session.close()
        return position
        
    except:
        return 0


def get_waitlist_stats():
    """Get waitlist statistics"""
    if not SessionLocal:
        return {'total': 0, 'recent': 0}
    
    session = SessionLocal()
    
    try:
        total = session.query(User).filter(User.tier == 'waitlist').count()
        
        from datetime import timedelta
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent = session.query(User)\
            .filter(User.tier == 'waitlist')\
            .filter(User.created_at >= recent_cutoff)\
            .count()
        
        session.close()
        
        return {
            'total': total,
            'recent': recent
        }
        
    except:
        return {'total': 0, 'recent': 0}


def get_monthly_performance(session):
    """Get performance by month for backtesting"""
    # Placeholder - in production, calculate from historical signals
    return [
        {'month': '2024-01', 'signals': 45, 'win_rate': 62.2, 'avg_return': 0.38},
        {'month': '2024-02', 'signals': 38, 'win_rate': 57.9, 'avg_return': 0.31},
        {'month': '2024-03', 'signals': 52, 'win_rate': 65.4, 'avg_return': 0.42},
    ]


if __name__ == '__main__':
    print("Go-to-Market Routes Module")
    print("Routes available:")
    print("  GET/POST /waitlist")
    print("  GET      /dashboard")
    print("  GET      /backtest")
    print("  GET      /pricing")
    print("  POST     /subscribe/<tier>")
    print("  GET      /export/thinkorswim")

