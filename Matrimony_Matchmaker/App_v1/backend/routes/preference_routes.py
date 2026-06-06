from flask import Blueprint, render_template, request, jsonify
from db import db
from models.preference_profile import PreferenceProfile

preference_bp = Blueprint('preference', __name__)

@preference_bp.route('/preferences/json/<int:user_id>', methods=['GET'])
def get_preferences_json(user_id):
    pref = PreferenceProfile.query.filter_by(user_id=user_id).first()
    if not pref:
        return jsonify({}), 404

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
    return jsonify(pref_data), 200


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

    # lists for autocomplete
    castes = list({
        "Brahmin","SC","OBC","Baisya","Kayastha","Banerjee","General","Tili",
        "Barujibi","Kumbhakar","Swarnakar","Napit","Namasudra","Sunni","Sadgop",
        "Goala","Kandi","Tambuli","Mukherjee","Roy","Biswas","Chatterjee",
        "Dutta","Banik","Ganguly","Bhattacharya","Aguri","Malakar","Yadav"
    })

    degrees = list({
        'B.Tech MBA','MBA','B.Tech','BSc','BA','MA B.Ed','MA','MSC B.Ed',
        'BA B.Ed','PhD','Bcom','LLB','LLM','MBBS','M.Tech','PHD','M.Tech',
        'M.SC','B.com','IIT','NIT'
    })

    professions = list({
        'B.Tech 10LPA', 'MBA 12LPA', 'B.Tech 15LPA', 'MBA 35LPA', 'MNC 18LPA', 'MNC 9LPA',
        'Working at Indian Oil 14LPA', 'Project Manager at IBM-35LPA', 'B.Tech MBA Pvt 10LPA',
        'M.Teach 14LPA', 'MNC-IT', 'MNC', 'IT', 'Researcg-Scholar-germany', 'Business', 'Bank',
        "Pharma Co B'loe", 'Law Firm', 'Advocate', 'College lecturer', "Digital Marketting B'lore",
        'Officer in Central Govt.', 'Asst Professor', 'Asst Professor in Govt College', 'Working at TCS',
        'MBA-10LPA', 'IT Engineer(U.K.)', 'Professor', 'Working IN U.S.', 'Railway Asst. Engineer',
        'Govt job', 'Bank Manager'
    })

    return render_template(
        'preferences.html',
        user_id=user_id,
        preferences=pref_data,
        castes=castes,
        degrees=degrees,
        professions=professions
    )


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
