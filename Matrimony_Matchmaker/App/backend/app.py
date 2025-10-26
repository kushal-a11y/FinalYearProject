from flask import Flask,render_template,jsonify, redirect, url_for
from db import app, db
import random, string
from models.user_profile import UserProfile
from datetime import datetime
from models.preference_profile import PreferenceProfile
from services.data_insertion import insert_user_profiles, insert_preference_profiles

from routes.user_routes import user_bp

app.register_blueprint(user_bp, url_prefix='/user')

@app.route('/')
def home():
    return "💍 Matrimonial Matchmaking API is running!"

@app.route('/registerMe')
def registerMe():
    return render_template('register.html')



@app.route('/admin/dashboard')
def admin_dashboard():
    try:
        all_users = db.session.execute(
            db.select(UserProfile).options(db.load(UserProfile.preference))
        ).scalars().all()
        
        return render_template('admin_dashboard.html', users=all_users)
        
    except Exception as e:
        # Simple error handling for database issues
        return f"Database Error: Could not fetch data. Ensure tables are created and data is inserted. Error: {e}", 500

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
    app.run(debug=True)
