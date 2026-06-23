import difflib
import os
import re
import string
from dataclasses import dataclass

from entity_ontology_v1 import split_entity_set


def normalize(value):
    text = "" if value is None else str(value).lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = text.strip(string.punctuation + " ")
    tokens = []
    for token in text.split():
        token = token.strip(string.punctuation)
        if len(token) > 3 and token.endswith("s"):
            token = token[:-1]
        if token:
            tokens.append(token)
    return " ".join(tokens)


def token_set(value):
    return set(re.findall(r"[a-z0-9]+", normalize(value)))


def safe_div(num, den):
    return num / den if den else 0.0


def soft_f1(precision, recall):
    return safe_div(2 * precision * recall, precision + recall)


def canonical_entities(values):
    output = set()
    for value in values:
        output.update(split_entity_set(value))
    return output


def exact_canonical_similarity(gold, pred):
    return 1.0 if canonical_entities([gold]) & canonical_entities([pred]) else 0.0


def normalized_exact_similarity(gold, pred):
    return 1.0 if normalize(gold) and normalize(gold) == normalize(pred) else 0.0


def token_jaccard_similarity(gold, pred):
    gold_tokens = token_set(gold)
    pred_tokens = token_set(pred)
    return safe_div(len(gold_tokens & pred_tokens), len(gold_tokens | pred_tokens))


def difflib_similarity(gold, pred):
    return difflib.SequenceMatcher(None, normalize(gold), normalize(pred)).ratio()


def greedy_soft_match(gold_values, pred_values, similarity_fn, threshold):
    pairs = []
    for gold_index, gold in enumerate(gold_values):
        for pred_index, pred in enumerate(pred_values):
            score = similarity_fn(gold, pred)
            if score >= threshold:
                pairs.append((score, gold_index, pred_index, gold, pred))
    pairs.sort(key=lambda item: (-item[0], item[1], item[2]))
    used_gold = set()
    used_pred = set()
    matches = []
    for score, gold_index, pred_index, gold, pred in pairs:
        if gold_index in used_gold or pred_index in used_pred:
            continue
        used_gold.add(gold_index)
        used_pred.add(pred_index)
        matches.append({"gold": gold, "pred": pred, "score": score})
    return matches


def score_pair(gold_values, pred_values, similarity_fn, threshold):
    gold_values = sorted({value for value in gold_values if value})
    pred_values = sorted({value for value in pred_values if value})
    matches = greedy_soft_match(gold_values, pred_values, similarity_fn, threshold)
    match_count = len(matches)
    precision = safe_div(match_count, len(pred_values))
    recall = safe_div(match_count, len(gold_values))
    return {
        "gold_count": len(gold_values),
        "pred_count": len(pred_values),
        "matches": match_count,
        "soft_precision": precision,
        "soft_recall": recall,
        "soft_f1": soft_f1(precision, recall),
        "soft_jaccard": safe_div(match_count, len(gold_values) + len(pred_values) - match_count),
        "matched_pairs": matches,
    }


def score_rows(row_pairs, similarity_fn, threshold):
    scored = [score_pair(gold, pred, similarity_fn, threshold) for gold, pred in row_pairs]
    n = len(scored)
    return {
        "rows": n,
        "soft_precision": safe_div(sum(row["soft_precision"] for row in scored), n),
        "soft_recall": safe_div(sum(row["soft_recall"] for row in scored), n),
        "soft_f1": safe_div(sum(row["soft_f1"] for row in scored), n),
        "soft_jaccard": safe_div(sum(row["soft_jaccard"] for row in scored), n),
    }


@dataclass
class EmbeddingMatcher:
    available: bool
    reason: str
    model: object = None
    embeddings: dict = None

    @classmethod
    def load(cls):
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:
            return cls(False, f"sentence-transformers unavailable: {exc}")
        try:
            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", local_files_only=True)
        except TypeError:
            try:
                model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            except Exception as exc:
                return cls(False, f"embedding model unavailable offline: {exc}")
        except Exception as exc:
            return cls(False, f"embedding model unavailable offline: {exc}")
        return cls(True, "available", model, {})

    def prepare(self, values):
        if not self.available:
            return
        missing = [value for value in sorted(set(values)) if value and value not in self.embeddings]
        if not missing:
            return
        vectors = self.model.encode(missing, normalize_embeddings=True, show_progress_bar=False)
        for value, vector in zip(missing, vectors):
            self.embeddings[value] = vector

    def similarity(self, gold, pred):
        if not self.available:
            return 0.0
        self.prepare([gold, pred])
        return float(self.embeddings[gold] @ self.embeddings[pred])


MATCHER_SPECS = [
    {"name": "M0_exact_canonical", "threshold": 1.0, "kind": "surface", "similarity": exact_canonical_similarity},
    {"name": "M1_normalized_exact", "threshold": 1.0, "kind": "surface", "similarity": normalized_exact_similarity},
    {"name": "M2_token_set_jaccard", "threshold": 0.3, "kind": "surface", "similarity": token_jaccard_similarity},
    {"name": "M2_token_set_jaccard", "threshold": 0.5, "kind": "surface", "similarity": token_jaccard_similarity},
    {"name": "M3_fuzzy_difflib", "threshold": 0.6, "kind": "surface", "similarity": difflib_similarity},
    {"name": "M3_fuzzy_difflib", "threshold": 0.7, "kind": "surface", "similarity": difflib_similarity},
    {"name": "M3_fuzzy_difflib", "threshold": 0.8, "kind": "surface", "similarity": difflib_similarity},
    {"name": "M3_fuzzy_difflib", "threshold": 0.9, "kind": "surface", "similarity": difflib_similarity},
]

EMBEDDING_THRESHOLDS = [0.5, 0.6, 0.7, 0.8]
