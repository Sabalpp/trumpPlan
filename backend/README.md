# Backend API

Flask-based REST API for the Political Sentiment Alpha Platform.

## Structure

```
backend/
├── app/                    # Flask application
│   ├── main.py            # Main Flask app
│   └── routes.py          # Additional routes
├── data/                   # Data ingestion modules
├── models/                 # Database models
├── nlp/                    # NLP processing pipeline
├── quant/                  # Quantitative analysis
├── tasks/                  # Celery async tasks
├── tests/                  # Test suite
├── config.py              # Configuration
└── requirements.txt       # Python dependencies
```

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
python app/main.py
```

## API Endpoints

- `POST /api/signal` - Generate trading signal
- `GET /api/signals` - List recent signals
- `GET /api/backtest` - View backtest results
- `GET /api/stats` - Platform statistics
- `GET /health` - Health check

## Environment Variables

Create a `.env` file in the backend directory:

```
X_API_BEARER_TOKEN=your_token
ALPHA_VANTAGE_API_KEY=your_key
DATABASE_URL=postgresql://...
SECRET_KEY=your_secret
```

