"""
QuantVision Backend Server Entry Point
For PyInstaller packaging
"""
import os
import sys

# Set working directory to the script location
if getattr(sys, 'frozen', False):
    # Running as compiled
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add the current directory to path
sys.path.insert(0, os.getcwd())

def main():
    import uvicorn
    from app.main import app

    # Get port from environment or use default
    port = int(os.environ.get('PORT', 8000))

    print(f"Starting QuantVision Backend on port {port}...")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    main()
