import os
import json
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, 'lightgbm_model.pkl')
LE_PATH = os.path.join(BASE_DIR, 'label_encoder.pkl')
CATS_PATH = os.path.join(BASE_DIR, 'categories_map.json')
FEATURES_PATH = os.path.join(BASE_DIR, 'feature_columns.json')


def load_artifacts():
    model = joblib.load(MODEL_PATH)
    le = joblib.load(LE_PATH)
    with open(CATS_PATH, 'r', encoding='utf-8') as f:
        categories_map = json.load(f)
    with open(FEATURES_PATH, 'r', encoding='utf-8') as f:
        feature_cols = json.load(f)
    return model, le, categories_map, feature_cols


def preprocess_row(sample, categories_map, feature_cols):
    # sample: dict mapping feature -> value
    # feature_cols: list of expected columns in order
    df = pd.DataFrame([sample])

    # ensure all expected columns exist
    for c in feature_cols:
        if c not in df.columns:
            df[c] = np.nan

    # Process categorical columns
    for col, cats in categories_map.items():
        # normalize
        df[col] = df[col].fillna('NA').astype(str)
        # map unknowns to 'UNK' if available else add UNK
        def map_unknown(v, cats):
            return v if v in cats else ('UNK' if 'UNK' in cats else v)
        df[col] = df[col].apply(lambda x: map_unknown(x, cats))
        # if 'UNK' wasn't in original categories but we mapped unknown values to themselves,
        # ensure categories include 'UNK' so we have a numeric code; otherwise we'll expand
        if 'UNK' not in cats:
            expanded = cats + ['UNK']
        else:
            expanded = cats
        df[col] = pd.Categorical(df[col], categories=expanded).codes.astype(int)

    # Numeric columns: coerce to numeric
    for col in feature_cols:
        if col not in categories_map:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df[feature_cols]


def predict(sample: dict):
    model, le, categories_map, feature_cols = load_artifacts()
    X = preprocess_row(sample, categories_map, feature_cols)
    # predict class index
    pred_idx = model.predict(X)[0]
    # map back to original label
    pred_label = le.inverse_transform([pred_idx])[0]
    # probability (if model supports predict_proba)
    try:
        proba = model.predict_proba(X)[0].max()
    except Exception:
        proba = None
    return pred_label, float(proba) if proba is not None else None


if __name__ == '__main__':
    # Example: create a sample dict using feature names — you can edit values as needed.
    model, le, categories_map, feature_cols = load_artifacts()
    example = {}
    for c in feature_cols:
        # fill numeric columns with median-like defaults, categoricals with first category
        if c in categories_map:
            example[c] = categories_map[c][0] if categories_map[c] else 'NA'
        else:
            example[c] = 0

    print('Example sample used for demo:')
    print(example)
    label, prob = predict(example)
    print('Predicted:', label, 'Prob:', prob)
