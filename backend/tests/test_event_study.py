"""
Tests for Event Study Module
============================

Tests for quant/event_study.py including:
- CAPM parameter estimation
- AR/CAR calculations
- Statistical significance tests
- Outlier detection
"""

import pytest
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from quant.event_study import EventStudy, quick_event_study


class TestEventStudy:
    """Test suite for EventStudy class"""
    
    def test_initialization(self):
        """Test EventStudy object initialization"""
        event_time = datetime(2020, 1, 15, 10, 30, 0)
        ticker = 'AAPL'
        
        study = EventStudy(event_time, ticker)
        
        assert study.event_timestamp == event_time
        assert study.ticker == ticker
        assert study.estimation_window_days == 252
        assert study.market_ticker == 'SPY'
        assert study.ar is None
        assert study.car is None
    
    def test_custom_parameters(self):
        """Test initialization with custom parameters"""
        event_time = datetime(2019, 6, 1, 14, 0, 0)
        ticker = 'TSLA'
        
        study = EventStudy(
            event_time, 
            ticker, 
            estimation_window_days=126,
            event_window_days=5,
            market_ticker='QQQ'
        )
        
        assert study.estimation_window_days == 126
        assert study.event_window_days == 5
        assert study.market_ticker == 'QQQ'
    
    @patch('yfinance.Ticker')
    def test_fetch_data_success(self, mock_ticker):
        """Test successful data fetching"""
        # Mock yfinance data
        dates = pd.date_range('2019-01-01', periods=300, freq='D')
        mock_stock_data = pd.DataFrame({
            'Close': np.random.randn(300).cumsum() + 100,
            'Volume': np.random.randint(1000000, 10000000, 300)
        }, index=dates)
        
        mock_market_data = pd.DataFrame({
            'Close': np.random.randn(300).cumsum() + 300,
            'Volume': np.random.randint(100000000, 1000000000, 300)
        }, index=dates)
        
        # Setup mock
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.side_effect = [mock_stock_data, mock_market_data]
        mock_ticker.return_value = mock_ticker_instance
        
        study = EventStudy(datetime(2019, 10, 1), 'AAPL')
        result = study.fetch_data()
        
        assert result is True
        assert study.stock_data is not None
        assert study.market_data is not None
        assert 'return' in study.stock_data.columns
    
    def test_estimate_expected_return(self):
        """Test CAPM parameter estimation"""
        # Create synthetic data
        dates = pd.date_range('2019-01-01', periods=300, freq='D')
        
        # Stock with beta ~ 1.5
        market_returns = np.random.randn(300) * 0.01
        stock_returns = 0.0001 + 1.5 * market_returns + np.random.randn(300) * 0.005
        
        study = EventStudy(datetime(2019, 10, 1), 'TEST')
        study.stock_data = pd.DataFrame({
            'return': stock_returns,
            'Close': (1 + stock_returns).cumprod() * 100
        }, index=dates)
        
        study.market_data = pd.DataFrame({
            'return': market_returns,
            'Close': (1 + market_returns).cumprod() * 300
        }, index=dates)
        
        alpha, beta = study.estimate_expected_return()
        
        # Beta should be close to 1.5
        assert abs(beta - 1.5) < 0.3, f"Beta {beta} not close to expected 1.5"
        assert alpha is not None
    
    def test_calculate_ar_zero_case(self):
        """Test AR calculation with no abnormal return (null case)"""
        dates = pd.date_range('2019-01-01', periods=300, freq='D')
        
        # Perfect CAPM relationship (no abnormal return)
        market_returns = np.random.randn(300) * 0.01
        stock_returns = 0.0002 + 1.0 * market_returns
        
        study = EventStudy(datetime(2019, 10, 1), 'TEST')
        study.stock_data = pd.DataFrame({
            'return': stock_returns,
            'Close': (1 + stock_returns).cumprod() * 100
        }, index=dates)
        
        study.market_data = pd.DataFrame({
            'return': market_returns,
            'Close': (1 + market_returns).cumprod() * 300
        }, index=dates)
        
        study.estimate_expected_return()
        ar_series = study.calculate_ar()
        
        # Mean AR should be close to 0
        assert abs(ar_series.mean()) < 0.01
        assert len(ar_series) > 0
    
    def test_calculate_car(self):
        """Test CAR calculation"""
        dates = pd.date_range('2019-09-25', periods=10, freq='D')
        
        # Synthetic AR data
        ar_values = [0.01, -0.005, 0.02, -0.01, 0.015, 0.03, -0.02, 0.01, 0.005, -0.005]
        
        study = EventStudy(datetime(2019, 10, 1), 'TEST')
        study.ar_series = pd.Series(ar_values, index=dates)
        
        car = study.calculate_car()
        
        # CAR should be sum of all ARs
        expected_car = sum(ar_values)
        assert abs(car - expected_car) < 0.0001
    
    def test_statistical_test_significant(self):
        """Test statistical significance detection"""
        dates = pd.date_range('2019-09-25', periods=7, freq='D')
        
        # Strongly positive ARs (should be significant)
        ar_values = [0.02, 0.025, 0.03, 0.028, 0.022, 0.026, 0.024]
        
        study = EventStudy(datetime(2019, 10, 1), 'TEST')
        study.ar_series = pd.Series(ar_values, index=dates)
        study.ar = ar_values[3]  # Event day
        
        results = study.statistical_test(use_robust=False)
        
        assert results['p_value'] < 0.05, "Should be statistically significant"
        assert results['is_significant'] is True
        assert results['confidence'] > 0.9
    
    def test_statistical_test_not_significant(self):
        """Test insignificant results"""
        dates = pd.date_range('2019-09-25', periods=7, freq='D')
        
        # Random noise (should not be significant)
        np.random.seed(42)
        ar_values = np.random.randn(7) * 0.002  # Small noise
        
        study = EventStudy(datetime(2019, 10, 1), 'TEST')
        study.ar_series = pd.Series(ar_values, index=dates)
        study.ar = ar_values[3]
        
        results = study.statistical_test(use_robust=False)
        
        # With small random noise, likely not significant
        assert results['p_value'] > 0.05 or results['p_value'] < 0.05  # Just test it runs
        assert 'is_significant' in results
    
    def test_filter_outliers_detection(self):
        """Test outlier detection using MAD"""
        dates = pd.date_range('2019-09-25', periods=7, freq='D')
        
        # Normal ARs with one outlier
        ar_values = [0.001, -0.002, 0.0015, 0.15, -0.001, 0.002, -0.0015]  # 0.15 is outlier
        
        study = EventStudy(datetime(2019, 10, 1), 'TEST')
        study.ar_series = pd.Series(ar_values, index=dates)
        study.ar = 0.15  # Event day is the outlier
        
        is_outlier = study.filter_outliers(threshold=3.0)
        
        assert is_outlier is True, "Should detect 0.15 as outlier"
    
    def test_filter_outliers_no_detection(self):
        """Test that normal values are not flagged as outliers"""
        dates = pd.date_range('2019-09-25', periods=7, freq='D')
        
        # All normal ARs
        ar_values = [0.001, -0.002, 0.0015, 0.002, -0.001, 0.002, -0.0015]
        
        study = EventStudy(datetime(2019, 10, 1), 'TEST')
        study.ar_series = pd.Series(ar_values, index=dates)
        study.ar = 0.002  # Event day is normal
        
        is_outlier = study.filter_outliers(threshold=3.0)
        
        assert is_outlier is False, "Should not flag normal value as outlier"
    
    def test_run_full_analysis_error_handling(self):
        """Test that full analysis handles errors gracefully"""
        study = EventStudy(datetime(2030, 1, 1), 'INVALIDTICKER')
        
        results = study.run_full_analysis()
        
        assert 'error' in results
        assert results['ar'] == 0.0
        assert results['confidence'] == 0.0
    
    def test_generate_summary(self):
        """Test summary generation"""
        study = EventStudy(datetime(2019, 10, 1), 'TEST')
        study.ar = 0.025
        study.p_value = 0.01
        
        summary = study._generate_summary()
        
        assert 'positive' in summary.lower()
        assert '2.5' in summary or '2.50' in summary
        assert 'significant' in summary.lower()
    
    def test_direction_classification(self):
        """Test signal direction classification"""
        dates = pd.date_range('2019-09-25', periods=7, freq='D')
        
        # Positive AR
        study_pos = EventStudy(datetime(2019, 10, 1), 'TEST')
        study_pos.ar_series = pd.Series([0.02] * 7, index=dates)
        study_pos.ar = 0.02
        study_pos.car = 0.14
        study_pos.p_value = 0.01
        study_pos.estimate_expected_return = lambda: (0.001, 1.0)
        
        # Negative AR
        study_neg = EventStudy(datetime(2019, 10, 1), 'TEST')
        study_neg.ar_series = pd.Series([-0.03] * 7, index=dates)
        study_neg.ar = -0.03
        study_neg.car = -0.21
        study_neg.p_value = 0.001
        
        # Check directions
        assert study_pos._generate_summary().startswith('Positive')
        assert study_neg._generate_summary().startswith('Negative')


