# Political Sentiment Alpha Platform MVP

A full-stack quantitative trading research tool that identifies short-term alpha opportunities by analyzing political communications (primarily Trump family social media) and their market impact.

## 🏗️ Architecture

This project is structured as a **modern full-stack application**:

- **Backend**: Python Flask REST API (`/backend`)
- **Frontend**: React single-page application (`/frontend`)

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
political-alpha-platform/
├── backend/                # Python Flask API
│   ├── app/               # Flask application
│   │   ├── main.py       # Main Flask app
│   │   └── routes.py     # Additional routes
│   ├── data/             # Data ingestion modules
│   ├── models/           # Database models
│   ├── nlp/              # NLP processing pipeline
│   ├── quant/            # Quantitative analysis
│   ├── tasks/            # Celery async tasks
│   ├── tests/            # Backend tests
│   ├── templates/        # Jinja2 templates
│   ├── static/           # Static files
│   ├── config.py         # Configuration
│   ├── requirements.txt  # Python dependencies
│   └── README.md         # Backend documentation
│
├── frontend/              # React application
│   ├── public/           # Static assets
│   ├── src/
│   │   ├── pages/       # React page components
│   │   │   ├── Dashboard.js
│   │   │   ├── Signals.js
│   │   │   ├── Backtest.js
│   │   │   ├── Waitlist.js
│   │   │   ├── Pricing.js
│   │   │   └── Disclaimer.js
│   │   ├── App.js       # Main app component
│   │   └── index.js     # Entry point
│   ├── package.json     # Node dependencies
│   └── README.md        # Frontend documentation
│
├── docs/                 # Project documentation
│   ├── compliance_checklist.md
│   ├── deployment_guide.md
│   ├── privacy.md
│   └── roadmap.md
│
├── run_backend.bat       # Start backend server
├── run_frontend.bat      # Start frontend server
├── start_all.bat         # Start both servers
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** - Backend API
2. **Node.js 16+** - Frontend application
3. **Git** - Version control

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Sabalpp/trumpPlan.git
cd trumpPlan
```

### Option 1: Run Everything (Recommended for Development)

**Windows:**
```cmd
start_all.bat
```

This will open two terminal windows:
- Backend API: http://localhost:5000
- Frontend React: http://localhost:3000

### Option 2: Run Individually

**Backend Only:**
```cmd
run_backend.bat
```

**Frontend Only:**
```cmd
run_frontend.bat
```

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Mac/Linux
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python app/main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm start
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

## 📱 Using the Platform

### Frontend Interface

Once both servers are running, open your browser to **http://localhost:3000**

**Available Pages:**
- **Dashboard** (`/`) - Real-time signal statistics and recent signals
- **Signals** (`/signals`) - Browse and filter historical trading signals
- **Backtest** (`/backtest`) - View backtesting performance metrics
- **Waitlist** (`/waitlist`) - Join the early access waitlist
- **Pricing** (`/pricing`) - View subscription tiers and features
- **Disclaimer** (`/disclaimer`) - Important legal disclaimer

### Backend API

The backend REST API runs on **http://localhost:5000**

**Key Endpoints:**
- `GET /` - API information
- `POST /api/signal` - Generate signal from text
- `GET /api/signals` - List trading signals
- `GET /api/backtest` - View backtest results
- `GET /api/stats` - Platform statistics
- `GET /health` - Health check

**Example: Generate Signal**
```bash
curl -X POST http://localhost:5000/api/signal \
  -H "Content-Type: application/json" \
  -d '{"text": "Apple is doing great things!", "run_event_study": false}'
```

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

## 🧪 Testing

**Backend Tests:**
```bash
cd backend
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test
pytest tests/test_event_study.py -v
```

**Frontend Tests:**
```bash
cd frontend
npm test
```

## 🚢 Deployment

### Backend (AWS Lambda + API Gateway)
```bash
cd backend
serverless deploy
```

### Frontend (Netlify / Vercel)
```bash
cd frontend
npm run build
# Deploy the 'build' folder to your hosting service
```

See `docs/deployment_guide.md` for detailed instructions.

## 📁 Folder Structure Benefits

**Separation of Concerns:**
- Backend and frontend are completely independent
- Easy to deploy separately (microservices architecture)
- Different teams can work on each part
- Clear API contract between layers

**Development Benefits:**
- Run backend and frontend on different ports
- Hot reload for both during development
- Independent dependency management
- Easier testing and debugging

## Contributing

This is a private MVP project. For questions or contributions, please open an issue on GitHub.

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
