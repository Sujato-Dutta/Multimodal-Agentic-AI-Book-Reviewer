from collections import Counter


def title_author_f1(predicted_title: str, predicted_author: str,
                    true_title: str, true_author: str) -> dict:
    """Token-level F1 for title and author."""
    def f1(pred: str, true: str) -> float:
        pred_tokens = Counter(pred.lower().split())
        true_tokens = Counter(true.lower().split())
        common = sum((pred_tokens & true_tokens).values())
        if common == 0:
            return 0.0
        precision = common / sum(pred_tokens.values())
        recall = common / sum(true_tokens.values())
        return 2 * precision * recall / (precision + recall)

    return {
        "title_f1": f1(predicted_title, true_title),
        "author_f1": f1(predicted_author, true_author),
        "combined_f1": (f1(predicted_title, true_title) + f1(predicted_author, true_author)) / 2,
    }


def precision_at_k(retrieved_sources: list[str],
                   relevant_sources: list[str], k: int = 5) -> float:
    top_k = retrieved_sources[:k]
    if not top_k:
        return 0.0
    relevant_set = set(s.lower() for s in relevant_sources)
    hits = sum(1 for s in top_k if s.lower() in relevant_set)
    return hits / len(top_k)


def citation_coverage(cited_sources: list[str],
                      available_sources: list[str]) -> float:
    if not available_sources:
        return 0.0
    cited_set = set(s.lower() for s in cited_sources)
    available_set = set(s.lower() for s in available_sources)
    if not available_set:
        return 0.0
    return len(cited_set & available_set) / len(available_set)


def hallucination_check(review_text: str, source_texts: list[str]) -> float:
    """Simple keyword-based hallucination detection.
    Returns fraction of review sentences that have some support in sources."""
    if not review_text or not source_texts:
        return 0.0

    combined_source = " ".join(source_texts).lower()
    sentences = [s.strip() for s in review_text.split(".") if len(s.strip()) > 10]
    if not sentences:
        return 1.0

    supported = 0
    for sentence in sentences:
        words = sentence.lower().split()
        key_words = [w for w in words if len(w) > 4]
        if not key_words:
            supported += 1
            continue
        matches = sum(1 for w in key_words if w in combined_source)
        if matches / len(key_words) > 0.3:
            supported += 1

    return supported / len(sentences)


def recommendation_agreement(predicted: str, expected: str) -> float:
    return 1.0 if predicted.lower() == expected.lower() else 0.0


def compute_latency_percentiles(latencies: list[float]) -> dict:
    if not latencies:
        return {"p50": 0.0, "p95": 0.0}
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    return {
        "p50": sorted_lat[int(n * 0.5)],
        "p95": sorted_lat[int(n * 0.95)] if n > 1 else sorted_lat[-1],
    }
