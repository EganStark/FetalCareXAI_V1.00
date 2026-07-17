"""
Prediction service for fetal health classification
"""
import joblib
import json
import os
import numpy as np
from typing import Dict, Any, Tuple

class PredictionService:
    def __init__(self):
        """Initialize prediction service"""
        self.model = None
        self.scaler = None
        self.features = None
        self.label_map = None
        self.label_mapping = None
        self._load_model()
        self._load_scaler()
        self._load_features()
        self._load_label_map()
        self._load_label_mapping()
    
    def _load_model(self):
        """Load the trained model from pickle file"""
        model_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'model.pkl')
        try:
            self.model = joblib.load(model_path)
            print(f"✅ Model loaded successfully from {model_path}")
            print(f"Model type: {type(self.model)}")
        except FileNotFoundError:
            print(f"❌ Error: Model file not found at {model_path}")
            raise
    
    def _load_scaler(self):
        """Load the trained scaler from pickle file"""
        scaler_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'scaler.pkl')
        try:
            self.scaler = joblib.load(scaler_path)
            print(f"✅ Scaler loaded successfully: {type(self.scaler)}")
        except FileNotFoundError:
            print(f"❌ Error: Scaler file not found at {scaler_path}")
            raise
    
    def _load_features(self):
        """Load the feature order from pickle file"""
        features_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'features.pkl')
        try:
            self.features = joblib.load(features_path)
            print(f"✅ Features loaded successfully: {len(self.features)} features")
            print(f"Feature order: {self.features}")
        except FileNotFoundError:
            print(f"❌ Error: Features file not found at {features_path}")
            raise
    
    def _load_label_mapping(self):
        """Load label mapping from pickle file"""
        label_mapping_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'label_mapping.pkl')
        try:
            self.label_mapping = joblib.load(label_mapping_path)
            print(f"✅ Label mapping loaded successfully: {self.label_mapping}")
        except FileNotFoundError:
            print(f"⚠️  Warning: Label mapping pickle not found, using JSON mapping")
    
    def _load_label_map(self):
        """Load label mapping from JSON file"""
        label_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'label_map.json')
        try:
            with open(label_path, 'r') as f:
                self.label_map = json.load(f)
            print(f"✅ Label map loaded successfully: {self.label_map}")
        except FileNotFoundError:
            print(f"❌ Error: Label map file not found at {label_path}")
            raise
    
    def _prepare_features(self, data: Dict[str, float]) -> np.ndarray:
        """
        Prepare features in the correct order and scale them for prediction
        
        Args:
            data: Dictionary of feature values
            
        Returns:
            Numpy array with features in correct order and scaled
        """
        if self.features is None:
            raise RuntimeError("Feature order not loaded")
        if self.scaler is None:
            raise RuntimeError("Scaler not loaded")
        
        print(f"🔄 Preparing features for prediction...")
        print(f"Input data keys: {list(data.keys())}")
        print(f"Expected feature order: {self.features}")
        
        # Map input data to features, handling different naming conventions
        feature_mapping = {
            # Map frontend names to model feature names
            'baseline_value': 'baseline value',
            'accelerations': 'accelerations',
            'fetal_movement': 'fetal_movement', 
            'uterine_contractions': 'uterine_contractions',
            'light_decelerations': 'light_decelerations',
            'severe_decelerations': 'severe_decelerations',
            'mean_value_of_short_term_variability': 'mean_value_of_short_term_variability',
            'mean_value_of_long_term_variability': 'mean_value_of_long_term_variability',
            'histogram_width': 'histogram_width',
            'histogram_min': 'histogram_min',
            'histogram_number_of_peaks': 'histogram_number_of_peaks',
            'histogram_number_of_zeroes': 'histogram_number_of_zeroes',
            'histogram_mode': 'histogram_mode',
            'histogram_mean': 'histogram_mean',
            'histogram_median': 'histogram_median',
            'histogram_variance': 'histogram_variance',
            'histogram_tendency': 'histogram_tendency',
            'prolongued_decelerations_abnormal_short_term_variability': 'prolongued_decelerations_abnormal_short_term_variability',
            'prolongued_decelerations_percentage_of_time_with_abnormal_long_term_variability': 'prolongued_decelerations_percentage_of_time_with_abnormal_long_term_variability'
        }
        
        # Create reverse mapping as well
        reverse_mapping = {v: k for k, v in feature_mapping.items()}
        
        # Prepare features in the exact order expected by the model
        features = []
        missing_features = []
        
        for expected_feature in self.features:
            # Try to find the feature in various ways
            value = None
            
            # Direct match
            if expected_feature in data:
                value = data[expected_feature]
            # Try mapped name
            elif expected_feature in reverse_mapping and reverse_mapping[expected_feature] in data:
                value = data[reverse_mapping[expected_feature]]
            # Try feature mapping
            elif expected_feature in feature_mapping and feature_mapping[expected_feature] in data:
                value = data[feature_mapping[expected_feature]]
            # Try lowercase/normalized versions
            else:
                for key in data.keys():
                    if key.lower().replace('_', ' ') == expected_feature.lower().replace('_', ' '):
                        value = data[key]
                        break
            
            if value is not None:
                features.append(float(value))
                print(f"✅ {expected_feature}: {value}")
            else:
                features.append(0.0)  # Default value
                missing_features.append(expected_feature)
                print(f"❌ {expected_feature}: MISSING (using 0.0)")
        
        if missing_features:
            print(f"⚠️  WARNING: Missing features: {missing_features}")
        
        # Convert to numpy array and reshape for single prediction
        features_array = np.array(features).reshape(1, -1)
        print(f"📊 Raw features shape: {features_array.shape}")
        print(f"📊 Raw features sample: {features_array[0][:5]}")
        
        # Apply scaling using the trained scaler
        scaled_features = self.scaler.transform(features_array)
        print(f"📊 Scaled features shape: {scaled_features.shape}")
        print(f"📊 Scaled features sample: {scaled_features[0][:5]}")
        
        return scaled_features
    
    def predict_details(self, data: Dict[str, float]) -> Dict[str, Any]:
        """Return the predicted class together with calibrated model probabilities."""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        features = self._prepare_features(data)
        probabilities = self.model.predict_proba(features)[0]
        predicted_class_idx = int(np.argmax(probabilities))

        mapping = {0: (1, 'Normal'), 1: (2, 'Suspect'), 2: (3, 'Pathological')}
        class_id, class_label = mapping[predicted_class_idx]

        # The serialized mapping is authoritative when it has the expected shape.
        if self.label_mapping and predicted_class_idx in self.label_mapping:
            mapped = self.label_mapping[predicted_class_idx]
            class_id = int(mapped.get('class_id', class_id))
            class_label = mapped.get('class_name', class_label)

        labels = ['Normal', 'Suspect', 'Pathological']
        probability_map = {
            label: round(float(probability), 6)
            for label, probability in zip(labels, probabilities)
        }
        return {
            'class_id': class_id,
            'class_label': class_label,
            'confidence': round(float(probabilities[predicted_class_idx]), 6),
            'probabilities': probability_map,
        }

    def predict(self, data: Dict[str, float]) -> Tuple[int, str]:
        """
        Make prediction on input data
        
        Args:
            data: Dictionary of feature values
            
        Returns:
            Tuple of (class_id, class_label)
        """
        details = self.predict_details(data)
        return details['class_id'], details['class_label']
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        if self.model is None:
            return {"status": "not_loaded"}
        
        model_type = type(self.model).__name__
        if hasattr(self.model, 'named_steps'):
            # Pipeline model
            steps = list(self.model.named_steps.keys())
            return {
                "status": "loaded",
                "type": "Pipeline",
                "steps": steps,
                "final_estimator": type(self.model.named_steps[steps[-1]]).__name__
            }
        else:
            return {
                "status": "loaded", 
                "type": model_type
            }
