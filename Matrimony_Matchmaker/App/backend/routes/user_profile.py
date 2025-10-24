#User registration, login, profile
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_mail import Mail, Message
from db import db, app
from models.user_profile import UserProfile

mail = Mail(app)

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='yourmail@gmail.com',
    MAIL_PASSWORD='your_app_password'
)
mail = Mail(app)


@app.route('/register', methods=['POST'])
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

    try:
        msg = Message(
            subject="Welcome to Matrimony Portal",
            recipients=[email],
            body=f"Hello!\n\nYour Matrimony account has been created.\n\nUser ID: {new_user.user_id}\nPassword: {password}\n\nUse these credentials to log in and complete your profile."
        )
        mail.send(msg)
    except Exception as e:
        print("Email sending failed:", e)

    return jsonify({
        'message': 'Registration successful! Check your email for your User ID.',
        'user_id': new_user.user_id
    }), 201


@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = UserProfile.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid email or password'}), 401

    user.last_logged_in = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Login successful',
        'user_id': user.user_id
    }), 200


@app.route('/complete-profile/<int:user_id>', methods=['POST'])
def complete_profile(user_id):
    user = UserProfile.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    # Only update non-null fields
    for key in ['name', 'age', 'gender', 'education', 'caste', 'profession', 'religion', 'residence', 'height_cm']:
        if key in data:
            setattr(user, key, data[key])

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200
