import os
import json
import joblib
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, 'xgb_model.pkl')
ENCODERS_PATH = os.path.join(BASE_DIR, 'encoders.pkl')
FEATURES_PATH = os.path.join(BASE_DIR, 'feature_columns.json')


def load_artifacts():
    model = joblib.load(MODEL_PATH)
    encoders = joblib.load(ENCODERS_PATH)
    with open(FEATURES_PATH, 'r', encoding='utf-8') as f:
        feature_cols = json.load(f)
    return model, encoders, feature_cols


def preprocess_row(sample: dict, encoders: dict, feature_cols: list):
    # Build DataFrame from sample and ensure all feature columns exist
    df = pd.DataFrame([sample])
    for c in feature_cols:
        if c not in df.columns:
            df[c] = np.nan

    # Apply encoders for categorical columns (encoders contains per-column LabelEncoder and 'target')
    for col, enc in encoders.items():
        if col == 'target':
            continue
        # if encoder is not a LabelEncoder instance (safety), skip
        try:
            classes = list(enc.classes_)
        except Exception:
            continue

        # normalize and handle unseen labels
        df[col] = df[col].fillna('NA').astype(str)
        def _map_value(v, classes):
            return v if v in classes else ('UNK' if 'UNK' in classes else v)
        df[col] = df[col].apply(lambda x: _map_value(x, classes))

        # If 'UNK' not in classes and value mapped to itself (unknown), append 'UNK'
        if 'UNK' not in classes:
            # expand classes to include UNK so transform works
            enc.classes_ = np.append(enc.classes_, 'UNK')

        # transform
        df[col] = enc.transform(df[col])

    # Convert remaining non-encoded columns to numeric (coerce)
    for col in feature_cols:
        if col not in encoders:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Return matrix in feature_cols order
    return df[feature_cols]


def predict(sample: dict):
    model, encoders, feature_cols = load_artifacts()
    X = preprocess_row(sample, encoders, feature_cols)
    pred_idx = model.predict(X)[0]
    # inverse transform using target encoder
    le_target = encoders.get('target')
    if le_target is not None:
        pred_label = le_target.inverse_transform([pred_idx])[0]
    else:
        pred_label = pred_idx
    try:
        proba = model.predict_proba(X)[0].max()
    except Exception:
        proba = None
    return pred_label, float(proba) if proba is not None else None


if __name__ == '__main__':
    model, encoders, feature_cols = load_artifacts()
    # Build an example sample using first available categorical values and zeros for numeric
    example = {}
    for c in feature_cols:
        if c in encoders and c != 'target':
            # pick first known class
            cls = encoders[c].classes_[0] if len(encoders[c].classes_)>0 else 'NA'
            example[c] = cls
        else:
            example[c] = 0

    print('Example sample:')
    print(example)
    label, prob = predict(example)
    print('Predicted:', label, 'Prob:', prob)
