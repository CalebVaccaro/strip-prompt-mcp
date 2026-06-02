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

EXTRA_STOP = {
    'hi', 'hey', 'hello', 'thanks', 'thank', 'please', 'okay', 'ok',
    'basically', 'essentially', 'literally', 'potentially', 'possibly',
    'certainly', 'definitely', 'absolutely', 'obviously', 'clearly',
}

KEEP = {
    'not', 'no', 'never', 'neither', 'nor', 'none', 'without',
    'more', 'most', 'less', 'least', 'also', 'both', 'each',
    'few', 'other', 'some', 'such', 'only', 'same', 'than',
    'why', 'how', 'what', 'when', 'where', 'which', 'who',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
}

STOP = (STOP | EXTRA_STOP) - KEEP


def compress(text: str) -> str:
    tokens = text.split()
    result = []
    for token in tokens:
        key = re.sub(r"[^a-z']", '', token.lower())
        if not key or key not in STOP:
            result.append(token)
    return re.sub(r'  +', ' ', ' '.join(result)).strip()
