import json
import requests
from urllib.parse import quote

DATASET_PATH = "test_dataset.json"
API_URL = "http://localhost:8000/documents-chunks/relevant"

TOP_K_VALUES = [5, 10]


def get_relevant_chunks(query, top_k):
    response = requests.get(
        API_URL,
        params={
            "query": query,
            "top_k": top_k,
        },
        headers={"accept": "application/json"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def is_valid_chunk(chunk, cited_docs):
    """
    A retrieved chunk is considered valid if any cited document ID
    occurs in chunk.content.
    """
    content = chunk.get("content", "")

    return any(doc_id in content for doc_id in cited_docs)


def evaluate_case(case):
    claim = case["claim"]
    cited_docs = case["cited_docs"]

    results = {}

    # Fetch top-10 once. Top-5 is simply the first 5.
    chunks = get_relevant_chunks(claim, 10)

    # In case API returns fewer than 10.
    chunks = chunks[:10]

    for k in TOP_K_VALUES:
        top_k_chunks = chunks[:k]

        relevant_positions = [
            rank
            for rank, chunk in enumerate(top_k_chunks, start=1)
            if is_valid_chunk(chunk, cited_docs)
        ]

        # R@k:
        # 1 if at least one relevant chunk was retrieved, otherwise 0.
        r_at_k = 1.0 if relevant_positions else 0.0

        # Recall@k:
        # Number of cited documents found / total number of cited documents.
        #
        # A document is considered found if its ID occurs in at least one
        # retrieved chunk's content.
        found_docs = {
            doc_id
            for doc_id in cited_docs
            if any(
                doc_id in chunk.get("content", "")
                for chunk in top_k_chunks
            )
        }

        recall_at_k = (
            len(found_docs) / len(set(cited_docs))
            if cited_docs
            else 0.0
        )

        results[f"r@{k}"] = r_at_k
        results[f"recall@{k}"] = recall_at_k

    # MRR: reciprocal rank of the first relevant retrieved chunk.
    relevant_positions = [
        rank
        for rank, chunk in enumerate(chunks, start=1)
        if is_valid_chunk(chunk, cited_docs)
    ]

    mrr = 1.0 / relevant_positions[0] if relevant_positions else 0.0

    results["mrr"] = mrr
    results["first_relevant_rank"] = (
        relevant_positions[0] if relevant_positions else None
    )

    return results


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    test_cases = dataset["test"]

    aggregate = {
        "r@5": 0.0,
        "recall@5": 0.0,
        "r@10": 0.0,
        "recall@10": 0.0,
        "mrr": 0.0,
    }

    case_results = []

    for i, case in enumerate(test_cases, start=1):
        try:
            result = evaluate_case(case)

            for metric in aggregate:
                aggregate[metric] += result[metric]

            case_results.append({
                "index": i,
                "claim": case["claim"],
                "cited_docs": case["cited_docs"],
                **result,
            })

            print(
                f"[{i}/{len(test_cases)}] "
                f"R@5={result['r@5']:.4f} "
                f"Recall@5={result['recall@5']:.4f} "
                f"R@10={result['r@10']:.4f} "
                f"Recall@10={result['recall@10']:.4f} "
                f"MRR={result['mrr']:.4f}"
            )

        except Exception as e:
            print(f"[{i}/{len(test_cases)}] ERROR: {e}")

    n = len(case_results)

    if n == 0:
        print("No test cases were successfully evaluated.")
        return

    aggregate = {
        metric: value / n
        for metric, value in aggregate.items()
    }

    print("\n" + "=" * 60)
    print("AGGREGATE RESULTS")
    print("=" * 60)

    for metric, value in aggregate.items():
        print(f"{metric:12s}: {value:.4f}")

    # Optional: save detailed results.
    output = {
        "num_test_cases": n,
        "metrics": aggregate,
        "cases": case_results,
    }

    with open("retrieval_eval_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\nDetailed results written to retrieval_eval_results.json")


if __name__ == "__main__":
    main()
