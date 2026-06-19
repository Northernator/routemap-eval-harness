import re, math, json
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import numpy as np

STOPWORDS = set("""
a an the and or to of in on for from by with is are be if when where that this it as what actual operative rule document definition modification exception
after before does not no only briefly mentions final starting meaning later adjustment exclusion passage find about
""".split())

def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="ignore")

def split_segments(text, max_chars=900):
    raw = re.split(r"\n\s*\n+|\n(?=#{1,6}\s)", text)
    segs = []
    for part in raw:
        part = re.sub(r"\s+", " ", part.strip())
        if len(part) < 40:
            continue
        if len(part) <= max_chars:
            segs.append(part)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", part)
            buf = ""
            for s in sentences:
                if len(buf) + len(s) < max_chars:
                    buf += (" " if buf else "") + s
                else:
                    if len(buf) > 40:
                        segs.append(buf)
                    buf = s
            if len(buf) > 40:
                segs.append(buf)
    return segs

def toks(s):
    return [t for t in re.findall(r"[a-zA-Z0-9_]+", str(s).lower().replace("-", "_")) if t not in STOPWORDS and len(t) > 1]

def token_overlap_score(q, d):
    qt, dt = set(toks(q)), set(toks(d))
    return len(qt & dt) / (math.sqrt(len(qt)) + 1e-9)

def reciprocal_rank(ids, target):
    for rank, sid in enumerate(ids, 1):
        if sid == target:
            return 1.0 / rank
    return 0.0