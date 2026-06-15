"""
routes/nlp_routes.py
====================

A tiny, self-contained blueprint that exposes the NLP preference parser to the
frontend.  It is purely *additive* - it does not touch the existing preference
save flow.  The endpoint only *reads* the user's free-text description and
returns the structured fields; the user then reviews them in the normal form
and saves with the existing "Save Preferences" button (unchanged logic).

Registered in app.py as:

    from routes.nlp_routes import nlp_bp
    app.register_blueprint(nlp_bp, url_prefix='/nlp')

Endpoint:
    POST /nlp/parse/<int:user_id>
        body : { "text": "I want a Hindu girl, 25-29, engineer in Kolkata" }
        200  : { "preferred_age_min": "25", ... , "_nlp": {...} }
"""

from flask import Blueprint, request, jsonify

from services.nlp_preference_parser import parse_preference_text

nlp_bp = Blueprint("nlp", __name__)


@nlp_bp.route("/parse/<int:user_id>", methods=["POST"])
def parse_preference(user_id):
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "Please type a short description first."}), 400

    try:
        parsed = parse_preference_text(text)
    except Exception as e:  # never break the page on an NLP hiccup
        return jsonify({"error": f"Could not analyse the text: {e}"}), 500

    return jsonify(parsed), 200
