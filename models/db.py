"""
Database Models for Political Sentiment Alpha Platform
=====================================================

SQLAlchemy models for:
- Events (political communications)
- Signals (trading signals generated)
- Disclosures (government filings)
- Users (for waitlist/pro tier)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB

from config import config

Base = declarative_base()


class Event(Base):
    """
    Political event/communication
    
    Stores raw political communications from all sources
    """
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(255), unique=True, index=True)  # Source-specific ID
    
    # Content
    text = Column(Text, nullable=False)
    source = Column(String(100), nullable=False, index=True)  # Twitter, Truth Social, etc.
    author = Column(String(100), index=True)  # Trump, family member, etc.
    
    # Timestamps
    event_timestamp = Column(DateTime, nullable=False, index=True)  # When event occurred
    ingested_at = Column(DateTime, default=datetime.utcnow)  # When we ingested it
    processed_at = Column(DateTime, nullable=True)  # When NLP processed
    
    # Metadata
    metadata = Column(JSONB, nullable=True)  # Likes, retweets, etc.
    
    # Relationships
    signals = relationship('Signal', back_populates='event', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Event(id={self.id}, author={self.author}, timestamp={self.event_timestamp})>"


class Signal(Base):
    """
    Trading signal generated from political event
    
    Output of NLP + Event Study analysis
    """
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False, index=True)
    
    # Signal details
    ticker = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(50), nullable=False)  # 'stock', 'sector_etf'
    direction = Column(String(20), nullable=False)  # 'long', 'short', 'neutral'
    
    # Confidence & metrics
    confidence = Column(Float, nullable=False)
    sentiment_polarity = Column(Float, nullable=True)
    tone = Column(String(50), nullable=True)
    
    # Event study results
    abnormal_return = Column(Float, nullable=True)
    car = Column(Float, nullable=True)  # Cumulative AR
    p_value = Column(Float, nullable=True)
    is_significant = Column(Boolean, default=False)
    beta = Column(Float, nullable=True)
    
    # Status
    is_outlier = Column(Boolean, default=False)
    status = Column(String(50), default='active')  # 'active', 'expired', 'executed'
    
    # Explanation (for compliance)
    explanation = Column(Text, nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    event = relationship('Event', back_populates='signals')
    
    def __repr__(self):
        return f"<Signal(id={self.id}, ticker={self.ticker}, direction={self.direction}, confidence={self.confidence:.2f})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'ticker': self.ticker,
            'type': self.signal_type,
            'direction': self.direction,
            'confidence': round(self.confidence, 3),
            'sentiment_polarity': round(self.sentiment_polarity, 3) if self.sentiment_polarity else None,
            'tone': self.tone,
            'abnormal_return': round(self.abnormal_return, 6) if self.abnormal_return else None,
            'ar_percentage': round(self.abnormal_return * 100, 4) if self.abnormal_return else None,
            'is_significant': self.is_significant,
            'is_outlier': self.is_outlier,
            'explanation': self.explanation,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'status': self.status
        }


class Disclosure(Base):
    """
    Government/family financial disclosure
    
    From FEC, OGE, or family member disclosures
    """
    __tablename__ = 'disclosures'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Source info
    source = Column(String(100), nullable=False)  # 'FEC', 'OGE', 'SEC'
    disclosure_type = Column(String(100), nullable=False)
    
    # Subject
    official_name = Column(String(255), nullable=False, index=True)
    position = Column(String(255), nullable=True)
    
    # Content
    entities = Column(JSONB, nullable=True)  # List of companies/holdings
    filing_date = Column(DateTime, nullable=False, index=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    # Metadata
    document_url = Column(String(500), nullable=True)
    raw_data = Column(JSONB, nullable=True)
    
    # Timestamps
    ingested_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Disclosure(id={self.id}, official={self.official_name}, type={self.disclosure_type})>"


class User(Base):
    """
    User account (for waitlist and pro tier)
    
    Minimal data collection for compliance
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic info
    email = Column(String(255), unique=True, nullable=False, index=True)
    tier = Column(String(50), default='waitlist')  # 'waitlist', 'free', 'pro', 'institutional'
    
    # Waitlist
    referral_code = Column(String(50), unique=True, nullable=True, index=True)
    referred_by = Column(String(50), nullable=True)
    referral_count = Column(Integer, default=0)
    
    # Subscription
    stripe_customer_id = Column(String(255), nullable=True)
    subscription_status = Column(String(50), default='inactive')  # 'active', 'inactive', 'cancelled'
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    
    # Access control
    is_active = Column(Boolean, default=True)
    api_key = Column(String(255), unique=True, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tier={self.tier})>"
    
    def to_dict(self):
        """Convert to dictionary (exclude sensitive fields)"""
        return {
            'id': self.id,
            'email': self.email,
            'tier': self.tier,
            'referral_code': self.referral_code,
            'referral_count': self.referral_count,
            'subscription_status': self.subscription_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BacktestResult(Base):
    """
    Backtesting results for historical validation
    """
    __tablename__ = 'backtest_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Backtest params
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    strategy = Column(String(100), nullable=False)
    
    # Performance metrics
    total_signals = Column(Integer, default=0)
    profitable_signals = Column(Integer, default=0)
    win_rate = Column(Float, nullable=True)
    average_return = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    
    # Details
    results_json = Column(JSONB, nullable=True)
    
    # Timestamps
    run_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BacktestResult(id={self.id}, win_rate={self.win_rate:.2f}%, sharpe={self.sharpe_ratio:.2f})>"


# Database initialization
def init_db(database_url: Optional[str] = None):
    """
    Initialize database connection and create tables
    
    Args:
        database_url: Database connection string (default from config)
    """
    db_url = database_url or config.DATABASE_URL
    
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    print(f"✓ Database initialized: {db_url.split('@')[-1] if '@' in db_url else 'local'}")
    
    return engine, SessionLocal


def get_session(SessionLocal):
    """
    Get database session with automatic cleanup
    
    Usage:
        with get_session(SessionLocal) as session:
            # use session
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


if __name__ == '__main__':
    # Test database initialization
    print("\n🧪 Testing Database Models\n")
    
    # Use SQLite for testing
    test_db_url = 'sqlite:///test_political_alpha.db'
    engine, SessionLocal = init_db(test_db_url)
    
    # Create test data
    session = SessionLocal()
    
    try:
        # Create test event
        event = Event(
            external_id='test_tweet_001',
            text='Boeing is doing great work on Air Force One!',
            source='Twitter',
            author='realDonaldTrump',
            event_timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        session.add(event)
        session.commit()
        
        print(f"✓ Created event: {event}")
        
        # Create test signal
        signal = Signal(
            event_id=event.id,
            ticker='BA',
            signal_type='stock',
            direction='long',
            confidence=0.85,
            sentiment_polarity=0.75,
            tone='Cooperative',
            abnormal_return=0.0025,
            is_significant=True,
            explanation='Positive sentiment with direct company mention'
        )
        session.add(signal)
        session.commit()
        
        print(f"✓ Created signal: {signal}")
        
        # Query test
        signals = session.query(Signal).filter(Signal.confidence > 0.8).all()
        print(f"\n✓ Found {len(signals)} high-confidence signals")
        
        for sig in signals:
            print(f"  {sig.ticker}: {sig.direction} (confidence: {sig.confidence:.2f})")
        
        print("\n✓ Database tests passed!")
        
    finally:
        session.close()

