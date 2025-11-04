"""
Configuration management for Political Sentiment Alpha Platform
Loads environment variables and provides centralized config access
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # API Keys
    X_API_BEARER_TOKEN = os.getenv('X_API_BEARER_TOKEN', '')
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    TRUTH_SOCIAL_API_KEY = os.getenv('TRUTH_SOCIAL_API_KEY', '')
    
    # AWS
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'political-alpha-data')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/political_alpha')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Performance Targets
    MAX_LATENCY_SECONDS = 300  # 5 minutes end-to-end
    INGESTION_TIMEOUT_SECONDS = 30
    NLP_TIMEOUT_SECONDS = 2
    EVENT_STUDY_TIMEOUT_SECONDS = 1
    API_TIMEOUT_MS = 500
    
    # Event Study Parameters
    ESTIMATION_WINDOW_DAYS = 252  # 1 year for CAPM
    RISK_FREE_RATE = 0.04  # 4% annual
    MARKET_INDEX = 'SPY'  # S&P 500 ETF as market proxy
    SIGNIFICANCE_LEVEL = 0.05  # p < 0.05
    
    # Data Sources
    TRUMP_TWITTER_ARCHIVE_URL = 'https://www.thetrumparchive.com/faq'
    KAGGLE_DATASET = 'austinreese/trump-tweets'
    
    # Compliance
    PLATFORM_NAME = 'Political Sentiment Alpha Platform'
    DISCLAIMER_TEXT = '''
    IMPORTANT DISCLAIMER: This platform provides general research and informational 
    content only. It does NOT constitute investment advice, personalized recommendations, 
    or an offer to buy/sell securities. We are NOT a registered investment advisor (RIA). 
    Past performance does not guarantee future results. All investing involves risk. 
    Consult with a licensed financial advisor before making investment decisions.
    '''
    
    @classmethod
    def validate(cls):
        """Validate that critical config values are set"""
        warnings = []
        
        if not cls.ALPHA_VANTAGE_API_KEY:
            warnings.append('ALPHA_VANTAGE_API_KEY not set - market data will be limited')
        
        if not cls.X_API_BEARER_TOKEN:
            warnings.append('X_API_BEARER_TOKEN not set - real-time Twitter data unavailable')
        
        if not cls.AWS_ACCESS_KEY_ID:
            warnings.append('AWS credentials not set - S3 storage unavailable')
        
        return warnings


# Create config instance
config = Config()

# Validate on import
warnings = config.validate()
if warnings:
    print("⚠️  Configuration Warnings:")
    for warning in warnings:
        print(f"  - {warning}")

