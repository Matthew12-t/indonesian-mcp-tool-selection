"""Analyze downloaded Kaggle outputs. Never invent or impute missing runs.

Usage: python 03_analyze_results.py <kaggle_dataset_dir> <downloaded_outputs_dir> <analysis_dir>
The output directory must contain one subdirectory per model with the raw JSONL
and run manifest downloaded from its completed Kaggle kernel.
"""

import csv
import hashlib
import json
import pathlib
import random
import sys
from collections import Counter, defaultdict


MODELS = ("qwen3_8b", "llama3.1_8b", "mistral_7b")
DESC = ("en", "id")
LANG = ("en", "id", "mix")
REPS = (1, 2, 3)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def subset(expected, actual):
    """Require every gold field, permitting additional optional model fields."""
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            k in actual and subset(v, actual[k]) for k, v in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) >= len(expected) and all(
            subset(e, a) for e, a in zip(expected, actual)
        )
    return expected == actual


def bootstrap_diff(pairs, seed=42, iterations=10000):
    """Paired query-cluster bootstrap; pairs are per-query means across repeats."""
    rng = random.Random(seed)
    n = len(pairs)
    if not n:
        raise ValueError("No pairs")
    diffs = sorted(sum(pairs[rng.randrange(n)] for _ in range(n)) / n
                   for _ in range(iterations))
    return round(diffs[int(.025 * iterations)], 6), round(diffs[int(.975 * iterations)], 6)


