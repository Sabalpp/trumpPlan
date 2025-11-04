"""
Celery Tasks for Async Processing
================================

Background tasks:
1. process_nlp_batch - Batch NLP processing
2. compute_event_study - Event study calculations
3. ingest_realtime_data - Periodic data ingestion
4. cleanup_expired_signals - Housekeeping
"""

from datetime import datetime, timedelta
from typing import List, Dict

from celery import Celery
from celery.schedules import crontab

from config import config
from models.db import init_db, Event, Signal
from nlp.pipeline import NLPPipeline
from quant.event_study import quick_event_study
from data.ingestion import aggregate_all_sources

# Initialize Celery
app = Celery(
    'political_alpha',
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Initialize database
try:
    engine, SessionLocal = init_db()
except Exception as e:
    print(f"⚠️  Celery: Database init failed: {str(e)}")
    SessionLocal = None

# NLP pipeline singleton
nlp_pipeline = None


def get_nlp_pipeline():
    """Lazy-load NLP pipeline"""
    global nlp_pipeline
    if nlp_pipeline is None:
        nlp_pipeline = NLPPipeline()
    return nlp_pipeline


@app.task(name='tasks.process_nlp_batch')
def process_nlp_batch(event_ids: List[int]):
    """
    Process multiple events through NLP pipeline
    
    Args:
        event_ids: List of Event IDs to process
    
    Returns:
        Dict with processing results
    """
    if not SessionLocal:
        return {'error': 'Database not available'}
    
    session = SessionLocal()
    pipeline = get_nlp_pipeline()
    
    processed_count = 0
    signal_count = 0
    
    try:
        events = session.query(Event).filter(Event.id.in_(event_ids)).all()
        
        for event in events:
            # Skip if already processed
            if event.processed_at:
                continue
            
            # Process through NLP
            nlp_result = pipeline.process_text(event.text, event.event_timestamp.isoformat())
            
            # Create signals
            for sig in nlp_result['signals']:
                signal = Signal(
                    event_id=event.id,
                    ticker=sig['ticker'],
                    signal_type=sig['type'],
                    direction=sig['direction'],
                    confidence=sig['confidence'],
                    sentiment_polarity=nlp_result['sentiment_polarity'],
                    tone=nlp_result['tone'],
                    explanation=sig['reason']
                )
                session.add(signal)
                signal_count += 1
            
            # Mark as processed
            event.processed_at = datetime.utcnow()
            processed_count += 1
        
        session.commit()
        
        return {
            'status': 'success',
            'processed_events': processed_count,
            'generated_signals': signal_count
        }
        
    except Exception as e:
        session.rollback()
        return {'error': str(e)}
    finally:
        session.close()


@app.task(name='tasks.compute_event_study')
def compute_event_study(signal_id: int):
    """
    Compute event study for a signal
    
    Args:
        signal_id: Signal ID to enhance with event study
    
    Returns:
        Dict with event study results
    """
    if not SessionLocal:
        return {'error': 'Database not available'}
    
    session = SessionLocal()
    
    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()
        
        if not signal:
            return {'error': f'Signal {signal_id} not found'}
        
        event = signal.event
        
        # Run event study
        event_study_result = quick_event_study(
            signal.ticker,
            event.event_timestamp,
            event.text
        )
        
        if 'error' not in event_study_result:
            # Update signal with event study results
            signal.abnormal_return = event_study_result.get('ar')
            signal.car = event_study_result.get('car')
            signal.p_value = event_study_result.get('p_value')
            signal.is_significant = event_study_result.get('is_significant', False)
            signal.beta = event_study_result.get('beta')
            signal.is_outlier = event_study_result.get('is_outlier', False)
            
            session.commit()
            
            return {
                'status': 'success',
                'signal_id': signal_id,
                'ar': event_study_result.get('ar'),
                'is_significant': event_study_result.get('is_significant')
            }
        else:
            return {'error': event_study_result['error']}
        
    except Exception as e:
        session.rollback()
        return {'error': str(e)}
    finally:
        session.close()


@app.task(name='tasks.ingest_realtime_data')
def ingest_realtime_data():
    """
    Periodic task to ingest real-time political data
    
    Runs every minute to check for new posts
    """
    if not SessionLocal:
        return {'error': 'Database not available'}
    
    try:
        # Fetch recent data (last 60 minutes)
        data = aggregate_all_sources(
            include_historical=False,
            include_realtime=True,
            include_government=False,
            include_family=True
        )
        
        if data.empty:
            return {'status': 'success', 'new_events': 0}
        
        session = SessionLocal()
        new_event_count = 0
        
        for _, row in data.iterrows():
            # Check if already exists
            existing = session.query(Event).filter(
                Event.external_id == row.get('id', f"auto_{row['timestamp']}")
            ).first()
            
            if existing:
                continue
            
            # Create new event
            event = Event(
                external_id=row.get('id', f"auto_{row['timestamp']}"),
                text=row['text'],
                source=row['source'],
                author=row.get('author', 'unknown'),
                event_timestamp=row['timestamp']
            )
            session.add(event)
            new_event_count += 1
        
        session.commit()
        session.close()
        
        # Trigger NLP processing for new events
        if new_event_count > 0:
            # Get IDs of new events
            session = SessionLocal()
            recent_unprocessed = session.query(Event)\
                .filter(Event.processed_at.is_(None))\
                .order_by(Event.ingested_at.desc())\
                .limit(new_event_count)\
                .all()
            
            event_ids = [e.id for e in recent_unprocessed]
            session.close()
            
            # Queue for processing
            if event_ids:
                process_nlp_batch.delay(event_ids)
        
        return {
            'status': 'success',
            'new_events': new_event_count,
            'queued_for_processing': new_event_count
        }
        
    except Exception as e:
        return {'error': str(e)}


@app.task(name='tasks.cleanup_expired_signals')
def cleanup_expired_signals():
    """
    Mark old signals as expired
    
    Signals older than 3 days are marked as expired
    Runs daily at midnight
    """
    if not SessionLocal:
        return {'error': 'Database not available'}
    
    session = SessionLocal()
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=3)
        
        expired_count = session.query(Signal)\
            .filter(Signal.generated_at < cutoff)\
            .filter(Signal.status == 'active')\
            .update({'status': 'expired'})
        
        session.commit()
        session.close()
        
        return {
            'status': 'success',
            'expired_signals': expired_count
        }
        
    except Exception as e:
        session.rollback()
        session.close()
        return {'error': str(e)}


