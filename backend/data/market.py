"""
Market Data Module
================

Fetch market data from multiple sources:
1. Alpha Vantage - Intraday and daily OHLCV
2. yfinance - Historical data and real-time quotes
3. Fallback mechanisms for redundancy

Handles rate limits, caching, and data validation.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import warnings

import pandas as pd
import numpy as np
import yfinance as yf
import requests

from config import config

warnings.filterwarnings('ignore')


class MarketDataFetcher:
    """Unified market data fetcher with multiple source support"""
    
    def __init__(self):
        self.alpha_vantage_key = config.ALPHA_VANTAGE_API_KEY
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # 5 minutes
    
    def get_historical_data(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (default: 1 year ago)
            end_date: End date (default: today)
            interval: Data interval ('1d', '1h', '5m', etc.)
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        # Set defaults
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)
        
        # Check cache
        cache_key = f"{ticker}_{start_date.date()}_{end_date.date()}_{interval}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                print(f"📦 Using cached data for {ticker}")
                return cached_data
        
        # Try yfinance first (faster and free)
        try:
            data = self._fetch_yfinance(ticker, start_date, end_date, interval)
            if not data.empty:
                self.cache[cache_key] = (data, time.time())
                return data
        except Exception as e:
            print(f"⚠️  yfinance failed for {ticker}: {str(e)}")
        
        # Fallback to Alpha Vantage
        if self.alpha_vantage_key and self.alpha_vantage_key != 'your_alpha_vantage_key_here':
            try:
                data = self._fetch_alpha_vantage(ticker, interval)
                if not data.empty:
                    # Filter by date range
                    data = data[(data.index >= start_date) & (data.index <= end_date)]
                    self.cache[cache_key] = (data, time.time())
                    return data
            except Exception as e:
                print(f"⚠️  Alpha Vantage failed for {ticker}: {str(e)}")
        
        print(f"❌ All data sources failed for {ticker}")
        return pd.DataFrame()
    
    def _fetch_yfinance(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> pd.DataFrame:
        """Fetch data from yfinance"""
        stock = yf.Ticker(ticker)
        
        # Map interval to yfinance format
        yf_interval = interval
        if interval == '1d':
            data = stock.history(start=start_date, end=end_date, interval='1d')
        elif interval == '1h':
            data = stock.history(start=start_date, end=end_date, interval='1h')
        elif interval == '5m':
            # yfinance limits 5m data to last 60 days
            data = stock.history(period='60d', interval='5m')
        elif interval == '1m':
            # 1m data limited to last 7 days
            data = stock.history(period='7d', interval='1m')
        else:
            data = stock.history(start=start_date, end=end_date)
        
        if data.empty:
            raise ValueError(f"No data returned for {ticker}")
        
        print(f"✓ Fetched {len(data)} rows for {ticker} from yfinance")
        return data
    
    def _fetch_alpha_vantage(
        self,
        ticker: str,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """Fetch data from Alpha Vantage API"""
        
        # Determine function type
        if interval == '1d':
            function = 'TIME_SERIES_DAILY_ADJUSTED'
            interval_key = None
        elif interval in ['1min', '5min', '15min', '30min', '60min']:
            function = 'TIME_SERIES_INTRADAY'
            interval_key = interval
        else:
            function = 'TIME_SERIES_DAILY_ADJUSTED'
            interval_key = None
        
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': function,
            'symbol': ticker,
            'apikey': self.alpha_vantage_key,
            'outputsize': 'full'
        }
        
        if interval_key:
            params['interval'] = interval_key
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            raise ValueError(f"Alpha Vantage API returned {response.status_code}")
        
        data = response.json()
        
        # Check for error message
        if 'Error Message' in data:
            raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
        
        if 'Note' in data:
            # Rate limit message
            raise ValueError("Alpha Vantage rate limit reached")
        
        # Parse time series data
        if function == 'TIME_SERIES_DAILY_ADJUSTED':
            time_series = data.get('Time Series (Daily)', {})
        elif function == 'TIME_SERIES_INTRADAY':
            time_series_key = f'Time Series ({interval_key})'
            time_series = data.get(time_series_key, {})
        else:
            raise ValueError("Unknown function type")
        
        if not time_series:
            raise ValueError(f"No time series data in response for {ticker}")
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Rename columns
        column_map = {
            '1. open': 'Open',
            '2. high': 'High',
            '3. low': 'Low',
            '4. close': 'Close',
            '5. adjusted close': 'Adj Close',
            '5. volume': 'Volume',
            '6. volume': 'Volume'
        }
        df.rename(columns=column_map, inplace=True)
        
        # Convert to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        print(f"✓ Fetched {len(df)} rows for {ticker} from Alpha Vantage")
        return df
    
    def get_realtime_quote(self, ticker: str) -> Dict:
        """
        Get real-time quote for a ticker
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dict with current price, volume, change, etc.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            quote = {
                'ticker': ticker,
                'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
                'timestamp': datetime.now(),
                'source': 'yfinance'
            }
            
            return quote
            
        except Exception as e:
            print(f"❌ Error fetching quote for {ticker}: {str(e)}")
            return {}
    
    def get_intraday_data(
        self,
        ticker: str,
        interval: str = '5m',
        days_back: int = 1
    ) -> pd.DataFrame:
        """
        Get intraday data for low-latency event studies
        
        Args:
            ticker: Stock ticker symbol
            interval: Time interval ('1m', '5m', '15m', '30m', '1h')
            days_back: Number of days of history
        
        Returns:
            DataFrame with intraday OHLCV
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        return self.get_historical_data(ticker, start_date, end_date, interval)
    
    def get_market_index(
        self,
        index: str = 'SPY',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get market index data (for CAPM calculations)
        
        Args:
            index: Index ticker (SPY, QQQ, DIA, etc.)
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame with index data
        """
        return self.get_historical_data(index, start_date, end_date, '1d')
    
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate market data quality
        
        Args:
            df: Market data DataFrame
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        if df.empty:
            return False, ['DataFrame is empty']
        
        required_cols = ['Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")
        
        # Check for excessive NaN values
        if 'Close' in df.columns:
            nan_pct = df['Close'].isna().sum() / len(df) * 100
            if nan_pct > 10:
                issues.append(f"High NaN percentage in Close: {nan_pct:.1f}%")
        
        # Check for negative prices
        if 'Close' in df.columns:
            negative = (df['Close'] < 0).sum()
            if negative > 0:
                issues.append(f"Found {negative} negative prices")
        
        # Check for zero volume days (potential data quality issue)
        if 'Volume' in df.columns:
            zero_vol = (df['Volume'] == 0).sum()
            if zero_vol > len(df) * 0.1:  # More than 10% zero volume
                issues.append(f"High number of zero volume days: {zero_vol}")
        
        is_valid = len(issues) == 0
        return is_valid, issues


class TickerMapper:
    """Map company names and entities to stock tickers"""
    
    def __init__(self):
        # Load comprehensive company-ticker mapping
        self.company_map = self._load_company_map()
    
    def _load_company_map(self) -> Dict[str, str]:
        """
        Load company name to ticker mapping
        
        In production, this should load from:
        - CSV with 5000+ companies
        - CUSIP lookup database
        - SEC EDGAR CIK mapping
        """
        # Extended mapping for MVP
        return {
            # Tech
            'apple': 'AAPL', 'amazon': 'AMZN', 'google': 'GOOGL', 
            'microsoft': 'MSFT', 'meta': 'META', 'facebook': 'META',
            'tesla': 'TSLA', 'netflix': 'NFLX', 'nvidia': 'NVDA',
            
            # Aerospace & Defense
            'boeing': 'BA', 'lockheed': 'LMT', 'lockheed martin': 'LMT',
            'raytheon': 'RTX', 'northrop': 'NOC', 'general dynamics': 'GD',
            
            # Auto
            'ford': 'F', 'gm': 'GM', 'general motors': 'GM',
            'tesla': 'TSLA', 'rivian': 'RIVN', 'lucid': 'LCID',
            
            # Retail
            'walmart': 'WMT', 'target': 'TGT', 'amazon': 'AMZN',
            'costco': 'COST', 'home depot': 'HD',
            
            # Pharma
            'pfizer': 'PFE', 'moderna': 'MRNA', 'johnson': 'JNJ',
            'merck': 'MRK', 'abbvie': 'ABBV',
            
            # Energy
            'exxon': 'XOM', 'chevron': 'CVX', 'conocophillips': 'COP',
            'bp': 'BP', 'shell': 'SHEL',
            
            # Finance
            'jpmorgan': 'JPM', 'goldman': 'GS', 'goldman sachs': 'GS',
            'bank of america': 'BAC', 'wells fargo': 'WFC',
            'morgan stanley': 'MS', 'citigroup': 'C',
            
            # Industrial
            'caterpillar': 'CAT', '3m': 'MMM', 'ge': 'GE',
            'honeywell': 'HON', 'united technologies': 'RTX',
            
            # Other
            'nike': 'NKE', 'starbucks': 'SBUX', 'mcdonald': 'MCD',
            'disney': 'DIS', 'comcast': 'CMCSA', 'verizon': 'VZ',
            'att': 'T', 'at&t': 'T'
        }
    
    def map_company_to_ticker(self, company_name: str) -> Optional[str]:
        """
        Map company name to ticker symbol
        
        Args:
            company_name: Company name or variant
        
        Returns:
            Ticker symbol or None if not found
        """
        name_lower = company_name.lower().strip()
        
        # Direct lookup
        if name_lower in self.company_map:
            return self.company_map[name_lower]
        
        # Partial match
        for key, ticker in self.company_map.items():
            if key in name_lower or name_lower in key:
                return ticker
        
        return None
    
    def get_sector_etf(self, sector: str) -> Optional[str]:
        """
        Map sector name to sector ETF ticker
        
        Args:
            sector: Sector name
        
        Returns:
            Sector ETF ticker
        """
        sector_etfs = {
            'technology': 'XLK',
            'financials': 'XLF',
            'healthcare': 'XLV',
            'energy': 'XLE',
            'industrials': 'XLI',
            'materials': 'XLB',
            'consumer discretionary': 'XLY',
            'consumer staples': 'XLP',
            'utilities': 'XLU',
            'real estate': 'XLRE',
            'communication services': 'XLC'
        }
        
        sector_lower = sector.lower()
        return sector_etfs.get(sector_lower)


if __name__ == '__main__':
    # Test market data fetcher
    print("\n🧪 Testing Market Data Module\n")
    
    fetcher = MarketDataFetcher()
    
    # Test historical data
    print("Testing historical data fetch...")
    start = datetime(2024, 1, 1)
    end = datetime(2024, 6, 1)
    data = fetcher.get_historical_data('AAPL', start, end)
    
    if not data.empty:
        print(f"✓ Fetched {len(data)} days of AAPL data")
        print(f"Date range: {data.index.min()} to {data.index.max()}")
        print(f"Columns: {list(data.columns)}")
        
        # Validate
        is_valid, issues = fetcher.validate_data(data)
        print(f"Data valid: {is_valid}")
        if issues:
            print(f"Issues: {issues}")
    
    # Test real-time quote
    print("\nTesting real-time quote...")
    quote = fetcher.get_realtime_quote('TSLA')
    if quote:
        print(f"✓ TSLA: ${quote['price']:.2f} ({quote['change_percent']:.2f}%)")
    
    # Test ticker mapper
    print("\nTesting ticker mapper...")
    mapper = TickerMapper()
    
    companies = ['Apple', 'Boeing', 'General Motors', 'Goldman Sachs']
    for company in companies:
        ticker = mapper.map_company_to_ticker(company)
        print(f"  {company} → {ticker}")
    
    print("\nSector ETF mapping:")
    sectors = ['technology', 'energy', 'healthcare']
    for sector in sectors:
        etf = mapper.get_sector_etf(sector)
        print(f"  {sector} → {etf}")

