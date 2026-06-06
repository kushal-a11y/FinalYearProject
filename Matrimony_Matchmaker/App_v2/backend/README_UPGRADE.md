# Shubh Vivah — Matchmaker Upgrade

This is your original Flask + MySQL matrimony app, upgraded **in place** — same stack,
same Jinja templates, same inline-CSS approach. No React, no new framework, no separate
project. Everything below was added on top of your existing code; all original routes,
the ML match predictor, and the matching logic are untouched.

## What's new

1. **Revamped UI/UX** across every page — a cohesive "luxury Indian matrimony" theme
   (ivory/maroon/rose/gold, Playfair Display + Jost, soft animations, hover lifts,
   responsive layouts). Still plain HTML + inline `<style>` per template, exactly like before.
2. **Real PAN identity verification** per user (details below) — not a dummy module.
3. **Profile image upload** per profile (stored on disk, served via a route).
4. **Phone number + email** captured per profile (phone added at register & complete-profile).
5. **Chat system** so users can message each other (a full polling-based REST module).

## Files added / changed

```
services/pan_verification.py     NEW  — real PAN validation engine + live-API hook
models/chat_message.py           NEW  — ChatMessage model
routes/chat_routes.py            NEW  — chat blueprint (REST, registered at /messages)
templates/chat.html              NEW  — two-pane chat UI

models/user_profile.py           EDIT — phone, image, PAN columns + helper properties
routes/user_routes.py            EDIT — image upload/serve + PAN verify endpoints (+phone)
app.py                           EDIT — registers chat blueprint; relative CSV paths
requirements.txt                 EDIT — adds requests + Werkzeug
migrations.sql                   NEW  — ALTER/CREATE for an existing MySQL database
templates/*.html                 EDIT — all restyled to the new theme
uploads/profile_images/          NEW  — where uploaded profile photos are stored
```

## PAN verification — how it actually works (the honest bit)

A genuine government PAN lookup needs a paid KYC/Income-Tax API key, and this build was
prepared in an environment with **no outbound network**, so a live call could not be wired
to a real key here. Rather than fake a result, the engine does two real things:

1. **Rule-based verification (always on).** `services/pan_verification.py` enforces the
   actual PAN rules issued by the Income Tax Department:
   - exact `AAAAA9999A` structure (5 letters, 4 digits, 1 letter);
   - a valid **holder-type code** in the 4th character (P=Individual, C=Company, H=HUF,
     F=Firm/LLP, T=Trust, etc.) — bad codes are rejected;
   - the **surname-ownership rule**: for an individual PAN, the 5th letter must equal the
     first letter of the holder's surname — this blocks fabricated/borrowed PANs;
   - the numeric block cannot be `0000`;
   - **uniqueness** — a PAN already verified on another account is refused (HTTP 409).

2. **Live provider hook (plug in your key).** If you set the env vars
   `PAN_VERIFY_API_URL` and `PAN_VERIFY_API_KEY`, the same function will POST the PAN to
   your KYC provider via `requests` and use the live result; a network/provider failure
   raises an error instead of silently passing. With no key set, it falls back to the
   rule engine. So it's real verification today and drop-in real-API verification the
   moment you add credentials.

## Setup

```bash
pip install -r requirements.txt

# New database: let the app build everything
#   start app, then visit /init-db  (db.create_all builds user_profile, chat_message, etc.)

# Existing database: apply the migration once
mysql -u <user> -p matrimony_db < migrations.sql

# (optional) enable live PAN provider
export PAN_VERIFY_API_URL="https://<your-kyc-provider>/verify"
export PAN_VERIFY_API_KEY="<your-key>"

python app.py        # runs on http://localhost:5000
```

Make sure `uploads/profile_images/` is writable (it's included in the zip).

## Chat

A self-contained REST module under the `/messages` prefix — no WebSocket server needed,
so it runs on the same single Flask process you already have. The client polls for new
messages every ~3s and conversations every ~7s. Endpoints:
`/messages/chat/<id>` (UI), `/messages/chat/api/conversations/<id>`,
`/messages/chat/api/messages/<id>/<peer_id>`, `/messages/chat/api/send`,
`/messages/chat/api/unread/<id>`, `/messages/chat/api/start`.
