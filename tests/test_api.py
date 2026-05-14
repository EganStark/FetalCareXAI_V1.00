"""
Test suite for Fetal Health Prediction API
"""
import pytest
import json
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
from services.validate import InputValidator
from services.predict import PredictionService

@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_input():
    """Sample valid input data for testing"""
    return {
        "baseline_value": 120.0,
        "accelerations": 0.0,
        "uterine_contractions": 0.0,
        "light_decelerations": 0.0,
        "mean_value_of_short_term_variability": 0.5,
        "mean_value_of_long_term_variability": 9.4,
        "histogram_width": 64.0,
        "histogram_min": 102.0,
        "histogram_number_of_peaks": 2.0,
        "histogram_mean": 136.0,
        "histogram_variance": 12.4,
        "histogram_tendency": 0.0,
        "prolongued_decelerations_abnormal_short_term_variability": 0.0,
        "prolongued_decelerations_percentage_of_time_with_abnormal_long_term_variability": 43.0
    }

class TestHealthEndpoint:
    """Test the health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check returns OK status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'model_info' in data

class TestSchemaEndpoint:
    """Test the schema endpoint"""
    
    def test_schema_endpoint(self, client):
        """Test schema endpoint returns feature definitions"""
        response = client.get('/schema')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'features' in data
        assert 'labels' in data
        assert 'required' in data
        assert len(data['features']) == 14  # 14 input features

class TestPreviewEndpoint:
    """Test the preview endpoint"""
    
    def test_preview_valid_input(self, client, sample_input):
        """Test preview with valid input"""
        response = client.post('/preview', 
                             data=json.dumps(sample_input),
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'valid'
        assert 'data' in data
        assert data['feature_count'] == 14
    
    def test_preview_missing_fields(self, client):
        """Test preview with missing required fields"""
        incomplete_input = {
            "baseline_value": 120.0,
            "accelerations": 0.0
        }
        
        response = client.post('/preview',
                             data=json.dumps(incomplete_input),
                             content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'errors' in data
    
    def test_preview_invalid_range(self, client, sample_input):
        """Test preview with values outside valid range"""
        invalid_input = sample_input.copy()
        invalid_input['baseline_value'] = 200.0  # Above max range
        
        response = client.post('/preview',
                             data=json.dumps(invalid_input),
                             content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_preview_no_data(self, client):
        """Test preview with no data"""
        response = client.post('/preview',
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data

class TestPredictEndpoint:
    """Test the predict endpoint"""
    
    def test_predict_valid_input(self, client, sample_input):
        """Test prediction with valid input"""
        response = client.post('/predict',
                             data=json.dumps(sample_input),
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'class_id' in data
        assert 'class_label' in data
        assert data['class_id'] in [1, 2, 3]
        assert data['class_label'] in ['Normal', 'Suspect', 'Pathological']
    
    def test_predict_invalid_input(self, client):
        """Test prediction with invalid input"""
        invalid_input = {
            "baseline_value": "invalid_string",
            "accelerations": 0.0
        }
        
        response = client.post('/predict',
                             data=json.dumps(invalid_input),
                             content_type='application/json')
        assert response.status_code == 400

class TestExplainEndpoint:
    """Test the explain endpoint"""
    
    def test_explain_valid_input(self, client, sample_input):
        """Test explanation with valid input"""
        response = client.post('/explain',
                             data=json.dumps(sample_input),
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'class_label' in data
        
        # Check if explanations are present (may be empty if LIME fails)
        if 'explanations' in data:
            assert isinstance(data['explanations'], list)

class TestInputValidator:
    """Test the input validation service"""
    
    def test_validator_initialization(self):
        """Test validator initializes correctly"""
        validator = InputValidator()
        assert validator.feature_metadata is not None
        assert len(validator.required_features) == 14
    
    def test_valid_input_validation(self, sample_input):
        """Test validation of valid input"""
        validator = InputValidator()
        is_valid, errors, cleaned_data = validator.validate_input(sample_input)
        
        assert is_valid is True
        assert len(errors) == 0
        assert len(cleaned_data) == 14
    
    def test_missing_field_validation(self):
        """Test validation with missing fields"""
        validator = InputValidator()
        incomplete_input = {"baseline_value": 120.0}
        
        is_valid, errors, cleaned_data = validator.validate_input(incomplete_input)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing required features" in error for error in errors)
    
    def test_fetal_health_input_rejection(self, sample_input):
        """Test that fetal_health input is rejected"""
        validator = InputValidator()
        invalid_input = sample_input.copy()
        invalid_input['fetal_health'] = 1  # Should not be present
        
        is_valid, errors, cleaned_data = validator.validate_input(invalid_input)
        
        assert is_valid is False
        assert any("fetal_health should not be provided" in error for error in errors)

class TestPredictionService:
    """Test the prediction service"""
    
    def test_prediction_service_initialization(self):
        """Test prediction service initializes"""
        service = PredictionService()
        assert service.model is not None
        assert service.label_map is not None
    
    def test_model_info(self):
        """Test getting model information"""
        service = PredictionService()
        info = service.get_model_info()
        assert 'status' in info
        assert info['status'] in ['loaded', 'not_loaded']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
