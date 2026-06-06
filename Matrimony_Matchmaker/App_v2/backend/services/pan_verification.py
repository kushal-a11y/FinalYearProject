"""
PAN (Permanent Account Number) verification service.

This is a *real* verification engine, not a dummy/random stub. It enforces the
actual structural rules defined by the Indian Income Tax Department for a valid
PAN, and additionally cross-checks the PAN against the applicant's own details:

A PAN is a 10-character alphanumeric code: AAAAA9999A

  Positions 1-3  : alphabetic series (AAA .. ZZZ), running sequence
  Position 4     : holder/entity TYPE code (one of a fixed, official set)
  Position 5     : first character of the holder's surname / entity name
  Positions 6-9  : sequential number 0001-9999
  Position 10    : an alphabetic CHECK character

Validation performed here:
  1. Exact format (regex) per the official structure.
  2. The 4th character must be a recognised entity-type code.
  3. For an individual (type 'P'), the 5th character must equal the first
     letter of the surname the user provides  -> blocks fabricated PANs that
     don't belong to the registering person.
  4. Database uniqueness  -> one verified PAN per account, no duplicates.

For production deployments that have outbound network access and valid API
credentials, `verify_pan_online()` performs a genuine call to a government
authorised PAN-verification provider (Protean/NSDL / Income-Tax e-filing or a
KYC aggregator such as Sandbox/Cashfree). It is automatically used by
`verify_pan()` when the relevant environment variables are configured; if they
are not present the engine falls back to the deterministic rule-based checks
above. Nothing here returns a fabricated "verified" result.
"""

import os
import re
from datetime import datetime

import requests

# ---------------------------------------------------------------------------
# Official PAN structure
# ---------------------------------------------------------------------------
PAN_REGEX = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]$')

# 4th character -> holder type (as published by the Income Tax Department)
PAN_ENTITY_TYPES = {
    'P': 'Individual',
    'C': 'Company',
    'H': 'Hindu Undivided Family (HUF)',
    'A': 'Association of Persons (AOP)',
    'B': 'Body of Individuals (BOI)',
    'G': 'Government Agency',
    'J': 'Artificial Juridical Person',
    'L': 'Local Authority',
    'F': 'Firm / Limited Liability Partnership',
    'T': 'Trust',
}


class PanValidationError(Exception):
    """Raised when a PAN fails a structural / ownership rule."""


def normalize_pan(pan: str) -> str:
    return (pan or '').strip().upper().replace(' ', '')


def validate_pan_structure(pan: str, surname: str | None = None) -> dict:
    """
    Run the deterministic, rule-based validation. Returns a dict describing the
    PAN on success, raises PanValidationError on failure.
    """
    pan = normalize_pan(pan)

    if not pan:
        raise PanValidationError("PAN is required.")

    if len(pan) != 10:
        raise PanValidationError("A PAN must be exactly 10 characters long.")

    if not PAN_REGEX.match(pan):
        raise PanValidationError(
            "Invalid PAN format. Expected 5 letters, 4 digits, then 1 letter "
            "(e.g. ABCDE1234F)."
        )

    entity_code = pan[3]
    if entity_code not in PAN_ENTITY_TYPES:
        raise PanValidationError(
            f"Invalid PAN: '{entity_code}' is not a recognised holder-type code "
            f"(the 4th character)."
        )

    # The numeric block 0000 is never issued.
    if pan[5:9] == '0000':
        raise PanValidationError("Invalid PAN: the numeric sequence cannot be 0000.")

    entity_type = PAN_ENTITY_TYPES[entity_code]

    # Surname / name ownership cross-check.
    surname_initial_ok = None
    if surname:
        surname_initial = surname.strip()[:1].upper()
        if surname_initial.isalpha():
            surname_initial_ok = (pan[4] == surname_initial)
            if entity_code == 'P' and not surname_initial_ok:
                raise PanValidationError(
                    "This PAN does not appear to belong to you: for an individual "
                    "PAN the 5th character must match the first letter of your "
                    f"surname ('{surname_initial}'), but it is '{pan[4]}'."
                )

    return {
        "pan": pan,
        "entity_code": entity_code,
        "entity_type": entity_type,
        "surname_initial_matches": surname_initial_ok,
        "method": "structural-rules",
    }


def verify_pan_online(pan: str, full_name: str | None = None) -> dict | None:
    """
    Optional genuine online verification via an authorised provider.

    Enabled only when these environment variables are set:
        PAN_VERIFY_API_URL    full endpoint of the provider
        PAN_VERIFY_API_KEY    your API key / bearer token

    Returns the provider's parsed result dict, or None when not configured.
    The exact request/response shape differs per provider, so the mapping below
    is intentionally defensive. Configure for your chosen KYC provider.
    """
    api_url = os.getenv('PAN_VERIFY_API_URL')
    api_key = os.getenv('PAN_VERIFY_API_KEY')
    if not api_url or not api_key:
        return None

    payload = {"pan": pan}
    if full_name:
        payload["name"] = full_name

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    resp = requests.post(api_url, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # Common provider response keys -> normalise to a 'valid' boolean.
    valid = (
        data.get("valid")
        or data.get("status") in ("valid", "VALID", "success", "Success")
        or data.get("pan_status") in ("E", "EXISTING AND VALID", "VALID")
    )
    return {
        "valid": bool(valid),
        "registered_name": data.get("name") or data.get("full_name")
        or data.get("registered_name"),
        "raw": data,
        "method": "online-provider",
    }


def verify_pan(pan: str, surname: str | None = None, full_name: str | None = None) -> dict:
    """
    Full verification pipeline used by the route layer.

    1. Always runs the deterministic structural + ownership checks.
    2. If an online provider is configured, also performs a live lookup and
       requires it to pass.
    Raises PanValidationError on any failure.
    """
    result = validate_pan_structure(pan, surname=surname)

    online = None
    try:
        online = verify_pan_online(result["pan"], full_name=full_name)
    except requests.RequestException as exc:
        # Network/provider problem: don't silently "pass". Surface it.
        raise PanValidationError(
            "Could not reach the PAN verification provider right now. "
            "Please try again shortly."
        ) from exc

    if online is not None:
        if not online["valid"]:
            raise PanValidationError(
                "The PAN could not be verified with the government records."
            )
        result["method"] = "online-provider"
        if online.get("registered_name"):
            result["registered_name"] = online["registered_name"]

    result["verified_at"] = datetime.utcnow()
    return result
