# 🚀 Quick Start Guide - Local Setup

**Get the Political Sentiment Alpha Platform running on your computer in 10 minutes!**

---

## ✅ Step-by-Step Setup (Windows)

### **Step 1: Open Command Prompt**
Press `Win + R`, type `cmd`, press Enter

### **Step 2: Navigate to Project Folder**
```bash
cd "C:\Users\sabal\Downloads\Trump Scarper plan"
```

### **Step 3: Create Virtual Environment**
```bash
python -m venv venv
venv\Scripts\activate
```
You should see `(venv)` appear in your command prompt.

### **Step 4: Install Requirements**
```bash
pip install -r requirements.txt
```
⏳ This will take 2-3 minutes. Wait for it to complete.

### **Step 5: Download NLP Model**
```bash
python -m spacy download en_core_web_sm
```

### **Step 6: Create Environment File**
```bash
copy .env.example .env
notepad .env
```

**In Notepad, paste this and save:**
```
# Minimal setup to get started
ALPHA_VANTAGE_API_KEY=DEMO_KEY
SECRET_KEY=change-this-to-something-random-later
DATABASE_URL=sqlite:///political_alpha.db
FLASK_ENV=development

# Optional - add if you have them
X_API_BEARER_TOKEN=
TRUTH_SOCIAL_API_KEY=
```

Save and close Notepad.

### **Step 7: Initialize Database**
```bash
python -c "from models.db import init_db; init_db()"
```
Should print: `✓ Database initialized: local`

### **Step 8: Test the Prototype**
```bash
python data_prototype.py
```

**Expected output:**
```
🚀 POLITICAL SENTIMENT ALPHA PLATFORM - PROTOTYPE
================================================================
📥 Loaded 5 sample Trump tweets
📊 Processing tweets and generating signals...
✓ BA: NEGATIVE (AR: -1.23%, Confidence: 0.75)
✓ AAPL: POSITIVE (AR: 0.45%, Confidence: 0.82)
...
✅ Prototype complete!
```

### **Step 9: Start the Web Server**
```bash
python app/main.py
```

**You should see:**
```
🚀 Starting Political Sentiment Alpha Platform API

Available endpoints:
  GET  /              - API info
  GET  /health        - Health check
  POST /api/signal    - Generate signal
  ...

 * Running on http://127.0.0.1:5000
```

### **Step 10: Test in Browser**
Open your browser and go to:
- **http://localhost:5000** - API info
- **http://localhost:5000/health** - Health check

You should see JSON responses!

---

## 🎉 Success! Your Platform is Running!

### **What You Can Do Now:**

#### **1. Test Signal Generation (via API)**
Open a new Command Prompt window and run:
```bash
curl -X POST http://localhost:5000/api/signal ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"Boeing is doing great work on the new aircraft!\"}"
```

Or use Postman/Thunder Client in VS Code.

#### **2. View Recent Signals**
Browser: http://localhost:5000/api/signals

#### **3. Check Platform Stats**
Browser: http://localhost:5000/api/stats

#### **4. Join Waitlist Page**
Browser: http://localhost:5000/waitlist

---

## 🔑 Get Real API Keys (Optional)

### **Alpha Vantage (Free - 2 minutes)**
1. Go to: https://www.alphavantage.co/support/#api-key
2. Enter your email
3. Copy the API key
4. Replace `DEMO_KEY` in your `.env` file

### **X (Twitter) API (Free/Paid - 1-2 days approval)**
1. Go to: https://developer.x.com/en/portal/dashboard
2. Sign up for developer account
3. Create a new app
4. Copy Bearer Token
5. Add to `.env` file

---

## 🧪 Run Tests

```bash
# Run all tests
pytest

# Run with details
pytest -v

# Run specific test
pytest tests/test_event_study.py -v
```

---

## 🛑 Stop the Server

Press `Ctrl + C` in the Command Prompt where the server is running.

---

## 📝 Common Commands

```bash
# Activate virtual environment (every time you open new terminal)
venv\Scripts\activate

# Run prototype
python data_prototype.py

# Start server
python app/main.py

# Run tests
pytest

# Deactivate virtual environment
deactivate
```

---

## ❌ Troubleshooting

### **Error: "python is not recognized"**
Install Python 3.10+ from: https://www.python.org/downloads/
Make sure to check "Add Python to PATH" during installation.

### **Error: "No module named 'flask'"**
Make sure virtual environment is activated:
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### **Error: "Database connection failed"**
Check that `.env` file exists and contains:
```
DATABASE_URL=sqlite:///political_alpha.db
```

### **Error: "spaCy model not found"**
Install the language model:
```bash
python -m spacy download en_core_web_sm
```

### **Port 5000 already in use**
Stop other applications using port 5000, or change port in `app/main.py`:
```python
app.run(host='0.0.0.0', port=5001)  # Changed to 5001
```

---

## 📚 Next Steps

1. ✅ Platform running locally
2. ⏳ Get Alpha Vantage API key (free)
3. ⏳ Apply for X (Twitter) API (1-2 days)
4. ⏳ Test signal generation with real data
5. ⏳ Deploy to AWS (see `docs/deployment_guide.md`)

---

## 🆘 Need Help?

- **Full Documentation**: See `docs/deployment_guide.md`
- **API Reference**: http://localhost:5000 (when running)
- **Issues**: Check `docs/troubleshooting.md`

---

## 🎯 Quick Reference

| What | Command |
|------|---------|
| Activate venv | `venv\Scripts\activate` |
| Run prototype | `python data_prototype.py` |
| Start server | `python app/main.py` |
| Run tests | `pytest` |
| Check health | http://localhost:5000/health |
| View signals | http://localhost:5000/api/signals |

---

**Made by**: Sabalpp  
**Platform**: Political Sentiment Alpha Platform  
**Version**: 0.1.0-MVP

🎉 **You're all set! Start generating trading signals from political sentiment!** 🚀

