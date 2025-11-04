"""
Event Study Methodology for Abnormal Return Calculation
======================================================

Implements the event study framework to measure stock price reactions to 
political events (Trump communications). Based on MacKinlay (1997) methodology.

Key Components:
1. Expected Return Estimation (CAPM with market model)
2. Abnormal Return (AR) Calculation: AR = Actual - Expected
3. Cumulative Abnormal Return (CAR) over event window
4. Statistical Significance Testing (t-test, robust regression)
5. Outlier Detection and Filtering

Formula:
    AR_it = R_it - E(R_it | X_t)
    Where:
        R_it = actual return of stock i at time t
        E(R_it | X_t) = expected return given information set X_t
        
    Using CAPM:
        E(R_it) = rf + β_i(R_mt - rf)
        β_i = Cov(R_i, R_m) / Var(R_m)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResults
import yfinance as yf

from config import config

warnings.filterwarnings('ignore')


class EventStudy:
    """
    Event Study analysis for measuring abnormal returns around political events
    
    Args:
        event_timestamp: UTC timestamp of the political event
        ticker: Stock ticker symbol to analyze
        estimation_window_days: Number of days for historical estimation (default: 252 = 1 year)
        event_window_days: Days before/after event to analyze (default: 3)
        market_ticker: Market index ticker for CAPM (default: SPY)
    """
    
    def __init__(
        self,
        event_timestamp: datetime,
        ticker: str,
        estimation_window_days: int = 252,
        event_window_days: int = 3,
        market_ticker: str = 'SPY'
    ):
        self.event_timestamp = event_timestamp
        self.ticker = ticker
        self.estimation_window_days = estimation_window_days
        self.event_window_days = event_window_days
        self.market_ticker = market_ticker
        self.rf_rate = config.RISK_FREE_RATE
        
        # Data storage
        self.stock_data: Optional[pd.DataFrame] = None
        self.market_data: Optional[pd.DataFrame] = None
        self.beta: Optional[float] = None
        self.alpha: Optional[float] = None
        
        # Results
        self.ar: Optional[float] = None
        self.car: Optional[float] = None
        self.ar_series: Optional[pd.Series] = None
        self.p_value: Optional[float] = None
        self.t_statistic: Optional[float] = None
        
    def fetch_data(self) -> bool:
        """
        Fetch historical stock and market data for analysis
        
        Returns:
            True if data successfully fetched, False otherwise
        """
        try:
            # Calculate date ranges
            event_date = self.event_timestamp.date()
            estimation_start = event_date - timedelta(days=self.estimation_window_days + 20)  # Buffer for weekends
            event_window_end = event_date + timedelta(days=self.event_window_days + 5)
            
            # Fetch stock data
            stock = yf.Ticker(self.ticker)
            self.stock_data = stock.history(start=estimation_start, end=event_window_end)
            
            if self.stock_data.empty:
                print(f"⚠️  No stock data available for {self.ticker}")
                return False
            
            # Fetch market data
            market = yf.Ticker(self.market_ticker)
            self.market_data = market.history(start=estimation_start, end=event_window_end)
            
            if self.market_data.empty:
                print(f"⚠️  No market data available for {self.market_ticker}")
                return False
            
            # Calculate returns
            self.stock_data['return'] = self.stock_data['Close'].pct_change()
            self.market_data['return'] = self.market_data['Close'].pct_change()
            
            # Align dates (only trading days present in both)
            common_dates = self.stock_data.index.intersection(self.market_data.index)
            self.stock_data = self.stock_data.loc[common_dates]
            self.market_data = self.market_data.loc[common_dates]
            
            # Remove NaN
            self.stock_data = self.stock_data.dropna(subset=['return'])
            self.market_data = self.market_data.dropna(subset=['return'])
            
            return len(self.stock_data) >= 50  # Need minimum data points
            
        except Exception as e:
            print(f"❌ Error fetching data: {str(e)}")
            return False
    
    def estimate_expected_return(self) -> Tuple[float, float]:
        """
        Estimate expected return using CAPM (market model)
        
        E(R_i) = α + β * R_m
        
        Where:
            α = alpha (stock-specific return)
            β = beta (systematic risk, sensitivity to market)
            R_m = market return
        
        Returns:
            Tuple of (alpha, beta)
        """
        if self.stock_data is None or self.market_data is None:
            raise ValueError("Data not fetched. Call fetch_data() first.")
        
        # Get estimation window (exclude event window)
        event_date = self.event_timestamp.date()
        estimation_end = event_date - timedelta(days=self.event_window_days)
        
        # Filter estimation window
        estimation_stock = self.stock_data[self.stock_data.index.date < estimation_end]
        estimation_market = self.market_data[self.market_data.index.date < estimation_end]
        
        # Take last N days
        if len(estimation_stock) > self.estimation_window_days:
            estimation_stock = estimation_stock.iloc[-self.estimation_window_days:]
            estimation_market = estimation_market.iloc[-self.estimation_window_days:]
        
        # Align
        common_dates = estimation_stock.index.intersection(estimation_market.index)
        stock_returns = estimation_stock.loc[common_dates, 'return']
        market_returns = estimation_market.loc[common_dates, 'return']
        
        # OLS Regression: R_i = α + β * R_m + ε
        X = sm.add_constant(market_returns.values)  # Add intercept
        y = stock_returns.values
        
        model = sm.OLS(y, X, missing='drop')
        results: RegressionResults = model.fit()
        
        self.alpha = results.params[0]
        self.beta = results.params[1]
        
        return self.alpha, self.beta
    
    def calculate_ar(self) -> pd.Series:
        """
        Calculate Abnormal Returns (AR) for event window
        
        AR_t = R_t - E(R_t)
        Where E(R_t) = α + β * R_m,t
        
        Returns:
            Series of abnormal returns indexed by date
        """
        if self.alpha is None or self.beta is None:
            self.estimate_expected_return()
        
        # Get event window
        event_date = self.event_timestamp.date()
        window_start = event_date - timedelta(days=self.event_window_days)
        window_end = event_date + timedelta(days=self.event_window_days)
        
        # Filter event window
        event_stock = self.stock_data[
            (self.stock_data.index.date >= window_start) & 
            (self.stock_data.index.date <= window_end)
        ]
        event_market = self.market_data[
            (self.market_data.index.date >= window_start) & 
            (self.market_data.index.date <= window_end)
        ]
        
        # Align
        common_dates = event_stock.index.intersection(event_market.index)
        
        if len(common_dates) == 0:
            print("⚠️  No trading days in event window")
            return pd.Series(dtype=float)
        
        stock_returns = event_stock.loc[common_dates, 'return']
        market_returns = event_market.loc[common_dates, 'return']
        
        # Calculate expected returns
        expected_returns = self.alpha + self.beta * market_returns
        
        # Calculate abnormal returns
        abnormal_returns = stock_returns - expected_returns
        
        self.ar_series = abnormal_returns
        
        # Store AR for event day (or closest)
        event_day_ar = None
        for date in abnormal_returns.index:
            if date.date() >= event_date:
                event_day_ar = abnormal_returns.loc[date]
                break
        
        self.ar = event_day_ar if event_day_ar is not None else abnormal_returns.mean()
        
        return abnormal_returns
    
    def calculate_car(self, window: Optional[Tuple[int, int]] = None) -> float:
        """
        Calculate Cumulative Abnormal Return (CAR)
        
        CAR = Σ AR_t over event window
        
        Args:
            window: Tuple of (days_before, days_after) relative to event.
                    If None, uses full event window.
        
        Returns:
            Cumulative abnormal return
        """
        if self.ar_series is None:
            self.calculate_ar()
        
        if window is not None:
            # Filter to specific window
            event_date = self.event_timestamp.date()
            window_start = event_date - timedelta(days=window[0])
            window_end = event_date + timedelta(days=window[1])
            
            filtered_ar = self.ar_series[
                (self.ar_series.index.date >= window_start) & 
                (self.ar_series.index.date <= window_end)
            ]
            car = filtered_ar.sum()
        else:
            car = self.ar_series.sum()
        
        self.car = car
        return car
    
    def statistical_test(self, use_robust: bool = True) -> Dict[str, float]:
        """
        Perform statistical significance test on abnormal returns
        
        H0: AR = 0 (no abnormal return)
        H1: AR ≠ 0 (significant abnormal return)
        
        Args:
            use_robust: If True, use robust regression (Huber-White) for outliers
        
        Returns:
            Dict with test statistics, p-value, and significance flag
        """
        if self.ar_series is None or len(self.ar_series) == 0:
            return {
                't_statistic': 0.0,
                'p_value': 1.0,
                'is_significant': False,
                'confidence': 0.0
            }
        
        # T-test: H0: mean(AR) = 0
        ar_values = self.ar_series.values
        
        if use_robust:
            # Robust t-test using median and MAD
            median_ar = np.median(ar_values)
            mad = np.median(np.abs(ar_values - median_ar))
            
            if mad > 0:
                robust_std = 1.4826 * mad  # MAD to std conversion
                t_stat = median_ar / (robust_std / np.sqrt(len(ar_values)))
            else:
                t_stat = 0.0
        else:
            # Standard t-test
            t_stat, p_val = stats.ttest_1samp(ar_values, 0)
            self.t_statistic = t_stat
            self.p_value = p_val
            
            is_significant = p_val < config.SIGNIFICANCE_LEVEL
            confidence = 1 - p_val if p_val < 1 else 0.0
            
            return {
                't_statistic': float(t_stat),
                'p_value': float(p_val),
                'is_significant': bool(is_significant),
                'confidence': float(min(confidence, 0.99))
            }
        
        # For robust, calculate p-value from t-distribution
        df = len(ar_values) - 1
        p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df))
        
        self.t_statistic = t_stat
        self.p_value = p_val
        
        is_significant = p_val < config.SIGNIFICANCE_LEVEL
        confidence = 1 - p_val if p_val < 1 else 0.0
        
        return {
            't_statistic': float(t_stat),
            'p_value': float(p_val),
            'is_significant': bool(is_significant),
            'confidence': float(min(confidence, 0.99)),
            'method': 'robust' if use_robust else 'standard'
        }
    
    def filter_outliers(self, threshold: float = 3.0) -> bool:
        """
        Detect if event is an outlier using MAD (Median Absolute Deviation)
        
        Outlier if: |AR - median(AR)| > threshold * MAD
        
        Args:
            threshold: Number of MADs for outlier detection (default: 3.0)
        
        Returns:
            True if event is an outlier, False otherwise
        """
        if self.ar_series is None or len(self.ar_series) < 3:
            return False
        
        ar_values = self.ar_series.values
        median_ar = np.median(ar_values)
        mad = np.median(np.abs(ar_values - median_ar))
        
        if mad == 0:
            return False
        
        # Check if event day AR is an outlier
        if self.ar is None:
            return False
        
        deviation = abs(self.ar - median_ar)
        is_outlier = deviation > (threshold * mad)
        
        return is_outlier
    
    def run_full_analysis(self) -> Dict:
        """
        Execute complete event study analysis pipeline
        
        Returns:
            Dict with all results: AR, CAR, statistical tests, confidence, etc.
        """
        # Step 1: Fetch data
        if not self.fetch_data():
            return {
                'ticker': self.ticker,
                'event_timestamp': self.event_timestamp.isoformat(),
                'error': 'Failed to fetch data',
                'ar': 0.0,
                'car': 0.0,
                'confidence': 0.0,
                'is_significant': False
            }
        
        try:
            # Step 2: Estimate expected returns (CAPM)
            alpha, beta = self.estimate_expected_return()
            
            # Step 3: Calculate AR
            ar_series = self.calculate_ar()
            
            if len(ar_series) == 0:
                return {
                    'ticker': self.ticker,
                    'event_timestamp': self.event_timestamp.isoformat(),
                    'error': 'No data in event window',
                    'ar': 0.0,
                    'car': 0.0,
                    'confidence': 0.0,
                    'is_significant': False
                }
            
            # Step 4: Calculate CAR
            car = self.calculate_car()
            
            # Step 5: Statistical test
            test_results = self.statistical_test(use_robust=True)
            
            # Step 6: Outlier detection
            is_outlier = self.filter_outliers()
            
            # Build result
            result = {
                'ticker': self.ticker,
                'event_timestamp': self.event_timestamp.isoformat(),
                'event_date': self.event_timestamp.date().isoformat(),
                
                # CAPM Parameters
                'alpha': round(alpha, 6),
                'beta': round(beta, 4),
                
                # Abnormal Returns
                'ar': round(self.ar, 6),
                'ar_percentage': round(self.ar * 100, 4),
                'car': round(car, 6),
                'car_percentage': round(car * 100, 4),
                
                # Statistical Tests
                't_statistic': test_results['t_statistic'],
                'p_value': test_results['p_value'],
                'is_significant': test_results['is_significant'],
                'confidence': round(test_results['confidence'], 3),
                
                # Quality Metrics
                'is_outlier': is_outlier,
                'num_observations': len(ar_series),
                'estimation_window_days': self.estimation_window_days,
                
                # Signal Direction
                'direction': 'positive' if self.ar > 0 else 'negative' if self.ar < 0 else 'neutral',
                
                # Summary
                'summary': self._generate_summary()
            }
            
            return result
            
        except Exception as e:
            return {
                'ticker': self.ticker,
                'event_timestamp': self.event_timestamp.isoformat(),
                'error': f'Analysis failed: {str(e)}',
                'ar': 0.0,
                'car': 0.0,
                'confidence': 0.0,
                'is_significant': False
            }
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary of results"""
        if self.ar is None:
            return "Insufficient data for analysis"
        
        direction = "positive" if self.ar > 0 else "negative"
        magnitude = abs(self.ar * 100)
        
        summary = f"{direction.capitalize()} abnormal return of {magnitude:.2f}%. "
        
        if self.p_value is not None and self.p_value < config.SIGNIFICANCE_LEVEL:
            summary += f"Statistically significant (p={self.p_value:.4f}). "
        else:
            summary += "Not statistically significant. "
        
        if self.filter_outliers():
            summary += "⚠️ Flagged as potential outlier."
        
        return summary


