from db import db
from sqlalchemy.dialects.mysql import JSON

class PreferenceProfile(db.Model):
    __tablename__ = 'preference_profile'

    preference_id = db.Column('PreferenceID', db.Integer, primary_key=True, autoincrement=True)
    age = db.Column('Age', db.String(20))
    gender = db.Column('Gender', db.String(10))
    education = db.Column('Education', db.String(50))
    caste = db.Column('Caste', db.String(50))
    profession = db.Column('Profession', db.String(50))
    residence = db.Column('Residence', db.String(50))
    religion = db.Column('Religion', db.String(50))
    height_cm = db.Column('Height_cm', db.String(20))
    extras = db.Column('Extras', JSON)

    user_id = db.Column('UserID', db.Integer, db.ForeignKey('user_profile.UserID', ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f"<PreferenceProfile(preference_id={self.preference_id}, user_id={self.user_id})>"
