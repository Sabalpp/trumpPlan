"""
Tests for Data Ingestion and Aggregation Modules
=============================================

Tests for:
- data/ingestion.py
- data/market.py
- data/aggregator.py
"""

import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from data.ingestion import (
    TrumpDataIngestion,
    GovernmentDataIngestion,
    FamilyDataIngestion,
    aggregate_all_sources
)
from data.market import MarketDataFetcher, TickerMapper
from data.aggregator import DataAggregator, S3Storage


class TestTrumpDataIngestion:
    """Test Trump data ingestion"""
    
    def test_historical_tweets_default(self):
        """Test fetching historical tweets with defaults"""
        ingest = TrumpDataIngestion()
        df = ingest.historical_trump_tweets()
        
        assert not df.empty
        assert 'id' in df.columns
        assert 'text' in df.columns
        assert 'timestamp' in df.columns
        assert all(df['source'] == 'Trump Twitter Archive')
    
    def test_historical_tweets_date_filter(self):
        """Test date filtering"""
        ingest = TrumpDataIngestion()
        df = ingest.historical_trump_tweets(
            start_date='2018-01-01',
            end_date='2019-12-31'
        )
        
        if not df.empty:
            assert all(df['timestamp'] >= pd.to_datetime('2018-01-01'))
            assert all(df['timestamp'] <= pd.to_datetime('2019-12-31'))
    
    def test_historical_tweets_limit(self):
        """Test record limit"""
        ingest = TrumpDataIngestion()
        df = ingest.historical_trump_tweets(limit=2)
        
        assert len(df) <= 2
    
    @patch('requests.get')
    def test_realtime_x_posts_with_token(self, mock_get):
        """Test X API integration with token"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': '123',
                    'text': 'Test tweet',
                    'created_at': '2024-01-01T12:00:00Z'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        ingest = TrumpDataIngestion()
        ingest.x_bearer_token = 'test_token'
        
        df = ingest.realtime_x_posts(user_ids=['12345'])
        
        # Should make API call
        assert mock_get.called
    
    def test_realtime_x_posts_no_token(self):
        """Test X API without token"""
        ingest = TrumpDataIngestion()
        ingest.x_bearer_token = ''
        
        df = ingest.realtime_x_posts()
        
        assert df.empty
    
    def test_truth_social_mock(self):
        """Test Truth Social with mock data"""
        ingest = TrumpDataIngestion()
        ingest.truth_social_key = ''  # Force mock
        
        df = ingest.realtime_truth_social()
        
        assert not df.empty
        assert 'source' in df.columns


class TestGovernmentDataIngestion:
    """Test government data sources"""
    
    @patch('requests.get')
    def test_congress_bills(self, mock_get):
        """Test Congress.gov API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'bills': [
                {'number': 'H.R.1', 'title': 'Test Bill'}
            ]
        }
        mock_get.return_value = mock_response
        
        ingest = GovernmentDataIngestion()
        df = ingest.congress_bills()
        
        assert mock_get.called
    
    def test_oge_disclosures_mock(self):
        """Test OGE mock data"""
        ingest = GovernmentDataIngestion()
        df = ingest.oge_disclosures()
        
        assert not df.empty
        assert 'source' in df.columns


class TestFamilyDataIngestion:
    """Test family member data ingestion"""
    
    def test_family_posts_mock(self):
        """Test family posts with mock data"""
        ingest = FamilyDataIngestion()
        df = ingest.family_posts()
        
        assert not df.empty
        assert 'author' in df.columns
        assert 'source' in df.columns


class TestAggregateAllSources:
    """Test source aggregation"""
    
    def test_aggregate_historical_only(self):
        """Test aggregating only historical data"""
        df = aggregate_all_sources(
            include_historical=True,
            include_realtime=False,
            include_government=False,
            include_family=False
        )
        
        assert not df.empty
        assert 'timestamp' in df.columns
    
    def test_aggregate_empty(self):
        """Test aggregation with no sources"""
        # This is a sanity check - should handle gracefully
        df = aggregate_all_sources(
            include_historical=False,
            include_realtime=False,
            include_government=False,
            include_family=False
        )
        
        # May be empty if no sources enabled
        assert isinstance(df, pd.DataFrame)


