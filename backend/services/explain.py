"""
LIME explanation service for fetal health predictions with graph generation
"""
import json
import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import lime
import lime.lime_tabular
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import uuid

class ExplanationService:
    def __init__(self, prediction_service):
        """
        Initialize explanation service
        
        Args:
            prediction_service: Instance of PredictionService
        """
        self.prediction_service = prediction_service
        self.graph_session_id = str(uuid.uuid4())[:8]
        self.feature_names = self._get_feature_names()
        self.background_data = self._load_background_data()
        self.explainer = self._create_explainer()
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names from the prediction service"""
        if hasattr(self.prediction_service, 'features') and self.prediction_service.features:
            print(f"✅ Using feature names from prediction service: {len(self.prediction_service.features)} features")
            return self.prediction_service.features
        else:
            print("⚠️  Using fallback feature names")
            return [
                'baseline_value',
                'accelerations', 
                'fetal_movement',
                'uterine_contractions',
                'light_decelerations',
                'severe_decelerations',
                'mean_value_of_short_term_variability',
                'mean_value_of_long_term_variability',
                'histogram_width',
                'histogram_min',
                'histogram_number_of_peaks',
                'histogram_number_of_zeroes',
                'histogram_mode',
                'histogram_mean',
                'histogram_median',
                'histogram_variance',
                'histogram_tendency',
                'prolongued_decelerations_abnormal_short_term_variability',
                'prolongued_decelerations_percentage_of_time_with_abnormal_long_term_variability'
            ]
    
    def _load_background_data(self) -> np.ndarray:
        """Load background data for LIME"""
        background_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'background_sample.csv')
        try:
            df = pd.read_csv(background_path)
            # Check if all required features are present
            missing_features = set(self.feature_names) - set(df.columns)
            if missing_features:
                print(f"Warning: Background CSV missing features: {missing_features}")
                print("Using synthetic background data instead")
                return self._create_synthetic_background()
            
            # Ensure columns are in correct order
            df = df[self.feature_names]
            return df.values
        except FileNotFoundError:
            print(f"Warning: Background data not found at {background_path}")
            print("Using synthetic background data")
            return self._create_synthetic_background()
    
    def _create_synthetic_background(self) -> np.ndarray:
        """Create synthetic background data using reasonable ranges for fetal health features"""
        np.random.seed(42)
        n_samples = 1000  # Increase samples for better LIME performance
        background = []
        
        # Create more realistic synthetic data for each feature based on actual fetal health ranges
        feature_ranges = {
            'baseline value': (106, 160),
            'accelerations': (0, 0.02),
            'fetal_movement': (0, 0.5),
            'uterine_contractions': (0, 0.02),
            'light_decelerations': (0, 0.02),
            'severe_decelerations': (0, 0.005),
            'mean_value_of_short_term_variability': (0.2, 7.0),
            'mean_value_of_long_term_variability': (1, 100),
            'histogram_width': (3, 180),
            'histogram_min': (50, 170),
            'histogram_number_of_peaks': (0, 18),
            'histogram_number_of_zeroes': (0, 10),
            'histogram_mode': (60, 180),
            'histogram_mean': (70, 180),
            'histogram_median': (70, 180),
            'histogram_variance': (0, 300),
            'histogram_tendency': (-1, 1),
            'prolongued_decelerations': (0, 0.01),
            'abnormal_short_term_variability': (0, 100),
            'percentage_of_time_with_abnormal_long_term_variability': (0, 100)
        }
        
        print(f"🔧 Creating synthetic background with {n_samples} samples for {len(self.feature_names)} features")
        
        for feature_name in self.feature_names:
            # Get range or use default
            min_val, max_val = feature_ranges.get(feature_name, (0, 1))
            
            # Generate values with more realistic distributions
            if 'percentage' in feature_name.lower() or 'abnormal' in feature_name.lower():
                # Use beta distribution for percentages (skewed towards lower values)
                values = np.random.beta(2, 5, n_samples) * 100
                values = np.clip(values, min_val, max_val)
            elif 'histogram' in feature_name.lower() and ('mean' in feature_name or 'mode' in feature_name or 'median' in feature_name):
                # Normal distribution for heart rate values
                mean_val = (min_val + max_val) / 2
                std_val = (max_val - min_val) / 6
                values = np.random.normal(mean_val, std_val, n_samples)
                values = np.clip(values, min_val, max_val)
            elif 'deceleration' in feature_name.lower() or 'acceleration' in feature_name.lower():
                # Exponential distribution for rare events
                scale = (max_val - min_val) / 4
                values = np.random.exponential(scale, n_samples) + min_val
                values = np.clip(values, min_val, max_val)
            elif 'tendency' in feature_name.lower():
                # Normal distribution centered at 0 for tendency
                values = np.random.normal(0, 0.3, n_samples)
                values = np.clip(values, min_val, max_val)
            else:
                # Uniform distribution as fallback
                values = np.random.uniform(min_val, max_val, n_samples)
            
            background.append(values)
            print(f"  📊 {feature_name}: [{min_val:.3f}, {max_val:.3f}] → range=[{np.min(values):.3f}, {np.max(values):.3f}]")
        
        result = np.array(background).T
        print(f"✅ Synthetic background shape: {result.shape}")
        return result
    
    def _create_explainer(self):
        """Create LIME tabular explainer"""
        try:
            # Use class names that match the model's output order (0,1,2 -> Normal,Suspect,Pathological)
            explainer = lime.lime_tabular.LimeTabularExplainer(
                self.background_data,
                feature_names=self.feature_names,
                class_names=['Normal (1)', 'Suspect (2)', 'Pathological (3)'],  # 0-indexed to match model output
                mode='classification',
                discretize_continuous=False
            )
            return explainer
        except Exception as e:
            print(f"Warning: Could not create LIME explainer: {e}")
            return None
    
    def _predict_fn(self, X: np.ndarray) -> np.ndarray:
        """
        Prediction function for LIME that uses the same preprocessing as the main prediction
        
        Args:
            X: Array of feature vectors (already in correct order, unscaled)
            
        Returns:
            Array of class probabilities
        """
        if self.prediction_service.model is None:
            # Return dummy probabilities for development
            n_samples = X.shape[0]
            return np.random.dirichlet([1, 1, 1], n_samples)
        
        try:
            print(f"🔍 LIME prediction function called with {X.shape[0]} samples")
            print(f"🔍 Sample input shape: {X.shape}")
            print(f"🔍 Sample input range: [{np.min(X):.3f}, {np.max(X):.3f}]")
            
            # Apply the same scaling that the prediction service uses
            if hasattr(self.prediction_service, 'scaler') and self.prediction_service.scaler is not None:
                X_scaled = self.prediction_service.scaler.transform(X)
                print(f"Applied scaling in LIME prediction function")
                print(f"🔍 Scaled range: [{np.min(X_scaled):.3f}, {np.max(X_scaled):.3f}]")
            else:
                X_scaled = X
                print(f"No scaler available in prediction service")
            
            # Get probabilities directly from the model
            if hasattr(self.prediction_service.model, 'predict_proba'):
                probabilities = self.prediction_service.model.predict_proba(X_scaled)
                print(f"LIME prediction function: got probabilities shape {probabilities.shape}")
                print(f"🔍 Sample probabilities: {probabilities[:3] if len(probabilities) > 2 else probabilities}")
                
                # Validate probabilities
                if np.any(np.isnan(probabilities)) or np.any(np.isinf(probabilities)):
                    print("⚠️  Warning: NaN or Inf values in probabilities")
                    # Replace with uniform distribution
                    probabilities = np.full(probabilities.shape, 1/3)
                
            else:
                # If only predictions available, convert to one-hot
                predictions = self.prediction_service.model.predict(X_scaled)
                n_samples = len(predictions)
                n_classes = 3
                probabilities = np.zeros((n_samples, n_classes))
                for i, pred in enumerate(predictions):
                    # Handle both 0-based and 1-based class labels
                    if pred in [0, 1, 2]:
                        class_idx = int(pred)  # 0-based for probabilities
                    elif pred in [1, 2, 3]:
                        class_idx = int(pred) - 1  # Convert 1-based to 0-based
                    else:
                        class_idx = 0  # Default fallback
                    
                    if 0 <= class_idx < n_classes:
                        probabilities[i, class_idx] = 1.0
                    else:
                        # Fallback for unknown classes
                        probabilities[i] = [1/n_classes] * n_classes
                print(f"LIME prediction function: converted predictions to probabilities")
            
            return probabilities
            
        except Exception as e:
            print(f"Error in LIME prediction function: {e}")
            # Return dummy probabilities as fallback
            n_samples = X.shape[0]
            return np.random.dirichlet([1, 1, 1], n_samples)

    def _generate_explanation_graph(self, explanations: List[Dict], class_label: str, instance_id: str) -> str:
        """
        Generate a matplotlib graph for LIME explanations matching the LIME library style
        
        Args:
            explanations: List of feature explanations
            class_label: Predicted class label
            instance_id: Unique identifier for this prediction
            
        Returns:
            Filename of the generated graph
        """
        try:
            # Set up matplotlib with clean style
            plt.style.use('default')
            
            # Create figure and axis with appropriate size
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Extract features and weights (top 10 most important)
            top_explanations = explanations[:10]
            features = []
            weights = []
            
            # Format feature names to show actual values and ensure non-zero weights
            for exp in top_explanations:
                # Use feature name and value for display
                display_name = f"{exp['feature']}"
                features.append(display_name)
                weight = exp['weight']
                weights.append(weight)
                print(f"  📊 Graph: {display_name} = {weight:.4f}")
            
            # Skip graph if all weights are zero
            if all(abs(w) < 0.0001 for w in weights):
                print("⚠️  All LIME weights are near zero - skipping graph generation")
                return None
            
            # Create colors: green for positive, red for negative (matching LIME)
            colors = ['#2ca02c' if w > 0 else '#d62728' for w in weights]
            
            # Create horizontal bar chart
            y_pos = np.arange(len(features))
            bars = ax.barh(y_pos, weights, color=colors, alpha=0.8, height=0.6)
            
            # Customize the plot to match LIME style
            ax.set_yticks(y_pos)
            ax.set_yticklabels(features, fontsize=10)
            ax.set_xlabel('LIME weight', fontsize=12)
            
            # Get class info for title - extract just the class name
            clean_class_name = class_label.split()[0] if ' ' in class_label else class_label
            class_idx_map = {'Normal': 'idx=0', 'Suspect': 'idx=1', 'Pathological': 'idx=2'}
            
            title = f'LIME weights — {class_label} ({class_idx_map.get(clean_class_name, "idx=0")})'
            ax.set_title(title, fontsize=14, pad=20)
            print(f"📊 Generated graph title: {title}")
            
            # Add vertical line at x=0
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
            
            # Set up the axes to match LIME style
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(True)
            ax.spines['bottom'].set_visible(True)
            
            # Adjust layout
            plt.tight_layout()
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'lime_explanation_{self.graph_session_id}_{instance_id}_{timestamp}.png'
            filepath = os.path.join(os.path.dirname(__file__), '..', 'static', 'graphs', filename)
            
            # Save the plot with high quality
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
            plt.close()  # Close the figure to free memory
            
            return filename
            
        except Exception as e:
            print(f"Error generating explanation graph: {e}")
            return None

    def _clean_old_graphs(self):
        """Clean up old graph files to prevent storage bloat"""
        try:
            graphs_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'graphs')
            if os.path.exists(graphs_dir):
                import time
                current_time = time.time()
                # Remove files older than 1 hour
                for filename in os.listdir(graphs_dir):
                    # Never remove repository assets or files from another app process.
                    if self.graph_session_id not in filename:
                        continue
                    filepath = os.path.join(graphs_dir, filename)
                    if os.path.isfile(filepath):
                        file_age = current_time - os.path.getmtime(filepath)
                        if file_age > 3600:  # 1 hour in seconds
                            os.remove(filepath)
        except Exception as e:
            print(f"Warning: Could not clean old graphs: {e}")
    
    def explain_prediction(self, data: Dict[str, float], num_features: int = 8) -> Dict[str, Any]:
        """
        Generate LIME explanation for a prediction
        
        Args:
            data: Dictionary of feature values
            num_features: Number of top features to include in explanation
            
        Returns:
            Dictionary containing explanation results
        """
        if self.explainer is None:
            return {
                "error": "LIME explainer not available",
                "class_label": "Unknown",
                "explanations": [],
                "graph_url": None
            }
        
        try:
            # Clean up old graphs
            self._clean_old_graphs()
            
            print(f"🔍 Generating LIME explanation for data: {data}")
            
            # Use the prediction service to prepare features correctly
            # This ensures LIME uses the same preprocessing as the actual prediction
            # But we need the unscaled features for LIME's background data comparison
            
            # Prepare features in the correct order (unscaled for LIME)
            features = []
            missing_features = []
            
            for expected_feature in self.feature_names:
                # Try to find the feature in various ways
                value = None
                
                # Direct match
                if expected_feature in data:
                    value = data[expected_feature]
                # Try feature mapping variations
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
            
            # Convert to numpy array for LIME (unscaled)
            instance = np.array(features)
            print(f"📊 LIME instance shape: {instance.shape}")
            print(f"📊 LIME instance sample: {instance[:5]}")
            
            # Get prediction for the class label
            class_id, class_label = self.prediction_service.predict(data)
            print(f"🎯 Prediction: {class_label} (ID: {class_id})")
            
            # Generate unique instance ID
            instance_id = str(uuid.uuid4())[:8]
            
            # Generate explanation
            explanation = self.explainer.explain_instance(
                instance,
                self._predict_fn,
                num_features=num_features,
                labels=[0, 1, 2]  # Use 0-based indices for all classes
            )
            
            # Get the explanation for the predicted class
            # Convert class_id (1,2,3) to 0-based index (0,1,2) for LIME
            predicted_class_idx = class_id - 1 if class_id in [1, 2, 3] else 0
            print(f"🎯 Class ID: {class_id}, LIME class index: {predicted_class_idx}")
            
            # Extract feature contributions for the predicted class
            feature_contributions = explanation.as_list(label=predicted_class_idx)
            print(f"🔍 LIME feature contributions: {feature_contributions[:5]}")  # Debug first 5
            
            # Format explanations with actual feature values from input
            explanations = []
            for feature_desc, weight in feature_contributions:
                # Parse feature description to get feature name - handle different LIME formats
                if '<=' in feature_desc:
                    feature_name = feature_desc.split('<=')[0].strip()
                elif '>' in feature_desc:
                    feature_name = feature_desc.split('>')[0].strip()
                elif '=' in feature_desc:
                    feature_name = feature_desc.split('=')[0].strip()
                else:
                    feature_name = feature_desc.strip()
                
                # Clean feature name
                feature_name = feature_name.replace('_', ' ').strip()
                
                # Try to find matching feature in input data
                input_value = 'Unknown'
                for key, value in data.items():
                    if (key.lower().replace('_', ' ') == feature_name.lower() or 
                        key.lower() == feature_name.lower().replace(' ', '_')):
                        input_value = value
                        break
                
                # If still not found, try original feature names
                if input_value == 'Unknown':
                    for original_name in self.feature_names:
                        if (original_name.lower().replace('_', ' ') == feature_name.lower() or
                            original_name.lower() == feature_name.lower()):
                            input_value = data.get(original_name, 'Unknown')
                            break
                
                explanations.append({
                    'feature': feature_name.title(),  # Make it readable
                    'value': input_value,
                    'weight': round(weight, 4),
                    'impact': 'Positive' if weight > 0 else 'Negative',
                    'description': feature_desc
                })
                print(f"  📝 {feature_name}: weight={weight:.4f}, value={input_value}")
            
            # Sort by absolute weight (importance)
            explanations.sort(key=lambda x: abs(x['weight']), reverse=True)
            print(f"📊 Total explanations: {len(explanations)}")
            print(f"📊 Top 3 weights: {[abs(exp['weight']) for exp in explanations[:3]]}")
            
            # Generate explanation graph
            graph_filename = self._generate_explanation_graph(explanations, class_label, instance_id)
            graph_url = f"/graphs/{graph_filename}" if graph_filename else None
            
            # Generate HTML visualization if available
            html_explanation = None
            try:
                html_explanation = explanation.as_html()
            except:
                html_explanation = None
            
            return {
                'class_label': class_label,
                'class_id': class_id,
                'explanations': explanations,
                'html': html_explanation,
                'graph_url': graph_url,
                'instance_id': instance_id,
                'num_features_explained': len(explanations)
            }
            
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return {
                "error": f"Failed to generate explanation: {str(e)}",
                "class_label": "Unknown", 
                "explanations": [],
                "graph_url": None
            }
