import os
from db import db,app
from mail import mail
from flask import Flask,jsonify
from datetime import date
from flask_mail import Message
from dotenv import load_dotenv
from models import User,Profile

load_dotenv()

#Database test
@app.route("/test-db")
def test_db():
    try:
        with db.engine.connect() as conn:
            result = conn.execute(db.text("SELECT NOW();"))
            return f"Current time: {list(result)[0][0]}"
    except:
        return "Database connection failed."

#Mail_test
@app.route("/check-mail")
def check_mail():
    try:    
        msg = Message(
            subject="Flask Mail Test",
            sender=os.getenv('MAIL_USERNAME'),
            recipients=['kushalstcet666@gmail.com'],  # put your email here
            body="Hello! This is a test email from Flask-Mail."
        )
        mail.send(msg)
        return "Mail Sent Successfully."
    except Exception as e:
        return f"Mail sending failed: {e}"

@app.route("/init-db")
def create_tables():
    try:
        with app.app_context():
            db.create_all()
        return jsonify({"message": "Database tables created successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/insert-user-profile", methods=["POST"])
def insert_user_profile():
    try:
        user = User(username="kushal")
        db.session.add(user)
        db.session.flush() 

        profile = Profile(
            bio="Full Stack Developer",
            dob=date(2000, 3, 14),
            userid=user.userid
        )

        db.session.add(profile)
        db.session.commit()

        return jsonify({
            "message": "User & Profile inserted successfully",
            "user_id": user.userid,
            "age": profile.calculate_age
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__=="__main__":
    app.run(debug=True)
