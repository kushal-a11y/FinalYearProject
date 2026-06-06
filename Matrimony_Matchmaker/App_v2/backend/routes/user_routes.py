import os
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify, render_template, send_file, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_mail import Message

from db import db, mail
from models.user_profile import UserProfile
from models.preference_priority import PreferencePriority
from services.flat_match import mutual_flat_match
from services.match_predictor import get_user_profile_helper, predict_match
from services.pan_verification import verify_pan, PanValidationError, PAN_ENTITY_TYPES

load_dotenv()

priority_bp = Blueprint("priority", __name__)
user_bp = Blueprint('user', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def _upload_dir():
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'uploads', 'profile_images')
    os.makedirs(base, exist_ok=True)
    return base


def _allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


# ===================== AUTH =====================
@user_bp.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    phone = (data.get('phone') or '').strip() or None

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    if UserProfile.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    new_user = UserProfile(email=email, password=generate_password_hash(password), phone=phone)
    db.session.add(new_user)
    db.session.commit()

    try:
        msg = Message(
            subject="Welcome to Matrimony Portal",
            sender=os.getenv('MAIL_USERNAME'),
            recipients=[email],
            body=(f"Hello!\n\nYour Matrimony account has been created.\n"
                  f"User ID: {new_user.user_id}\n\n"
                  f"Use your email and password to log in and complete your profile.")
        )
        mail.send(msg)
    except Exception as e:
        print("Email sending failed:", str(e))

    return jsonify({
        'message': 'Registration successful! Check your email for your User ID.',
        'user_id': new_user.user_id
    }), 201


@user_bp.route('/loginPage')
def loginPage():
    return render_template('login.html')


@user_bp.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = UserProfile.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    user.last_logged_in = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Login successful',
        'user_id': user.user_id,
        'profile_complete': all([user.name, user.age, user.gender, user.education,
                                 user.caste, user.profession, user.religion,
                                 user.residence, user.height_cm])
    }), 200


# ===================== PROFILE =====================
@user_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = UserProfile.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        "user_id": user.user_id, "name": user.name, "age": user.age,
        "gender": user.gender, "education": user.education,
        "profession": user.profession, "caste": user.caste,
        "religion": user.religion, "residence": user.residence,
        "height_cm": user.height_cm, "phone": user.phone, "email": user.email,
        "image_url": user.image_url, "verified": bool(user.pan_verified),
    }), 200


@user_bp.route('/complete-profile/<int:user_id>', methods=['GET'])
def show_complete_profile(user_id):
    user = UserProfile.query.get(user_id)
    if not user:
        return "User not found", 404
    return render_template('complete_profile.html', user_id=user.user_id, user=user)


@user_bp.route('/complete-profile/<int:user_id>', methods=['POST'])
def complete_profile(user_id):
    user = UserProfile.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    for key in ['name', 'age', 'gender', 'education', 'caste', 'profession',
                'religion', 'residence', 'height_cm', 'phone']:
        if key in data and data[key] not in (None, ''):
            setattr(user, key, data[key])

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200


@user_bp.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    user = UserProfile.query.get(user_id)
    if not user:
        return "User not found", 404
    return render_template('dashboard.html', user=user)


# ===================== PROFILE IMAGE =====================
@user_bp.route('/upload-image/<int:user_id>', methods=['POST'])
def upload_image(user_id):
    user = UserProfile.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not _allowed_image(file.filename):
        return jsonify({'error': 'Unsupported file type. Use PNG, JPG, WEBP or GIF.'}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_IMAGE_BYTES:
        return jsonify({'error': 'Image too large (max 5 MB).'}), 400

    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    fname = f"user_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
    path = os.path.join(_upload_dir(), fname)

    if user.image_filename:
        old = os.path.join(_upload_dir(), user.image_filename)
        if os.path.exists(old):
            try:
                os.remove(old)
            except OSError:
                pass

    file.save(path)
    user.image_filename = fname
    db.session.commit()
    return jsonify({'message': 'Image uploaded', 'image_url': user.image_url}), 200


@user_bp.route('/profile-image/<int:user_id>', methods=['GET'])
def profile_image(user_id):
    user = UserProfile.query.get(user_id)
    if not user or not user.image_filename:
        abort(404)
    path = os.path.join(_upload_dir(), user.image_filename)
    if not os.path.exists(path):
        abort(404)
    return send_file(path)


# ===================== PAN VERIFICATION =====================
@user_bp.route('/pan-status/<int:user_id>', methods=['GET'])
def pan_status(user_id):
    user = UserProfile.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'verified': bool(user.pan_verified),
        'pan_masked': (f"{user.pan_number[:2]}XXXXX{user.pan_number[-1]}"
                       if user.pan_number else None),
        'verified_at': user.pan_verified_at.isoformat() if user.pan_verified_at else None,
        'entity_types': PAN_ENTITY_TYPES,
    }), 200


