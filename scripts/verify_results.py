#!/usr/bin/env python3
"""Audit persisted results against source tokens and independent conservation identities.

Example: python3 scripts/verify_results.py --corpus ../sblgnt --results results \
    --mask-file data/quote_verses.json

Standard library only. Temporary corruption probes run outside the repository.
This checks numerical/provenance claims, not the validity of authorship inference.
"""

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import unicodedata


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def close(actual, expected, label):
    require(math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12),
            f"{label}: {actual!r} != {expected!r}")


def read_csv(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(args):
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "analyze.py"
    summary = json.loads((args.results / "summary.json").read_text())
    require(summary["script_sha256"] == digest(script), "Results use a different analysis script")
    if summary["mask_sha256"] is not None:
        require(args.mask_file is not None, "Pass the mask file used to generate these results")
        require(summary["mask_sha256"] == digest(args.mask_file), "Result mask hash mismatch")

    raw, masks = {}, {}
    for item in summary["corpus_files"]:
        path = args.corpus / item["filename"]
        require(digest(path) == item["sha256"], f"Input hash mismatch: {path.name}")
        raw[item["book"]] = [line.split() for line in path.read_text().splitlines()]
        require(len(raw[item["book"]]) == item["tokens"], "Source token total mismatch")
    if args.mask_file:
        for book, intervals in json.loads(args.mask_file.read_text()).items():
            if not book.startswith("_"):
                masks[book] = {(chapter, verse) for chapter, first, last in intervals
                               for verse in range(first, last + 1)}
    configs = {r["config_id"]: r for r in summary["configurations"]}
    references = [b for members in summary["groups"].values() for b in members]
    source_cache, counts_cache = {}, {}

    def source(cid, text):
        key = cid, text
        if key not in source_cache:
            cfg = configs[cid]
            book = "Heb" if text == "Heb_without_ch13" else text
            kept = []
            for index, fields in enumerate(raw[book], 1):
                chapter, verse = int(fields[0][2:4]), int(fields[0][4:6])
                if text == "Heb_without_ch13" and chapter == 13:
                    continue
                if cfg["mask_mode"] == "quote_masked" and (chapter, verse) in masks.get(book, set()):
                    continue
                kept.append((index, fields))
            source_cache[key] = kept
        return source_cache[key]

    def counts(cid, rows):
        cfg = configs[cid]
        allowed = {"C-", "P-", "RA", "X-"}
        if cfg["pronouns"]:
            allowed.update({"RD", "RI", "RP", "RR"})
        column = 5 if cfg["form"] == "surface" else 6
        return Counter(unicodedata.normalize("NFC", fields[column])
                       for _, fields in rows if fields[1] in allowed)

    def whole_counts(cid, text):
        key = cid, text
        if key not in counts_cache:
            counts_cache[key] = counts(cid, source(cid, text))
        return counts_cache[key]

    features = defaultdict(list)
    for row in read_csv(args.results / "fold_features.csv"):
        features[row["config_id"], row["fold"]].append(row)
    for (cid, fold), rows in features.items():
        expected = [b for b in references if fold != f"holdout_{b}"]
        for row in rows:
            require(row["training_books"].split("|") == expected, f"Wrong fold membership: {cid} {fold}")
            require(int(row["n_training_books"]) == len(expected), "Wrong training-book denominator")
            word = row["feature"]
            frequencies = {b: whole_counts(cid, b)[word] / len(source(cid, b)) for b in expected}
            close(float(row["mean_training_frequency"]), statistics.mean(frequencies.values()), "Training mean")
            close(float(row["training_book_sd"]), statistics.stdev(frequencies.values()), "Training sample SD")
            for group, field in [("Paul_reference", "paul_centroid_frequency"),
                                 ("Luke_Acts_reference", "luke_acts_centroid_frequency")]:
                values = [frequencies[b] for b in expected if b in summary["groups"][group]]
                close(float(row[field]), statistics.mean(values), "Equal-book centroid")

    whole = list(read_csv(args.results / "whole_book_distances.csv"))
    whole_index = {(r["config_id"], r["metric"], r["text"]): r for r in whole}
    for row in whole:
        cid, text = row["config_id"], row["text"]
        fs = features[cid, row["fold"]]
        n = len(source(cid, text))
        require(n == int(row["tokens"]), "Whole-text denominator mismatch")
        x = [whole_counts(cid, text)[r["feature"]] / n for r in fs]
        x.append(1 - math.fsum(x))
        for group, field in [("paul", "distance_paul"), ("luke_acts", "distance_luke_acts")]:
            mu = [float(r[group + "_centroid_frequency"]) for r in fs]
            mu.append(1 - math.fsum(mu))
            if row["metric"] == "hellinger":
                distance = math.sqrt(math.fsum((math.sqrt(a) - math.sqrt(b)) ** 2
                                               for a, b in zip(x, mu)) / 2)
            else:
                terms = [abs(x[j] - mu[j]) / float(f["training_book_sd"])
                         for j, f in enumerate(fs) if f["active_for_delta"] == "True"]
                distance = statistics.mean(terms)
            close(distance, float(row[field]), "Raw-source reconstruction of distance")
        close(float(row["margin_luke_minus_paul"]),
              float(row["distance_luke_acts"]) - float(row["distance_paul"]), "Margin sign")

    contributions = defaultdict(lambda: [0.0, 0.0])
    for row in read_csv(args.results / "feature_contributions.csv"):
        key = row["config_id"], row["metric"], row["text"]
        contributions[key][0] += float(row["paul_distance_contribution"])
        contributions[key][1] += float(row["luke_acts_distance_contribution"])
    for key, values in contributions.items():
        for value, field in zip(values, ["distance_paul", "distance_luke_acts"]):
            expected = float(whole_index[key][field])
            close(value, expected ** 2 if key[1] == "hellinger" else expected, "Contribution conservation")

    chunks = {}
    for row in read_csv(args.results / "chunk_frequencies.csv.gz"):
        cid, text, fold = row["config_id"], row["text"], row["fold"]
        size, index = int(row["chunk_size"]), int(row["chunk_index"])
        key = cid, text, fold, size, index
        if key not in chunks:
            block = source(cid, text)[(index - 1) * size:index * size]
            require(len(block) == size, "Incomplete block included")
            chunks[key] = {"counts": counts(cid, block), "seen": set(), "sum_count": 0, "sum_freq": 0.0}
        state = chunks[key]
        selected = [f["feature"] for f in features[cid, fold]]
        word = row["feature"]
        require(word not in state["seen"], "Duplicate chunk feature")
        require(word in selected or word == "<OTHER>", "Unexpected chunk feature")
        expected = (size - sum(state["counts"][f] for f in selected)
                    if word == "<OTHER>" else state["counts"][word])
        require(int(row["count"]) == expected, "Chunk count differs from raw retained tokens")
        close(float(row["frequency"]), expected / size, "Chunk feature denominator")
        state["seen"].add(word)
        state["sum_count"] += expected
        state["sum_freq"] += float(row["frequency"])
    for key, state in chunks.items():
        expected_features = {f["feature"] for f in features[key[0], key[2]]} | {"<OTHER>"}
        require(state["seen"] == expected_features, "Missing chunk feature rows")
        require(state["sum_count"] == key[3], "Chunk counts do not conserve tokens")
        close(state["sum_freq"], 1, "Chunk distribution normalization")
    actual_blocks = Counter((cid, text, size) for cid, text, _, size, _ in chunks)
    for row in read_csv(args.results / "chunk_coverage.csv"):
        cid, text, size = row["config_id"], row["text"], int(row["chunk_size"])
        n = len(source(cid, text))
        require(int(row["retained_tokens"]) == n, "Coverage retained-token total")
        require(int(row["complete_chunks"]) == n // size, "Coverage complete-block count")
        require(actual_blocks[cid, text, size] == n // size, "Missing or extra chunk profiles")
        require(int(row["tail_tokens_excluded"]) == n % size, "Coverage tail count")
        close(float(row["tail_fraction"]), (n % size) / n, "Coverage tail denominator")

    spec = importlib.util.spec_from_file_location("hebrews_analysis_audit", script)
    analysis = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = analysis
    spec.loader.exec_module(analysis)
    corpus, manifest = analysis.load_corpus(args.corpus)
    profiles = {b: analysis.profile(ts, "lemma", False) for b, ts in corpus.items()}
    original = analysis.fit(profiles, references, 30)
    for book in ["Heb"] + summary["comparison_texts_without_assigned_authorship_truth"]:
        profiles[book] = {"n": 1, "counts": Counter({"AUDIT_SENTINEL": 999})}
    require(analysis.fit(profiles, references, 30) == original, "Target/control mutation affected training")
    held = references[0]
    train = [b for b in references if b != held]
    original = analysis.fit(profiles, train, 30)
    profiles[held] = {"n": 1, "counts": Counter({"AUDIT_HELDOUT": 999})}
    require(analysis.fit(profiles, train, 30) == original, "Held-out mutation affected training")
    with tempfile.TemporaryDirectory(prefix="hebrews-source-audit-") as temporary:
        folder = Path(temporary)
        for item in manifest:
            shutil.copyfile(args.corpus / item["filename"], folder / item["filename"])
        changed = folder / manifest[0]["filename"]
        changed.write_bytes(changed.read_bytes() + b"\n")
        try:
            analysis.load_corpus(folder)
        except ValueError as error:
            require("SHA-256 mismatch" in str(error), "Unexpected corruption error")
        else:
            raise AssertionError("Corrupted source was accepted")
    return {"status": "passed", "whole_text_records_recomputed": len(whole),
            "fold_feature_sets_checked": len(features), "chunk_profiles_recomputed": len(chunks),
            "checks": ["source/script/mask hashes", "fold training exclusion and source-derived moments",
                       "raw-source distance reconstruction", "feature contribution conservation",
                       "raw-source chunk counts and normalization", "complete-block/tail accounting",
                       "target/control and held-out mutation invariance", "source corruption rejected"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--mask-file", type=Path)
    print(json.dumps(audit(parser.parse_args()), indent=2))
