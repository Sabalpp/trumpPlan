#!/usr/bin/env python3
"""
Political Sentiment Alpha Platform - Prototype Script
=====================================================

This prototype demonstrates the core hypothesis: Political communications 
(Trump tweets) can generate statistically significant abnormal returns (~0.25%).

Flow:
1. Load sample Trump tweets (simulated Kaggle data)
2. Compute basic sentiment score using VADER
3. Extract company mentions and map to tickers
4. Fetch historical stock data via yfinance
5. Calculate simple abnormal return (AR) using 1-day window
6. Output signal with confidence score

Performance Target: <1 minute execution time
"""

import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings

import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yfinance as yf

# Import the Event Study module
from quant.event_study import quick_event_study

warnings.filterwarnings('ignore')


class PrototypePipeline:
    """MVP prototype demonstrating the Trump sentiment → stock alpha concept"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        # Simple company name → ticker mapping (expand in production)
        self.company_ticker_map = {
            'apple': 'AAPL', 'amazon': 'AMZN', 'google': 'GOOGL', 
            'microsoft': 'MSFT', 'tesla': 'TSLA', 'meta': 'META',
            'boeing': 'BA', 'ford': 'F', 'gm': 'GM', 'general motors': 'GM',
            'walmart': 'WMT', 'target': 'TGT', 'nike': 'NKE',
            'lockheed': 'LMT', 'lockheed martin': 'LMT',
            'caterpillar': 'CAT', 'harley': 'HOG', 'harley davidson': 'HOG',
            'carrier': 'CARR', 'northrop': 'NOC', 'raytheon': 'RTX',
            'pfizer': 'PFE', 'merck': 'MRK', 'johnson': 'JNJ',
            'exxon': 'XOM', 'chevron': 'CVX', 'bp': 'BP',
            'goldman': 'GS', 'goldman sachs': 'GS', 'jpmorgan': 'JPM',
            'bank of america': 'BAC', 'wells fargo': 'WFC',
            'twitter': 'TWTR', 'facebook': 'META',
        }
    
    def load_sample_tweets(self) -> List[Dict]:
        """
        Simulate loading Trump tweets from Kaggle dataset
        In production, this would fetch from Trump Twitter Archive or Kaggle API
        """
        # Sample tweets based on historical Trump communications
        sample_tweets = [
            {
                'text': 'Boeing is building a brand new 747 Air Force One for future presidents, but costs are out of control, more than $4 billion. Cancel order!',
                'timestamp': '2016-12-06 13:52:00',
                'id': '806134244384899072'
            },
            {
                'text': 'Just had a very good call with Apple CEO Tim Cook. Discussed many things including how the U.S. has been treated unfairly on trade with China.',
                'timestamp': '2019-08-20 14:30:00',
                'id': '1163861532819763200'
            },
            {
                'text': 'General Motors is very counter to what we want. We don\'t want General Motors to be building plants outside of this country.',
                'timestamp': '2018-11-27 09:45:00',
                'id': '1067431826154508289'
            },
            {
                'text': 'Amazon should be paying the U.S. Post Office massive amounts of money for using it as their delivery boy. If this doesn\'t change, the post office will lose billions!',
                'timestamp': '2017-12-29 08:30:00',
                'id': '946731072826937344'
            },
            {
                'text': 'Ford, Fiat Chrysler, and General Motors announced plans to invest billions of dollars in the United States. Great news!',
                'timestamp': '2017-01-17 12:00:00',
                'id': '821385815052627968'
            }
        ]
        
        print(f"📥 Loaded {len(sample_tweets)} sample Trump tweets")
        return sample_tweets
    
    def compute_sentiment(self, text: str) -> Dict:
        """
        Compute sentiment using VADER (Valence Aware Dictionary and sEntiment Reasoner)
        Returns: {'neg': 0.0-1.0, 'neu': 0.0-1.0, 'pos': 0.0-1.0, 'compound': -1.0-1.0}
        """
        scores = self.sentiment_analyzer.polarity_scores(text)
        return scores
    
    def extract_companies(self, text: str) -> List[str]:
        """
        Extract company mentions from text using simple keyword matching
        In production, this would use spaCy NER + CUSIP lookup
        """
        text_lower = text.lower()
        found_tickers = []
        
        for company, ticker in self.company_ticker_map.items():
            if company in text_lower:
                found_tickers.append(ticker)
        
        return list(set(found_tickers))  # Remove duplicates
    
    def fetch_market_data(self, ticker: str, event_date: str, window_days: int = 5) -> Optional[pd.DataFrame]:
        """
        Fetch historical stock data around event date
        Args:
            ticker: Stock ticker symbol
            event_date: Date of Trump tweet (YYYY-MM-DD HH:MM:SS)
            window_days: Days before/after event to fetch
        """
        try:
            event_dt = pd.to_datetime(event_date)
            start_date = event_dt - timedelta(days=window_days)
            end_date = event_dt + timedelta(days=window_days)
            
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                print(f"⚠️  No data available for {ticker} around {event_date}")
                return None
            
            return hist
        
        except Exception as e:
            print(f"❌ Error fetching data for {ticker}: {str(e)}")
            return None
    
    def calculate_simple_ar(self, ticker: str, event_date: str, sentiment_score: float) -> Dict:
        """
        Calculate simple Abnormal Return (AR) using 1-day window
        
        Simplified AR = (Actual Return - Expected Return)
        Expected Return ≈ Mean return of prior 5 days
        
        Args:
            ticker: Stock ticker
            event_date: Date of event
            sentiment_score: Compound sentiment score (-1 to +1)
        
        Returns:
            Dict with AR, confidence, and signal details
        """
        hist_data = self.fetch_market_data(ticker, event_date, window_days=10)
        
        if hist_data is None or len(hist_data) < 5:
            return {
                'ticker': ticker,
                'ar': 0.0,
                'confidence': 0.0,
                'error': 'Insufficient data'
            }
        
        # Calculate returns
        hist_data['return'] = hist_data['Close'].pct_change()
        
        # Find event date in data
        event_dt = pd.to_datetime(event_date)
        
        # Get the closest trading day on or after event
        valid_dates = hist_data.index[hist_data.index >= event_dt]
        if len(valid_dates) == 0:
            # Event is after last available data
            event_idx = len(hist_data) - 1
        else:
            event_dt_actual = valid_dates[0]
            event_idx = hist_data.index.get_loc(event_dt_actual)
        
        # Need at least 5 days before event
        if event_idx < 5:
            return {
                'ticker': ticker,
                'ar': 0.0,
                'confidence': 0.0,
                'error': 'Event too early in dataset'
            }
        
        # Expected return = mean of prior 5 days
        prior_returns = hist_data['return'].iloc[event_idx-5:event_idx]
        expected_return = prior_returns.mean()
        
        # Actual return on event day (or next available day)
        if event_idx < len(hist_data):
            actual_return = hist_data['return'].iloc[event_idx]
        else:
            actual_return = 0.0
        
        # Abnormal Return
        ar = actual_return - expected_return
        
        # Confidence based on:
        # 1. Sentiment strength (|compound score|)
        # 2. Consistency of prior returns (lower std = higher confidence)
        sentiment_strength = abs(sentiment_score)
        return_volatility = prior_returns.std()
        
        # Normalize confidence to 0-1
        base_confidence = sentiment_strength * 0.7  # Sentiment contributes 70%
        volatility_penalty = min(return_volatility * 10, 0.3)  # High vol reduces confidence
        confidence = max(0.0, min(1.0, base_confidence - volatility_penalty))
        
        # Outlier filter: Flag if AR is > 3 std devs
        ar_std = prior_returns.std()
        is_outlier = abs(ar) > (3 * ar_std) if ar_std > 0 else False
        
        return {
            'ticker': ticker,
            'ar': round(ar, 6),
            'car': round(ar, 6),  # For 1-day window, CAR = AR
            'expected_return': round(expected_return, 6),
            'actual_return': round(actual_return, 6),
            'confidence': round(confidence, 3),
            'is_outlier': is_outlier,
            'event_date': event_dt.strftime('%Y-%m-%d'),
            'actual_event_date': hist_data.index[event_idx].strftime('%Y-%m-%d')
        }
    
    def generate_signal(self, tweet: Dict, use_advanced: bool = True) -> Dict:
        """
        Generate trading signal from single tweet
        
        Args:
            tweet: Dict with 'text' and 'timestamp'
            use_advanced: If True, use full Event Study module (slower but more accurate)
        
        Returns:
            {
                'ticker': str,
                'direction': 'positive'|'negative'|'neutral',
                'ar': float,
                'confidence': float,
                'event_text': str,
                'timestamp': str,
                'explanation': str
            }
        """
        text = tweet['text']
        timestamp = tweet['timestamp']
        
        # Step 1: Sentiment analysis
        sentiment = self.compute_sentiment(text)
        compound_score = sentiment['compound']
        
        # Step 2: Extract companies/tickers
        tickers = self.extract_companies(text)
        
        if not tickers:
            return {
                'ticker': None,
                'direction': 'neutral',
                'ar': 0.0,
                'confidence': 0.0,
                'event_text': text[:100] + '...',
                'timestamp': timestamp,
                'explanation': 'No company mentions found'
            }
        
        # Step 3: Calculate AR for first ticker (in production, process all)
        ticker = tickers[0]
        
        if use_advanced:
            # Use full Event Study methodology (CAPM, robust stats)
            try:
                event_dt = pd.to_datetime(timestamp)
                event_study_result = quick_event_study(ticker, event_dt, text)
                
                if 'error' not in event_study_result:
                    ar_result = {
                        'ar': event_study_result.get('ar', 0.0),
                        'confidence': event_study_result.get('confidence', 0.0),
                        'actual_event_date': event_study_result.get('event_date', timestamp),
                        'is_outlier': event_study_result.get('is_outlier', False),
                        'beta': event_study_result.get('beta', 1.0),
                        'p_value': event_study_result.get('p_value', 1.0)
                    }
                else:
                    # Fallback to simple method
                    ar_result = self.calculate_simple_ar(ticker, timestamp, compound_score)
            except Exception as e:
                print(f"  ⚠️  Advanced analysis failed: {str(e)}, using simple method")
                ar_result = self.calculate_simple_ar(ticker, timestamp, compound_score)
        else:
            ar_result = self.calculate_simple_ar(ticker, timestamp, compound_score)
        
        # Step 4: Determine direction
        if compound_score > 0.05:
            direction = 'positive'
        elif compound_score < -0.05:
            direction = 'negative'
        else:
            direction = 'neutral'
        
        # Step 5: Build explanation
        explanation = f"Sentiment: {compound_score:.2f} ({direction}), "
        explanation += f"Mentioned: {', '.join(tickers)}, "
        explanation += f"AR: {ar_result.get('ar', 0.0):.4f} ({ar_result.get('ar', 0.0)*100:.2f}%)"
        
        if 'beta' in ar_result:
            explanation += f", Beta: {ar_result['beta']:.2f}"
        if 'p_value' in ar_result:
            explanation += f", p-val: {ar_result['p_value']:.3f}"
        
        return {
            'ticker': ticker,
            'all_tickers': tickers,
            'direction': direction,
            'sentiment_score': round(compound_score, 3),
            'abnormal_return': ar_result.get('ar', 0.0),
            'ar_percentage': round(ar_result.get('ar', 0.0) * 100, 4),
            'confidence': ar_result.get('confidence', 0.0),
            'event_text': text[:150] + ('...' if len(text) > 150 else ''),
            'timestamp': timestamp,
            'actual_event_date': ar_result.get('actual_event_date', timestamp),
            'explanation': explanation,
            'is_significant': abs(ar_result.get('ar', 0.0)) > 0.001,  # >0.1% considered significant
            'is_outlier': ar_result.get('is_outlier', False),
            'beta': ar_result.get('beta'),
            'p_value': ar_result.get('p_value')
        }
    
    def run_prototype(self):
        """Execute full prototype pipeline"""
        print("\n" + "="*70)
        print("🚀 POLITICAL SENTIMENT ALPHA PLATFORM - PROTOTYPE")
        print("="*70 + "\n")
        
        start_time = time.time()
        
        # Load sample data
        tweets = self.load_sample_tweets()
        
        print("\n📊 Processing tweets and generating signals...\n")
        
        signals = []
        for i, tweet in enumerate(tweets, 1):
            print(f"[{i}/{len(tweets)}] Processing tweet from {tweet['timestamp']}...")
            # Use simple method for speed in prototype (set to True for full CAPM analysis)
            signal = self.generate_signal(tweet, use_advanced=False)
            signals.append(signal)
            
            # Print signal summary
            if signal['ticker']:
                print(f"  ✓ {signal['ticker']}: {signal['direction'].upper()} "
                      f"(AR: {signal['ar_percentage']:.2f}%, Confidence: {signal['confidence']:.2f})")
            else:
                print(f"  ⊘ No signal: {signal['explanation']}")
            print()
        
        elapsed = time.time() - start_time
        
        # Summary statistics
        print("\n" + "="*70)
        print("📈 PROTOTYPE RESULTS SUMMARY")
        print("="*70 + "\n")
        
        valid_signals = [s for s in signals if s['ticker'] is not None]
        significant_signals = [s for s in valid_signals if s['is_significant']]
        
        print(f"Total Tweets Processed: {len(tweets)}")
        print(f"Valid Signals Generated: {len(valid_signals)}")
        print(f"Significant Signals (|AR| > 0.1%): {len(significant_signals)}")
        
        if valid_signals:
            avg_ar = np.mean([s['abnormal_return'] for s in valid_signals])
            avg_confidence = np.mean([s['confidence'] for s in valid_signals])
            
            print(f"\nAverage Abnormal Return: {avg_ar:.6f} ({avg_ar*100:.4f}%)")
            print(f"Average Confidence Score: {avg_confidence:.3f}")
            
            print(f"\n⏱️  Execution Time: {elapsed:.2f} seconds")
            print(f"✓ Performance Target: {'PASS' if elapsed < 60 else 'FAIL'} (<60s)")
            
            # Show top signals
            print("\n" + "-"*70)
            print("🎯 TOP 3 SIGNALS (by absolute AR):")
            print("-"*70 + "\n")
            
            sorted_signals = sorted(valid_signals, key=lambda x: abs(x['abnormal_return']), reverse=True)
            for i, signal in enumerate(sorted_signals[:3], 1):
                print(f"{i}. {signal['ticker']} - {signal['direction'].upper()}")
                print(f"   AR: {signal['ar_percentage']:.2f}% | Confidence: {signal['confidence']:.2f}")
                print(f"   Date: {signal['actual_event_date']}")
                print(f"   Text: {signal['event_text']}")
                print()
        
        print("="*70)
        print("✅ Prototype complete! Hypothesis validation:")
        
        if valid_signals:
            avg_ar_pct = np.mean([abs(s['abnormal_return']) for s in valid_signals]) * 100
            print(f"   Expected: ~0.25% AR")
            print(f"   Observed: ~{avg_ar_pct:.2f}% |AR|")
            print(f"   Status: {'✓ VALIDATED' if avg_ar_pct > 0.15 else '✗ NEEDS MORE DATA'}")
        else:
            print("   Status: ⚠️  Insufficient valid signals")
        
        print("="*70 + "\n")
        
        return signals


def main():
    """Entry point for prototype script"""
    pipeline = PrototypePipeline()
    signals = pipeline.run_prototype()
    
    # Export results
    if signals:
        results_df = pd.DataFrame(signals)
        results_df.to_csv('prototype_signals.csv', index=False)
        print("💾 Results saved to: prototype_signals.csv\n")


if __name__ == '__main__':
    main()

