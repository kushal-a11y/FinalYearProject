from models.user_profile import UserProfile
from models.preference_profile import PreferenceProfile

def flat_match(user_id):
    user = UserProfile.query.filter_by(user_id=user_id).first()
    prefs = user.preference
    return []