def quick_event_study(ticker: str, event_timestamp: datetime, event_text: str = "") -> Dict:
    """
    Convenience function for quick event study analysis
    
    Args:
        ticker: Stock ticker symbol
        event_timestamp: Datetime of event
        event_text: Optional text description of event
    
    Returns:
        Dict with analysis results
    """
    study = EventStudy(event_timestamp, ticker)
    results = study.run_full_analysis()
    
    if event_text:
        results['event_text'] = event_text[:200]
    
    return results


if __name__ == '__main__':
    # Example usage
    print("\n🧪 Testing Event Study Module\n")
    
    # Test case: Hypothetical Trump tweet about Boeing
    test_event = datetime(2016, 12, 6, 13, 52, 0)
    test_ticker = 'BA'
    test_text = 'Boeing is building a brand new 747 Air Force One for future presidents, but costs are out of control, more than $4 billion. Cancel order!'
    
    print(f"Event: {test_text[:80]}...")
    print(f"Date: {test_event.date()}")
    print(f"Ticker: {test_ticker}\n")
    
    results = quick_event_study(test_ticker, test_event, test_text)
    
    print("Results:")
    print(f"  AR: {results.get('ar_percentage', 0):.2f}%")
    print(f"  CAR: {results.get('car_percentage', 0):.2f}%")
    print(f"  p-value: {results.get('p_value', 1):.4f}")
    print(f"  Significant: {results.get('is_significant', False)}")
    print(f"  Confidence: {results.get('confidence', 0):.2f}")
    print(f"  Beta: {results.get('beta', 0):.3f}")
    print(f"\nSummary: {results.get('summary', 'N/A')}\n")

