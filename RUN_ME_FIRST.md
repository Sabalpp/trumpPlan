# 🚀 How to Run Your App in VS Code

**3 Easy Ways to Run the Political Sentiment Alpha Platform**

---

## ⚡ FASTEST WAY (Recommended)

### **Option 1: Double-Click the Batch File**

1. Find `run_app.bat` in your project folder
2. **Double-click it**
3. Wait for setup to complete
4. Server starts automatically at http://localhost:5000

**That's it!** ✅

---

## 🎮 VS Code Play Button Method

### **Step 1: One-Time Setup**

**In VS Code Terminal** (press `Ctrl + ~`):
```bash
# Copy and paste this entire block:
cd "C:\Users\sabal\Downloads\Trump Scarper plan"
python -m venv venv
.\venv\Scripts\activate
pip install flask flask-cors python-dotenv sqlalchemy
echo ALPHA_VANTAGE_API_KEY=DEMO_KEY > .env
echo SECRET_KEY=my-secret-key >> .env
echo DATABASE_URL=sqlite:///political_alpha.db >> .env
```

### **Step 2: Click Play Button**

1. Open `app/main.py` (already open!)
2. Look at **top-right corner**
3. Click **green ▶ Play button**

**OR**

- Press **`F5`** (debug mode)
- Press **`Ctrl + F5`** (run without debug)

---

## 💻 Terminal Method

### **Run in VS Code Terminal:**

```bash
# Open terminal: Ctrl + ~
cd "C:\Users\sabal\Downloads\Trump Scarper plan"
.\venv\Scripts\activate
python app/main.py
```

---

## 🌐 After Server Starts

Open browser and visit:

- **http://localhost:5000/health** ← Test if working
- **http://localhost:5000** ← API info
- **http://localhost:5000/waitlist** ← Waitlist page
- **http://localhost:5000/disclaimer** ← Legal info

---

## 🐛 Troubleshooting

### **Error: "Python not recognized"**
Install Python from: https://www.python.org/downloads/
✅ Check "Add Python to PATH" during installation

### **Error: "Flask not found"**
```bash
pip install flask flask-cors python-dotenv
```

### **Error: "Cannot activate venv"**
In PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **Error: "Port 5000 in use"**
```bash
# Find what's using port 5000
netstat -ano | findstr :5000
# Kill it (replace PID with actual number)
taskkill /PID <PID> /F
```

---

## ✅ Success Indicators

**In Terminal:**
```
🚀 Starting Political Sentiment Alpha Platform API
...
 * Running on http://127.0.0.1:5000
```

**In Browser (http://localhost:5000/health):**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## 🎯 Quick Commands Reference

| What | Command |
|------|---------|
| **Install everything** | Double-click `INSTALL.bat` |
| **Run the app** | Double-click `run_app.bat` |
| **Run in VS Code** | Click ▶ Play button |
| **Stop server** | Press `Ctrl + C` |

---

## 📁 Files I Created for You

- ✅ `run_app.bat` - Run everything with one click
- ✅ `INSTALL.bat` - Install all dependencies
- ✅ `run_simple.py` - Python launcher script
- ✅ `.vscode/launch.json` - VS Code debug config

---

## 🆘 Still Not Working?

**Copy and paste this error to me:**
1. What you see in the terminal
2. Any red error messages
3. What step you're stuck on

I'll help you fix it! 🚀

---

**Made with ❤️ for easy running!**

