from flask import Flask, request, jsonify
from db import get_connection

app = Flask(__name__)

@app.route("/api/Admin/profiles", methods=["GET"])
def getProfiles():
    conn = db.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM profiles")
    profiles = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(profiles)

@app.route("/api/profiles/search", methods=["POST",])
def search_partner():
    filters = request.json
    query = "SELECT * from profiles where 1=1"
    params = []

    # Religion
    if "Religion" in filters:
        query += " AND religion = %s"
        params.append(filters["Religion"])

    # Caste
    if "Caste" in filters:
        query += " AND caste = %s"
        params.append(filters["Caste"])

    # Mother Tongue
    if "Mother_Tongue" in filters:
        query += " AND mother_tongue = %s"
        params.append(filters["Mother_Tongue"])

    # Profession
    if "Profession" in filters:
        query += " AND profession = %s"
        params.append(filters["Profession"])

    # Education
    if "Education" in filters:
        query += " AND education = %s"
        params.append(filters["Education"])

    # Age range
    if "AgeMin" in filters and "AgeMax" in filters:
        query += " AND age BETWEEN %s AND %s"
        params.extend([filters["AgeMin"], filters["AgeMax"]])

    # Height range (in cm)
    if "HeightMin" in filters and "HeightMax" in filters:
        query += " AND height_cm BETWEEN %s AND %s"
        params.extend([filters["HeightMin"], filters["HeightMax"]])

    # Country
    if "Country" in filters:
        query += " AND country = %s"
        params.append(filters["Country"])

    # State
    if "State" in filters:
        query += " AND state = %s"
        params.append(filters["State"])

    # City
    if "City" in filters:
        query += " AND city = %s"
        params.append(filters["City"])

    # Gender
    if "Gender" in filters:
        query += " AND gender = %s"
        params.append(filters["Gender"])

    # Income
    if "Income" in filters:
        query += " AND income = %s"
        params.append(filters["Income"])

    # Independency
    if "Independency" in filters:
        query += " AND independency = %s"
        params.append(filters["Independency"])

    # Previous Marriage
    if "Previous_Marriage" in filters:
        query += " AND previous_marriage = %s"
        params.append(filters["Previous_Marriage"])

    # Addiction
    if "Addiction" in filters:
        query += " AND addiction = %s"
        params.append(filters["Addiction"])

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query,tuple(params))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(results) 



if __name__ == "__main__":
    app.run(debug=True)