# Dataset and preparation notes

Source: Wolberg, W., Mangasarian, O., Street, N., & Street, W. (1993). Breast Cancer Wisconsin (Diagnostic). UCI Machine Learning Repository. DOI: https://doi.org/10.24432/C5DW2B . CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . This project redistributes derived labels/predictions with attribution; it does not change the original reference labels.

Official source: https://archive.ics.uci.edu/dataset/17/breast-cancer-wisconsin-diagnostic
Loader documentation: https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_breast_cancer.html

The original dataset has 569 samples and 30 numerical features computed from digitized fine-needle-aspirate images of breast masses. Labels describe benign or malignant samples. The scikit-learn loader maps 0 to malignant and 1 to benign; the learner CSV uses explicit text labels to avoid interpreting 1 as malignant by mistake.

The author prepared a fixed split: 426 training samples and 143 test samples, stratified by the original label with random_state=42 and test_size=0.25. StandardScaler was fitted on training features only, followed by LogisticRegression(solver='liblinear', max_iter=2000, random_state=42). The test split was not used to select or tune this model. No attempt was made to optimise the model for this teaching example. The report project does not train, tune or deploy a classifier.

`sample_id` is an index into the loader's row order (zero-based), not a patient's name or identifier. `reference_label` is the dataset label; `predicted_label` is the fixed baseline prediction. The CSV contains only the held-out samples, sorted by this index. `reference-results.json` contains reference counts, rounded metrics, a CSV checksum and preparation metadata. A matching checksum confirms the fixed file, not medical validity.

These retrospective results describe one educational split. They do not establish clinical usefulness, safety, fairness or performance on future populations. No patient diagnosis or treatment decision is supported by this exercise.

## Optional reproduction, separate from the learner task

The public package includes `prepare_predictions.py`. Core report notebooks require only the package-root requirements, not scikit-learn. To reproduce the author baseline, use a separate local preparation environment with:

```
python -m pip install scikit-learn==1.6.1 numpy==2.1.3 scipy==1.15.3
python prepare_predictions.py --output reproduced-results
```

Compare both generated files with the supplied versions; do not replace the fixed learner inputs during the report exercise. Other library versions may produce different results. Model objects are not distributed or needed. The optional script is not run automatically by any notebook.
