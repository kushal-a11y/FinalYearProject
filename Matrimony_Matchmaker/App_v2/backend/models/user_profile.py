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
    matches = db.Column('Matches', JSON, default=list)

    # Applicable for user registration
    name = db.Column('Name', db.String(100), nullable=True)
    email = db.Column('Email', db.String(100), nullable=True)
    password = db.Column('Password', db.String(255), nullable=True)
    last_logged_in = db.Column('LastLoggedIn', db.DateTime, nullable=True)

    # --- NEW: contact + media + identity verification ---
    phone = db.Column('Phone', db.String(20), nullable=True)
    image_filename = db.Column('ImageFilename', db.String(255), nullable=True)

    pan_number = db.Column('PanNumber', db.String(10), nullable=True, unique=True)
    pan_holder_name = db.Column('PanHolderName', db.String(120), nullable=True)
    pan_verified = db.Column('PanVerified', db.Boolean, default=False)
    pan_verified_at = db.Column('PanVerifiedAt', db.DateTime, nullable=True)

    preference = db.relationship('PreferenceProfile', backref='user', uselist=False, cascade="all, delete")

    @property
    def profile_complete(self):
        # Profile is complete if all these fields are filled
        required_fields = ['name', 'age', 'gender', 'education', 'caste',
                           'profession', 'religion', 'residence', 'height_cm']
        return all(getattr(self, f) for f in required_fields)

    @property
    def is_verified(self):
        return bool(self.pan_verified)

    @property
    def image_url(self):
        if self.image_filename:
            return f"/user/profile-image/{self.user_id}"
        return None

    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, gender={self.gender}, profession={self.profession})>"
