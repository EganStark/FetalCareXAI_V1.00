"""Production-ready Flask API for FetalCare XAI."""
import json
import hashlib
import logging
import math
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from .services.explain import ExplanationService
from .services.predict import PredictionService
from .services.validate import InputValidator

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
MODEL_DIR = BASE_DIR / "model"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")
app.config.update(
    JSON_SORT_KEYS=False,
    MAX_CONTENT_LENGTH=64 * 1024,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
if allowed_origins:
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

prediction_service = PredictionService()
validator = InputValidator(prediction_service)
explanation_service = ExplanationService(prediction_service)

with (MODEL_DIR / "label_map.json").open(encoding="utf-8") as label_file:
    label_map = json.load(label_file)

with (MODEL_DIR / "metadata.json").open(encoding="utf-8") as metadata_file:
    model_metadata = json.load(metadata_file)

with (MODEL_DIR / "evaluation_summary.json").open(encoding="utf-8") as evaluation_file:
    evaluation_summary = json.load(evaluation_file)


def model_artifact_hash():
    digest = hashlib.sha256()
    with (MODEL_DIR / "model.pkl").open("rb") as model_file:
        for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def error_response(message, status=400, *, details=None):
    payload = {"status": "error", "error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status


def validated_payload():
    if not request.is_json:
        return None, error_response("Content-Type must be application/json", 415)
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return None, error_response("No input data provided")
    is_valid, errors, cleaned_data = validator.validate_input(data)
    if not is_valid:
        return None, error_response("Please review the highlighted measurements.", details=errors)
    return cleaned_data, None


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self'; "
        "script-src 'self'; connect-src 'self'; font-src 'self'; frame-ancestors 'none'",
    )
    return response


@app.get("/health")
def health_check():
    return jsonify({
        "status": "ok",
        "service": "FetalCare XAI",
        "model": prediction_service.get_model_info(),
    })


@app.get("/schema")
def get_schema():
    schema = validator.get_feature_schema()
    schema.update({"labels": label_map, "target": "fetal_health"})
    return jsonify(schema)


@app.get("/model-card")
def get_model_card():
    metrics = {
        name: value if isinstance(value, (int, float)) and math.isfinite(value) else None
        for name, value in model_metadata.get("metrics", {}).items()
    }
    return jsonify({
        "model": {
            "name": "FetalCare XAI LightGBM classifier",
            "algorithm": model_metadata.get("best_model_name", "LightGBM"),
            "version": model_metadata.get("timestamp", "undocumented"),
            "artifact_hash": model_artifact_hash(),
            "features": len(prediction_service.features),
            "classes": ["Normal", "Suspect", "Pathological"],
        },
        "evaluation": {
            "metrics": metrics,
            "evaluation_split": evaluation_summary["preserved_evaluation"]["lineage"],
            "class_balance": evaluation_summary["dataset"]["class_counts"],
            "confusion_matrix": evaluation_summary["held_out_evaluation"]["confusion_matrix"],
            "per_class_metrics": evaluation_summary["held_out_evaluation"]["per_class"],
            "diagnostic_scope": "held_out_test_set",
            "diagnostic_warning": "Metrics reconstructed on the 423-row stratified held-out set; accuracy and macro F1 exactly match the serialized metadata.",
            "calibration": {
                "multiclass_brier": evaluation_summary["held_out_evaluation"]["multiclass_brier"],
                "ece_10_bin": evaluation_summary["held_out_evaluation"]["ece_10_bin"],
                "bins": evaluation_summary["held_out_evaluation"]["calibration_bins"],
            },
        },
        "provenance": {
            "dataset": evaluation_summary["dataset"],
            "trained_at": model_metadata.get("timestamp"),
            "library_versions": model_metadata.get("versions", {}),
        },
        "intended_use": [
            "Education and research prototyping",
            "Demonstrating explainable ML workflows with non-identifying CTG data",
        ],
        "out_of_scope": [
            "Clinical diagnosis, triage, treatment, or patient monitoring",
            "Use as a medical device or replacement for professional interpretation",
        ],
        "limitations": [
            "Evaluation uses one public CTG dataset; external clinical validation has not been demonstrated",
            "The supplied notebook's visible experiment uses 15 features, while the serialized production artifact uses 19 features",
            "LIME is a local approximation and does not establish causality",
            "Performance may change under dataset shift or measurement error",
        ],
    })


@app.post("/preview")
def preview_input():
    data, error = validated_payload()
    if error:
        return error
    return jsonify({"status": "valid", "data": data, "feature_count": len(data)})


@app.post("/predict")
def predict():
    data, error = validated_payload()
    if error:
        return error
    try:
        result = prediction_service.predict_details(data)
        return jsonify({"status": "success", **result})
    except Exception:
        app.logger.exception("Prediction failed")
        return error_response("The model could not complete this assessment.", 500)


@app.post("/explain")
def explain_prediction():
    data, error = validated_payload()
    if error:
        return error
    try:
        explanation = explanation_service.explain_prediction(data)
        if explanation.get("error"):
            app.logger.error("Explanation failed: %s", explanation["error"])
            return error_response("An explanation could not be generated for this result.", 503)
        explanation.pop("html", None)  # Avoid returning executable third-party HTML.
        return jsonify({"status": "success", **explanation})
    except Exception:
        app.logger.exception("Explanation failed")
        return error_response("An explanation could not be generated for this result.", 500)


@app.get("/")
def serve_frontend():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/<path:filename>")
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith(("/predict", "/preview", "/explain", "/schema", "/health")):
        return error_response("Endpoint not found", 404)
    return send_from_directory(STATIC_DIR, "index.html")


@app.errorhandler(413)
def request_too_large(_error):
    return error_response("Request is too large", 413)


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
