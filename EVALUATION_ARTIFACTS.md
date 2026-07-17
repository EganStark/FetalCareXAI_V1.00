# Model evaluation and lineage

This document records the evidence behind the production model card. It keeps
verified results separate from historical project material and prevents metrics
from being presented without their evaluation context.

## Evidence status

| Artifact or claim | Status | Verification |
|---|---|---|
| Production model, scaler, feature order, and labels | Verified | Source and project files have matching SHA-256 hashes |
| Dataset | Verified | 2,126-row CSV matches documented UCI structure |
| Dataset source and license | Verified | UCI DOI and CC BY 4.0 license |
| Duplicate policy | Verified | `drop_duplicates(keep='first')` |
| Evaluation split | Verified | Stratified 80/20, `random_state=42` |
| Held-out accuracy and macro F1 | Verified | Reconstruction exactly matches `metadata.json` |
| Production export script | Not recovered | Historical notebook does not export the 19-feature artifact |

## Dataset identity

- Name: Cardiotocography
- Records: 2,126
- Measured predictors: 21
- Production model predictors: 19
- Missing values: 0
- Duplicate rows before cleaning: 13
- Dataset SHA-256: `90bd62b95020ffa466f01a2942a79cf6b8b04cc5ac680144d705002d893f6622`
- Excluded predictors: `histogram_max`, `histogram_number_of_zeroes`

**Citation:** Campos, D. & Bernardes, J. (2000). *Cardiotocography*
[Dataset]. UCI Machine Learning Repository.
<https://doi.org/10.24432/C51S4N>

## Reconstructed split

```text
Original rows           2,126
Rows after deduplication 2,113
Training rows            1,690
Held-out test rows         423
Split                     80/20, stratified
Random state              42
```

Test-index fingerprint:
`de1bcdca552edb2e1785c48d306321b749a8fd27204bc7963e156fa4d2dfd274`

## Held-out performance

| Metric | Value |
|---|---:|
| Accuracy | 0.966903 |
| Macro F1 | 0.942748 |
| Weighted F1 | 0.965545 |
| ROC AUC OVR | 0.989928 |
| Log loss | 0.166730 |
| Multiclass Brier score | 0.063149 |
| 10-bin expected calibration error | 0.027322 |

<details>
<summary><strong>Confusion matrix and class report</strong></summary>

| Actual \ Predicted | Normal | Suspect | Pathological |
|---|---:|---:|---:|
| Normal | 329 | 1 | 0 |
| Suspect | 11 | 46 | 1 |
| Pathological | 1 | 0 | 34 |

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Normal | 0.964809 | 0.996970 | 0.980626 | 330 |
| Suspect | 0.978723 | 0.793103 | 0.876190 | 58 |
| Pathological | 0.971429 | 0.971429 | 0.971429 | 35 |

</details>

## Historical-material notes

The supplied historical notebook includes a visible 15-feature LightGBM
experiment, while the serialized production artifact expects 19 features. The
capstone poster also contains an older 96.45% narrative result alongside a final
96.69% LightGBM table.

The application reports 96.69% because:

1. The production metadata records `0.966903073286052`.
2. The reconstructed 423-row held-out split produces the same value exactly.
3. Its reconstructed macro F1 also matches metadata exactly.
4. The poster's final comparison table reports 96.69%.

These checks establish evaluation lineage without claiming that the historical
15-feature notebook is the production export pipeline.

## Requirements for future model versions

A replacement model should include:

- Versioned training and export code
- Dataset citation, license, and fingerprint
- Exact ordered features and preprocessing artifacts
- Reproducible split indices or held-out predictions
- Confusion matrix and per-class precision, recall, F1, and support
- Probability calibration evidence
- Documented intended use, exclusions, and limitations

Do not commit identifiable patient data or evaluate a replacement solely on its
training set.