def main():
    dataset, downloads, out = map(pathlib.Path, sys.argv[1:4])
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((dataset / "dataset_manifest.json").read_text(encoding="utf-8"))
    for name in ("tools_id.json", "queries.json"):
        assert sha(dataset / name) == manifest["sha256"][name], name
    queries = json.loads((dataset / "queries.json").read_text(encoding="utf-8"))["queries"]
    assert len(queries) == 150
    by_id = {q["id"]: q for q in queries}
    assert len(by_id) == len(queries)
    all_records = {}
    for model in MODELS:
        root = downloads / model
        raw = root / f"raw_results_{model}.jsonl"
        meta = root / f"run_manifest_{model}.json"
        assert raw.is_file() and meta.is_file(), f"Missing completed Kaggle output: {model}"
        m = json.loads(meta.read_text(encoding="utf-8"))
        assert m["raw_results_sha256"] == sha(raw), f"Raw hash mismatch: {model}"
        assert m["dataset_sha256"] == manifest["sha256"], f"Dataset hash mismatch: {model}"
        assert m["tools_en_sha256"] == sha(dataset / "tools_en.json"), model
        assert m["n_calls"] == 2700, model
        seen = set()
        for line in raw.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            assert r["model"].replace(":", "_") == model
            key = (model, r["rep"], r["desc_lang"], r["query_lang"], r["qid"])
            assert key not in seen, f"Duplicate {key}"
            seen.add(key)
            q = by_id[r["qid"]]
            assert r["gold_tool"] == q["gold_tool"] and r["category"] == q["category"]
            r["tool_correct"] = r["first_tool"] == q["gold_tool"]
            r["tool_lenient"] = r["first_tool"] in [q["gold_tool"], *q["lenient_alt_tools"]]
            r["params_correct"] = r["tool_correct"] and subset(q["gold_params"], r["first_args"])
            r["joint_correct"] = r["params_correct"]
            all_records[key] = r
        assert len(seen) == 2700, f"Incomplete run: {model}, {len(seen)} rows"
        expected = {(model, rep, dl, ql, qid) for rep in REPS for dl in DESC
                    for ql in LANG for qid in by_id}
        assert seen == expected, f"Missing or unexpected conditions: {model}"

    summary = []
    for model in MODELS:
        for dl in DESC:
            for ql in LANG:
                rows = [all_records[model, rep, dl, ql, qid]
                        for rep in REPS for qid in by_id]
                correct = sum(r["tool_correct"] for r in rows)
                summary.append({
                    "model": model, "description_language": dl, "query_language": ql,
                    "n": len(rows), "tool_accuracy": correct / len(rows),
                    "tool_accuracy_lenient": sum(r["tool_lenient"] for r in rows) / len(rows),
                    "parameter_accuracy_conditional":
                        sum(r["params_correct"] for r in rows) / correct if correct else "",
                    "joint_accuracy": sum(r["joint_correct"] for r in rows) / len(rows),
                    "no_tool_rate": sum(r["first_tool"] is None for r in rows) / len(rows),
                    "error_rate": sum(bool(r["error"]) for r in rows) / len(rows),
                })
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    by_category = []
    for model in MODELS:
        for dl in DESC:
            for ql in LANG:
                for category in ("direct", "confusable", "complex"):
                    qids = [qid for qid, q in by_id.items() if q["category"] == category]
                    rows = [all_records[model, rep, dl, ql, qid]
                            for rep in REPS for qid in qids]
                    by_category.append({"model": model, "description_language": dl,
                                        "query_language": ql, "category": category,
                                        "n": len(rows),
                                        "tool_accuracy": sum(r["tool_correct"] for r in rows) / len(rows)})
    with (out / "category_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(by_category[0]))
        writer.writeheader()
        writer.writerows(by_category)

    paired = []
    for model in MODELS:
        for ql in LANG:
            query_diffs = []
            for qid in by_id:
                a = sum(all_records[model, rep, "id", ql, qid]["tool_correct"] for rep in REPS) / len(REPS)
                b = sum(all_records[model, rep, "en", ql, qid]["tool_correct"] for rep in REPS) / len(REPS)
                query_diffs.append(a - b)
            lo, hi = bootstrap_diff(query_diffs)
            paired.append({"model": model, "query_language": ql,
                           "id_minus_en_accuracy": sum(query_diffs) / len(query_diffs),
                           "ci95_low": lo, "ci95_high": hi, "n_query_clusters": len(query_diffs)})
    with (out / "paired_description_effect.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(paired[0]))
        writer.writeheader()
        writer.writerows(paired)

    language_effects = []
    for model in MODELS:
        for dl in DESC:
            for newer, baseline in (("id", "en"), ("mix", "en"), ("mix", "id")):
                query_diffs = []
                for qid in by_id:
                    a = sum(all_records[model, rep, dl, newer, qid]["tool_correct"]
                            for rep in REPS) / len(REPS)
                    b = sum(all_records[model, rep, dl, baseline, qid]["tool_correct"]
                            for rep in REPS) / len(REPS)
                    query_diffs.append(a - b)
                lo, hi = bootstrap_diff(query_diffs)
                language_effects.append({"model": model, "description_language": dl,
                                         "contrast": f"{newer}_minus_{baseline}",
                                         "accuracy_difference": sum(query_diffs) / len(query_diffs),
                                         "ci95_low": lo, "ci95_high": hi,
                                         "n_query_clusters": len(query_diffs)})
    with (out / "paired_query_language_effect.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(language_effects[0]))
        writer.writeheader()
        writer.writerows(language_effects)
    server_summary = []
    outcome_summary = []
    repeat_consistency = []
    wrong_tool_pairs = []
    for model in MODELS:
        model_rows = [r for (m, *_), r in all_records.items() if m == model]
        pair_counts = Counter((r["gold_tool"], r["first_tool"]) for r in model_rows
                              if r["first_tool"] is not None and not r["tool_correct"])
        wrong_tool_pairs.extend({"model": model, "gold_tool": gold, "selected_tool": selected,
                                 "n": count}
                                for (gold, selected), count in sorted(
                                    pair_counts.items(), key=lambda item: (-item[1], item[0])))
        for server in ("filesystem", "git", "memory", "time", "fetch"):
            rows = [r for r in model_rows if by_id[r["qid"]]["server"] == server]
            server_summary.append({
                "model": model, "server": server, "n": len(rows),
                "tool_accuracy": sum(r["tool_correct"] for r in rows) / len(rows),
                "joint_accuracy": sum(r["joint_correct"] for r in rows) / len(rows),
                "no_tool_rate": sum(r["first_tool"] is None for r in rows) / len(rows),
            })
        outcomes = defaultdict(int)
        for r in model_rows:
            if r["error"]:
                outcomes["api_error"] += 1
            elif r["first_tool"] is None:
                outcomes["no_call"] += 1
            elif not r["tool_correct"]:
                outcomes["wrong_tool"] += 1
            elif not r["params_correct"]:
                outcomes["correct_tool_wrong_args"] += 1
            else:
                outcomes["joint_correct"] += 1
        assert sum(outcomes.values()) == 2700
        outcome_summary.append({"model": model, "n": 2700, **{
            k: outcomes[k] for k in ("api_error", "no_call", "wrong_tool",
                                  "correct_tool_wrong_args", "joint_correct")}})
        for dl in DESC:
            for ql in LANG:
                clusters = [[all_records[model, rep, dl, ql, qid] for rep in REPS]
                            for qid in by_id]
                repeat_consistency.append({
                    "model": model, "description_language": dl, "query_language": ql,
                    "n_query_clusters": len(clusters),
                    "same_first_tool_rate": sum(len({r["first_tool"] for r in c}) == 1
                                                for c in clusters) / len(clusters),
                    "same_first_args_rate": sum(len({json.dumps(r["first_args"], sort_keys=True)
                                                    for r in c}) == 1
                                                for c in clusters) / len(clusters),
                    "same_correctness_rate": sum(len({r["tool_correct"] for r in c}) == 1
                                                 for c in clusters) / len(clusters),
                    "all_three_correct_rate": sum(all(r["tool_correct"] for r in c)
                                                  for c in clusters) / len(clusters),
                    "any_correct_rate": sum(any(r["tool_correct"] for r in c)
                                            for c in clusters) / len(clusters),
                })
    for filename, rows in (("server_summary.csv", server_summary),
                           ("outcome_summary.csv", outcome_summary),
                           ("repeat_consistency.csv", repeat_consistency),
                           ("wrong_tool_pairs.csv", wrong_tool_pairs)):
        with (out / filename).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(f"Verified {len(all_records)} Kaggle responses; wrote summaries and diagnostics to {out}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main()
