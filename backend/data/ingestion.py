"""
Political Data Ingestion Module
==============================

Multi-source data ingestion for political communications:
1. Historical: Trump Twitter Archive, Kaggle datasets
2. Real-time: X API v2, Truth Social API
3. Government: Congress.gov, FEC/OGE disclosures
4. Family: Trump family members' social media

Handles API failures, rate limits, and data normalization.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings

import requests
import pandas as pd
from bs4 import BeautifulSoup

from config import config

warnings.filterwarnings('ignore')


class TrumpDataIngestion:
    """Ingest Trump's political communications from multiple sources"""
    
    def __init__(self):
        self.x_bearer_token = config.X_API_BEARER_TOKEN
        self.truth_social_key = config.TRUTH_SOCIAL_API_KEY
        
    def historical_trump_tweets(
        self, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch historical Trump tweets from Trump Twitter Archive
        
        Args:
            start_date: Start date (YYYY-MM-DD), default: 2015-01-01
            end_date: End date (YYYY-MM-DD), default: 2021-01-08 (last tweet)
            limit: Maximum number of tweets to fetch
        
        Returns:
            DataFrame with columns: id, text, timestamp, retweets, likes, source
        """
        print("📥 Fetching historical Trump tweets...")
        
        # For MVP, use Kaggle dataset or pre-downloaded data
        # In production, integrate with Trump Twitter Archive API
        
        # Simulated data for prototype
        # In production, replace with:
        # - Kaggle API: kaggle datasets download -d austinreese/trump-tweets
        # - Trump Archive: https://www.thetrumparchive.com/
        
        sample_tweets = [
            {
                'id': '806134244384899072',
                'text': 'Boeing is building a brand new 747 Air Force One for future presidents, but costs are out of control, more than $4 billion. Cancel order!',
                'timestamp': '2016-12-06 13:52:00',
                'retweets': 35000,
                'likes': 98000,
                'source': 'Trump Twitter Archive'
            },
            {
                'id': '1163861532819763200',
                'text': 'Just had a very good call with Apple CEO Tim Cook. Discussed many things including how the U.S. has been treated unfairly on trade with China.',
                'timestamp': '2019-08-20 14:30:00',
                'retweets': 28000,
                'likes': 125000,
                'source': 'Trump Twitter Archive'
            },
            {
                'id': '1067431826154508289',
                'text': 'General Motors is very counter to what we want. We don\'t want General Motors to be building plants outside of this country.',
                'timestamp': '2018-11-27 09:45:00',
                'retweets': 15000,
                'likes': 67000,
                'source': 'Trump Twitter Archive'
            },
            {
                'id': '946731072826937344',
                'text': 'Amazon should be paying the U.S. Post Office massive amounts of money for using it as their delivery boy. If this doesn\'t change, the post office will lose billions!',
                'timestamp': '2017-12-29 08:30:00',
                'retweets': 42000,
                'likes': 156000,
                'source': 'Trump Twitter Archive'
            },
            {
                'id': '821385815052627968',
                'text': 'Ford, Fiat Chrysler, and General Motors announced plans to invest billions of dollars in the United States. Great news!',
                'timestamp': '2017-01-17 12:00:00',
                'retweets': 31000,
                'likes': 122000,
                'source': 'Trump Twitter Archive'
            },
        ]
        
        df = pd.DataFrame(sample_tweets)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter by date if provided
        if start_date:
            df = df[df['timestamp'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['timestamp'] <= pd.to_datetime(end_date)]
        
        df = df.head(limit)
        
        print(f"✓ Fetched {len(df)} historical tweets")
        return df
    
    def realtime_x_posts(
        self,
        user_ids: List[str] = None,
        since_minutes: int = 60
    ) -> pd.DataFrame:
        """
        Fetch real-time posts from X (Twitter) API v2
        
        Args:
            user_ids: List of user IDs to monitor (default: Trump family)
            since_minutes: Fetch posts from last N minutes
        
        Returns:
            DataFrame with recent posts
        """
        if not self.x_bearer_token:
            print("⚠️  X API bearer token not configured")
            return pd.DataFrame()
        
        if user_ids is None:
            # Trump family user IDs (example - update with real IDs)
            user_ids = [
                '25073877',  # @realDonaldTrump (suspended, for historical reference)
                '19546277',  # @DonaldJTrumpJr
                '22203756',  # @EricTrump
                '30584246',  # @IvankaTrump
            ]
        
        try:
            headers = {'Authorization': f'Bearer {self.x_bearer_token}'}
            all_tweets = []
            
            for user_id in user_ids:
                url = f'https://api.twitter.com/2/users/{user_id}/tweets'
                params = {
                    'max_results': 10,
                    'tweet.fields': 'created_at,public_metrics,entities',
                    'start_time': (datetime.utcnow() - timedelta(minutes=since_minutes)).isoformat() + 'Z'
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        all_tweets.extend(data['data'])
                elif response.status_code == 429:
                    print(f"⚠️  Rate limit reached for user {user_id}")
                    time.sleep(60)
                else:
                    print(f"⚠️  API error {response.status_code} for user {user_id}")
            
            if not all_tweets:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_tweets)
            df.rename(columns={'created_at': 'timestamp'}, inplace=True)
            df['source'] = 'X API v2'
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            print(f"✓ Fetched {len(df)} real-time X posts")
            return df
            
        except Exception as e:
            print(f"❌ Error fetching X posts: {str(e)}")
            return pd.DataFrame()
    
    def realtime_truth_social(self, since_minutes: int = 60) -> pd.DataFrame:
        """
        Fetch Trump posts from Truth Social
        
        Note: Truth Social doesn't have a public API. Options:
        1. Commercial API (e.g., ScrapeCreators)
        2. Web scraping (legal gray area)
        3. Mock data for MVP
        
        Args:
            since_minutes: Fetch posts from last N minutes
        
        Returns:
            DataFrame with Truth Social posts
        """
        if not self.truth_social_key:
            print("⚠️  Truth Social API key not configured - using mock data")
            
            # Mock data for MVP
            mock_posts = [
                {
                    'id': 'ts_001',
                    'text': 'The economy is stronger than ever! Jobs are coming back to America.',
                    'timestamp': datetime.utcnow() - timedelta(minutes=30),
                    'likes': 15000,
                    'reposts': 3000,
                    'source': 'Truth Social (Mock)'
                }
            ]
            
            df = pd.DataFrame(mock_posts)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        
        try:
            # Integration with commercial Truth Social API
            url = 'https://api.scrapecreators.com/truth-social/posts'
            headers = {'Authorization': f'Bearer {self.truth_social_key}'}
            params = {
                'username': 'realDonaldTrump',
                'limit': 10,
                'since': (datetime.utcnow() - timedelta(minutes=since_minutes)).isoformat()
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data.get('posts', []))
                df['source'] = 'Truth Social'
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                print(f"✓ Fetched {len(df)} Truth Social posts")
                return df
            else:
                print(f"⚠️  Truth Social API error: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error fetching Truth Social: {str(e)}")
            return pd.DataFrame()


class GovernmentDataIngestion:
    """Ingest government data: Congress.gov, FEC, OGE disclosures"""
    
    def __init__(self):
        self.congress_api_key = 'DEMO_KEY'  # Replace with real key from api.data.gov
        self.fec_api_key = 'DEMO_KEY'
    
    def congress_bills(
        self,
        congress_number: int = 118,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Fetch recent congressional bills from Congress.gov API
        
        Args:
            congress_number: Congress session (118 = 2023-2024)
            limit: Max number of bills
        
        Returns:
            DataFrame with bill data
        """
        try:
            url = f'https://api.congress.gov/v3/bill/{congress_number}'
            params = {
                'api_key': self.congress_api_key,
                'limit': limit,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                bills = data.get('bills', [])
                
                df = pd.DataFrame(bills)
                df['source'] = 'Congress.gov'
                
                print(f"✓ Fetched {len(df)} congressional bills")
                return df
            else:
                print(f"⚠️  Congress API error: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error fetching Congress data: {str(e)}")
            return pd.DataFrame()
    
    def fec_disclosures(
        self,
        candidate_name: str = 'Trump',
        years: List[int] = None
    ) -> pd.DataFrame:
        """
        Fetch FEC financial disclosures
        
        Args:
            candidate_name: Candidate to search
            years: Years to search (default: current + last year)
        
        Returns:
            DataFrame with disclosure data
        """
        if years is None:
            current_year = datetime.now().year
            years = [current_year, current_year - 1]
        
        try:
            url = 'https://api.open.fec.gov/v1/candidates/search/'
            params = {
                'api_key': self.fec_api_key,
                'q': candidate_name,
                'page': 1,
                'per_page': 20
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                df = pd.DataFrame(results)
                df['source'] = 'FEC'
                
                print(f"✓ Fetched {len(df)} FEC records")
                return df
            else:
                print(f"⚠️  FEC API error: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error fetching FEC data: {str(e)}")
            return pd.DataFrame()
    
    def oge_disclosures(
        self,
        official_name: str = 'Trump'
    ) -> pd.DataFrame:
        """
        Fetch OGE (Office of Government Ethics) financial disclosures
        
        Note: OGE data typically requires web scraping or manual download
        
        Args:
            official_name: Name of official
        
        Returns:
            DataFrame with disclosure data
        """
        print("⚠️  OGE integration not yet implemented (requires web scraping)")
        
        # Mock data for MVP
        mock_disclosures = [
            {
                'name': 'Donald J. Trump',
                'year': 2020,
                'position': 'President',
                'entities': ['Trump Organization', 'Mar-a-Lago', 'Trump National Golf Club'],
                'source': 'OGE (Mock)'
            }
        ]
        
        df = pd.DataFrame(mock_disclosures)
        return df


class FamilyDataIngestion:
    """Ingest Trump family communications"""
    
    def __init__(self):
        self.x_bearer_token = config.X_API_BEARER_TOKEN
    
    def family_posts(
        self,
        family_handles: List[str] = None,
        since_hours: int = 24
    ) -> pd.DataFrame:
        """
        Fetch posts from Trump family members
        
        Args:
            family_handles: X handles to monitor
            since_hours: Hours of history to fetch
        
        Returns:
            DataFrame with family posts
        """
        if family_handles is None:
            family_handles = [
                'DonaldJTrumpJr',
                'EricTrump',
                'IvankaTrump',
                'LaraLeaTrump',
                'TiffanyATrump'
            ]
        
        print(f"📥 Fetching posts from {len(family_handles)} family members...")
        
        # Mock data for MVP (replace with real X API calls)
        mock_posts = [
            {
                'id': 'dtj_001',
                'author': 'DonaldJTrumpJr',
                'text': 'Energy independence is critical for America. We need to support domestic oil and gas.',
                'timestamp': datetime.utcnow() - timedelta(hours=2),
                'source': 'X - Family'
            },
            {
                'id': 'et_001',
                'author': 'EricTrump',
                'text': 'The Trump Organization is expanding. New projects in development.',
                'timestamp': datetime.utcnow() - timedelta(hours=5),
                'source': 'X - Family'
            }
        ]
        
        df = pd.DataFrame(mock_posts)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        print(f"✓ Fetched {len(df)} family posts")
        return df


def aggregate_all_sources(
    include_historical: bool = True,
    include_realtime: bool = True,
    include_government: bool = False,
    include_family: bool = False
) -> pd.DataFrame:
    """
    Aggregate data from all sources into unified DataFrame
    
    Args:
        include_historical: Include historical Trump tweets
        include_realtime: Include real-time X/Truth Social
        include_government: Include Congress/FEC/OGE
        include_family: Include family posts
    
    Returns:
        Unified DataFrame with all political data
    """
    print("\n📊 Aggregating data from all sources...\n")
    
    all_data = []
    
    # Trump data
    trump_ingest = TrumpDataIngestion()
    
    if include_historical:
        historical = trump_ingest.historical_trump_tweets()
        if not historical.empty:
            all_data.append(historical)
    
    if include_realtime:
        x_posts = trump_ingest.realtime_x_posts()
        if not x_posts.empty:
            all_data.append(x_posts)
        
        truth_posts = trump_ingest.realtime_truth_social()
        if not truth_posts.empty:
            all_data.append(truth_posts)
    
    # Government data
    if include_government:
        gov_ingest = GovernmentDataIngestion()
        
        bills = gov_ingest.congress_bills()
        if not bills.empty:
            all_data.append(bills)
        
        fec = gov_ingest.fec_disclosures()
        if not fec.empty:
            all_data.append(fec)
    
    # Family data
    if include_family:
        family_ingest = FamilyDataIngestion()
        family_posts = family_ingest.family_posts()
        if not family_posts.empty:
            all_data.append(family_posts)
    
    if not all_data:
        print("⚠️  No data fetched from any source")
        return pd.DataFrame()
    
    # Combine all dataframes
    combined = pd.concat(all_data, ignore_index=True, sort=False)
    
    # Normalize columns
    if 'timestamp' in combined.columns:
        combined['timestamp'] = pd.to_datetime(combined['timestamp'])
        combined = combined.sort_values('timestamp', ascending=False)
    
    print(f"\n✓ Aggregated {len(combined)} total records from {len(all_data)} sources\n")
    
    return combined


if __name__ == '__main__':
    # Test data ingestion
    print("\n🧪 Testing Data Ingestion Module\n")
    
    # Test historical tweets
    trump_data = TrumpDataIngestion()
    historical = trump_data.historical_trump_tweets(limit=5)
    print(f"\nHistorical tweets sample:\n{historical[['timestamp', 'text']].head()}\n")
    
    # Test aggregation
    all_data = aggregate_all_sources(
        include_historical=True,
        include_realtime=False,
        include_government=False,
        include_family=False
    )
    
    print(f"Total records: {len(all_data)}")
    print(f"Date range: {all_data['timestamp'].min()} to {all_data['timestamp'].max()}")

