import joblib
import pandas as pd
import numpy as np
from flask import jsonify
from models.user_profile import UserProfile

model = joblib.load(r"D:\FinalYearProject\Matrimony_Matchmaker\notebooks\Model-LightGBM\lightGBM_model.pkl")

CLASS_MAP = {
    0: "High_No",
    1: "High_Yes",
    2: "Low_No",
    3: "Low_Yes",
    4: "Medium_No",
    5: "Medium_Yes"
}
FEATURES = [
    'Age_at_Marriage', 'Gender', 'Education_Level', 'Caste_Match', 'Religion',
    'Urban_Rural', 'Income_Level', 'Spouse_Working', 'Inter-Caste', 'Inter-Religion'
]

CATEGORICAL_COLS = [
    'Gender', 'Education_Level', 'Caste_Match', 'Religion',
    'Urban_Rural', 'Income_Level', 'Spouse_Working', 'Inter-Caste', 'Inter-Religion'
]

def get_user_profile_helper(identifier):
    if identifier.isdigit():
        return UserProfile.query.filter_by(user_id=int(identifier)).first()
    elif "@" in identifier:
        return UserProfile.query.filter_by(email=identifier).first()
    else:
        return UserProfile.query.filter_by(name=identifier).first()

def predict_match(user1_id, user2_id):
    if not user1_id or not user2_id:
        return jsonify({"error": "Please provide both user1 and user2 identifiers"}), 400

    user1 = get_user_profile_helper(user1_id)
    user2 = get_user_profile_helper(user2_id)
    if not user1 or not user2:
        return jsonify({"error": "One or both users not found"}), 404

    data = {
        'Age_at_Marriage': abs(user2.age),
        'Gender': str(user2.gender),
        'Education_Level': 'Same' if user1.education == user2.education else 'Different',
        'Caste_Match': 'Same' if user1.caste == user2.caste else 'Different',
        'Religion': 'Same' if user1.religion == user2.religion else 'Different',
        'Urban_Rural': 'Same' if user1.residence == user2.residence else 'Different',
        'Income_Level': 'Same' if user1.profession == user2.profession else 'Different',
        'Spouse_Working': 'Yes' if (
            (user1.extras and user1.extras.get('spouse_working') == 'Yes') or 
            (user2.extras and user2.extras.get('spouse_working') == 'Yes')
        ) else 'No',
        'Inter-Caste': 'Yes' if user1.caste != user2.caste else 'No',
        'Inter-Religion': 'Yes' if user1.religion != user2.religion else 'No'
    }

    df = pd.DataFrame([data])[FEATURES]

    # Force exact same dtype setup as training
    for col in CATEGORICAL_COLS:
        df[col] = df[col].astype("category")
    df['Age_at_Marriage'] = pd.to_numeric(df['Age_at_Marriage'], errors='coerce')

    # Direct LightGBM Booster predict call (it handles categorical internally)
    prediction = model.predict(df, num_iteration=model.best_iteration)

    if prediction.ndim > 1:
        predicted_index = int(prediction.argmax(axis=1)[0])
    else:
        predicted_index = int(prediction[0])

    predicted_label = CLASS_MAP[predicted_index]
    return jsonify({
        "user1": user1.name,
        "user2": user2.name,
        "features": data,
        "predicted_class": predicted_label
    })
