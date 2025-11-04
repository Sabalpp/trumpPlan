# Political Sentiment Alpha Platform MVP

## Executive Summary

A quantitative trading research tool that identifies short-term alpha opportunities by analyzing political communications (primarily Trump family social media) and their market impact. This platform is designed for **informational purposes only** and does not constitute investment advice.

### Core Hypothesis

**Trump Effect**: Presidential/political communications can generate statistically significant abnormal returns (AR) of approximately 0.25% within a 1-3 day window around key events, based on historical event study analysis.

### MVP Features

1. **Political Data Ingestion**
   - Historical: Trump Twitter Archive (2015-2021), Kaggle datasets
   - Real-time: X API v2, Truth Social (via commercial API)
   - Government feeds: Congress.gov, FEC/OGE disclosures

2. **NLP Sentiment Analysis**
   - Sentiment scoring (positive/negative/neutral)
   - Named Entity Recognition (NER) for company/ticker extraction
   - Tone classification (Aggressive/Cooperative/Neutral)
   - Topic modeling (LDA) for sector mapping

3. **Event Study Methodology**
   - CAPM-based expected return estimation
   - Abnormal Return (AR) and Cumulative AR (CAR) calculation
   - Statistical significance testing (t-test, robust regression)
   - Outlier filtering (MAD-based)

4. **Simple Web Display**
   - Flask-based API
   - Signal display with confidence scores
   - Compliance disclaimers on all pages

5. **Backtesting Interface**
   - Historical signal generation
   - Performance metrics
   - Thinkorswim Paper Money CSV export

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA INGESTION LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Trump Twitter│  │ Truth Social │  │ Government Disclosures │ │
│  │   Archive    │  │  (API/Mock)  │  │   (FEC/OGE/Congress)   │ │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬────────────┘ │
│         │                  │                       │              │
│         └──────────────────┴───────────────────────┘              │
│                            │                                      │
└────────────────────────────┼──────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       NLP PROCESSING LAYER                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Stage 1: Sentiment (Transformer) → Polarity + Tone        │ │
│  │  Stage 2: NER (spaCy) → Company/Ticker Extraction          │ │
│  │  Stage 3: Topic Modeling (LDA) → Sector/ETF Mapping        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    QUANTITATIVE ANALYSIS LAYER                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  • CAPM Expected Return Estimation (252-day window)        │ │
│  │  • Abnormal Return (AR) Calculation                        │ │
│  │  • Cumulative AR (CAR) over event window                   │ │
│  │  • Statistical Significance Testing (t-test, p<0.05)       │ │
│  │  • Outlier Filtering (MAD-based)                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     STORAGE & API LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  PostgreSQL  │  │   Amazon S3  │  │    Flask REST API      │ │
│  │  (Signals DB)│  │(Raw Data Lake)│  │ /signal /backtest etc. │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PRESENTATION LAYER                         │
│  • Web Dashboard (with disclaimers)                             │
│  • Signal Display (Ticker, Direction, Confidence, Explanation)  │
│  • Backtesting UI                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Language**: Python 3.10+
- **Web Framework**: Flask 3.0
- **Database**: PostgreSQL (AWS RDS)
- **Storage**: Amazon S3
- **Compute**: AWS Lambda (serverless)
- **Queue**: Celery + Redis/SQS
- **NLP**: Hugging Face Transformers, spaCy, VADER
- **Quant**: NumPy, Pandas, SciPy, statsmodels
- **Financial Data**: yfinance, Alpha Vantage

## Project Structure

