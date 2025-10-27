from flask import Blueprint, render_template, request, jsonify
from db import db
from models.preference_profile import PreferenceProfile

preference_bp = Blueprint('preference', __name__)

@preference_bp.route('/preferences/<int:user_id>', methods=['GET'])
def preferences_page(user_id):
    pref = PreferenceProfile.query.filter_by(user_id=user_id).first()

    if pref:
        pref_data = {
            "age": pref.age,
            "gender": pref.gender,
            "education": pref.education,
            "caste": pref.caste,
            "profession": pref.profession,
            "residence": pref.residence,
            "religion": pref.religion,
            "height_cm": pref.height_cm
        }
    else:
        pref_data = {}

    return render_template('preferences.html', user_id=user_id, preferences=pref_data)


@preference_bp.route('/preferences/<int:user_id>', methods=['POST'])
def save_preferences(user_id):
    data = request.get_json()
    
    # Fetch existing preference record
    pref = PreferenceProfile.query.filter_by(user_id=user_id).first()
    if not pref:
        pref = PreferenceProfile(user_id=user_id)
        db.session.add(pref)

    # Map frontend fields to model columns
    # Combine min/max age into age string
    if 'preferred_age_min' in data or 'preferred_age_max' in data:
        min_age = data.get('preferred_age_min', '')
        max_age = data.get('preferred_age_max', '')
        pref.age = f"{min_age} - {max_age}" if min_age or max_age else None

    # Direct mappings
    if 'preferred_gender' in data:
        pref.gender = data['preferred_gender']
    if 'preferred_education' in data:
        pref.education = data['preferred_education']
    if 'preferred_caste' in data:
        pref.caste = data['preferred_caste']
    if 'preferred_profession' in data:
        pref.profession = data['preferred_profession']
    if 'preferred_residence' in data:
        pref.residence = data['preferred_residence']
    if 'preferred_religion' in data:
        pref.religion = data['preferred_religion']
    if 'preferred_height_cm' in data:
        pref.height_cm = data['preferred_height_cm']

    # Store any other extra preferences in JSON
    extras = {k: v for k, v in data.items() if k not in [
        'preferred_age_min','preferred_age_max','preferred_gender',
        'preferred_education','preferred_caste','preferred_profession',
        'preferred_residence','preferred_religion','preferred_height_cm'
    ]}
    pref.extras = extras if extras else None

    db.session.commit()

    return jsonify({'message': 'Preferences saved successfully', 'user_id': user_id}), 200
