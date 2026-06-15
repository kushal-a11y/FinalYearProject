"""
services/nlp_preference_parser.py
=================================

Natural Language Processing (NLP) module for the Matchmaker.

It lets a user describe, in plain English, the kind of partner they are looking
for (e.g. "I want a Hindu Brahmin girl between 25 and 29, a software engineer
based in Kolkata, at least 160 cm tall") and turns that sentence into the very
same structured fields the preference *form* uses:

    preferred_age_min, preferred_age_max, preferred_gender, preferred_education,
    preferred_profession, preferred_caste, preferred_religion,
    preferred_residence, preferred_height_cm

Pipeline (in order):
    1. Text preprocessing        - normalise / clean the raw sentence
    2. Tokenization              - split into word tokens
    3. Stop-word removal         - drop "the", "a", "want", ...
    4. Lemmatization             - "engineers" -> "engineer", "studying" -> "study"
    5. Feature extraction        - pull out the meaningful preference features

Backend selection is automatic and degrades gracefully:
    * spaCy  (preferred - gives lemmas + Named-Entity Recognition for cities)
    * NLTK   (punkt + stopwords + WordNet lemmatizer)
    * pure-Python regex fallback (works with zero extra installs)

So the file imports and runs even before you install spaCy/NLTK; it simply uses
a lighter engine until the models are present.  Nothing else in the app needs to
change to use it.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Optional engines - loaded lazily and cached.  Missing engines never crash.
# ---------------------------------------------------------------------------
_SPACY_NLP = None
_SPACY_TRIED = False

_NLTK = None            # holds the nltk module if usable
_NLTK_TRIED = False
_NLTK_LEMMATIZER = None
_NLTK_STOPWORDS = set()


def _load_spacy():
    """Return a loaded spaCy pipeline, or None if spaCy/model unavailable."""
    global _SPACY_NLP, _SPACY_TRIED
    if _SPACY_TRIED:
        return _SPACY_NLP
    _SPACY_TRIED = True
    try:
        import spacy
        try:
            _SPACY_NLP = spacy.load("en_core_web_sm")
        except Exception:
            # model not downloaded - fall back to a blank English tokenizer
            _SPACY_NLP = spacy.blank("en")
    except Exception:
        _SPACY_NLP = None
    return _SPACY_NLP


def _load_nltk():
    """Return the nltk module (with data ensured) or None."""
    global _NLTK, _NLTK_TRIED, _NLTK_LEMMATIZER, _NLTK_STOPWORDS
    if _NLTK_TRIED:
        return _NLTK
    _NLTK_TRIED = True
    try:
        import nltk
        from nltk.corpus import stopwords, wordnet  # noqa: F401
        from nltk.stem import WordNetLemmatizer
        from nltk.tokenize import word_tokenize  # noqa: F401

        # Make sure the required corpora exist; download silently if not.
        for pkg, path in [
            ("punkt", "tokenizers/punkt"),
            ("punkt_tab", "tokenizers/punkt_tab"),
            ("stopwords", "corpora/stopwords"),
            ("wordnet", "corpora/wordnet"),
            ("omw-1.4", "corpora/omw-1.4"),
        ]:
            try:
                nltk.data.find(path)
            except LookupError:
                try:
                    nltk.download(pkg, quiet=True)
                except Exception:
                    pass

        _NLTK_LEMMATIZER = WordNetLemmatizer()
        try:
            _NLTK_STOPWORDS = set(stopwords.words("english"))
        except Exception:
            _NLTK_STOPWORDS = set()
        _NLTK = nltk
    except Exception:
        _NLTK = None
    return _NLTK


# A small built-in stop-word list used by the pure-Python fallback so the
# module still removes noise words even with neither spaCy nor NLTK installed.
_BASIC_STOPWORDS = {
    "i", "me", "my", "we", "our", "you", "your", "a", "an", "the", "and", "or",
    "but", "if", "of", "at", "by", "for", "with", "about", "to", "from", "in",
    "on", "is", "am", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "so", "than", "that", "this", "these",
    "those", "want", "wants", "looking", "look", "would", "like", "prefer",
    "preferred", "preference", "someone", "partner", "person", "should", "who",
    "whom", "ideally", "please", "kindly", "find", "me", "must", "need",
}


# ---------------------------------------------------------------------------
# Default vocabularies (mirrors the lists used in routes/preference_routes.py)
# You can override any of these by passing arguments to parse_preference_text.
# ---------------------------------------------------------------------------
DEFAULT_CASTES = [
    "Brahmin", "SC", "OBC", "Baisya", "Kayastha", "Banerjee", "General", "Tili",
    "Barujibi", "Kumbhakar", "Swarnakar", "Napit", "Namasudra", "Sunni", "Sadgop",
    "Goala", "Kandi", "Tambuli", "Mukherjee", "Roy", "Biswas", "Chatterjee",
    "Dutta", "Banik", "Ganguly", "Bhattacharya", "Aguri", "Malakar", "Yadav",
]

DEFAULT_DEGREES = [
    "B.Tech MBA", "MBA", "B.Tech", "BSc", "BA", "MA B.Ed", "MA", "MSC B.Ed",
    "BA B.Ed", "PhD", "Bcom", "LLB", "LLM", "MBBS", "M.Tech", "PHD", "M.SC",
    "B.com", "IIT", "NIT",
]

DEFAULT_PROFESSIONS = [
    "MNC", "IT", "Business", "Bank", "Law Firm", "Advocate", "College lecturer",
    "Asst Professor", "Professor", "Bank Manager", "Govt job", "Project Manager",
    "Engineer", "Doctor", "Teacher", "Lawyer", "Officer",
]

# religion keyword -> canonical label
_RELIGIONS = {
    "hindu": "Hindu", "hinduism": "Hindu",
    "muslim": "Muslim", "islam": "Muslim", "islamic": "Muslim",
    "christian": "Christian", "christianity": "Christian", "catholic": "Christian",
    "sikh": "Sikh", "sikhism": "Sikh",
    "jain": "Jain", "jainism": "Jain",
    "buddhist": "Buddhist", "buddhism": "Buddhist",
    "parsi": "Parsi", "zoroastrian": "Parsi",
    "jewish": "Jewish",
}

# generic education words -> a representative degree string
_EDU_KEYWORDS = {
    "engineer": "B.Tech", "engineering": "B.Tech",
    "doctor": "MBBS", "medical": "MBBS", "physician": "MBBS",
    "mba": "MBA", "management": "MBA",
    "graduate": "BA", "graduation": "BA", "bachelor": "BA", "bachelors": "BA",
    "postgraduate": "MA", "post-graduate": "MA", "masters": "MA", "master": "MA",
    "doctorate": "PhD", "phd": "PhD", "doctoral": "PhD",
    "law": "LLB", "lawyer": "LLB", "advocate": "LLB",
}

# generic profession words -> a representative profession string
_PROF_KEYWORDS = {
    "doctor": "Doctor", "physician": "Doctor", "surgeon": "Doctor",
    "engineer": "Engineer", "developer": "Engineer", "programmer": "Engineer",
    "teacher": "Teacher", "lecturer": "College lecturer", "professor": "Professor",
    "lawyer": "Advocate", "advocate": "Advocate",
    "banker": "Bank", "bank": "Bank",
    "business": "Business", "businessman": "Business", "entrepreneur": "Business",
    "government": "Govt job", "govt": "Govt job", "officer": "Officer",
    "manager": "Project Manager", "scientist": "IT", "researcher": "IT",
    "it": "IT", "software": "IT", "mnc": "MNC",
}

# small list of common Indian cities for residence detection in the fallback path
_KNOWN_CITIES = {
    "kolkata", "calcutta", "delhi", "mumbai", "bangalore", "bengaluru",
    "chennai", "hyderabad", "pune", "ahmedabad", "jaipur", "lucknow", "kanpur",
    "nagpur", "indore", "bhopal", "patna", "ranchi", "guwahati", "siliguri",
    "durgapur", "asansol", "howrah", "kharagpur", "burdwan", "bardhaman",
    "gurgaon", "gurugram", "noida", "surat", "vadodara", "coimbatore", "kochi",
    "thiruvananthapuram", "visakhapatnam", "bhubaneswar", "cuttack", "agra",
    "varanasi", "amritsar", "ludhiana", "chandigarh", "dehradun", "shillong",
}


# ===========================================================================
# 1. TEXT PREPROCESSING
# ===========================================================================
def preprocess(text: str) -> str:
    """Lower-case, collapse whitespace and strip stray punctuation noise."""
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"\s+", " ", text)
    return text


# ===========================================================================
# 2. TOKENIZATION
# ===========================================================================
def tokenize(text: str):
    """Split text into word tokens using the best available engine."""
    nlp = _load_spacy()
    if nlp is not None:
        return [t.text for t in nlp(text) if not t.is_space]
    nltk = _load_nltk()
    if nltk is not None:
        try:
            from nltk.tokenize import word_tokenize
            return word_tokenize(text)
        except Exception:
            pass
    # fallback: simple word regex (keeps things like b.tech, 5'8")
    return re.findall(r"[a-zA-Z]+(?:\.[a-zA-Z]+)*|\d+(?:'\d+\"?)?|\d+", text)


# ===========================================================================
# 3. STOP-WORD REMOVAL
# ===========================================================================
def remove_stopwords(tokens):
    """Drop common, low-information words."""
    _load_nltk()  # populates _NLTK_STOPWORDS if available
    stop = _NLTK_STOPWORDS if _NLTK_STOPWORDS else _BASIC_STOPWORDS
    return [t for t in tokens if t.lower() not in stop and len(t.strip()) > 0]


# ===========================================================================
# 4. LEMMATIZATION
# ===========================================================================
def lemmatize(tokens):
    """Reduce each token to its dictionary base form."""
    nlp = _load_spacy()
    if nlp is not None:
        try:
            # only meaningful if the loaded pipeline has a lemmatizer
            doc = nlp(" ".join(tokens))
            lemmas = [t.lemma_ if t.lemma_ and t.lemma_ != "-PRON-" else t.text
                      for t in doc]
            if any(lemmas):
                return [l.lower() for l in lemmas]
        except Exception:
            pass
    nltk = _load_nltk()
    if nltk is not None and _NLTK_LEMMATIZER is not None:
        try:
            return [_NLTK_LEMMATIZER.lemmatize(t.lower()) for t in tokens]
        except Exception:
            pass
    # fallback: naive plural stripper
    out = []
    for t in tokens:
        t = t.lower()
        if t.endswith("ies") and len(t) > 4:
            t = t[:-3] + "y"
        elif t.endswith("es") and len(t) > 4:
            t = t[:-2]
        elif t.endswith("s") and not t.endswith("ss") and len(t) > 3:
            t = t[:-1]
        out.append(t)
    return out


# ===========================================================================
# 5a. INDIVIDUAL FEATURE EXTRACTORS (run on the raw, preprocessed text)
# ===========================================================================
def _extract_age(text: str):
    """Return (min_age, max_age) as strings, or (None, None)."""
    # between X and Y  /  X to Y  /  X - Y
    m = re.search(r"(\d{2})\s*(?:-|to|and|–|until|upto|up to)\s*(\d{2})", text)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return str(min(a, b)), str(max(a, b))
    # "in his/her 30s" or "30s"
    m = re.search(r"\b(\d0)s\b", text)
    if m:
        base = int(m.group(1))
        return str(base), str(base + 9)
    # around / about / approximately X  -> +/- 2
    m = re.search(r"(?:around|about|approx\w*|near)\s+(\d{2})", text)
    if m:
        v = int(m.group(1))
        return str(v - 2), str(v + 2)
    # at least / above / over / older than X  -> min only
    m = re.search(r"(?:at least|above|over|older than|more than|minimum|min)\s+(\d{2})", text)
    if m:
        return str(int(m.group(1))), ""
    # below / under / younger than / at most / max X  -> max only
    m = re.search(r"(?:below|under|younger than|less than|at most|maximum|max|upto|up to)\s+(\d{2})", text)
    if m:
        return "", str(int(m.group(1)))
    # a bare "aged 27" / "27 years"
    m = re.search(r"(?:aged|age)\s+(\d{2})", text) or re.search(r"\b(\d{2})\s*(?:years?|yrs?|yo)\b", text)
    if m:
        v = int(m.group(1))
        if 18 <= v <= 80:
            return str(v - 2), str(v + 2)
    return None, None


def _extract_height(text: str):
    """Return preferred height in centimetres (string) or None."""
    # 165 cm / 165 centimeters
    m = re.search(r"(\d{3})\s*(?:cm|centimet)", text)
    if m:
        return str(int(m.group(1)))
    # feet/inches:  5'8  /  5'8"  /  5 feet 8 / 5 ft 8 inches
    m = re.search(r"(\d)\s*(?:'|feet|foot|ft)\s*(\d{1,2})?", text)
    if m:
        feet = int(m.group(1))
        inches = int(m.group(2)) if m.group(2) else 0
        if 4 <= feet <= 7:
            cm = round((feet * 12 + inches) * 2.54)
            return str(cm)
    return None


def _extract_gender(text: str):
    male = ["groom", "man", "male", "boy", "guy", "gentleman", "husband", "him", "he"]
    female = ["bride", "woman", "female", "girl", "lady", "gentlewoman", "wife", "her", "she"]
    tokens = set(re.findall(r"[a-z]+", text))
    if tokens & set(female):
        return "Female"
    if tokens & set(male):
        return "Male"
    return None


def _extract_religion(lemmas):
    for lemma in lemmas:
        if lemma in _RELIGIONS:
            return _RELIGIONS[lemma]
    return None


def _match_from_vocab(text, vocab):
    """Return the first vocabulary entry that appears in the text (longest first)."""
    for item in sorted(vocab, key=len, reverse=True):
        token = item.lower().strip()
        if not token:
            continue
        # word-boundary match, tolerant of dots in things like b.tech
        pattern = r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            return item
    return None


def _extract_education(text, lemmas, degrees):
    hit = _match_from_vocab(text, degrees)
    if hit:
        return hit
    for lemma in lemmas:
        if lemma in _EDU_KEYWORDS:
            return _EDU_KEYWORDS[lemma]
    return None


def _extract_profession(text, lemmas, professions):
    hit = _match_from_vocab(text, professions)
    if hit:
        return hit
    for lemma in lemmas:
        if lemma in _PROF_KEYWORDS:
            return _PROF_KEYWORDS[lemma]
    return None


def _extract_caste(text, castes):
    return _match_from_vocab(text, castes)


def _extract_residence(raw_text, preprocessed):
    """Use spaCy NER (GPE) if available, else a cities list / 'in <City>' regex."""
    nlp = _load_spacy()
    if nlp is not None:
        try:
            doc = nlp(raw_text)
            for ent in doc.ents:
                if ent.label_ in ("GPE", "LOC"):
                    return ent.text.title()
        except Exception:
            pass
    # known-city lookup
    for city in _KNOWN_CITIES:
        if re.search(r"(?<![a-z])" + re.escape(city) + r"(?![a-z])", preprocessed):
            return "Kolkata" if city == "calcutta" else city.title()
    # "(based/living/settled/residing) in <Word>" / "from <Word>"
    m = re.search(r"(?:based in|living in|lives in|settled in|residing in|stays in|from|in)\s+([a-z]+)", preprocessed)
    if m:
        candidate = m.group(1)
        if candidate not in _BASIC_STOPWORDS and len(candidate) > 2:
            return candidate.title()
    return None


# ===========================================================================
# 5b. PUBLIC ENTRY POINT
# ===========================================================================
def parse_preference_text(text, castes=None, degrees=None, professions=None):
    """
    Run the full NLP pipeline on `text` and return a dict whose keys match the
    preference form fields.  Only fields the model is confident about are
    filled; everything else is returned as "" so the form is easy to populate.

    The returned dict also carries a private "_nlp" block (tokens, lemmas,
    engine used) which is handy for debugging / showing the user what was
    understood.  The frontend can ignore it.
    """
    castes = castes or DEFAULT_CASTES
    degrees = degrees or DEFAULT_DEGREES
    professions = professions or DEFAULT_PROFESSIONS

    raw = text or ""
    clean = preprocess(raw)

    # pipeline steps (kept explicit so each stage is observable)
    tokens = tokenize(clean)
    content_tokens = remove_stopwords(tokens)
    lemmas = lemmatize(content_tokens)

    age_min, age_max = _extract_age(clean)

    result = {
        "preferred_age_min": age_min or "",
        "preferred_age_max": age_max or "",
        "preferred_gender": _extract_gender(clean) or "",
        "preferred_education": _extract_education(clean, lemmas, degrees) or "",
        "preferred_profession": _extract_profession(clean, lemmas, professions) or "",
        "preferred_caste": _extract_caste(clean, castes) or "",
        "preferred_religion": _extract_religion(lemmas) or "",
        "preferred_residence": _extract_residence(raw, clean) or "",
        "preferred_height_cm": _extract_height(clean) or "",
    }

    engine = "spacy" if _load_spacy() else ("nltk" if _load_nltk() else "regex")
    result["_nlp"] = {
        "engine": engine,
        "tokens": tokens,
        "content_tokens": content_tokens,
        "lemmas": lemmas,
    }
    return result


# Quick manual test:  python -m services.nlp_preference_parser
if __name__ == "__main__":
    samples = [
        "I want a Hindu Brahmin girl between 25 and 29, a software engineer based in Kolkata, at least 160 cm tall.",
        "Looking for a Muslim groom, doctor, around 32, living in Delhi, 5'10\".",
        "Prefer a postgraduate woman from Bangalore working in an MNC, age under 30.",
    ]
    for s in samples:
        print("\nINPUT:", s)
        out = parse_preference_text(s)
        meta = out.pop("_nlp")
        print("ENGINE:", meta["engine"])
        for k, v in out.items():
            if v:
                print(f"  {k:24} -> {v}")
