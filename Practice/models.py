from db import db
from datetime import date

class User(db.Model):
    __tablename__="users"

    userid = db.Column("userid", db.Integer, primary_key=True, autoincrement=True)
    username = db.Column("username", db.String(40))
    profile = db.relationship("Profile",backref="users",cascade="all,delete",uselist=False)
    def __repr__(self):
        return f"User{self.id} || username = {self.username}"

class Profile(db.Model):
    __tablename__="profiles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bio = db.Column(db.String(250), nullable=True)
    dob = db.Column(db.Date, nullable=True)

    userid = db.Column(db.Integer, db.ForeignKey("users.userid"), nullable=False, unique=True)

    @property
    def calculate_age(self):
        if not self.dob:
            return None
        today = date.today()
        return today.year - self.dob.year - (
            (today.month, today.day) < (self.dob.month, self.dob.day)
        )
       