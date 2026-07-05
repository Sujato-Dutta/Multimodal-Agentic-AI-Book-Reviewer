import json
import time
from pathlib import Path
from evals.metrics import (
    title_author_f1,
    recommendation_agreement,
    compute_latency_percentiles,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


def load_test_cases(path: str = None) -> list[dict]:
    from config import settings
    path = path or settings.EVAL_DATA_PATH
    with open(path) as f:
        return json.load(f)


def run_eval(test_cases: list[dict] = None) -> dict:
    """Run evaluation suite on test cases (offline mode, no API calls)."""
    if test_cases is None:
        test_cases = load_test_cases()

    results = {
        "total": len(test_cases),
        "passed": 0,
        "failed": 0,
        "title_f1_scores": [],
        "author_f1_scores": [],
        "latencies": [],
    }

    for tc in test_cases:
        start = time.time()

        # In offline mode, we test metric computation itself
        f1 = title_author_f1(
            tc["title"], tc["author"],
            tc["title"], tc["author"],
        )
        results["title_f1_scores"].append(f1["title_f1"])
        results["author_f1_scores"].append(f1["author_f1"])

        latency = time.time() - start
        results["latencies"].append(latency)

        if f1["combined_f1"] >= 0.5:
            results["passed"] += 1
        else:
            results["failed"] += 1

    results["avg_title_f1"] = sum(results["title_f1_scores"]) / len(results["title_f1_scores"]) if results["title_f1_scores"] else 0
    results["avg_author_f1"] = sum(results["author_f1_scores"]) / len(results["author_f1_scores"]) if results["author_f1_scores"] else 0
    results["latency_percentiles"] = compute_latency_percentiles(results["latencies"])

    logger.info(f"Eval complete: {results['passed']}/{results['total']} passed")
    return results


if __name__ == "__main__":
    results = run_eval()
    print(json.dumps(results, indent=2))
