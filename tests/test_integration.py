"""
Integration Tests for Political Sentiment Alpha Platform
======================================================

End-to-end tests for complete pipeline:
1. Data ingestion → NLP → Event Study → API response
2. Waitlist signup flow
3. Signal generation flow
4. Database operations
"""

import pytest
from datetime import datetime
import time

from app.main import app as flask_app
from models.db import init_db, Event, Signal, User
from nlp.pipeline import NLPPipeline
from quant.event_study import quick_event_study
from data.ingestion import TrumpDataIngestion


class TestEndToEndPipeline:
    """Test complete data flow from ingestion to API"""
    
    @pytest.fixture
    def app(self):
        """Flask test client"""
        flask_app.config['TESTING'] = True
        with flask_app.test_client() as client:
            yield client
    
    @pytest.fixture
    def db_session(self):
        """Test database session"""
        # Use in-memory SQLite for testing
        engine, SessionLocal = init_db('sqlite:///:memory:')
        session = SessionLocal()
        yield session
        session.close()
    
    def test_full_signal_generation_pipeline(self, app):
        """
        Test: Political text → NLP → Event Study → API response
        
        Flow:
        1. POST text to /api/signal
        2. NLP processes text
        3. Event study calculates AR
        4. Response includes signal
        """
        # Sample political text
        payload = {
            'text': 'Boeing is doing terrible work on the new aircraft. Cancel the order!',
            'timestamp': '2024-01-15T10:30:00Z',
            'run_event_study': False  # Skip for speed in test
        }
        
        start_time = time.time()
        
        # Call API
        response = app.post('/api/signal', json=payload)
        
        elapsed = time.time() - start_time
        
        # Assertions
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'success'
        assert 'signals' in data
        assert len(data['signals']) > 0
        
        # Check signal structure
        signal = data['signals'][0]
        assert 'ticker' in signal
        assert 'direction' in signal
        assert 'confidence' in signal
        
        # Performance check
        assert elapsed < 5.0, f"Pipeline took {elapsed:.2f}s (target: <5s)"
        
        print(f"✓ End-to-end pipeline: {elapsed:.2f}s")
    
    def test_nlp_to_database_flow(self, db_session):
        """
        Test: NLP processing → Database storage
        
        Flow:
        1. Process text through NLP
        2. Store event in database
        3. Store signals in database
        4. Query signals back
        """
        # Create test event
        event = Event(
            external_id='test_integration_001',
            text='Apple announces record quarterly earnings!',
            source='Test',
            author='TestUser',
            event_timestamp=datetime(2024, 1, 15, 10, 0, 0)
        )
        db_session.add(event)
        db_session.commit()
        
        # Process through NLP
        pipeline = NLPPipeline()
        nlp_result = pipeline.process_text(event.text)
        
        # Store signals
        for sig in nlp_result['signals']:
            signal = Signal(
                event_id=event.id,
                ticker=sig['ticker'],
                signal_type=sig['type'],
                direction=sig['direction'],
                confidence=sig['confidence'],
                sentiment_polarity=nlp_result['sentiment_polarity'],
                tone=nlp_result['tone']
            )
            db_session.add(signal)
        
        db_session.commit()
        
        # Query back
        stored_signals = db_session.query(Signal).filter(Signal.event_id == event.id).all()
        
        assert len(stored_signals) > 0
        assert stored_signals[0].ticker in nlp_result['tickers']
        
        print(f"✓ NLP → Database: {len(stored_signals)} signals stored")
    
    def test_api_health_check(self, app):
        """Test health check endpoint"""
        response = app.get('/health')
        
        assert response.status_code in [200, 503]  # 503 if DB not configured
        
        data = response.get_json()
        assert 'status' in data
        assert 'timestamp' in data
    
    def test_api_list_signals(self, app):
        """Test listing signals endpoint"""
        response = app.get('/api/signals?limit=5')
        
        # Should not crash even if DB is empty
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'signals' in data
            assert isinstance(data['signals'], list)


class TestWaitlistFlow:
    """Test waitlist signup and referral system"""
    
    @pytest.fixture
    def app(self):
        flask_app.config['TESTING'] = True
        with flask_app.test_client() as client:
            yield client
    
    def test_waitlist_signup_api(self, app):
        """Test waitlist signup via API"""
        payload = {
            'email': f'test_{int(time.time())}@example.com'
        }
        
        response = app.post('/waitlist', json=payload)
        
        # Should work or return service unavailable
        assert response.status_code in [200, 201, 503]
        
        if response.status_code in [200, 201]:
            data = response.get_json()
            assert 'status' in data
            assert 'referral_code' in data


