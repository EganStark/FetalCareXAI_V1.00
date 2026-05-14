# Fetal Health Prediction Application

A professional web application for predicting fetal health using machine learning with explainable AI (LIME) explanations.

## Features

- **Modern Web Interface**: Clean, responsive design with intuitive user experience
- **ML Prediction**: Classifies fetal health as Normal, Suspect, or Pathological
- **Input Validation**: Comprehensive validation with helpful error messages
- **Preview Mode**: Review inputs before making predictions
- **XAI Explanations**: LIME-powered explanations showing feature contributions
- **Local Caching**: Automatically saves inputs in browser localStorage
- **Accessibility**: High contrast, keyboard navigation support

## Tech Stack

- **Backend**: Python 3.10+, Flask, scikit-learn, LIME
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **ML**: scikit-learn compatible models (.pkl format)
- **Explanation**: LIME (Local Interpretable Model-agnostic Explanations)

## Project Structure

```
project/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── model/
│   │   ├── model.pkl          # Trained ML model (place your model here)
│   │   ├── label_map.json     # Class label mapping
│   │   ├── feature_metadata.json  # Feature definitions and ranges
│   │   └── background_sample.csv  # Background data for LIME
│   ├── services/
│   │   ├── validate.py        # Input validation service
│   │   ├── predict.py         # Prediction service
│   │   └── explain.py         # LIME explanation service
│   └── static/                # Frontend files
│       ├── index.html         # Main web page
│       ├── styles.css         # Styling
│       └── app.js             # Frontend JavaScript
├── tests/
│   └── test_api.py           # API test suite
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Place Your Model

Place your trained model file as `backend/model/model.pkl`. The model should:
- Accept 14 input features (see Feature List below)
- Return predictions as class IDs: 1=Normal, 2=Suspect, 3=Pathological
- Be scikit-learn compatible or implement `.predict()` method

### 3. Run the Application

```bash
cd backend
python app.py
```

### 4. Access the Application

Open your browser and navigate to: `http://127.0.0.1:5000`

## Feature List (14 Input Features)

The application expects exactly 14 input features:

1. **baseline_value** - Baseline fetal heart rate (106.0 - 160.0 BPM)
2. **accelerations** - Number of accelerations per second (0.0 - 0.019)
3. **uterine_contractions** - Number of uterine contractions per second (0.0 - 0.015)
4. **light_decelerations** - Number of light decelerations per second (0.0 - 0.015)
5. **mean_value_of_short_term_variability** - Mean value of short term variability (0.2 - 7.0)
6. **mean_value_of_long_term_variability** - Mean value of long term variability (0.0 - 91.0)
7. **histogram_width** - Width of FHR histogram (3.0 - 180.0)
8. **histogram_min** - Minimum value of FHR histogram (50.0 - 159.0)
9. **histogram_number_of_peaks** - Number of histogram peaks (0.0 - 18.0)
10. **histogram_mean** - Mean value of FHR histogram (73.0 - 182.0)
11. **histogram_variance** - Variance of FHR histogram (0.0 - 269.0)
12. **histogram_tendency** - Histogram tendency (-1.0 to 1.0: -1=left asymmetric, 0=symmetric, 1=right asymmetric)
13. **prolongued_decelerations_abnormal_short_term_variability** - Abnormal short term variability rate (0.0 - 0.001)
14. **prolongued_decelerations_percentage_of_time_with_abnormal_long_term_variability** - Percentage of time with abnormal long term variability (0.0 - 97.0)

**Target Variable (Output Only):**
- **fetal_health** - Classes: 1=Normal, 2=Suspect, 3=Pathological

## API Endpoints

### GET /health
Health check endpoint
```json
{
  "status": "ok",
  "message": "Fetal Health Prediction API is running",
  "model_info": {...}
}
```

### GET /schema
Get feature schema and label mapping
```json
{
  "features": {...},
  "labels": {"1": "Normal", "2": "Suspect", "3": "Pathological"},
  "required": [...]
}
```

### POST /preview
Validate and preview input data
```json
{
  "status": "valid",
  "data": {...},
  "feature_count": 14
}
```

### POST /predict
Make prediction
```json
{
  "status": "success",
  "class_id": 1,
  "class_label": "Normal",
  "input_data": {...}
}
```

### POST /explain
Generate LIME explanation
```json
{
  "status": "success",
  "class_label": "Normal",
  "explanations": [
    {
      "feature": "baseline_value",
      "value": 120.0,
      "weight": 0.1234,
      "impact": "Positive"
    }
  ]
}
```

## Sample Test Payload

```json
{
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
```

## Running Tests

```bash
cd project
python -m pytest tests/test_api.py -v
```

## Replacing the Model

To use your own trained model:

1. Ensure your model is trained on the 14 features listed above
2. Save your model using joblib: `joblib.dump(model, 'model.pkl')`
3. Place the file in `backend/model/model.pkl`
4. Update `feature_metadata.json` if your feature ranges differ
5. Update `background_sample.csv` with representative training data for LIME

## LIME Explanations

The application uses LIME (Local Interpretable Model-agnostic Explanations) to explain individual predictions. LIME requires background data to understand feature importance. The app uses:

1. `background_sample.csv` if available
2. Synthetic data generated from feature ranges as fallback

Explanations show:
- Top contributing features
- Positive/negative impact on prediction
- Feature values and weights
- Optional HTML visualization

## Development Notes

- The app includes a dummy model for development if `model.pkl` is not found
- Input validation enforces feature ranges and data types
- CORS is enabled for frontend-backend communication
- LocalStorage automatically saves user inputs
- Responsive design works on desktop and mobile

## Customization

### Styling
- Modify `static/styles.css` to change the appearance
- CSS variables at the top of the file control colors and spacing

### Features
- Update `feature_metadata.json` to change feature definitions
- Modify validation logic in `services/validate.py`

### Model Integration
- Update `services/predict.py` for custom model preprocessing
- Modify `services/explain.py` for custom explanation logic

## Troubleshooting

### Model Not Loading
- Ensure `model.pkl` is in the correct location
- Check that the model is scikit-learn compatible
- Review console output for error messages

### LIME Explanations Failing
- Verify `background_sample.csv` contains valid data
- Check that feature names match exactly
- Ensure the model supports probability prediction

### API Errors
- Check Flask console for detailed error messages
- Validate input data format and ranges
- Ensure all required dependencies are installed

## License

This project is created for educational/research purposes. Please ensure compliance with your institution's policies when using medical prediction models.
