"""
Flask application for Fetal Health Prediction
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from .services.validate import InputValidator, ValidationError
from .services.predict import PredictionService
from .services.explain import ExplanationService

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize services
prediction_service = PredictionService()
validator = InputValidator(prediction_service)
explanation_service = ExplanationService(prediction_service)

# Load label mapping
def load_label_map():
    """Load label mapping from JSON file"""
    label_path = os.path.join(os.path.dirname(__file__), 'model', 'label_map.json')
    with open(label_path, 'r') as f:
        return json.load(f)

label_map = load_label_map()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Fetal Health Prediction API is running",
        "model_info": prediction_service.get_model_info()
    })

@app.route('/schema', methods=['GET'])
def get_schema():
    """Get API schema with feature definitions and label mapping"""
    schema = validator.get_feature_schema()
    schema['labels'] = label_map
    schema['target'] = 'fetal_health'
    return jsonify(schema)

@app.route('/preview', methods=['POST'])
def preview_input():
    """Preview and validate input data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No input data provided"
            }), 400
        
        # Validate input
        is_valid, errors, cleaned_data = validator.validate_input(data)
        
        if not is_valid:
            return jsonify({
                "error": "Validation failed",
                "errors": errors
            }), 400
        
        return jsonify({
            "status": "valid",
            "message": "Input validation successful",
            "data": cleaned_data,
            "feature_count": len(cleaned_data)
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/predict', methods=['POST'])
def predict():
    """Make prediction on input data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No input data provided"
            }), 400
        
        # Validate input
        is_valid, errors, cleaned_data = validator.validate_input(data)
        
        if not is_valid:
            return jsonify({
                "error": "Validation failed",
                "errors": errors
            }), 400
        
        # Make prediction
        class_id, class_label = prediction_service.predict(cleaned_data)
        
        return jsonify({
            "status": "success",
            "class_id": class_id,
            "class_label": class_label,
            "input_data": cleaned_data
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Prediction error: {str(e)}"
        }), 500

@app.route('/explain', methods=['POST'])
def explain_prediction():
    """Generate LIME explanation for prediction"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No input data provided"
            }), 400
        
        # Validate input
        is_valid, errors, cleaned_data = validator.validate_input(data)
        
        if not is_valid:
            return jsonify({
                "error": "Validation failed", 
                "errors": errors
            }), 400
        
        # Generate explanation
        explanation = explanation_service.explain_prediction(cleaned_data)
        
        return jsonify({
            "status": "success",
            **explanation
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Explanation error: {str(e)}"
        }), 500

# Serve static files (frontend)
@app.route('/')
def serve_frontend():
    """Serve the main frontend page"""
    return send_from_directory('static', 'index.html')

@app.route('/graphs/<filename>')
def serve_graph(filename):
    """Serve generated explanation graphs"""
    return send_from_directory('static/graphs', filename)

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "GET /health",
            "GET /schema", 
            "POST /preview",
            "POST /predict",
            "POST /explain"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal server error",
        "message": "Please check server logs for details"
    }), 500

if __name__ == '__main__':
    print("="*50)
    print("Fetal Health Prediction API")
    print("="*50)
    print("Starting Flask application...")
    print(f"Model status: {prediction_service.get_model_info()}")
    print("Available endpoints:")
    print("  GET  /health    - Health check")
    print("  GET  /schema    - API schema")
    print("  POST /preview   - Validate input")
    print("  POST /predict   - Make prediction")
    print("  POST /explain   - Generate explanation")
    print("  GET  /          - Frontend application")
    print("="*50)
    
    # Run the application
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