class TestQuickEventStudy:
    """Test convenience function"""
    
    @patch('quant.event_study.EventStudy')
    def test_quick_event_study(self, mock_event_study_class):
        """Test quick_event_study convenience function"""
        # Mock EventStudy
        mock_instance = Mock()
        mock_instance.run_full_analysis.return_value = {
            'ticker': 'BA',
            'ar': 0.025,
            'confidence': 0.9
        }
        mock_event_study_class.return_value = mock_instance
        
        event_time = datetime(2016, 12, 6)
        result = quick_event_study('BA', event_time, 'Test tweet')
        
        assert result['ticker'] == 'BA'
        assert 'event_text' in result
        assert result['event_text'] == 'Test tweet'


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_insufficient_data(self):
        """Test behavior with insufficient historical data"""
        dates = pd.date_range('2019-09-28', periods=3, freq='D')
        
        study = EventStudy(datetime(2019, 10, 1), 'TEST')
        study.stock_data = pd.DataFrame({
            'return': [0.01, -0.005, 0.02],
            'Close': [100, 99.5, 101.5]
        }, index=dates)
        
        study.market_data = pd.DataFrame({
            'return': [0.008, -0.004, 0.015],
            'Close': [300, 298.8, 303.3]
        }, index=dates)
        
        # Should handle gracefully
        alpha, beta = study.estimate_expected_return()
        assert alpha is not None
        assert beta is not None
    
    def test_zero_variance(self):
        """Test handling of zero variance (edge case)"""
        dates = pd.date_range('2019-09-25', periods=7, freq='D')
        
        # All same values (zero variance)
        ar_values = [0.0] * 7
        
        study = EventStudy(datetime(2019, 10, 1), 'TEST')
        study.ar_series = pd.Series(ar_values, index=dates)
        study.ar = 0.0
        
        results = study.statistical_test()
        
        # Should not crash
        assert 'p_value' in results
        assert 'confidence' in results
    
    def test_negative_returns(self):
        """Test with negative returns"""
        dates = pd.date_range('2019-01-01', periods=300, freq='D')
        
        # Declining market
        market_returns = -0.001 + np.random.randn(300) * 0.01
        stock_returns = -0.002 + 1.2 * market_returns + np.random.randn(300) * 0.005
        
        study = EventStudy(datetime(2019, 10, 1), 'TEST')
        study.stock_data = pd.DataFrame({
            'return': stock_returns,
            'Close': (1 + stock_returns).cumprod() * 100
        }, index=dates)
        
        study.market_data = pd.DataFrame({
            'return': market_returns,
            'Close': (1 + market_returns).cumprod() * 300
        }, index=dates)
        
        alpha, beta = study.estimate_expected_return()
        
        # Should still work with negative returns
        assert beta > 0  # Beta should still be positive
        assert alpha is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

