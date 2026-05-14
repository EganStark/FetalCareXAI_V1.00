#!/usr/bin/env python3
"""
Test script to verify pathological prediction
"""
import requests
import json
import time

def test_pathological_prediction():
    # Wait a moment for server to be ready
    time.sleep(1)
    
    # Pathological test case - values indicating serious fetal distress
    pathological_data = {
        'baseline_value': 180,  # High baseline (normal ~120-160)
        'accelerations': 0.000,  # No accelerations (bad sign)
        'fetal_movement': 0.000,  # No fetal movement (very bad)
        'uterine_contractions': 0.008,  # Normal contractions
        'light_decelerations': 0.006,  # Some light decelerations
        'severe_decelerations': 0.005,  # Severe decelerations (very bad)
        'mean_value_of_short_term_variability': 12,  # Low variability
        'mean_value_of_long_term_variability': 8,  # Very low variability (bad)
        'histogram_width': 50,  # Narrow width (bad)
        'histogram_min': 90,  # Low minimum
        'histogram_number_of_peaks': 1,  # Single peak (bad)
        'histogram_number_of_zeroes': 10,  # Many zeros
        'histogram_mode': 180,  # Mode matches high baseline
        'histogram_mean': 175,  # High mean
        'histogram_median': 180,  # High median
        'histogram_variance': 20,  # Low variance (bad)
        'histogram_tendency': 1,  # Tendency present
        'prolongued_decelerations_abnormal_short_term_variability': 85,  # High percentage (very bad)
        'prolongued_decelerations_percentage_of_time_with_abnormal_long_term_variability': 90  # Very high (pathological)
    }

    print("🔍 Testing Pathological Prediction...")
    print("=" * 50)
    
    try:
        print("Sending request to http://127.0.0.1:5000/predict")
        response = requests.post(
            'http://127.0.0.1:5000/predict', 
            json=pathological_data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n🎯 PREDICTION RESULT:")
            print("=" * 30)
            print(f"Class ID: {result.get('class_id')}")
            print(f"Class Label: {result.get('class_label')}")
            print(f"Message: {result.get('message', 'N/A')}")
            
            # Check if prediction is correct
            expected_class = "Pathological"
            actual_class = result.get('class_label')
            
            if expected_class in str(actual_class):
                print("\n✅ SUCCESS: Model correctly predicted Pathological!")
            else:
                print(f"\n❌ ISSUE: Expected '{expected_class}' but got '{actual_class}'")
            
            print("\nFull Response:")
            print(json.dumps(result, indent=2))
            
        else:
            print(f"\n❌ Error Response (Status {response.status_code}):")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to Flask server at http://127.0.0.1:5000")
        print("Make sure the Flask server is running.")
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Request took too long")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_pathological_prediction()
