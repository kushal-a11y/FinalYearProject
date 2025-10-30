from db import db

class PreferencePriority(db.Model):
    __tablename__ = "preference_priorities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profile.UserID'), unique=True, nullable=False)

    age_priority = db.Column(db.Integer, default=1)
    religion_priority = db.Column(db.Integer, default=1)
    caste_priority = db.Column(db.Integer, default=1)
    education_priority = db.Column(db.Integer, default=1)
    profession_priority = db.Column(db.Integer, default=1)
    residence_priority = db.Column(db.Integer, default=1)

    user = db.relationship("UserProfile", backref=db.backref("priority_profile", uselist=False))

    def to_dict(self):
        """Return as JSON-ready dict."""
        return {
            "user_id": self.user_id,
            "age_priority": self.age_priority,
            "religion_priority": self.religion_priority,
            "caste_priority": self.caste_priority,
            "education_priority": self.education_priority,
            "profession_priority": self.profession_priority,
            "residence_priority": self.residence_priority
        }
