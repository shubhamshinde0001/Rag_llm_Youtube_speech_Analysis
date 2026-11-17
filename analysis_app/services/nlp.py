import re
from collections import Counter

# Lightweight bilingual stop-word list. Extend this as your corpus grows.
STOP_WORDS = set("""
a an the and or but if then is am are was were be been being to of in on at for
from by with as it this that these those we our you your they their he she his her
i me my us do does did have has had will would can could should may might
hai hain tha thi the ho ka ki ke ko se mein me par aur ya ek yeh vah woh hum
aap apne apni apna is us un in kaam liye liye bhi nahi nahin kya kaise jo jab
tak toh to par ek aur se mein main mera meri mere ham hum unka unki unke
""".split())

TOKEN_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|[\u0900-\u097F]+", re.UNICODE)

def tokenize(text, remove_stopwords=True):
    tokens = [t.lower() for t in TOKEN_RE.findall(text or "")]
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
    return tokens

def calculate_ngrams(text, max_n=3):
    tokens = tokenize(text)
    result = []
    for n in range(1, max_n + 1):
        counts = Counter(" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1))
        result.extend((phrase, n, count) for phrase, count in counts.most_common(100))
    return result

def count_words(text):
    return len(tokenize(text, remove_stopwords=False))