@app.task(name='tasks.daily_summary')
def generate_daily_summary():
    """
    Generate daily statistics summary
    
    Runs daily at 6am UTC
    """
    if not SessionLocal:
        return {'error': 'Database not available'}
    
    session = SessionLocal()
    
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Count events and signals
        events_count = session.query(Event)\
            .filter(Event.event_timestamp >= yesterday)\
            .count()
        
        signals_count = session.query(Signal)\
            .filter(Signal.generated_at >= yesterday)\
            .count()
        
        # Average confidence
        from sqlalchemy import func
        avg_confidence = session.query(func.avg(Signal.confidence))\
            .filter(Signal.generated_at >= yesterday)\
            .scalar()
        
        # Top tickers
        from sqlalchemy import func, desc
        top_tickers = session.query(
            Signal.ticker,
            func.count(Signal.id).label('count')
        ).filter(Signal.generated_at >= yesterday)\
         .group_by(Signal.ticker)\
         .order_by(desc('count'))\
         .limit(5)\
         .all()
        
        session.close()
        
        summary = {
            'date': yesterday.date().isoformat(),
            'events': events_count,
            'signals': signals_count,
            'average_confidence': round(float(avg_confidence), 3) if avg_confidence else 0.0,
            'top_tickers': [{'ticker': t, 'count': c} for t, c in top_tickers]
        }
        
        return {
            'status': 'success',
            'summary': summary
        }
        
    except Exception as e:
        return {'error': str(e)}


# Periodic task schedule
app.conf.beat_schedule = {
    'ingest-realtime-every-minute': {
        'task': 'tasks.ingest_realtime_data',
        'schedule': 60.0,  # Every minute
    },
    'cleanup-expired-signals-daily': {
        'task': 'tasks.cleanup_expired_signals',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'daily-summary': {
        'task': 'tasks.daily_summary',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6am UTC
    },
}


if __name__ == '__main__':
    print("\n🔄 Celery Worker - Political Sentiment Alpha Platform\n")
    print("Configured tasks:")
    print("  - process_nlp_batch")
    print("  - compute_event_study")
    print("  - ingest_realtime_data (every 1 min)")
    print("  - cleanup_expired_signals (daily at midnight)")
    print("  - daily_summary (daily at 6am UTC)")
    print("\nStarting worker...\n")
    
    # Start worker
    app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=4'
    ])

