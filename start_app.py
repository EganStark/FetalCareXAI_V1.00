import os
import sys

# Add the current directory to Python path
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

print("Starting Flask app...")
print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path[:3]}")

# Import and run the Flask app
try:
    from backend.app import app
    print("✅ Flask app imported successfully")
    
    print("="*50)
    print("🚀 FETAL HEALTH PREDICTION API")
    print("="*50)
    print("Starting server on http://127.0.0.1:5000")
    print("Available endpoints:")
    print("  GET  /health    - Health check")
    print("  POST /predict   - Make prediction")
    print("  POST /explain   - Generate explanation")
    print("  GET  /          - Web interface")
    print("="*50)
    
    # Run the app
    app.run(host='127.0.0.1', port=5000, debug=True)
    
except Exception as e:
    print(f"❌ Error starting Flask app: {e}")
    import traceback
    traceback.print_exc()
