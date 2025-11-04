#!/usr/bin/env python3
"""
Simple launcher for Political Sentiment Alpha Platform
Handles setup and runs the server
"""

import os
import sys
import subprocess

def run_command(cmd, description):
    """Run a command and show progress"""
    print(f"\n[*] {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ⚠️  Warning: {result.stderr.strip()}")
    else:
        print(f"    ✓ Done")
    return result.returncode == 0

def main():
    print("=" * 60)
    print("🚀 Political Sentiment Alpha Platform - Quick Launcher")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('app/main.py'):
        print("\n❌ Error: app/main.py not found!")
        print("Please run this from the project root directory.")
        sys.exit(1)
    
    # Check Python version
    print(f"\n✓ Python version: {sys.version.split()[0]}")
    
    # Create .env if it doesn't exist
    if not os.path.exists('.env'):
        print("\n[*] Creating .env file...")
        with open('.env', 'w') as f:
            f.write("""ALPHA_VANTAGE_API_KEY=DEMO_KEY
SECRET_KEY=my-secret-key-12345
DATABASE_URL=sqlite:///political_alpha.db
FLASK_ENV=development
""")
        print("    ✓ Created .env file")
    else:
        print("\n✓ .env file exists")
    
    # Check if Flask is installed
    try:
        import flask
        print(f"✓ Flask version: {flask.__version__}")
    except ImportError:
        print("\n[*] Installing Flask...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask", "flask-cors", "python-dotenv"])
    
    # Initialize database
    print("\n[*] Initializing database...")
    try:
        from models.db import init_db
        init_db()
        print("    ✓ Database initialized")
    except Exception as e:
        print(f"    ⚠️  Database warning: {str(e)}")
    
    # Run the app
    print("\n" + "=" * 60)
    print("🎉 Starting Flask Server...")
    print("=" * 60)
    print("\n📍 Server will be available at: http://localhost:5000")
    print("📍 Health check: http://localhost:5000/health")
    print("\n⛔ Press Ctrl+C to stop the server\n")
    
    try:
        # Import and run the app
        sys.path.insert(0, os.path.dirname(__file__))
        from app import main as app_main
        
        # Run the Flask app
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", "app/main.py")
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
    except KeyboardInterrupt:
        print("\n\n⛔ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTry running manually:")
        print("  python app/main.py")
        sys.exit(1)

if __name__ == '__main__':
    main()

