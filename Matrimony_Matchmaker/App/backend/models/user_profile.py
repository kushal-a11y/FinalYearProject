from db import db
from sqlalchemy.dialects.mysql import JSON

class UserProfile(db.Model):
    __tablename__ = 'user_profile'

    user_id = db.Column('UserID', db.Integer, primary_key=True, autoincrement=True)
    age = db.Column('Age', db.Integer)
    gender = db.Column('Gender', db.String(10))
    education = db.Column('Education', db.String(50))
    caste = db.Column('Caste', db.String(50))
    profession = db.Column('Profession', db.String(50))
    religion = db.Column('Religion', db.String(50))
    residence = db.Column('Residence', db.String(50))
    height_cm = db.Column('Height_cm', db.Float)
    extras = db.Column('Extras', JSON)
    matches = db.Column('Matches', JSON)

    #Applicable for user registration
    name = db.Column('Name', db.String(100), nullable=True)
    email = db.Column('Email', db.String(100), nullable=True)
    password = db.Column('Password', db.String(255), nullable=True)
    last_logged_in = db.Column('LastLoggedIn', db.DateTime, nullable=True)
    
    preference = db.relationship('PreferenceProfile', backref='user', uselist=False, cascade="all, delete")

    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, gender={self.gender}, profession={self.profession})>"
