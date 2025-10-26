from flask import Blueprint, render_template, request, jsonify
from db import db
from models.preference_profile import PreferenceProfile

preference_bp = Blueprint('preference', __name__)

@preference_bp.route('/preferences/<int:user_id>')
def preferences_page(user_id):
    # Fetch existing preferences if any
    pref = PreferenceProfile.query.filter_by(user_id=user_id).first()
    return render_template('preferences.html', user_id=user_id, preferences=pref)

@preference_bp.route('/preferences/<int:user_id>', methods=['POST'])
def save_preferences(user_id):
    data = request.get_json()
    pref = PreferenceProfile.query.filter_by(user_id=user_id).first()
    
    if not pref:
        pref = PreferenceProfile(user_id=user_id)
        db.session.add(pref)

    # Update preference fields
    for key, value in data.items():
        setattr(pref, key, value)

    db.session.commit()
    return jsonify({'message': 'Preferences saved successfully', 'user_id': user_id}), 200
