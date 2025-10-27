from flask import Blueprint, request, jsonify,render_template
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_mail import Message
from db import db, mail
from models.user_profile import UserProfile
from services.flat_match import mutual_flat_match


user_bp = Blueprint('user', __name__)

# Always use @user_bp.route instead of @app.route

@user_bp.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    existing_user = UserProfile.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'Email already registered'}), 400

    hashed_pw = generate_password_hash(password)
    new_user = UserProfile(email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

    # Send confirmation email
    try:
        msg = Message(
            subject="Welcome to Matrimony Portal",
            recipients=[email],
            body=f"Hello!\n\nYour Matrimony account has been created.\nUser ID: {new_user.user_id}\nPassword: {password}\n\nUse these credentials to log in and complete your profile."
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
        'profile_complete': all([user.name, user.age, user.gender, user.education, user.caste, user.profession, user.religion, user.residence, user.height_cm])
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
    for key in ['name', 'age', 'gender', 'education', 'caste', 'profession', 'religion', 'residence', 'height_cm']:
        if key in data:
            setattr(user, key, data[key])

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200

@user_bp.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    user = UserProfile.query.get(user_id)
    if not user:
        return "User not found", 404
    return render_template('dashboard.html', user=user)

@user_bp.route('/flat-match/<int:user_id>', methods=['GET'])
def get_flat_match(user_id):
    try:
        result = mutual_flat_match(user_id)
        return jsonify(result), 200
    except Exception as e:
        print("Flat match error:", e)
        return jsonify({'error': str(e)}), 500

@user_bp.route('/flatmatch-results/<int:user_id>')
def flatmatch_results(user_id):
    return render_template('flatmatch_results.html', user_id=user_id)

