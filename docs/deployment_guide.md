# Deployment Guide - Political Sentiment Alpha Platform

**Version**: 0.1.0-MVP  
**Last Updated**: November 3, 2025

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [AWS Deployment](#aws-deployment)
4. [Database Setup](#database-setup)
5. [Environment Variables](#environment-variables)
6. [Monitoring & Logging](#monitoring--logging)
7. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### Required Accounts & Services
- [x] AWS Account (free tier eligible)
- [x] GitHub account (for code repository)
- [x] Domain name (optional, for custom URL)
- [x] Stripe account (for payments, optional for MVP)

### API Keys Needed
- [x] **Alpha Vantage**: [Get free key](https://www.alphavantage.co/support/#api-key)
- [x] **X (Twitter) API**: [Apply here](https://developer.x.com/en/portal/dashboard)
- [ ] **Truth Social API** (optional): [ScrapeCreators](https://scrapecreators.com)

### Local Development Tools
```bash
# Check versions
python --version  # Should be 3.10+
node --version    # For Serverless Framework (optional)
aws --version     # AWS CLI
git --version
```

---

## 2. Local Development Setup

### Step 1: Clone Repository
```bash
git clone https://github.com/Sabalpp/trumpPlan.git
cd trumpPlan
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Step 4: Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
# (Use notepad, vim, or your preferred editor)
```

Example `.env`:
```
X_API_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAABCDEFGHetc...
ALPHA_VANTAGE_API_KEY=DEMO_KEY
DATABASE_URL=sqlite:///political_alpha.db
SECRET_KEY=your-secret-key-here-change-in-production
```

### Step 5: Initialize Database
```bash
python -c "from models.db import init_db; init_db()"
```

### Step 6: Run Prototype
```bash
# Test the prototype
python data_prototype.py

# Expected output: Trading signals generated
```

### Step 7: Start Flask Development Server
```bash
python app/main.py

# Server runs at http://localhost:5000
# Visit http://localhost:5000/health to verify
```

### Step 8: Run Tests (Optional)
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_integration.py -v
```

---

## 3. AWS Deployment

### Option A: Serverless Framework (Recommended)

#### Install Serverless Framework
```bash
npm install -g serverless
npm install --save-dev serverless-python-requirements
```

#### Configure AWS Credentials
```bash
# Configure AWS CLI
aws configure

# Enter:
# AWS Access Key ID: YOUR_KEY
# AWS Secret Access Key: YOUR_SECRET
# Default region: us-east-1
# Default output: json
```

#### Deploy to AWS
```bash
# Deploy to dev environment
serverless deploy --stage dev

# Deploy to production
serverless deploy --stage prod

# Expected output:
# ✓ Service deployed to stack political-alpha-platform-dev
# endpoints:
#   POST - https://abc123.execute-api.us-east-1.amazonaws.com/dev/api/signal
#   GET - https://abc123.execute-api.us-east-1.amazonaws.com/dev/health
```

#### Verify Deployment
```bash
# Test health endpoint
curl https://YOUR_API_URL/health

# Expected: {"status": "healthy", ...}
```

### Option B: AWS Elastic Beanstalk

#### Create Application
```bash
# Install EB CLI
pip install awsebcli

# Initialize Elastic Beanstalk
eb init -p python-3.10 political-alpha-platform --region us-east-1

# Create environment
eb create political-alpha-env

# Deploy
eb deploy
```

#### Check Status
```bash
eb status
eb logs
```

### Option C: Manual EC2 Deployment

```bash
# 1. Launch EC2 instance (t2.micro for free tier)
# 2. SSH into instance
ssh -i your-key.pem ec2-user@your-instance-ip

# 3. Install dependencies
sudo yum update -y
sudo yum install python3 python3-pip git -y

# 4. Clone repo
git clone https://github.com/Sabalpp/trumpPlan.git
cd trumpPlan

# 5. Install requirements
pip3 install -r requirements.txt

# 6. Set up environment
cp .env.example .env
nano .env  # Edit with your keys

# 7. Run with Gunicorn
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app

# 8. Set up systemd service (optional, for auto-restart)
# See systemd service example below
```

---

## 4. Database Setup

### Option A: SQLite (Development Only)
```python
# Already configured in .env
DATABASE_URL=sqlite:///political_alpha.db
```

### Option B: PostgreSQL (Local)
```bash
# Install PostgreSQL
# Windows: Download from postgresql.org
# Mac: brew install postgresql
# Linux: sudo apt-get install postgresql

# Create database
psql -U postgres
CREATE DATABASE political_alpha;
CREATE USER alpha_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE political_alpha TO alpha_user;
\q

# Update .env
DATABASE_URL=postgresql://alpha_user:your_password@localhost:5432/political_alpha
```

### Option C: AWS RDS (Production)

```bash
# 1. Create RDS PostgreSQL instance via AWS Console
# Instance type: db.t3.micro (free tier)
# Storage: 20GB
# Multi-AZ: No (for dev)

# 2. Note connection details:
# Endpoint: your-db.abc123.us-east-1.rds.amazonaws.com
# Port: 5432
# Username: postgres
# Password: (your chosen password)

# 3. Update environment variable
DATABASE_URL=postgresql://postgres:password@your-db.abc123.us-east-1.rds.amazonaws.com:5432/political_alpha

# 4. Initialize schema
python -c "from models.db import init_db; init_db()"
```

---

## 5. Environment Variables

### Required Variables
```bash
# API Keys
X_API_BEARER_TOKEN=your_token_here
ALPHA_VANTAGE_API_KEY=your_key_here

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Flask
SECRET_KEY=generate-random-secret-key
FLASK_ENV=production

# AWS
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=political-alpha-data-prod
```

### Optional Variables
```bash
# Additional Services
TRUTH_SOCIAL_API_KEY=your_key_here
REDIS_URL=redis://localhost:6379/0
STRIPE_SECRET_KEY=sk_test_...

# Configuration
DEBUG=False
LOG_LEVEL=INFO
```

### Setting Environment Variables

#### AWS Lambda
```bash
# Via Serverless Framework (serverless.yml)
provider:
  environment:
    X_API_BEARER_TOKEN: ${env:X_API_BEARER_TOKEN}
    DATABASE_URL: ${env:DATABASE_URL}

# Or via AWS Console → Lambda → Configuration → Environment variables
```

#### Elastic Beanstalk
```bash
eb setenv X_API_BEARER_TOKEN=your_token DATABASE_URL=postgresql://...
```

#### EC2 / Local
```bash
# Add to ~/.bashrc or /etc/environment
export X_API_BEARER_TOKEN=your_token
export DATABASE_URL=postgresql://...

# Or use .env file (loaded by python-dotenv)
```

---

## 6. Monitoring & Logging

### CloudWatch Setup (AWS)

```bash
# Logs are automatically sent to CloudWatch by Lambda

# View logs
aws logs tail /aws/lambda/political-alpha-platform-dev-api --follow

# Create custom metrics
aws cloudwatch put-metric-data \
  --namespace PoliticalAlpha \
  --metric-name SignalsGenerated \
  --value 1
```

### Application Monitoring

#### Add to `app/main.py`:
```python
import logging
from flask import request
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.before_request
def log_request():
    request.start_time = time.time()

@app.after_request
def log_response(response):
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        logger.info(f"{request.method} {request.path} - {response.status_code} - {elapsed:.3f}s")
    return response
```

### Error Tracking

#### Integrate Sentry (Optional)
```bash
pip install sentry-sdk[flask]
```

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your_sentry_dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

---

## 7. Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'X'"
```bash
# Solution: Reinstall requirements
pip install -r requirements.txt
```

#### 2. "Database connection failed"
```bash
# Check DATABASE_URL is set correctly
echo $DATABASE_URL

# Test connection
python -c "from models.db import init_db; init_db()"
```

#### 3. "API key invalid" (Alpha Vantage, Twitter)
```bash
# Verify keys are set
echo $ALPHA_VANTAGE_API_KEY
echo $X_API_BEARER_TOKEN

# Test API directly
curl "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey=$ALPHA_VANTAGE_API_KEY"
```

#### 4. Lambda "Task timed out after 300 seconds"
```bash
# Solution: Increase timeout in serverless.yml
functions:
  api:
    timeout: 900  # 15 minutes
```

#### 5. "Rate limit exceeded" (APIs)
```bash
# Solution: Implement caching or upgrade API tier
# Alpha Vantage: Max 5 requests/min on free tier
# Twitter: Check rate limits in response headers
```

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

API_URL="https://your-api-url.com"

# Check health endpoint
HEALTH=$(curl -s $API_URL/health)
STATUS=$(echo $HEALTH | jq -r '.status')

if [ "$STATUS" = "healthy" ]; then
    echo "✓ API is healthy"
    exit 0
else
    echo "✗ API is unhealthy: $HEALTH"
    exit 1
fi
```

### Debugging Tips

1. **Enable Debug Mode (Development Only)**
   ```python
   app.run(debug=True)
   ```

2. **Check Logs**
   ```bash
   # AWS Lambda
   aws logs tail /aws/lambda/function-name --follow
   
   # Local
   tail -f logs/app.log
   ```

3. **Test Individual Components**
   ```bash
   # Test NLP
   python -c "from nlp.pipeline import NLPPipeline; p = NLPPipeline(); print(p.process_text('Boeing is great!'))"
   
   # Test Event Study
   python quant/event_study.py
   
   # Test Data Ingestion
   python data/ingestion.py
   ```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (`pytest`)
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] API keys valid and tested
- [ ] Disclaimer/privacy policy reviewed

### Production Deployment
- [ ] Set `FLASK_ENV=production`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure production database (RDS)
- [ ] Set up CloudWatch alarms
- [ ] Enable HTTPS (API Gateway auto-enables)
- [ ] Review IAM permissions (least privilege)
- [ ] Set up backups (RDS automated backups)

### Post-Deployment
- [ ] Test health endpoint
- [ ] Generate test signal via API
- [ ] Monitor logs for errors
- [ ] Verify database writes
- [ ] Test waitlist signup
- [ ] Load test (optional: use `locust` or `ab`)

---

## Quick Reference Commands

```bash
# Local development
python app/main.py

# Run tests
pytest

# Deploy to AWS
serverless deploy --stage prod

# View logs
aws logs tail /aws/lambda/political-alpha-platform-prod-api --follow

# Database migration (if using Alembic)
alembic upgrade head

# Check API status
curl https://your-api-url.com/health
```

---

## Support & Resources

- **Documentation**: `docs/` folder
- **API Reference**: `http://localhost:5000/` (local) or your deployed URL
- **Issues**: [GitHub Issues](https://github.com/Sabalpp/trumpPlan/issues)
- **Email**: support@politicalalpha.com (setup your email)

---

**Next Steps After Deployment:**
1. Set up custom domain (Route 53 + CloudFront)
2. Configure CI/CD (GitHub Actions)
3. Add monitoring dashboards (Grafana/CloudWatch)
4. Schedule regular backups
5. Review security (AWS Security Hub)

---

© 2025 Political Sentiment Alpha Platform | Deployment Guide v1.0

