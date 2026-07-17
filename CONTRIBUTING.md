# Contributing to FetalCare XAI

Thank you for helping improve the project. Contributions should preserve its
research-only scope, privacy boundary, and evidence-first presentation.

## Development workflow

1. Create a focused branch from the latest default branch.
2. Create a Python 3.12 virtual environment.
3. Install `requirements.txt`.
4. Make one coherent change at a time.
5. Run the complete test suite before opening a pull request.

```bash
python -m pytest -q
```

## Code expectations

- Keep API errors safe for public display; log internal exceptions server-side.
- Never log, persist, or add CTG input values to analytics.
- Preserve keyboard access, semantic markup, and responsive behavior.
- Keep model probabilities distinct from clinical certainty.
- Add tests for API contracts, validation rules, or model-response changes.
- Do not commit virtual environments, `.env` files, generated graphs, or patient data.

## Model changes

A model or preprocessing change must include:

- The exact ordered feature list
- Scaler and label-mapping artifacts
- Training and evaluation code
- Dataset citation, license, and fingerprint
- Reproducible split or held-out prediction artifacts
- Confusion matrix and per-class precision, recall, F1, and support
- Calibration evidence where probabilities are shown to users
- Updated model version and artifact hash

Do not replace the production model based only on training accuracy or
full-dataset resubstitution scores.

## Documentation

Update the README, deployment guide, model card, and safety language whenever a
change affects behavior, dependencies, data handling, evaluation, or intended use.

## Pull requests

A pull request should explain:

- What changed and why
- How it was tested
- Any privacy, safety, accessibility, or deployment impact
- Screenshots for visible interface changes
- Evaluation evidence for model changes

Keep pull requests small enough to review confidently.
