"""
Input validation service for fetal health prediction
"""
import json
import os
from typing import Dict, Any, Tuple, List

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class InputValidator:
    def __init__(self, prediction_service=None):
        """Initialize validator with feature metadata"""
        self.prediction_service = prediction_service
        self.feature_metadata = self._load_feature_metadata()
        self.required_features = self._get_required_features()
    
    def _get_required_features(self) -> List[str]:
        """Get required features from prediction service or fallback to metadata"""
        if (self.prediction_service and 
            hasattr(self.prediction_service, 'features') and 
            self.prediction_service.features):
            print(f"✅ Using features from prediction service: {len(self.prediction_service.features)} features")
            return self.prediction_service.features
        else:
            print("⚠️  Using features from metadata file")
            return list(self.feature_metadata.keys())
    
    def _load_feature_metadata(self) -> Dict:
        """Load feature metadata from JSON file"""
        # Try corrected metadata first, then fallback to original
        corrected_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'feature_metadata_corrected.json')
        original_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'feature_metadata.json')
        
        try:
            with open(corrected_path, 'r') as f:
                print("✅ Using corrected feature metadata")
                return json.load(f)
        except FileNotFoundError:
            print("⚠️  Corrected metadata not found, using original")
            with open(original_path, 'r') as f:
                return json.load(f)
    
    def _get_default_feature_meta(self, feature_name: str) -> Dict:
        """Get default metadata for features not in metadata file"""
        # Default ranges based on typical fetal health data
        defaults = {
            'type': 'float',
            'min': 0.0,
            'max': 1.0,
            'description': f'Feature: {feature_name}'
        }
        
        # Specific defaults for known patterns
        if 'baseline' in feature_name.lower():
            defaults.update({'min': 106.0, 'max': 160.0, 'description': 'Baseline fetal heart rate'})
        elif 'histogram' in feature_name.lower():
            if 'mean' in feature_name or 'mode' in feature_name or 'median' in feature_name:
                defaults.update({'min': 60.0, 'max': 200.0, 'description': 'Histogram central tendency'})
            elif 'variance' in feature_name:
                defaults.update({'min': 0.0, 'max': 300.0, 'description': 'Histogram variance'})
            elif 'width' in feature_name:
                defaults.update({'min': 3.0, 'max': 200.0, 'description': 'Histogram width'})
            elif 'min' in feature_name:
                defaults.update({'min': 50.0, 'max': 160.0, 'description': 'Histogram minimum'})
            elif 'peaks' in feature_name:
                defaults.update({'min': 0.0, 'max': 20.0, 'description': 'Number of histogram peaks'})
            elif 'tendency' in feature_name:
                defaults.update({'min': -1.0, 'max': 1.0, 'description': 'Histogram tendency'})
        elif 'percentage' in feature_name.lower() or 'abnormal' in feature_name.lower():
            defaults.update({'min': 0.0, 'max': 100.0, 'description': 'Percentage of abnormal time'})
        elif 'variability' in feature_name.lower():
            defaults.update({'min': 0.0, 'max': 100.0, 'description': 'Variability measure'})
        elif 'deceleration' in feature_name.lower():
            defaults.update({'min': 0.0, 'max': 0.01, 'description': 'Deceleration rate'})
        elif 'acceleration' in feature_name.lower():
            defaults.update({'min': 0.0, 'max': 0.02, 'description': 'Acceleration rate'})
        elif 'movement' in feature_name.lower():
            defaults.update({'min': 0.0, 'max': 0.5, 'description': 'Movement rate'})
        elif 'contraction' in feature_name.lower():
            defaults.update({'min': 0.0, 'max': 0.02, 'description': 'Contraction rate'})
            
        return defaults
    
    def validate_input(self, data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate input data against feature metadata
        
        Args:
            data: Input data dictionary
            
        Returns:
            Tuple of (is_valid, errors, cleaned_data)
        """
        errors = []
        cleaned_data = {}
        
        # Check for missing features
        missing_features = set(self.required_features) - set(data.keys())
        if missing_features:
            errors.append(f"Missing required features: {', '.join(missing_features)}")
        
        # Check for extra features (excluding fetal_health which should not be present)
        extra_features = set(data.keys()) - set(self.required_features) - {'fetal_health'}
        if extra_features:
            errors.append(f"Unexpected features: {', '.join(extra_features)}")
        
        # Validate each feature
        for feature_name in self.required_features:
            if feature_name in data:
                value = data[feature_name]
                
                # Get metadata for this feature, or create default if missing
                if feature_name in self.feature_metadata:
                    feature_meta = self.feature_metadata[feature_name]
                else:
                    # Create default metadata for features not in metadata file
                    feature_meta = self._get_default_feature_meta(feature_name)
                    print(f"⚠️  Using default metadata for {feature_name}")
                
                # Type validation and conversion
                try:
                    if feature_meta['type'] == 'float':
                        cleaned_value = float(value)
                    elif feature_meta['type'] == 'int':
                        cleaned_value = int(value)
                    else:
                        cleaned_value = value
                except (ValueError, TypeError):
                    errors.append(f"Invalid type for {feature_name}: expected {feature_meta['type']}")
                    continue
                
                # Range validation
                if 'min' in feature_meta and cleaned_value < feature_meta['min']:
                    errors.append(f"{feature_name} value {cleaned_value} below minimum {feature_meta['min']}")
                
                if 'max' in feature_meta and cleaned_value > feature_meta['max']:
                    errors.append(f"{feature_name} value {cleaned_value} above maximum {feature_meta['max']}")
                
                cleaned_data[feature_name] = cleaned_value
        
        # Check if fetal_health is present (it shouldn't be for input)
        if 'fetal_health' in data:
            errors.append("fetal_health should not be provided as input - it is the prediction target")
        
        is_valid = len(errors) == 0
        return is_valid, errors, cleaned_data
    
    def get_feature_schema(self) -> Dict:
        """Return the feature schema for frontend"""
        # Build schema using required features and metadata (with defaults for missing features)
        schema_features = {}
        
        for feature_name in self.required_features:
            if feature_name in self.feature_metadata:
                schema_features[feature_name] = self.feature_metadata[feature_name]
            else:
                schema_features[feature_name] = self._get_default_feature_meta(feature_name)
        
        schema = {
            'features': schema_features,
            'required': self.required_features
        }
        return schema
