import pandas as pd
from db import db
from models.user_profile import UserProfile
from models.preference_profile import PreferenceProfile

# ---------- USER PROFILE INSERTION ----------
def insert_user_profiles(filepath):
    # Load and clean CSV
    df = pd.read_csv(filepath)
    df.replace(['', 'N/A', 'n/a', '-', ' '], pd.NA, inplace=True)
    df = df.where(pd.notna(df), None)

    # Select first 200 rows
    batch_df = df.head(200)

    # Insert into database
    for _, row in batch_df.iterrows():
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
    print("200 User Profiles inserted successfully!")

    # Remove inserted rows from CSV
    remaining_df = df.iloc[200:]
    remaining_df.to_csv(filepath, index=False)
    print("First 200 rows deleted from the CSV file.")


# ---------- PREFERENCE PROFILE INSERTION ----------
def insert_preference_profiles(filepath):
    # Load and clean CSV
    df = pd.read_csv(filepath)
    df.replace(['', 'N/A', 'n/a', '-', ' '], pd.NA, inplace=True)
    df = df.where(pd.notna(df), None)

    # Select first 200 rows
    batch_df = df.head(200)

    # Insert into database
    for _, row in batch_df.iterrows():
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
    print("200 Preference Profiles inserted successfully!")

    # Remove inserted rows from CSV
    remaining_df = df.iloc[200:]
    remaining_df.to_csv(filepath, index=False)
    print("First 200 rows deleted from the CSV file.")
