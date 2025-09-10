import pandas as pd
from db import get_connection

def load_profiles():
    df = pd.read_csv("./dataset/processed_vivah_profiles.csv")

    conn = get_connection()
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO profile
            (`religion`, `caste`, `mother_tongue`, `profession`, `education`, `age`, 
             `height_cm`, `height_ft_in`, `country`, `state`, `city`, `gender`, 
             `income`, `independency`, `previous_marriage`, `addiction`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row["Religion"],
            row["Caste"],
            row["Mother Tongue"],     
            row["Profession"],
            row["Education"],
            int(row["Age"]) if not pd.isna(row["Age"]) else None,
            int(row["Height in cm"]) if not pd.isna(row["Height in cm"]) else None,
            row["Height_ft_in"],
            row["Country"],
            row["State"],
            row["City"],
            row["Gender"],
            row["Income"],
            row["Independency"],
            int(row["Previous Marriage"]) if not pd.isna(row["Previous Marriage"]) else 0,
            row["Addiction"]
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print("Profiles uploaded successfully")

if __name__ == "__main__":
    load_profiles()
