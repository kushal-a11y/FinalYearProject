import pandas as pd
from db import db
from models.user_profile import UserProfile
from models.preference_profile import PreferenceProfile

def insert_user_profiles(filepath):
    df = pd.read_csv(filepath).head(100)
    df.replace(['', 'N/A', 'n/a', '-', ' '], pd.NA, inplace=True)
    df = df.where(pd.notna(df), None)
    for _, row in df.iterrows():
        user = UserProfile(
            age=row['Age'],
            gender=row['Gender'],
            education=row['Education'],
            caste=row['Caste'],
            profession=row['Profession'],
            religion=row['Religion'],
            residence=row['Residence'],
            height_cm=row['Height_cm'],
            extras={},      # placeholder JSON
            matches=[]
        )
        db.session.add(user)
    db.session.commit()
    print("100 User Profiles inserted successfully!")


def insert_preference_profiles(filepath):
    df = pd.read_csv(filepath).head(100)
    df.replace(['', 'N/A', 'n/a', '-', ' '], pd.NA, inplace=True)
    df = df.where(pd.notna(df), None)

    for _, row in df.iterrows():
        pref = PreferenceProfile(
            age=row['Age'],
            gender=row['Gender'],
            education=row['Education'],
            caste=row['Caste'],
            profession=row['Profession'],
            residence=row['Residence'],
            religion=row['Religion'],
            height_cm=row['Height_cm'],
            extras={},
            user_id=row['userID']
        )
        db.session.add(pref)
    db.session.commit()
    print("100 Preference Profiles inserted successfully!")
