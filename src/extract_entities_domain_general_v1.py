import argparse
import csv
import json
import re
import string
from collections import Counter
from pathlib import Path

from entity_matchers_diagnostic import normalize


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "for", "from", "has",
    "have", "if", "in", "into", "is", "it", "its", "not", "of", "on", "or", "rather",
    "should", "so", "than", "that", "the", "their", "then", "there", "this", "to",
    "under", "unless", "use", "when", "where", "which", "with", "without",
}
SENTENCE_INITIAL_COMMON = {
    "A", "An", "And", "As", "During", "For", "If", "In", "On", "The", "This", "When",
}
MAX_SPAN_WORDS = 6
NOUN_CHUNK_TOP_K = 8


def clean_span(value):
    text = "" if value is None else str(value).strip()
    text = text.strip(string.punctuation + " ")
    text = re.sub(r"\s+", " ", text)
    return text


def span_words(span):
    return re.findall(r"[A-Za-z0-9][\w&/-]*", span)


def is_stopword_span(span):
    words = [word.lower() for word in span_words(span)]
    return not words or all(word in STOPWORDS for word in words)


def valid_span(span, max_words=MAX_SPAN_WORDS):
    words = span_words(span)
    return bool(words) and 1 <= len(words) <= max_words and not is_stopword_span(span)


def dedupe_spans(spans):
    seen = set()
    output = []
    for span in spans:
        cleaned = clean_span(span)
        key = normalize(cleaned)
        if not key or key in seen or not valid_span(cleaned):
            continue
        seen.add(key)
        output.append(cleaned)
    return output


def proper_quoted(text):
    spans = []
    for match in re.finditer(r"[\"']([^\"']{2,120})[\"']", text):
        spans.append(match.group(1))
    pattern = re.compile(r"\b[A-Z][\w&/-]*(?:\s+[A-Z][\w&/-]*)*")
    for match in pattern.finditer(text):
        span = clean_span(match.group(0))
        words = span_words(span)
        if len(words) == 1 and words[0] in SENTENCE_INITIAL_COMMON:
            continue
        spans.append(span)
    return dedupe_spans(spans)


def content_tokens(text):
    tokens = []
    for token in re.findall(r"[A-Za-z0-9][\w&/-]*", text):
        norm = normalize(token)
        if not norm or norm in STOPWORDS:
            tokens.append(None)
        else:
            tokens.append(token)
    return tokens


def noun_chunks_topk(text):
    chunks = []
    current = []
    for token in content_tokens(text):
        if token is None:
            if current:
                chunks.append(current)
                current = []
            continue
        current.append(token)
    if current:
        chunks.append(current)

    candidates = []
    for chunk in chunks:
        for start in range(len(chunk)):
            for end in range(start + 1, min(len(chunk), start + 4) + 1):
                words = chunk[start:end]
                span = clean_span(" ".join(words))
                if valid_span(span, max_words=4):
                    candidates.append(span)
    counts = Counter(normalize(span) for span in candidates)
    best_by_key = {}
    for span in candidates:
        key = normalize(span)
        words = span_words(span)
        has_capital = any(word[:1].isupper() for word in words)
        score = counts[key] * (1 + 0.5 * int(has_capital)) * min(len(words), 3)
        current = best_by_key.get(key)
        if current is None or score > current[0]:
            best_by_key[key] = (score, span)
    ranked = sorted(best_by_key.values(), key=lambda item: (-item[0], normalize(item[1]), item[1]))
    return [span for _, span in ranked[:NOUN_CHUNK_TOP_K]]


def extract_entities(text, variant):
    if variant == "proper_quoted":
        return proper_quoted(text)
    if variant == "noun_chunks_topk":
        return noun_chunks_topk(text)
    raise ValueError(f"Unknown variant: {variant}")


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_predictions(gold_path, variant, out_path):
    rows = []
    for row in read_rows(gold_path):
        text = row.get("segment_text") or row.get("text", "")
        pred_entities = extract_entities(text, variant)
        rows.append({
            "segment_id": row["segment_id"],
            "segment_text": text,
            "gold_entities": row.get("gold_entities", ""),
            "pred_entities": "; ".join(pred_entities),
        })
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["segment_id", "segment_text", "gold_entities", "pred_entities"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--variant", choices=["proper_quoted", "noun_chunks_topk"], required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    rows = write_predictions(args.gold, args.variant, Path(args.out))
    print("domain_general_entity_extractor_v1")
    print(f"variant={args.variant}")
    print(f"rows={len(rows)}")
    print(f"out={args.out}")


if __name__ == "__main__":
    main()
