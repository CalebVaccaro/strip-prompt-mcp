import re
import sys

try:
    import nltk
    try:
        from nltk.corpus import stopwords
        STOP = set(stopwords.words('english'))
    except LookupError:
        nltk.download('stopwords', quiet=True)
        from nltk.corpus import stopwords
        STOP = set(stopwords.words('english'))
except ImportError:
    print("nltk not installed. Run: pip install nltk", file=sys.stderr)
    sys.exit(1)

# -- phrase patterns (pre-pass) -----------------------------------------------
# Applied in order before word-level stop words. Each is a compiled regex
# matched against the full text so multi-word scaffolding is consumed as a unit.
# ORDER MATTERS: 3A must precede 4A (see comment on 3A).

PHRASE_PATTERNS = [
    # 1. Frame opener: 'as part of our/this/the [adj?] [initiative|effort|...] to'
    (re.compile(
        r'\bas\s+part\s+of\s+(?:our|this|the|an?)\s+'
        r'(?:(?:ongoing|current|existing|broader|larger|new)\s+)?'
        r'(?:initiative|effort|work|program|plan|project|engagement|roadmap|strategy)\s+to\b',
        re.IGNORECASE), ''),

    # 2. Purpose declaration: 'the [objective|goal|...] of this [effort|ticket|...] is to'
    #    Noun list restricted to ticket-domain words so 'goal of this function' doesn't fire.
    (re.compile(
        r'\bthe\s+(?:objective|goal|aim|purpose|intent(?:ion)?)\s+of\s+(?:this|the)\s+'
        r'(?:effort|initiative|work|project|engagement|program|sprint|task|epic|ticket)\s+is\s+to\b',
        re.IGNORECASE), ''),

    # 3A. '[verb] opportunities to' — MUST precede 4A.
    #     Without this order, 'we would like to explore opportunities to enhance'
    #     strips 'we would like to' first (4A), leaving 'explore opportunities to'
    #     which then strips 'opportunities to' (3B), yielding orphaned 'explore enhance'.
    #     With 3A first, 'explore opportunities to' is consumed as a unit → 'enhance'.
    (re.compile(r'\b\w+\s+opportunities\s+to\b', re.IGNORECASE), ''),

    # 3B. Fallback: bare 'opportunities to'
    (re.compile(r'\bopportunities\s+to\b', re.IGNORECASE), ''),

    # 4A. Modal+intent: 'we/I'd like to', 'we would like to'
    #     Does NOT match 'we would like 5 endpoints' (requires trailing 'to').
    (re.compile(r"\b(?:we|i|they)\'?(?:d|ll)?\s+(?:would\s+)?like\s+to\b", re.IGNORECASE), ''),

    # 4B. Modal+intent with role NP: 'we would like the engineering team to'
    #     Noun list restricted so 'we would like the API to return' doesn't fire.
    (re.compile(
        r"\b(?:we|i|they)\'?(?:d|ll)?\s+(?:would\s+)?like\s+the\s+"
        r'(?:engineering|product|development|design|security|platform|ops|devops|'
        r'qa|backend|frontend|architecture|data|ml|mobile)\s+'
        r'(?:team|group|squad|chapter|guild)\s+to\b',
        re.IGNORECASE), ''),

    # 5. Other modal+intent: 'we hope/want/wish/intend/plan/strive to'
    #    'need' and 'aim' excluded — they signal real requirements/metrics.
    (re.compile(
        r"\b(?:we|i|they|the\s+(?:team|organization|company|group))\'?(?:d|ll)?\s+"
        r'(?:would\s+)?(?:hope|want|wish|intend|plan|strive|endeavor)\s+to\b',
        re.IGNORECASE), ''),

    # 6. Continuous intent: 'we are looking/trying/hoping/working to'
    (re.compile(
        r'\b(?:we|i|the\s+(?:engineering|product|development|platform|\w+)?\s*team)\s+'
        r'(?:are|is|were)\s+(?:looking|trying|hoping|working)\s+to\b',
        re.IGNORECASE), ''),

    # 7. Obligation rewrite: 'are required to' → 'must' (preserves meaning, saves 2 words)
    (re.compile(r'\b(?:are|is|were|be)\s+required\s+to\b', re.IGNORECASE), 'must'),

    # 8. 'in order to' → 'to'
    (re.compile(r'\bin\s+order\s+to\b', re.IGNORECASE), 'to'),

    # 9A. MUST precede 9B: 'and provide recommendations regarding' → ', recommend'
    #     Absorbs 'and' so it isn't left as an orphaned conjunction.
    (re.compile(r'\band\s+provide\s+recommendations\s+regarding\b', re.IGNORECASE), ', recommend'),

    # 9B. 'provide recommendations regarding' → 'recommend'
    (re.compile(r'\bprovide\s+recommendations\s+regarding\b', re.IGNORECASE), 'recommend'),

    # 10. Risk boilerplate tail: ', and any risks that should be considered throughout the X process'
    (re.compile(
        r',?\s*(?:and\s+)?(?:any\s+)?risks?\s+that\s+should\s+be\s+considered\s+'
        r'(?:throughout|during|across)\s+the\s+\w+(?:\s+\w+)?\s+process\b',
        re.IGNORECASE), ''),

    # 11. Consequence clause: 'which has resulted in' → ','
    #     'setup, which has resulted in feedback' → 'setup, feedback'
    (re.compile(r',?\s*(?:which\s+)?(?:has|have)\s+resulted\s+in\b', re.IGNORECASE), ','),

    # 12. Stance opener: 'it is important/critical to note that'
    (re.compile(
        r'\bit\s+(?:is|should\s+be)\s+(?:important|worth|critical|key|essential)\s+to\s+'
        r'(?:note|mention|highlight|emphasize)\s+that\b',
        re.IGNORECASE), ''),

    # 13. 'it should be noted that'
    (re.compile(r'\bit\s+should\s+be\s+noted\s+that\b', re.IGNORECASE), ''),

    # 14. Transition filler phrases
    (re.compile(
        r'\b(?:with\s+(?:this|that)\s+in\s+mind|that\s+being\s+said|with\s+that\s+said)\b',
        re.IGNORECASE), ''),

    # 15. Alignment clause: 'that/which aligns with' → 'for'
    (re.compile(r'\b(?:that|which)\s+aligns?\s+with\b', re.IGNORECASE), 'for'),

    # 16. 'please provide a detailed' → 'provide'
    (re.compile(r'\bplease\s+provide\s+a\s+detailed\b', re.IGNORECASE), 'provide'),

    # 17. Interest scaffold: 'we are interested in understanding/exploring/evaluating'
    (re.compile(
        r'\b(?:we|i|they)\s+(?:are|am|were)\s+interested\s+in\s+'
        r'(?:understanding|exploring|evaluating|assessing|reviewing)\b',
        re.IGNORECASE), ''),
]

