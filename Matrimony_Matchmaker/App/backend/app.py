from flask import Flask,render_template,jsonify, redirect, url_for
from db import app, db
from models.user_profile import UserProfile
from models.preference_profile import PreferenceProfile
from services.data_insertion import insert_user_profiles, insert_preference_profiles

@app.route('/')
def home():
    return "💍 Matrimonial Matchmaking API is running!"

@app.route('/admin/dashboard')
def admin_dashboard():
    try:
        all_users = db.session.execute(
            db.select(UserProfile).options(db.joinedload(UserProfile.preference))
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

@app.route('/update-religion', methods=['GET'])
def update_religion():
    """
    Updates religion of all users in the database based on their assigned caste.
    After update, redirects back to the admin dashboard.
    """
    try:
        users = UserProfile.query.all()
        updated_count = 0

        for user in users:
            caste = (user.caste or "").strip().lower()

            if caste == "sunni":
                user.religion = "Muslim"
            elif caste in [
                "brahmin", "sc", "obc", "baisya", "kayastha", "banerjee", "general",
                "tili", "barujibi", "kumbhakar", "swarnakar", "napit", "namasudra",
                "sadgop", "goala", "kandi", "tambuli", "mukherjee", "roy", "biswas",
                "chatterjee", "dutta", "banik", "ganguly", "bhattacharya", "aguri",
                "malakar", "yadav"
            ]:
                user.religion = "Hindu"
            elif caste:
                user.religion = "Other"
            else:
                user.religion = None

            updated_count += 1

        db.session.commit()

        # optional flash message or redirect back to dashboard
        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        db.session.rollback()
        return f"Error updating religions: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
