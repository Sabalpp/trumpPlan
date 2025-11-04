"""
Flask Application - Political Sentiment Alpha Platform
====================================================

Main API endpoints:
- /signal - Generate signal from text
- /signals - List recent signals
- /backtest - Run historical backtest
- /health - Health check
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sqlalchemy.orm import Session

from config import config
from models.db import init_db, Event, Signal, User, BacktestResult
from nlp.pipeline import NLPPipeline
from quant.event_study import quick_event_study

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
CORS(app)  # Enable CORS for web clients

# Register GTM Blueprint (waitlist, pricing, etc.)
try:
    from app.routes import gtm
    app.register_blueprint(gtm)
    print("✓ GTM routes registered")
except ImportError as e:
    print(f"⚠️  GTM routes not available: {str(e)}")

# Initialize database
try:
    engine, SessionLocal = init_db()
    print("✓ Database connected")
except Exception as e:
    print(f"⚠️  Database connection failed: {str(e)}")
    SessionLocal = None

# Initialize NLP pipeline (singleton)
nlp_pipeline = None


def get_nlp_pipeline():
    """Lazy-load NLP pipeline"""
    global nlp_pipeline
    if nlp_pipeline is None:
        nlp_pipeline = NLPPipeline()
    return nlp_pipeline


@app.route('/')
def index():
    """Home page"""
    return jsonify({
        'name': config.PLATFORM_NAME,
        'version': '0.1.0-MVP',
        'status': 'operational',
        'endpoints': {
            'POST /api/signal': 'Generate trading signal from political text',
            'GET /api/signals': 'List recent signals',
            'GET /api/backtest': 'View backtest results',
            'GET /api/stats': 'Platform statistics',
            'GET /health': 'Health check',
            'GET/POST /waitlist': 'Join waitlist',
            'GET /dashboard': 'User dashboard',
            'GET /pricing': 'Pricing information'
        },
        'disclaimer': config.DISCLAIMER_TEXT.strip()
    })


@app.route('/health')
def health():
    """Health check endpoint for AWS ELB/monitoring"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if SessionLocal else 'disconnected',
        'nlp': 'loaded' if nlp_pipeline else 'not loaded'
    }
    
    status_code = 200 if SessionLocal else 503
    return jsonify(health_status), status_code