```
political-alpha-mvp/
├── app/                    # Flask application
│   ├── main.py            # Main Flask app
│   └── routes.py          # API endpoints
├── data/                   # Data ingestion modules
│   ├── ingestion.py       # Multi-source data fetchers
│   ├── market.py          # Market data (Alpha Vantage, yfinance)
│   └── aggregator.py      # ETL and normalization
├── nlp/                    # NLP processing
│   ├── pipeline.py        # 3-stage NLP pipeline
│   └── train_nlp.py       # Model fine-tuning
├── quant/                  # Quantitative models
│   └── event_study.py     # Event study methodology
├── models/                 # Database models
│   └── db.py              # SQLAlchemy schemas
├── tasks/                  # Async processing
│   └── celery_app.py      # Celery tasks
├── tests/                  # Test suite
│   ├── test_event_study.py
│   ├── test_nlp.py
│   └── test_ingestion.py
├── templates/              # HTML templates
│   └── disclaimer.html
├── static/                 # Static assets
├── docs/                   # Documentation
│   ├── privacy.md
│   └── roadmap.md
├── config.py              # Configuration management
├── data_prototype.py      # MVP proof-of-concept script
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Setup Instructions

### Prerequisites

1. **Python 3.10+** installed
2. **AWS Account** (free tier eligible)
3. **API Keys** (obtain before running):
   - X API v2 (Bearer Token) - [developer.x.com](https://developer.x.com)
   - Alpha Vantage (free) - [alphavantage.co](https://www.alphavantage.co/support/#api-key)
   - Truth Social API (optional, via ScrapeCreators) - [scrapecreators.com](https://scrapecreators.com)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Sabalpp/trumpPlan.git
cd trumpPlan

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download spaCy model
python -m spacy download en_core_web_sm

# 5. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 6. Run prototype
python data_prototype.py
```

### Environment Variables

Create a `.env` file:

```
# API Keys
X_API_BEARER_TOKEN=your_twitter_bearer_token
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
TRUTH_SOCIAL_API_KEY=your_truth_social_key  # Optional

# AWS
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=political-alpha-data

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/political_alpha

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Flask
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
```

## Quick Start: Running the Prototype

The `data_prototype.py` script demonstrates the core concept:

```bash
python data_prototype.py
```

**Expected Output:**
```json
{
  "ticker": "AAPL",
  "direction": "positive",
  "abnormal_return": 0.0025,
  "confidence": 0.8,
  "event_text": "Apple is doing great things...",
  "timestamp": "2019-01-15T14:30:00Z",
  "explanation": "High positive sentiment (0.85) + direct company mention"
}
```

This validates the hypothesis: ~0.25% AR from political communications.

## Performance Targets

- **Latency**: <5 minutes end-to-end (ingestion → signal generation)
- **Ingestion**: <30 seconds per batch
- **NLP Processing**: <2 seconds per text
- **Event Study Calculation**: <1 second per ticker
- **API Response**: <500ms

## Compliance & Disclaimers

⚠️ **IMPORTANT**: This platform is for **general research and informational purposes only**. It does NOT:
- Provide personalized investment advice
- Recommend specific securities
- Act as a registered investment advisor (RIA)
- Guarantee returns or accuracy

All users must acknowledge disclaimers before accessing signals. See `docs/privacy.md` for full compliance details.

## Development Roadmap

### Phase 1: MVP (Months 1-3)
- ✅ Project setup and prototype
- 🔄 Event study engine
- ⏳ Data ingestion pipeline
- ⏳ Basic NLP sentiment
- ⏳ Flask API + simple UI
- ⏳ Compliance framework

### Phase 2: Validation (Month 4)
- Backtesting on 2015-2021 data
- Performance metrics (Sharpe, win rate)
- Latency optimization
- User testing (50-person alpha)

### Phase 3: Scale (Months 5-6)
- Advanced NLP (fine-tuned models)
- Multi-family tracking (Kushner, Vance)
- Real-time data streams
- Tiered monetization ($29/mo Pro)

### Phase 4: Production (Months 7-12)
- AWS auto-scaling
- Mobile app
- ThinkorSwim/Interactive Brokers integration
- Institutional API ($500/mo)

## Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=. --cov-report=html

# Specific test module
pytest tests/test_event_study.py -v
```

## Contributing

This is a private MVP project. For questions, contact: [your_email@example.com]

## License

Proprietary - All Rights Reserved

## Citations & Research

Based on academic research:
- Event Study Methodology (MacKinlay, 1997)
- Trump Twitter Effect (Brans & Scholtens, 2020)
- Political Sentiment Analysis (Nyman et al., 2021)

Full bibliography available in `docs/references.md`

---

**Version**: 0.1.0 (MVP)  
**Last Updated**: November 3, 2025  
**Status**: ✅ Prototype Phase
