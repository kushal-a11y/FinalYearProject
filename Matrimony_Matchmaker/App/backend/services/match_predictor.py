import joblib
import pandas as pd
import numpy as np
from flask import jsonify
from models.user_profile import UserProfile # Assuming this is your DB model

# =====================================================================
# 1. LOAD MODEL ARTIFACTS
# =====================================================================
# Load the trained XGBoost model and the exact list of feature columns
MODEL_PATH = r"C:\Users\Administrator\OneDrive\Desktop\FYP_Resources\X_GBOOST\Clustering + rule based(69.35%)\final_xgboost_deterministic_model.pkl"
COLS_PATH = r"C:\Users\Administrator\OneDrive\Desktop\FYP_Resources\Encoders\model_feature_columns.pkl"

model = joblib.load(MODEL_PATH)
model_features = joblib.load(COLS_PATH) # This contains all the "State_West Bengal", etc. columns

CLASS_MAP = {
    0: "Stable / Safe (High Compatibility)",
    1: "High Risk / Unstable (Low Compatibility)"
}

# =====================================================================
# 2. DOMAIN MAPPING FUNCTIONS (Platform -> DHS Format)
# =====================================================================
# The DHS model doesn't know what a "B.Tech" is. It knows "Higher Secondary", 
# "Post-Graduate", etc. We must map your platform's specific strings to DHS categories.

def map_education(degree_str):
    """Maps custom matrimonial degrees to DHS Education Levels."""
    if not degree_str: return "Secondary or below"
    degree_str = degree_str.upper()
    
    post_grad = ['MBA', 'M.TECH', 'PHD', 'MA', 'MSC', 'LLM', 'MD']
    higher_sec = ['B.TECH', 'BSC', 'BA', 'BCOM', 'MBBS', 'LLB', 'IIT', 'NIT']
    
    if any(deg in degree_str for deg in post_grad):
        return "Post-Graduate (MBA/MA)"
    elif any(deg in degree_str for deg in higher_sec):
        return "Higher Secondary"
    return "Secondary or below"

def map_occupation(job_str):
    """Maps custom matrimonial jobs/salaries to DHS Occupation Groups."""
    if not job_str: return "Not working"
    job_str = job_str.upper()
    
    prof_tech = ['MNC', 'IT', 'MANAGER', 'PROFESSOR', 'ENGINEER', 'GOVT', 'BANK', 'OFFICER']
    clerical = ['CLERK', 'DATA ENTRY']
    sales = ['BUSINESS', 'MARKETING', 'SALES']
    
    if any(job in job_str for job in prof_tech): return "Professional / technical / managerial"
    if any(job in job_str for job in clerical): return "Clerical"
    if any(job in job_str for job in sales): return "Sales"
    return "Other"

def map_ethnicity(caste_str):
    """Maps custom castes to DHS Ethnicity Groups."""
    if not caste_str: return "Don't know"
    caste_str = caste_str.upper()
    
    # Map General/Upper castes to "No caste / tribe"
    general = ['BRAHMIN', 'KAYASTHA', 'GENERAL', 'BANERJEE', 'MUKHERJEE', 'BAISYA']
    if any(c in caste_str for c in general): return "No caste / tribe"
    if 'SC' in caste_str or 'OBC' in caste_str: return "Tribe" # Assuming DHS bundled these
    
    return "Other"

# =====================================================================
# 3. HELPER FUNCTIONS
# =====================================================================
def get_user_profile_helper(identifier):
    if identifier.isdigit():
        return UserProfile.query.filter_by(user_id=int(identifier)).first()
    elif "@" in identifier:
        return UserProfile.query.filter_by(email=identifier).first()
    else:
        return UserProfile.query.filter_by(name=identifier).first()

# =====================================================================
# 4. MAIN PREDICTION ENDPOINT
# =====================================================================
def predict_match(male_id, female_id):
    if not male_id or not female_id:
        return jsonify({"error": "Please provide both male and female identifiers"}), 400

    male = get_user_profile_helper(male_id)
    female = get_user_profile_helper(female_id)
    
    if not male or not female:
        return jsonify({"error": "One or both users not found"}), 404

    # ---------------------------------------------------------
    # STEP A: Create a DataFrame with 1 row, completely filled with 0s.
    # The columns MUST perfectly match the saved model_features list.
    # ---------------------------------------------------------
    df_infer = pd.DataFrame(0, index=[0], columns=model_features)

    # ---------------------------------------------------------
    # STEP B: Fill in the Continuous (Numerical) Variables
    # ---------------------------------------------------------
    # Using .get() or direct attribute access based on your DB schema
    df_infer.at[0, 'Husband_age'] = float(male.age)
    df_infer.at[0, "Wife's_current_age"] = float(female.age)
    df_infer.at[0, "Wife's height(centimeters)"] = float(female.height) if hasattr(female, 'height') else 155.0

    # ---------------------------------------------------------
    # STEP C: Map and trigger the Categorical Dummy Variables (1s)
    # ---------------------------------------------------------
    # We figure out what DHS category they belong to, build the exact dummy 
    # column string (e.g., "State_West Bengal"), and if that column exists 
    # in the model's feature list, we flip its value from 0 to 1.
    
    features_to_map = {
        "Husband's Education Level": map_education(male.education),
        "Wife's Education Level": map_education(female.education),
        "Husband Occupation_(grouped)": map_occupation(male.profession),
        "Wife's_occupation_(grouped)": map_occupation(female.profession),
        "Husband Ethnicity": map_ethnicity(male.caste),
        "Wife's Ethnicity": map_ethnicity(female.caste),
        "Husband Religion": male.religion if male.religion else "Hindu",
        "Wife's Religion": female.religion if female.religion else "Hindu",
        "residence": male.residence if male.residence else "Urban",
        "State": male.state if hasattr(male, 'state') and male.state else "West Bengal"
    }

    for base_feature, category_val in features_to_map.items():
        # Construct the dummy column name exactly as pd.get_dummies does it
        dummy_col_name = f"{base_feature}_{category_val}"
        
        # If the column exists (meaning it wasn't dropped as the 'first' baseline)
        if dummy_col_name in df_infer.columns:
            df_infer.at[0, dummy_col_name] = 1

    # ---------------------------------------------------------
    # STEP D: Execute Prediction
    # ---------------------------------------------------------
    # XGBoost handles this 1-row matrix effortlessly
    prediction = model.predict(df_infer)
    prediction_prob = model.predict_proba(df_infer)[0] # Get confidence scores
    
    predicted_index = int(prediction[0])
    predicted_label = CLASS_MAP[predicted_index]

    return jsonify({
        "male_profile": male.user_id if male.name is None else male.name,
        "female_profile": female.user_id if female.name is None else female.name,
        "prediction_result": predicted_label,
        "risk_probability": f"{prediction_prob[1] * 100:.1f}%",
        "stability_probability": f"{prediction_prob[0] * 100:.1f}%"
    })