from flask import Flask,render_template,jsonify, redirect, url_for
from db import app, db
from sqlalchemy.orm import joinedload
import random, string
from models.user_profile import UserProfile
from datetime import datetime
from models.preference_profile import PreferenceProfile
from services.data_insertion import insert_user_profiles, insert_preference_profiles

from routes.user_routes import user_bp,priority_bp
from routes.preference_routes import preference_bp

app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(priority_bp, url_prefix="/priority")
app.register_blueprint(preference_bp, url_prefix='/preference')

@app.route('/')
def home():
    return redirect(url_for('registerPage'))

@app.route('/registerPage')
def registerPage():
    return render_template('register.html')


@app.route('/complete_profile/<int:user_id>')
def complete_profile(user_id):
    return render_template('complete_profile.html', user_id=user_id)

@app.route('/admin/dashboard')
def admin_dashboard():
    try:
        all_users = (
            db.session.query(UserProfile)
            .options(joinedload(UserProfile.preference))
            .all()
        )
        return render_template('admin_dashboard.html', users=all_users)
    except Exception as e:
        return f"Database Error: {e}", 500

@app.route('/init-db')
def init_db():
    db.create_all()
    return "Tables created successfully!"

@app.route('/insert-data')
def insert_data():
    insert_user_profiles('D:/FinalYearProject/Matrimony_Matchmaker/App/backend/uploads/user_profiles.csv')
    insert_preference_profiles('D:/FinalYearProject/Matrimony_Matchmaker/App/backend/uploads/user_preferences.csv')
    return "Inserted 100 records from Excel files!"


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)