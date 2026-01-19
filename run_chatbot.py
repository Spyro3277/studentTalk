#!/usr/bin/env python3
"""
Student Chatbot Startup Script
"""

import subprocess
import sys
import time
import requests
import os

def check_ollama():
    """Check if Ollama is running and has the required model"""
    try:
        # Check if ollama is running
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Ollama is not running. Please start it with 'ollama serve'")
            return False
        
        # Check if llama3.1:8b is available
        if 'llama3.1:8b' not in result.stdout:
            print("📥 Downloading llama3.1:8b model (this may take a few minutes)...")
            download_result = subprocess.run(['ollama', 'pull', 'llama3.1:8b'])
            if download_result.returncode != 0:
                print("❌ Failed to download model")
                return False
        
        print("✅ Ollama and model are ready")
        return True
    except FileNotFoundError:
        print("❌ Ollama not found. Please install Ollama first.")
        return False

def install_requirements():
    """Install required Python packages"""
    packages = [
        'fastapi',
        'uvicorn[standard]',
        'websockets',
        'sentence-transformers',
        'textblob',
        'vaderSentiment',
        'PyPDF2',
        'faiss-cpu',
        'ollama',
        'python-multipart'
    ]
    
    print("📦 Installing required packages...")
    for package in packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                         check=True, capture_output=True)
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting chatbot server...")
    print("📝 Access the chatbot at: http://localhost:8000")
    print("📊 Wellbeing dashboard at: http://localhost:8000/wellbeing_dashboard")
    print("\n🔄 Press Ctrl+C to stop the server\n")
    
    try:
        import uvicorn
        from main import app
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except ImportError:
        print("❌ Could not import required modules. Please check your installation.")

def main():
    print("🎓 Student Chatbot Setup")
    print("=" * 40)
    
    # Check if we're in the right conda environment
    if 'student-chatbot' not in os.environ.get('CONDA_DEFAULT_ENV', ''):
        print("⚠️  Warning: You might not be in the 'student-chatbot' conda environment")
        print("   Run: conda activate student-chatbot")
        print("")
    
    # Install requirements
    if not install_requirements():
        print("❌ Failed to install requirements")
        return
    
    # Check Ollama
    if not check_ollama():
        print("❌ Ollama setup failed")
        return
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()