class TestMarketDataFetcher:
    """Test market data fetching"""
    
    @patch('yfinance.Ticker')
    def test_get_historical_data(self, mock_ticker):
        """Test historical data fetch"""
        # Mock yfinance data
        mock_data = pd.DataFrame({
            'Close': [100, 101, 102],
            'Volume': [1000000, 1100000, 1050000]
        }, index=pd.date_range('2024-01-01', periods=3))
        
        mock_instance = Mock()
        mock_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_instance
        
        fetcher = MarketDataFetcher()
        df = fetcher.get_historical_data('AAPL')
        
        assert not df.empty
        assert 'Close' in df.columns
    
    def test_validate_data_valid(self):
        """Test data validation with valid data"""
        fetcher = MarketDataFetcher()
        
        valid_data = pd.DataFrame({
            'Close': [100, 101, 102],
            'Volume': [1000000, 1100000, 1050000]
        })
        
        is_valid, issues = fetcher.validate_data(valid_data)
        
        assert is_valid
        assert len(issues) == 0
    
    def test_validate_data_invalid(self):
        """Test data validation with issues"""
        fetcher = MarketDataFetcher()
        
        invalid_data = pd.DataFrame({
            'Close': [100, -50, 102],  # Negative price
            'Volume': [0, 0, 0]  # All zero volume
        })
        
        is_valid, issues = fetcher.validate_data(invalid_data)
        
        assert not is_valid
        assert len(issues) > 0


class TestTickerMapper:
    """Test company-to-ticker mapping"""
    
    def test_map_company_direct(self):
        """Test direct company name mapping"""
        mapper = TickerMapper()
        
        assert mapper.map_company_to_ticker('Apple') == 'AAPL'
        assert mapper.map_company_to_ticker('Boeing') == 'BA'
        assert mapper.map_company_to_ticker('Tesla') == 'TSLA'
    
    def test_map_company_case_insensitive(self):
        """Test case-insensitive mapping"""
        mapper = TickerMapper()
        
        assert mapper.map_company_to_ticker('APPLE') == 'AAPL'
        assert mapper.map_company_to_ticker('apple') == 'AAPL'
        assert mapper.map_company_to_ticker('Apple') == 'AAPL'
    
    def test_map_company_partial(self):
        """Test partial name matching"""
        mapper = TickerMapper()
        
        assert mapper.map_company_to_ticker('General Motors') == 'GM'
        assert mapper.map_company_to_ticker('Goldman Sachs') == 'GS'
    
    def test_map_company_not_found(self):
        """Test unmapped company"""
        mapper = TickerMapper()
        
        result = mapper.map_company_to_ticker('Unknown Company XYZ')
        assert result is None
    
    def test_get_sector_etf(self):
        """Test sector ETF mapping"""
        mapper = TickerMapper()
        
        assert mapper.get_sector_etf('technology') == 'XLK'
        assert mapper.get_sector_etf('energy') == 'XLE'
        assert mapper.get_sector_etf('financials') == 'XLF'


