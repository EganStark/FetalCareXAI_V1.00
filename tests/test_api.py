"""
Test suite for Fetal Health Prediction API
"""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app import app
from backend.services.validate import InputValidator
from backend.services.predict import PredictionService

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
        "baseline value": 120.0,
        "accelerations": 0.0,
        "fetal_movement": 0.0,
        "uterine_contractions": 0.0,
        "light_decelerations": 0.0,
        "severe_decelerations": 0.0,
        "mean_value_of_short_term_variability": 0.5,
        "mean_value_of_long_term_variability": 9.4,
        "histogram_width": 64.0,
        "histogram_min": 102.0,
        "histogram_number_of_peaks": 2.0,
        "histogram_mode": 120.0,
        "histogram_mean": 136.0,
        "histogram_median": 120.0,
        "histogram_variance": 12.4,
        "histogram_tendency": 0.0,
        "prolongued_decelerations": 0.0,
        "abnormal_short_term_variability": 20.0,
        "percentage_of_time_with_abnormal_long_term_variability": 43.0
    }

class TestHealthEndpoint:
    """Test the health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check returns OK status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'model' in data

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
        assert len(data['features']) == 19

    def test_model_card_is_truthful_and_versioned(self, client):
        response = client.get('/model-card')
        assert response.status_code == 200
        data = response.get_json()
        assert data['model']['features'] == 19
        assert len(data['model']['artifact_hash']) == 12
        assert data['evaluation']['metrics']['accuracy'] > 0
        assert data['evaluation']['metrics']['roc_auc_ovr'] is None
        assert len(data['evaluation']['confusion_matrix']) == 3
        assert data['evaluation']['diagnostic_scope'] == 'held_out_test_set'
        assert data['evaluation']['class_balance']['Normal'] == 1655
        assert data['evaluation']['confusion_matrix'] == [[329, 1, 0], [11, 46, 1], [1, 0, 34]]

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
        assert data['feature_count'] == 19
    
    def test_preview_missing_fields(self, client):
        """Test preview with missing required fields"""
        incomplete_input = {
            "baseline value": 120.0,
            "accelerations": 0.0
        }
        
        response = client.post('/preview',
                             data=json.dumps(incomplete_input),
                             content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'details' in data
    
    def test_preview_invalid_range(self, client, sample_input):
        """Test preview with values outside valid range"""
        invalid_input = sample_input.copy()
        invalid_input['baseline value'] = 200.0  # Above max range
        
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
        assert 0 <= data['confidence'] <= 1
        assert set(data['probabilities']) == {'Normal', 'Suspect', 'Pathological'}
        assert 'input_data' not in data
    
    def test_predict_invalid_input(self, client):
        """Test prediction with invalid input"""
        invalid_input = {
            "baseline value": "invalid_string",
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
        assert len(validator.required_features) == 19
    
    def test_valid_input_validation(self, sample_input):
        """Test validation of valid input"""
        validator = InputValidator()
        is_valid, errors, cleaned_data = validator.validate_input(sample_input)
        
        assert is_valid is True
        assert len(errors) == 0
        assert len(cleaned_data) == 19
    
    def test_missing_field_validation(self):
        """Test validation with missing fields"""
        validator = InputValidator()
        incomplete_input = {"baseline value": 120.0}
        
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
