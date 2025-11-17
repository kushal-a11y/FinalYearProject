from db import db
from models.user_profile import UserProfile
from models.preference_profile import PreferenceProfile
from models.preference_priority import PreferencePriority


def parse_age_range(age_str):
    if not age_str or not isinstance(age_str, str):
        return None, None
    try:
        parts = [p.strip() for p in age_str.replace("–", "-").split("-") if p.strip().isdigit()]
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        elif len(parts) == 1:
            val = int(parts[0])
            return val, val
        return None, None
    except Exception:
        return None, None


def has_common_term(a, b):
    if not a or not b:
        return False
    a_tokens = [x.strip().lower() for x in a.replace("/", ",").split(",") if x.strip()]
    b_tokens = [x.strip().lower() for x in b.replace("/", ",").split(",") if x.strip()]
    return any(p in q or q in p for p in a_tokens for q in b_tokens)


def feature_match_count(profile, pref):
    """Return how many features (0–6) match flatly."""
    count = 0
    min_age, max_age = parse_age_range(pref.age)

    try:
        age = int(profile.age)
    except Exception:
        age = None

    if age and min_age and max_age and (min_age <= age <= max_age):
        count += 1
    if pref.religion and profile.religion and pref.religion.lower() == profile.religion.lower():
        count += 1
    if pref.caste and profile.caste and (pref.caste.lower() in profile.caste.lower() or profile.caste.lower() in pref.caste.lower()):
        count += 1
    if has_common_term(pref.education, profile.education):
        count += 1
    if has_common_term(pref.profession, profile.profession):
        count += 1
    if pref.residence and profile.residence and pref.residence.lower() == profile.residence.lower():
        count += 1

    return count


def weighted_score(profile, pref, priority):
    """Weighted 0–100 score."""
    if not profile or not pref or not priority:
        return 0

    weights = {
        "age": priority.age_priority or 1,
        "religion": priority.religion_priority or 1,
        "caste": priority.caste_priority or 1,
        "education": priority.education_priority or 1,
        "profession": priority.profession_priority or 1,
        "residence": priority.residence_priority or 1,
    }
    total_weight = sum(weights.values())
    matched_weight = 0

    min_age, max_age = parse_age_range(pref.age)
    try:
        age = int(profile.age)
    except Exception:
        age = None

    if age and min_age and max_age and (min_age <= age <= max_age):
        matched_weight += weights["age"]
    if pref.religion and profile.religion and pref.religion.lower() == profile.religion.lower():
        matched_weight += weights["religion"]
    if pref.caste and profile.caste and (pref.caste.lower() in profile.caste.lower() or profile.caste.lower() in pref.caste.lower()):
        matched_weight += weights["caste"]
    if has_common_term(pref.education, profile.education):
        matched_weight += weights["education"]
    if has_common_term(pref.profession, profile.profession):
        matched_weight += weights["profession"]
    if pref.residence and profile.residence and pref.residence.lower() == profile.residence.lower():
        matched_weight += weights["residence"]

    return round((matched_weight / total_weight) * 100, 2)


def satisfies_preference(profile, pref, threshold=2):
    """Return True if at least threshold features match."""
    return feature_match_count(profile, pref) >= threshold


def mutual_flat_match(seeker_id):
    seeker_profile = UserProfile.query.filter_by(user_id=seeker_id).first()
    seeker_pref = PreferenceProfile.query.filter_by(user_id=seeker_id).first()
    seeker_priority = PreferencePriority.query.filter_by(user_id=seeker_id).first()

    if not seeker_profile or not seeker_pref:
        return {"user_id": seeker_id, "error": "Incomplete data", "matches": []}

    candidates = (
        UserProfile.query.filter_by(gender="Male").all()
        if seeker_profile.gender == "Female"
        else UserProfile.query.filter_by(gender="Female").all()
    )

    matches = []

    for cand in candidates:
        cand_pref = PreferenceProfile.query.filter_by(user_id=cand.user_id).first()
        cand_priority = PreferencePriority.query.filter_by(user_id=cand.user_id).first()
        if not cand_pref:
            continue

        if not (satisfies_preference(cand, seeker_pref) and satisfies_preference(seeker_profile, cand_pref)):
            continue

        seeker_features = feature_match_count(cand, seeker_pref)
        candidate_features = feature_match_count(seeker_profile, cand_pref)

        is_weighted = bool(seeker_priority or cand_priority)
        if is_weighted:
            seeker_percent = weighted_score(cand, seeker_pref, seeker_priority or PreferencePriority())
            candidate_percent = weighted_score(seeker_profile, cand_pref, cand_priority or PreferencePriority())
            mutual_percent = round((seeker_percent + candidate_percent) / 2, 2)
        else:
            seeker_percent = round((seeker_features / 6) * 100, 2)
            candidate_percent = round((candidate_features / 6) * 100, 2)
            mutual_percent = round((seeker_percent + candidate_percent) / 2, 2)

        matches.append({
            "candidate_id": cand.user_id,
            "candidate_name": cand.name or f"User {cand.user_id}",
            "seeker_to_candidate": seeker_features,
            "candidate_to_seeker": candidate_features,
            "seeker_to_candidate_percent": seeker_percent,
            "candidate_to_seeker_percent": candidate_percent,
            "mutual_match_percent": mutual_percent,
            "match_type": "weighted" if is_weighted else "flat",
        })

    # === Update Matches in Database ===
    if matches:
        try:
            # Update seeker's matches
            seeker_profile.matches = [m["candidate_id"] for m in matches]

            # Update reciprocal matches for each candidate
            for m in matches:
                cand = UserProfile.query.filter_by(user_id=m["candidate_id"]).first()
                if cand:
                    existing = set(cand.matches or [])
                    existing.add(seeker_profile.user_id)
                    cand.matches = list(existing)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Failed to update matches in DB: {e}")

    return {
        "user_id": seeker_id,
        "total_matches": len(matches),
        "matches": sorted(matches, key=lambda x: x["mutual_match_percent"], reverse=True),
    }
