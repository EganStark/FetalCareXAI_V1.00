import urllib.request
import json

def test_server():
    try:
        # Test health endpoint first
        print("Testing server health...")
        response = urllib.request.urlopen('http://127.0.0.1:5000/health')
        health_data = json.loads(response.read().decode())
        print("Health check:", health_data)
        
        # Test prediction
        print("\nTesting pathological prediction...")
        pathological_data = {
            'baseline_value': 180,
            'accelerations': 0.000,
            'fetal_movement': 0.000,
            'uterine_contractions': 0.008,
            'light_decelerations': 0.006,
            'severe_decelerations': 0.005,
            'mean_value_of_short_term_variability': 12,
            'mean_value_of_long_term_variability': 8,
            'histogram_width': 50,
            'histogram_min': 90,
            'histogram_number_of_peaks': 1,
            'histogram_number_of_zeroes': 10,
            'histogram_mode': 180,
            'histogram_mean': 175,
            'histogram_median': 180,
            'histogram_variance': 20,
            'histogram_tendency': 1,
            'prolongued_decelerations_abnormal_short_term_variability': 85,
            'prolongued_decelerations_percentage_of_time_with_abnormal_long_term_variability': 90
        }
        
        data = json.dumps(pathological_data).encode('utf-8')
        req = urllib.request.Request(
            'http://127.0.0.1:5000/predict',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        
        print("Prediction Result:")
        print(f"  Class ID: {result.get('class_id')}")
        print(f"  Class Label: {result.get('class_label')}")
        print(f"  Message: {result.get('message')}")
        
        if 'Pathological' in str(result.get('class_label')):
            print("\n✅ SUCCESS: Correctly predicted Pathological!")
        else:
            print(f"\n❌ ISSUE: Expected 'Pathological' but got '{result.get('class_label')}'")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_server()