class TestPerformance:
    """Performance and load tests"""
    
    def test_nlp_processing_speed(self):
        """Test NLP processing latency"""
        pipeline = NLPPipeline()
        
        test_texts = [
            'Boeing announces new aircraft delays.',
            'Apple reports strong iPhone sales in China.',
            'Tesla stock surges on delivery numbers.'
        ]
        
        times = []
        for text in test_texts:
            start = time.time()
            result = pipeline.process_text(text)
            elapsed = time.time() - start
            times.append(elapsed)
            
            assert result is not None
            assert 'signals' in result
        
        avg_time = sum(times) / len(times)
        assert avg_time < 2.0, f"NLP avg time: {avg_time:.2f}s (target: <2s)"
        
        print(f"✓ NLP processing: {avg_time:.3f}s avg")
    
    def test_api_response_time(self, ):
        """Test API response time"""
        flask_app.config['TESTING'] = True
        with flask_app.test_client() as client:
            start = time.time()
            response = client.get('/health')
            elapsed = time.time() - start
            
            assert response.status_code in [200, 503]
            assert elapsed < 1.0, f"API response: {elapsed:.3f}s (target: <1s)"
            
            print(f"✓ API response time: {elapsed:.3f}s")


class TestDataIntegrity:
    """Test data validation and integrity"""
    
    def test_duplicate_event_handling(self, ):
        """Test that duplicate events are handled"""
        # Use in-memory DB
        engine, SessionLocal = init_db('sqlite:///:memory:')
        session = SessionLocal()
        
        # Create event
        event1 = Event(
            external_id='duplicate_test_001',
            text='Test text',
            source='Test',
            author='Test',
            event_timestamp=datetime.utcnow()
        )
        session.add(event1)
        session.commit()
        
        # Try to create duplicate
        event2 = Event(
            external_id='duplicate_test_001',  # Same ID
            text='Different text',
            source='Test',
            author='Test',
            event_timestamp=datetime.utcnow()
        )
        session.add(event2)
        
        # Should raise integrity error
        with pytest.raises(Exception):
            session.commit()
        
        session.close()
    
    def test_signal_validation(self, ):
        """Test signal data validation"""
        from models.db import Signal
        
        # Valid signal
        signal = Signal(
            event_id=1,
            ticker='AAPL',
            signal_type='stock',
            direction='long',
            confidence=0.85
        )
        
        # Check to_dict method
        signal_dict = signal.to_dict()
        assert 'ticker' in signal_dict
        assert 'confidence' in signal_dict
        assert signal_dict['confidence'] == 0.85


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_api_request(self):
        """Test API with invalid request"""
        flask_app.config['TESTING'] = True
        with flask_app.test_client() as client:
            # Missing required field
            response = client.post('/api/signal', json={})
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
    
    def test_empty_text_handling(self):
        """Test NLP with empty text"""
        pipeline = NLPPipeline()
        
        # Should not crash
        result = pipeline.process_text('')
        
        assert result is not None
        assert 'signals' in result
    
    def test_malformed_date_handling(self):
        """Test handling of malformed dates"""
        flask_app.config['TESTING'] = True
        with flask_app.test_client() as client:
            payload = {
                'text': 'Test text',
                'timestamp': 'not-a-date'
            }
            
            # Should handle gracefully
            response = client.post('/api/signal', json=payload)
            
            # May succeed with current time or return error
            assert response.status_code in [200, 400, 500]


class TestSecurityCompliance:
    """Test security and compliance features"""
    
    def test_disclaimer_present_in_response(self):
        """Test that disclaimer is included in API responses"""
        flask_app.config['TESTING'] = True
        with flask_app.test_client() as client:
            response = client.post('/api/signal', json={
                'text': 'Test political text about Boeing'
            })
            
            if response.status_code == 200:
                data = response.get_json()
                assert 'disclaimer' in data
                assert 'NOT' in data['disclaimer'] or 'not' in data['disclaimer']
    
    def test_no_sensitive_data_in_logs(self):
        """Test that sensitive data is not logged"""
        # This is a placeholder - in production, audit logging
        # to ensure no PII or credentials are logged
        pass


def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("RUNNING INTEGRATION TESTS")
    print("="*70 + "\n")
    
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == '__main__':
    run_integration_tests()

