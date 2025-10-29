from db import db
from models.user_profile import UserProfile
from models.preference_profile import PreferenceProfile

def parse_age_range(age_str):
    """Convert '23-34' or '28' to (min_age, max_age)."""
    if not age_str or not isinstance(age_str, str):
        return None, None
    try:
        parts = age_str.split('-')
        parts = [p.strip() for p in parts if p.strip().isdigit()]
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        elif len(parts) == 1:
            val = int(parts[0])
            return val, val
        else:
            return None, None
    except Exception:
        return None, None


def satisfies_preference(candidate, preference, threshold=2):
    """
    Returns True if candidate satisfies at least 'threshold' number of preference conditions.
    - Handles None safely.
    - Converts all string comparisons to lowercase.
    - Allows partial matches for education, profession, and caste (e.g., 'MNC' in 'MBA MNC').
    """
    if not candidate or not preference:
        return False  # Missing data

    match_count = 0

    # --- AGE ---
    min_age, max_age = parse_age_range(preference.age)
    try:
        cand_age = int(candidate.age) if candidate.age else None
    except ValueError:
        cand_age = None

    if cand_age and min_age and max_age and (min_age <= cand_age <= max_age):
        match_count += 1

    # --- RELIGION ---
    if preference.religion and candidate.religion:
        if preference.religion.strip().lower() == candidate.religion.strip().lower():
            match_count += 1

    # --- CASTE (partial match allowed) ---
    if preference.caste and candidate.caste:
        pref_caste = preference.caste.strip().lower()
        cand_caste = candidate.caste.strip().lower()
        if pref_caste in cand_caste or cand_caste in pref_caste:
            match_count += 1

    # --- EDUCATION (partial match allowed) ---
    if preference.education and candidate.education:
        pref_edu = preference.education.strip().lower()
        cand_edu = candidate.education.strip().lower()
        if pref_edu in cand_edu or cand_edu in pref_edu:
            match_count += 1

    # --- PROFESSION (partial match allowed) ---
    if preference.profession and candidate.profession:
        pref_prof = preference.profession.strip().lower()
        cand_prof = candidate.profession.strip().lower()
        if pref_prof in cand_prof or cand_prof in pref_prof:
            match_count += 1

    # --- RESIDENCE ---
    if preference.residence and candidate.residence:
        if preference.residence.strip().lower() == candidate.residence.strip().lower():
            match_count += 1

    return match_count >= threshold


def mutual_score(profile, pref):
    """Calculate mutual compatibility (0–100%) safely."""
    if not profile or not pref:
        return 0

    total = 6
    score = 0

    # --- AGE ---
    min_age, max_age = parse_age_range(pref.age)
    try:
        user_age = int(profile.age) if profile.age else None
    except ValueError:
        user_age = None

    if user_age and min_age and max_age and (min_age <= user_age <= max_age):
        score += 1

    # --- OTHER ATTRIBUTES ---
    if pref.religion and pref.religion == profile.religion:
        score += 1
    if pref.caste and pref.caste == profile.caste:
        score += 1
    if pref.education and pref.education == profile.education:
        score += 1
    if pref.profession and pref.profession == profile.profession:
        score += 1
    if pref.residence and pref.residence == profile.residence:
        score += 1

    return score


def mutual_flat_match(seeker_id):
    """
    Finds mutual flat matches safely, skipping users with missing preferences.
    """
    seeker_profile = UserProfile.query.filter_by(user_id=seeker_id).first()
    seeker_pref = PreferenceProfile.query.filter_by(user_id=seeker_id).first()

    if not seeker_profile or not seeker_pref:
        return {"user_id": seeker_id, "error": "Incomplete seeker data", "matches": []}

    # Fetch opposite gender users
    if seeker_profile.gender == "Female":
        candidates = UserProfile.query.filter_by(gender="Male").all()
    else:
        candidates = UserProfile.query.filter_by(gender="Female").all()

    matches = []
    seeker_matches = []

    for candidate in candidates:
        candidate_pref = PreferenceProfile.query.filter_by(user_id=candidate.user_id).first()

        # Skip candidates without preferences
        if not candidate_pref:
            continue

        try:
            seeker_likes_candidate = satisfies_preference(candidate, seeker_pref)
            candidate_likes_seeker = satisfies_preference(seeker_profile, candidate_pref)
        except Exception:
            continue  # Skip any malformed entry

        if seeker_likes_candidate and candidate_likes_seeker:
            seeker_score = mutual_score(candidate, seeker_pref)
            candidate_score = mutual_score(seeker_profile, candidate_pref)
            mutual_percent = round((seeker_score + candidate_score) * 100/ 12 , 2)

            matches.append({
                "seeker_id": seeker_id,
                "candidate_id": candidate.user_id,
                "seeker_to_candidate": seeker_score,
                "candidate_to_seeker": candidate_score,
                "mutual_match_percent": mutual_percent
            })

            # Update match lists safely
            seeker_profile.matches = (seeker_profile.matches or [])
            candidate.matches = (candidate.matches or [])

            if candidate.user_id not in seeker_profile.matches:
                seeker_profile.matches.append(candidate.user_id)
            if seeker_profile.user_id not in candidate.matches:
                candidate.matches.append(seeker_profile.user_id)

            seeker_matches.append(candidate.user_id)

    db.session.commit()

    return {
        "user_id": seeker_id,
        "total_matches": len(matches),
        "match_ids": seeker_matches,
        "matches": sorted(matches, key=lambda x: x["mutual_match_percent"], reverse=True)
    }