@app.route('/api/signal', methods=['POST'])
def generate_signal():
    """
    Generate trading signal from political text
    
    POST /api/signal
    Body: {
        "text": "Political communication text",
        "timestamp": "2024-01-01T12:00:00Z" (optional),
        "run_event_study": true (optional, default false for speed)
    }
    
    Returns: {
        "signal": {...},
        "explanation": "...",
        "disclaimer": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing required field: text'}), 400
        
        text = data['text']
        timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        run_event_study = data.get('run_event_study', False)
        
        # Process through NLP pipeline
        pipeline = get_nlp_pipeline()
        nlp_result = pipeline.process_text(text, timestamp)
        
        # Optionally run event study for first ticker
        event_study_result = None
        if run_event_study and nlp_result['tickers']:
            ticker = nlp_result['tickers'][0]
            try:
                event_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                event_study_result = quick_event_study(ticker, event_dt, text)
            except Exception as e:
                print(f"⚠️  Event study failed: {str(e)}")
        
        # Store to database
        if SessionLocal:
            session = SessionLocal()
            try:
                # Create event record
                event = Event(
                    external_id=f"api_{datetime.utcnow().timestamp()}",
                    text=text,
                    source='API',
                    author='user_submitted',
                    event_timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00')),
                    processed_at=datetime.utcnow()
                )
                session.add(event)
                session.flush()
                
                # Create signal records
                for sig in nlp_result['signals']:
                    signal = Signal(
                        event_id=event.id,
                        ticker=sig['ticker'],
                        signal_type=sig['type'],
                        direction=sig['direction'],
                        confidence=sig['confidence'],
                        sentiment_polarity=nlp_result['sentiment_polarity'],
                        tone=nlp_result['tone'],
                        explanation=sig['reason'],
                        abnormal_return=event_study_result.get('ar') if event_study_result else None,
                        is_significant=event_study_result.get('is_significant', False) if event_study_result else False
                    )
                    session.add(signal)
                
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"⚠️  Database insert failed: {str(e)}")
            finally:
                session.close()
        
        # Prepare response
        response = {
            'status': 'success',
            'nlp_analysis': nlp_result,
            'event_study': event_study_result,
            'signals': nlp_result['signals'],
            'summary': nlp_result['summary'],
            'disclaimer': config.DISCLAIMER_TEXT.strip()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/signals', methods=['GET'])
def list_signals():
    """
    List recent trading signals
    
    GET /api/signals?limit=10&min_confidence=0.7&ticker=AAPL
    
    Query params:
    - limit: Max number of signals (default: 20)
    - min_confidence: Minimum confidence score (default: 0.0)
    - ticker: Filter by ticker symbol (optional)
    - days: Days of history (default: 7)
    """
    if not SessionLocal:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        # Parse query params
        limit = int(request.args.get('limit', 20))
        min_confidence = float(request.args.get('min_confidence', 0.0))
        ticker = request.args.get('ticker', None)
        days = int(request.args.get('days', 7))
        
        # Build query
        session = SessionLocal()
        query = session.query(Signal)
        
        # Filters
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Signal.generated_at >= cutoff_date)
        query = query.filter(Signal.confidence >= min_confidence)
        
        if ticker:
            query = query.filter(Signal.ticker == ticker.upper())
        
        # Order and limit
        query = query.order_by(Signal.generated_at.desc())
        query = query.limit(limit)
        
        signals = query.all()
        
        # Convert to dict
        results = [sig.to_dict() for sig in signals]
        
        session.close()
        
        response = {
            'status': 'success',
            'count': len(results),
            'signals': results,
            'filters': {
                'limit': limit,
                'min_confidence': min_confidence,
                'ticker': ticker,
                'days': days
            },
            'disclaimer': config.DISCLAIMER_TEXT.strip()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest', methods=['GET'])
def view_backtest():
    """
    View backtesting results
    
    GET /api/backtest?start_date=2020-01-01&end_date=2021-12-31
    """
    if not SessionLocal:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        session = SessionLocal()
        
        # Get latest backtest result
        latest = session.query(BacktestResult)\
            .order_by(BacktestResult.run_at.desc())\
            .first()
        
        if not latest:
            session.close()
            return jsonify({
                'status': 'success',
                'message': 'No backtest results available',
                'backtest': None
            }), 200
        
        result = {
            'id': latest.id,
            'start_date': latest.start_date.isoformat(),
            'end_date': latest.end_date.isoformat(),
            'strategy': latest.strategy,
            'total_signals': latest.total_signals,
            'profitable_signals': latest.profitable_signals,
            'win_rate': round(latest.win_rate, 2) if latest.win_rate else None,
            'average_return': round(latest.average_return, 4) if latest.average_return else None,
            'sharpe_ratio': round(latest.sharpe_ratio, 2) if latest.sharpe_ratio else None,
            'max_drawdown': round(latest.max_drawdown, 4) if latest.max_drawdown else None,
            'run_at': latest.run_at.isoformat()
        }
        
        session.close()
        
        return jsonify({
            'status': 'success',
            'backtest': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def platform_stats():
    """
    Get platform statistics
    
    GET /api/stats
    """
    if not SessionLocal:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        session = SessionLocal()
        
        # Count statistics
        total_events = session.query(Event).count()
        total_signals = session.query(Signal).count()
        
        # Recent stats (last 7 days)
        cutoff = datetime.utcnow() - timedelta(days=7)
        recent_signals = session.query(Signal)\
            .filter(Signal.generated_at >= cutoff)\
            .count()
        
        # Average confidence
        from sqlalchemy import func
        avg_confidence = session.query(func.avg(Signal.confidence))\
            .filter(Signal.generated_at >= cutoff)\
            .scalar()
        
        session.close()
        
        stats = {
            'total_events': total_events,
            'total_signals': total_signals,
            'recent_signals_7d': recent_signals,
            'average_confidence': round(float(avg_confidence), 3) if avg_confidence else 0.0,
            'platform_uptime': 'operational',
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/disclaimer')
def disclaimer():
    """Display disclaimer page"""
    try:
        return render_template('disclaimer.html')
    except:
        # Fallback if template not found
        return jsonify({
            'disclaimer': config.DISCLAIMER_TEXT.strip(),
            'note': 'HTML template not found, showing text version'
        })


@app.route('/privacy')
def privacy():
    """Display privacy policy"""
    try:
        # Read privacy.md and convert to HTML (simplified)
        with open('docs/privacy.md', 'r') as f:
            content = f.read()
        return f"<pre style='white-space: pre-wrap; font-family: Arial;'>{content}</pre>"
    except:
        return jsonify({
            'error': 'Privacy policy not found',
            'note': 'See docs/privacy.md in the repository'
        })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("\n🚀 Starting Political Sentiment Alpha Platform API\n")
    print(f"Environment: {config.FLASK_ENV}")
    print(f"Debug: {config.DEBUG}")
    print("\nAvailable endpoints:")
    print("  GET  /              - API info")
    print("  GET  /health        - Health check")
    print("  POST /api/signal    - Generate signal")
    print("  GET  /api/signals   - List signals")
    print("  GET  /api/backtest  - View backtest results")
    print("  GET  /api/stats     - Platform statistics")
    print("  GET  /waitlist      - Join waitlist")
    print("  GET  /dashboard     - Dashboard")
    print("  GET  /pricing       - Pricing page")
    print("  GET  /disclaimer    - Legal disclaimer")
    print("  GET  /privacy       - Privacy policy")
    print("\n" + "="*70)
    print(config.DISCLAIMER_TEXT.strip())
    print("="*70 + "\n")
    
    # Run Flask development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.DEBUG
    )