# -- word-level stop sets -----------------------------------------------------
EXTRA_STOP = {
    'hi', 'hey', 'hello', 'thanks', 'thank', 'please', 'okay', 'ok',
    'basically', 'essentially', 'literally', 'potentially', 'possibly',
    'certainly', 'definitely', 'absolutely', 'obviously', 'clearly',
    'indicating',  # hedging: 'indicating potential friction' → 'potential friction'
    'various',     # vague quantifier: 'various stakeholders' → 'stakeholders'
}

KEEP = {
    'not', 'no', 'never', 'neither', 'nor', 'none', 'without',
    'more', 'most', 'less', 'least', 'also', 'both', 'each',
    'few', 'other', 'some', 'such', 'only', 'same', 'than',
    'why', 'how', 'what', 'when', 'where', 'which', 'who',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'can',  # NLTK strips 'can' but 'Users can complete onboarding' must survive in AC items
}

STOP = (STOP | EXTRA_STOP) - KEEP

# -- passes -------------------------------------------------------------------

def _pre_pass(text: str) -> str:
    for pattern, replacement in PHRASE_PATTERNS:
        text = pattern.sub(replacement, text)
    return re.sub(r'[ \t]+', ' ', text)  # collapse horizontal space, preserve newlines


def _stop_pass(text: str) -> str:
    lines = text.split('\n')
    out = []
    for line in lines:
        tokens = line.split()
        kept = []
        for token in tokens:
            key = re.sub(r"[^a-z']", '', token.lower())
            if not key or key not in STOP:
                kept.append(token)
        out.append(' '.join(kept))
    return '\n'.join(out)


def _post_pass(text: str) -> str:
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            cleaned.append('')
            continue
        line = re.sub(r' ([,;:.!?])', r'\1', line)        # space before punctuation
        line = re.sub(r'([,;:])(\s*[,;:])+', r'\1', line)  # double punctuation
        line = re.sub(r'\.{2,}', '.', line)                # double periods
        line = re.sub(r'^[,;\s]+', '', line)               # leading punctuation artifacts
        line = re.sub(r'\band\s+to\b', 'to', line, flags=re.IGNORECASE)  # orphaned 'and to'
        line = re.sub(r'^(?:and|or|but),?\s+', '', line, flags=re.IGNORECASE)
        if line:
            line = line[0].upper() + line[1:]
        cleaned.append(line)
    text = '\n'.join(cleaned)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return re.sub(r'  +', ' ', text).strip()


def compress(text: str) -> str:
    text = _pre_pass(text)
    text = _stop_pass(text)
    text = _post_pass(text)
    return text