@user_bp.route('/verify-pan/<int:user_id>', methods=['POST'])
def verify_pan_route(user_id):
    user = UserProfile.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    pan = data.get('pan')
    full_name = (data.get('full_name') or user.name or '').strip()
    surname = (data.get('surname') or '').strip()
    if not surname and full_name:
        surname = full_name.split()[-1]

    try:
        result = verify_pan(pan, surname=surname, full_name=full_name or None)
    except PanValidationError as e:
        return jsonify({'verified': False, 'error': str(e)}), 400

    clash = (UserProfile.query
             .filter(UserProfile.pan_number == result['pan'],
                     UserProfile.user_id != user_id)
             .first())
    if clash:
        return jsonify({'verified': False,
                        'error': 'This PAN is already linked to another account.'}), 409

    user.pan_number = result['pan']
    user.pan_holder_name = result.get('registered_name') or full_name or None
    user.pan_verified = True
    user.pan_verified_at = result.get('verified_at') or datetime.utcnow()
    db.session.commit()

    return jsonify({
        'verified': True,
        'message': 'PAN verified successfully.',
        'entity_type': result.get('entity_type'),
        'method': result.get('method'),
        'pan_masked': f"{result['pan'][:2]}XXXXX{result['pan'][-1]}",
    }), 200


# ===================== PRIORITIES =====================
@priority_bp.route("/get-priority/<int:user_id>", methods=["GET"])
def get_priority(user_id):
    user = UserProfile.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    priority = PreferencePriority.query.filter_by(user_id=user_id).first()
    if not priority:
        return jsonify({"user_id": user_id, "age_priority": 1, "religion_priority": 1,
                        "caste_priority": 1, "education_priority": 1,
                        "profession_priority": 1, "residence_priority": 1}), 200
    return jsonify(priority.to_dict()), 200


@priority_bp.route("/set-priority/<int:user_id>", methods=["POST"])
def set_priority(user_id):
    user = UserProfile.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json() or {}
    priority = PreferencePriority.query.filter_by(user_id=user_id).first()
    if not priority:
        priority = PreferencePriority(user_id=user_id)
        db.session.add(priority)
    for field in ["age_priority", "religion_priority", "caste_priority",
                  "education_priority", "profession_priority", "residence_priority"]:
        setattr(priority, field, int(data.get(field, 5)))
    db.session.commit()
    return jsonify({"message": "Priorities saved successfully"}), 200


# ===================== MATCHING =====================
@user_bp.route('/flat-match/<int:user_id>', methods=['GET'])
def get_flat_match(user_id):
    try:
        return jsonify(mutual_flat_match(user_id)), 200
    except Exception as e:
        print("Flat match error:", e)
        return jsonify({'error': str(e)}), 500


@user_bp.route('/flatmatch-results/<int:user_id>')
def flatmatch_results(user_id):
    return render_template('flatmatch_results.html', user_id=user_id)


@user_bp.route('/get_user', methods=['GET'])
def get_user():
    identifier = (request.args.get('id') or request.args.get('username') or
                  request.args.get('email') or request.args.get('input'))
    if not identifier:
        return jsonify({"error": "Provide id, name, or email"}), 400
    user = get_user_profile_helper(identifier)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "user_id": user.user_id, "name": user.name, "email": user.email,
        "age": user.age, "gender": user.gender, "education": user.education,
        "caste": user.caste, "profession": user.profession,
        "religion": user.religion, "residence": user.residence,
        "height_cm": user.height_cm, "phone": user.phone,
        "image_url": user.image_url, "verified": bool(user.pan_verified),
        "extras": user.extras, "matches": user.matches,
    })


@user_bp.route('/predict-match', methods=['POST'])
def predict_match_route():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    male_id = data.get("male_id")
    female_id = data.get("female_id")
    if not male_id or not female_id:
        return jsonify({"error": "Please provide both male_id and female_id"}), 400
    return predict_match(str(male_id), str(female_id))