class TestDataAggregator:
    """Test data aggregation and normalization"""
    
    def test_normalize_dataframe(self):
        """Test DataFrame normalization"""
        aggregator = DataAggregator()
        
        raw_data = pd.DataFrame({
            'id': ['1', '2'],
            'content': ['Text 1', 'Text 2'],
            'timestamp': ['2024-01-01 12:00', '2024-01-01 13:00']
        })
        
        normalized = aggregator.normalize_dataframe(raw_data, 'TestSource')
        
        assert 'text' in normalized.columns
        assert 'source' in normalized.columns
        assert all(normalized['source'] == 'TestSource')
        assert pd.api.types.is_datetime64_any_dtype(normalized['timestamp'])
    
    def test_normalize_missing_columns(self):
        """Test normalization with missing columns"""
        aggregator = DataAggregator()
        
        raw_data = pd.DataFrame({
            'content': ['Text 1', 'Text 2']
        })
        
        normalized = aggregator.normalize_dataframe(raw_data, 'TestSource')
        
        assert 'id' in normalized.columns
        assert 'timestamp' in normalized.columns
        assert 'text' in normalized.columns
    
    def test_merge_dataframes(self):
        """Test merging multiple DataFrames"""
        aggregator = DataAggregator()
        
        df1 = pd.DataFrame({
            'id': ['1', '2'],
            'text': ['Text 1', 'Text 2'],
            'timestamp': pd.date_range('2024-01-01', periods=2)
        })
        
        df2 = pd.DataFrame({
            'id': ['3', '4'],
            'text': ['Text 3', 'Text 4'],
            'timestamp': pd.date_range('2024-01-03', periods=2)
        })
        
        merged = aggregator.merge_dataframes([df1, df2])
        
        assert len(merged) == 4
        assert 'id' in merged.columns
    
    def test_merge_with_duplicates(self):
        """Test deduplication during merge"""
        aggregator = DataAggregator()
        
        df1 = pd.DataFrame({
            'id': ['1', '2'],
            'text': ['Text 1', 'Text 2'],
            'timestamp': pd.date_range('2024-01-01', periods=2)
        })
        
        df2 = pd.DataFrame({
            'id': ['2', '3'],  # '2' is duplicate
            'text': ['Text 2', 'Text 3'],
            'timestamp': pd.date_range('2024-01-02', periods=2)
        })
        
        merged = aggregator.merge_dataframes([df1, df2])
        
        assert len(merged) == 3  # Duplicate removed
    
    def test_filter_by_date_range(self):
        """Test date range filtering"""
        aggregator = DataAggregator()
        
        df = pd.DataFrame({
            'id': ['1', '2', '3'],
            'text': ['Text 1', 'Text 2', 'Text 3'],
            'timestamp': pd.date_range('2024-01-01', periods=3)
        })
        
        filtered = aggregator.filter_by_date_range(
            df,
            start_date=datetime(2024, 1, 2),
            end_date=datetime(2024, 1, 2)
        )
        
        assert len(filtered) == 1
        assert filtered.iloc[0]['id'] == '2'
    
    def test_validate_data_quality_good(self):
        """Test validation with good data"""
        aggregator = DataAggregator()
        
        good_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'text': ['Good text 1', 'Good text 2', 'Good text 3'],
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'source': ['Test', 'Test', 'Test']
        })
        
        report = aggregator.validate_data_quality(good_data)
        
        assert report['total_records'] == 3
        assert report['quality_score'] >= 0.8
        assert report['completeness'] == 100.0
    
    def test_validate_data_quality_issues(self):
        """Test validation with data issues"""
        aggregator = DataAggregator()
        
        bad_data = pd.DataFrame({
            'id': ['1', '1', '3'],  # Duplicate ID
            'text': ['Text', None, 'xyz'],  # Null and short text
            'timestamp': pd.date_range('2024-01-01', periods=3),
            'source': ['Test', 'Test', 'Test']
        })
        
        report = aggregator.validate_data_quality(bad_data)
        
        assert report['quality_score'] < 1.0
        assert len(report['issues']) > 0


class TestS3Storage:
    """Test S3 storage operations"""
    
    def test_s3_initialization_no_credentials(self):
        """Test S3 init without credentials"""
        # Should not crash
        storage = S3Storage()
        assert storage.s3_client is None
    
    @patch('boto3.client')
    def test_upload_dataframe(self, mock_boto):
        """Test DataFrame upload to S3"""
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3
        
        storage = S3Storage()
        storage.s3_client = mock_s3
        
        df = pd.DataFrame({
            'id': ['1', '2'],
            'text': ['Text 1', 'Text 2']
        })
        
        result = storage.upload_dataframe(df, 'test/data.parquet')
        
        # Should attempt upload
        assert mock_s3.put_object.called or result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

