# Evaluation artifacts needed

## Current status

Recovered and verified:

- Original 2,126-row CSV and matching production model artifacts
- UCI source, DOI, citation, and CC BY 4.0 license
- Duplicate removal followed by a stratified 80/20 split with `random_state=42`
- A 423-row held-out set whose accuracy and macro F1 exactly match model metadata
- Held-out confusion matrix, per-class metrics, ROC AUC, Brier score, and ECE

Still missing:

- The exact script or notebook cell that exported the 19-feature production artifacts
- Resolution of the historical notebook's 15-feature experiment versus the 19-feature artifact
- Resolution of the poster narrative's older 96.45% value versus its final 96.69% table

The dashboard intentionally shows only evidence preserved with the current model.
To regenerate the missing confusion matrix, class balance, per-class metrics, and
calibration results, provide the following artifacts.

## Preferred option: reproducible training package

1. `fetal_health.csv`
   - The same 19 feature columns listed by `backend/model/features.pkl`.
   - One target column named `fetal_health` with labels `1`, `2`, or `3`.
   - Remove names, record IDs, dates, institutions, and other identifiers first.
2. The original training notebook or Python script.
3. The exact train/test split indices, or the split method and random seed.
4. Any preprocessing, resampling, feature selection, or class-weight settings.

## Minimum option: held-out predictions

Provide `test_predictions.csv` with these columns:

```text
y_true,y_pred,prob_normal,prob_suspect,prob_pathological
1,1,0.94,0.05,0.01
2,2,0.12,0.81,0.07
```

This is enough to calculate:

- Confusion matrix
- Class counts and proportions for the held-out set
- Precision, recall, and F1 for each class
- Macro and weighted averages
- ROC AUC where mathematically valid
- Reliability curves, Brier score, and expected calibration error

It is not enough to reproduce training or verify dataset provenance.

## Dataset documentation

Also provide, where known:

- Dataset name and authoritative source URL or citation
- License and allowed use
- Collection setting and time period
- Inclusion/exclusion criteria
- Sample count before and after cleaning
- Missing-value handling
- Duplicate handling
- Known demographic or institutional limitations

Do not add private or identifiable patient information to this repository.
