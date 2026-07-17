# FetalCare XAI

An explainable machine-learning application for exploring fetal cardiotocography
(CTG) patterns. FetalCare XAI combines a LightGBM classifier with LIME local
explanations in a responsive, privacy-conscious Flask application.

> **Research and education only.** FetalCare XAI is not a medical device and
> must not be used for diagnosis, triage, treatment, or patient monitoring.

## Overview

The model evaluates 19 CTG measurements and estimates probabilities for three
pattern classes:

- **Normal**
- **Suspect**
- **Pathological**

The interface presents the probability distribution, uncertainty guidance, a
plain-language explanation, and the original LIME weight chart. Measurements
and results remain transient in the browser tab; this release has no accounts,
cloud history, or patient-record storage.

## Highlights

- Modern dark-first interface with a fully responsive light theme
- Range-aware validation for all 19 model features
- Verified Normal, Suspect, Pathological, and randomized demo inputs
- Real model probabilities rather than simulated confidence values
- LIME contribution summaries and generated weight charts
- Privacy-safe, in-memory session analytics
- CSV template download and validated CSV import
- Printable assessment reports with browser-based PDF export
- Temporary side-by-side assessment comparison
- Versioned model card, dataset provenance, and held-out evaluation dashboard
- Security headers, request limits, production error handling, and Docker support

## Verified evaluation

The serialized production model was evaluated on a reconstructed, stratified
20% test split. The reconstruction uses duplicate removal and `random_state=42`;
its accuracy and macro F1 match the stored model metadata exactly.

| Metric | Value |
|---|---:|
| Test records | 423 |
| Accuracy | 96.69% |
| Macro F1 | 94.27% |
| Weighted F1 | 96.55% |
| ROC AUC, one-vs-rest | 98.99% |

The Suspect class is the most difficult class, with held-out recall of 79.31%.
See the in-application model card for the confusion matrix, per-class measures,
calibration diagnostics, and limitations.

## Dataset

The project uses the Cardiotocography dataset: 2,126 CTG records, 21 measured
predictors, no missing values, and fetal-state consensus labels assigned by
three expert obstetricians. The deployed model uses 19 of those predictors.

**Citation:** Campos, D. & Bernardes, J. (2000). *Cardiotocography* [Dataset].
UCI Machine Learning Repository. <https://doi.org/10.24432/C51S4N>

- [Authoritative UCI repository](https://archive.ics.uci.edu/dataset/193/cardiotocography)
- [Kaggle mirror](https://www.kaggle.com/datasets/andrewmvd/fetal-health-classification)
- License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Technology

| Layer | Technologies |
|---|---|
| Application | Python 3.12, Flask, Gunicorn |
| Model | LightGBM, scikit-learn, Joblib |
| Explainability | LIME, Matplotlib |
| Interface | Semantic HTML, modern CSS, vanilla JavaScript |
| Quality | pytest, GitHub Actions, Docker |

## Local development

### Requirements

- Python 3.12
- `uv` or `pip`

### Setup with `uv`

```bash
uv python install 3.12.11
uv venv --python 3.12.11 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
```

On macOS or Linux, replace `.venv/Scripts/python.exe` with
`.venv/bin/python`.

### Run

```bash
python start_app.py
```

Open <http://127.0.0.1:5000>. The health endpoint is available at
<http://127.0.0.1:5000/health>.

### Test

```bash
python -m pytest -q
```

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service and model health |
| `GET` | `/schema` | Feature definitions and accepted ranges |
| `GET` | `/model-card` | Versioned provenance and evaluation evidence |
| `POST` | `/preview` | Validate a measurement payload |
| `POST` | `/predict` | Return class probabilities and classification |
| `POST` | `/explain` | Generate a local LIME explanation |

Prediction and explanation requests accept a JSON object containing exactly the
19 features returned by `/schema`.

## Project structure

```text
backend/
  app.py                   Flask routes and production safeguards
  model/                   Serialized model, metadata, and evaluation summary
  services/                Validation, prediction, and explanation services
  static/                  Application interface
tests/                     Maintained pytest suite
DEPLOYMENT.md              Hosting and production checklist
EVALUATION_ARTIFACTS.md    Evaluation lineage and artifact requirements
Dockerfile                 Reproducible production container
render.yaml                Render service blueprint
```

## Deployment

The recommended first production target is a Docker-based Render web service.
The native LightGBM runtime and LIME/Matplotlib dependencies are a better fit for
a container than a Vercel serverless function. See [DEPLOYMENT.md](DEPLOYMENT.md).

## Privacy and responsible use

- Do not submit identifiable patient information.
- Raw CTG measurements are not sent to analytics or stored as history.
- Session analytics are aggregated in memory and disappear on refresh.
- LIME explains local model behavior; it does not establish clinical causality.
- External clinical validation and applicable regulatory review are required
  before any clinical use.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development, testing, and model-change
requirements.

## License

Application source code is available under the [MIT License](LICENSE). Dataset
use remains subject to the dataset's CC BY 4.0 terms and attribution requirements.
