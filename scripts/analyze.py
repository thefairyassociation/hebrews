#!/usr/bin/env python3
"""Reproducible exploratory Greek style distances, not authorship probabilities.

Run: python3 scripts/analyze.py --corpus ../sblgnt --output results
     [--mask-file data/quote_verses.json]

Uses Python's standard library only. No target data select features or fit scales.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import unicodedata


PINNED_COMMIT = "aaed91e57c8e4a8dc9a2383e129ca5e75fe6393d"
GROUPS = {
    "Paul_reference": ["Ro", "1Co", "2Co", "Ga", "Php", "1Th", "Phm"],
    "Luke_Acts_reference": ["Lk", "Ac"],
}
REFERENCES = sum(GROUPS.values(), [])
CONTROLS = ["Jas", "1Pe", "1Jn", "Mk", "Mt", "Jn"]
BOOKS = REFERENCES + ["Heb"] + CONTROLS
BASE_POS = frozenset(["C-", "P-", "RA", "X-"])
PRONOUN_POS = frozenset(["RD", "RI", "RP", "RR"])
OTHER = "<OTHER>"


@dataclass(frozen=True)
class Token:
    chapter: int
    verse: int
    pos: str
    surface: str
    lemma: str
    original_index: int


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_corpus(path: Path) -> tuple[dict, list]:
    pinned_path = Path(__file__).resolve().parents[1] / "data" / "corpus-manifest.json"
    pinned = json.loads(pinned_path.read_text(encoding="utf-8"))
    if pinned["commit"] != PINNED_COMMIT:
        raise ValueError("Manifest commit does not match the analysis's pinned corpus commit")
    books, manifest = {}, []
    for book in BOOKS:
        candidates = sorted(path.glob(f"*-{book}-morphgnt.txt"))
        if len(candidates) != 1:
            raise ValueError(f"Expected one source file for {book}: {candidates}")
        source = candidates[0]
        digest = sha256(source)
        if digest != pinned["files"][source.name]["sha256"]:
            raise ValueError(f"Corpus SHA-256 mismatch for {source.name}")
        tokens = []
        for index, line in enumerate(source.read_text(encoding="utf-8").splitlines()):
            parts = line.split()
            if len(parts) != 7 or len(parts[0]) != 6:
                raise ValueError(f"Unexpected MorphGNT record at {source.name}:{index + 1}")
            ref, pos, _parse, _text, _word, normalized, lemma = parts
            tokens.append(Token(int(ref[2:4]), int(ref[4:6]), pos,
                                unicodedata.normalize("NFC", normalized),
                                unicodedata.normalize("NFC", lemma), index + 1))
        books[book] = tokens
        manifest.append({"book": book, "filename": source.name,
                         "sha256": digest, "tokens": len(tokens)})
    return books, manifest


def read_masks(path: Path | None, books: dict) -> dict:
    if path is None:
        return {}
    masks = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(masks, dict):
        raise ValueError("Mask must map book abbreviations to [chapter,startverse,endverse] lists")
    # Underscore-prefixed metadata keys are permitted, but never interpreted as masks.
    result = {}
    for book, intervals in masks.items():
        if book.startswith("_"):
            continue
        if book not in books:
            raise ValueError(f"Unknown or unused mask book: {book}")
        available = {(t.chapter, t.verse) for t in books[book]}
        excluded = set()
        for interval in intervals:
            if (not isinstance(interval, list) or len(interval) != 3
                    or any(type(v) is not int for v in interval)):
                raise ValueError(f"Malformed mask interval: {book} {interval}")
            chapter, first, last = interval
            if first > last:
                raise ValueError(f"Reversed mask: {book} {interval}")
            for verse in range(first, last + 1):
                if (chapter, verse) not in available:
                    raise ValueError(f"Nonexistent source verse: {book} {chapter}:{verse}")
                excluded.add((chapter, verse))
        result[book] = excluded
    return result


def eligible_counts(tokens: list[Token], form: str, pronouns: bool) -> Counter:
    eligible = BASE_POS | PRONOUN_POS if pronouns else BASE_POS
    return Counter(getattr(t, form) for t in tokens if t.pos in eligible)


def profile(tokens: list[Token], form: str, pronouns: bool) -> dict:
    if not tokens:
        raise ValueError("Cannot profile an empty text")
    return {"n": len(tokens), "counts": eligible_counts(tokens, form, pronouns)}


def vector(prof: dict, features: list[str]) -> list[float]:
    values = [prof["counts"][f] / prof["n"] for f in features]
    residual = 1.0 - math.fsum(values)
    if residual < -1e-12:
        raise AssertionError("Selected feature frequencies exceed one")
    result = values + [max(0.0, residual)]
    assert math.isclose(math.fsum(result), 1.0, abs_tol=1e-12)
    return result


def fit(profiles: dict, train_books: list[str], top_k: int) -> dict:
    if not train_books:
        raise ValueError("Empty training set")
    # Equal book weighting in selection; pooled token counts are output separately.
    vocabulary = set().union(*(profiles[b]["counts"] for b in train_books))
    mean_freq = {
        f: math.fsum(profiles[b]["counts"][f] / profiles[b]["n"]
                     for b in train_books) / len(train_books)
        for f in vocabulary
    }
    features = sorted(vocabulary, key=lambda f: (-mean_freq[f], f))[:top_k]
    vectors = {b: vector(profiles[b], features) for b in train_books}
    centers = {}
    for group, members in GROUPS.items():
        included = [b for b in train_books if b in members]
        if not included:
            raise ValueError(f"No training books remain for {group}")
        centers[group] = [statistics.fmean(vectors[b][j] for b in included)
                          for j in range(len(features) + 1)]
    # Burrows Delta uses selected features only; OTHER is a redundant composite.
    sd = [statistics.stdev(vectors[b][j] for b in train_books)
          for j in range(len(features))]
    active = [j for j, value in enumerate(sd) if value > 1e-15]
    if not active:
        raise ValueError("No nonconstant selected features")
    return {"features": features, "centers": centers, "sd": sd,
            "active": active, "train_books": list(train_books),
            "selection_mean_frequency": mean_freq, "vectors": vectors}


def distance(x: list[float], center: list[float], model: dict, metric: str) -> float:
    if metric == "hellinger":
        return math.sqrt(0.5 * math.fsum((math.sqrt(a) - math.sqrt(b)) ** 2
                                        for a, b in zip(x, center)))
    if metric == "burrows_delta":
        return statistics.fmean(abs(x[j] - center[j]) / model["sd"][j]
                                for j in model["active"])
    raise ValueError(metric)


def scores(prof: dict, model: dict, metric: str) -> dict:
    x = vector(prof, model["features"])
    d = {g: distance(x, center, model, metric)
         for g, center in model["centers"].items()}
    paul, luke = d["Paul_reference"], d["Luke_Acts_reference"]
    nearest = "tie" if abs(paul - luke) < 1e-14 else (
        "Paul_reference" if paul < luke else "Luke_Acts_reference")
    return {"distance_paul": paul, "distance_luke_acts": luke,
            "margin_luke_minus_paul": luke - paul, "nearest_reference": nearest}


def location(token: Token) -> str:
    return f"{token.chapter}:{token.verse}"


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    if path.suffix == ".gz":
        # Fixed mtime and omitted filename make gzip output byte-reproducible.
        with path.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
                with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def config_id(mode: str, form: str, pronouns: bool, top_k: int) -> str:
    return f"{mode}__{form}__{'with_pronouns' if pronouns else 'core'}__top{top_k}"


def run(args: argparse.Namespace) -> dict:
    corpus, manifest = load_corpus(args.corpus)
    masks = read_masks(args.mask_file, corpus)
    modes = {"full": corpus}
    if args.mask_file is not None:
        modes["quote_masked"] = {
            b: [t for t in ts if (t.chapter, t.verse) not in masks.get(b, set())]
            for b, ts in corpus.items()
        }
    args.output.mkdir(parents=True, exist_ok=True)
    whole_rows, feature_rows, chunk_rows = [], [], []
    chunk_frequency_rows, chunk_summary_rows, driver_rows = [], [], []
    validation_rows, coverage_rows, books_rows = [], [], []
    variants = []
    for mode, mode_books in modes.items():
        for book in BOOKS:
            books_rows.append({"mask_mode": mode, "book": book,
                               "original_tokens": len(corpus[book]),
                               "retained_tokens": len(mode_books[book]),
                               "removed_tokens": len(corpus[book]) - len(mode_books[book]),
                               "masked_verse_count": len(masks.get(book, set()))
                               if mode == "quote_masked" else 0})
        texts = dict(mode_books)
        texts["Heb_without_ch13"] = [t for t in mode_books["Heb"] if t.chapter != 13]
        for form in ("surface", "lemma"):
            for pronouns in (False, True):
                profiles = {b: profile(ts, form, pronouns) for b, ts in texts.items()}
                for top_k in (30, 50):
                    cid = config_id(mode, form, pronouns, top_k)
                    cfg = {"config_id": cid, "mask_mode": mode, "form": form,
                           "pronouns": pronouns, "top_k_requested": top_k}
                    variants.append(cfg)
                    models = {"all_references": fit(profiles, REFERENCES, top_k)}
                    for held in REFERENCES:
                        models[f"holdout_{held}"] = fit(
                            profiles, [b for b in REFERENCES if b != held], top_k)
                        assert held not in models[f"holdout_{held}"]["train_books"]
                    for fold, model in models.items():
                        for rank, word in enumerate(model["features"], start=1):
                            j = rank - 1
                            feature_rows.append({
                                **cfg, "fold": fold, "rank": rank, "feature": word,
                                "n_training_books": len(model["train_books"]),
                                "training_books": "|".join(model["train_books"]),
                                "mean_training_frequency": model["selection_mean_frequency"][word],
                                "pooled_training_count": sum(profiles[b]["counts"][word]
                                                             for b in model["train_books"]),
                                "training_book_sd": model["sd"][j],
                                "active_for_delta": j in model["active"],
                                "paul_centroid_frequency": model["centers"]["Paul_reference"][j],
                                "luke_acts_centroid_frequency": model["centers"]["Luke_Acts_reference"][j],
                            })
                    for metric in ("hellinger", "burrows_delta"):
                        for held in REFERENCES:
                            model = models[f"holdout_{held}"]
                            expected = next(g for g, members in GROUPS.items() if held in members)
                            result = scores(profiles[held], model, metric)
                            whole_rows.append({
                                **cfg, "metric": metric, "role": "heldout_reference",
                                "text": held, "fold": f"holdout_{held}",
                                "tokens": profiles[held]["n"],
                                "features_used": len(model["features"]),
                                "expected_reference_group": expected,
                                "matches_reference_group": result["nearest_reference"] == expected,
                                **result,
                            })
                        validation = [r for r in whole_rows if r["config_id"] == cid
                                      and r["metric"] == metric
                                      and r["role"] == "heldout_reference"]
                        group_rates = {}
                        for group, members in GROUPS.items():
                            relevant = [r for r in validation if r["text"] in members]
                            group_rates[group] = sum(r["matches_reference_group"] for r in relevant) / len(relevant)
                        validation_rows.append({
                            **cfg, "metric": metric,
                            "heldout_books": len(validation),
                            "correct_reference_groups": sum(r["matches_reference_group"] for r in validation),
                            "paul_correct": sum(r["matches_reference_group"] for r in validation
                                                if r["expected_reference_group"] == "Paul_reference"),
                            "paul_total": len(GROUPS["Paul_reference"]),
                            "luke_acts_correct": sum(r["matches_reference_group"] for r in validation
                                                     if r["expected_reference_group"] == "Luke_Acts_reference"),
                            "luke_acts_total": len(GROUPS["Luke_Acts_reference"]),
                            "macro_reference_group_accuracy": statistics.fmean(group_rates.values()),
                        })
                        model = models["all_references"]
                        for target in ["Heb", "Heb_without_ch13"] + CONTROLS:
                            result = scores(profiles[target], model, metric)
                            whole_rows.append({
                                **cfg, "metric": metric,
                                "role": "target" if target.startswith("Heb") else "comparison_text",
                                "text": target, "fold": "all_references",
                                "tokens": profiles[target]["n"],
                                "features_used": len(model["features"]),
                                "expected_reference_group": "",
                                "matches_reference_group": "", **result,
                            })
                        # All features, not a hand-picked subset, expose distance drivers.
                        for target in ("Heb", "Heb_without_ch13"):
                            x = vector(profiles[target], model["features"])
                            c_p = model["centers"]["Paul_reference"]
                            c_l = model["centers"]["Luke_Acts_reference"]
                            for j, word in enumerate(model["features"] + [OTHER]):
                                if metric == "hellinger":
                                    p_part = 0.5 * (math.sqrt(x[j]) - math.sqrt(c_p[j])) ** 2
                                    l_part = 0.5 * (math.sqrt(x[j]) - math.sqrt(c_l[j])) ** 2
                                    measure = "squared_hellinger_contribution"
                                else:
                                    if j not in model["active"]:
                                        continue
                                    p_part = abs(x[j] - c_p[j]) / model["sd"][j] / len(model["active"])
                                    l_part = abs(x[j] - c_l[j]) / model["sd"][j] / len(model["active"])
                                    measure = "delta_contribution"
                                driver_rows.append({
                                    **cfg, "metric": metric, "text": target,
                                    "feature": word, "measure": measure,
                                    "text_frequency": x[j],
                                    "paul_frequency": c_p[j], "luke_acts_frequency": c_l[j],
                                    "paul_distance_contribution": p_part,
                                    "luke_acts_distance_contribution": l_part,
                                    "contribution_luke_minus_paul": l_part - p_part,
                                })
                    # Descriptive non-overlapping blocks are never training units.
                    # Reference chunks are scored with their entire book held out.
                    for text_name, tokens in texts.items():
                        fold = f"holdout_{text_name}" if text_name in REFERENCES else "all_references"
                        model = models[fold]
                        for chunk_size in args.chunk_sizes:
                            n_chunks, tail = divmod(len(tokens), chunk_size)
                            coverage_rows.append({
                                **cfg, "text": text_name, "chunk_size": chunk_size,
                                "retained_tokens": len(tokens), "complete_chunks": n_chunks,
                                "tokens_in_complete_chunks": n_chunks * chunk_size,
                                "tail_tokens_excluded": tail,
                                "tail_fraction": tail / len(tokens),
                                "tail_start_original_token": tokens[n_chunks * chunk_size].original_index if tail else "",
                            })
                            for chunk_i in range(n_chunks):
                                chunk = tokens[chunk_i * chunk_size:(chunk_i + 1) * chunk_size]
                                prof = profile(chunk, form, pronouns)
                                x = vector(prof, model["features"])
                                basic = {
                                    **cfg, "text": text_name, "fold": fold,
                                    "chunk_size": chunk_size, "chunk_index": chunk_i + 1,
                                    "first_original_token": chunk[0].original_index,
                                    "last_original_token": chunk[-1].original_index,
                                    "first_verse": location(chunk[0]), "last_verse": location(chunk[-1]),
                                    "source_tokens_spanned": chunk[-1].original_index - chunk[0].original_index + 1,
                                }
                                for j, word in enumerate(model["features"] + [OTHER]):
                                    chunk_frequency_rows.append({
                                        "config_id": cid, "text": text_name, "fold": fold,
                                        "chunk_size": chunk_size, "chunk_index": chunk_i + 1,
                                        "feature": word, "frequency": x[j],
                                        "count": prof["counts"][word] if word != OTHER
                                        else chunk_size - sum(prof["counts"][f] for f in model["features"]),
                                    })
                                for metric in ("hellinger", "burrows_delta"):
                                    chunk_rows.append({**basic, "metric": metric,
                                                       **scores(prof, model, metric)})
                            for metric in ("hellinger", "burrows_delta"):
                                selected = [r for r in chunk_rows if r["config_id"] == cid
                                            and r["text"] == text_name and r["chunk_size"] == chunk_size
                                            and r["metric"] == metric]
                                margins = [r["margin_luke_minus_paul"] for r in selected]
                                chunk_summary_rows.append({
                                    **cfg, "metric": metric, "text": text_name,
                                    "fold": fold, "chunk_size": chunk_size,
                                    "complete_chunks": len(selected), "excluded_tail_tokens": tail,
                                    "nearer_paul_chunks": sum(r["nearest_reference"] == "Paul_reference" for r in selected),
                                    "nearer_luke_acts_chunks": sum(r["nearest_reference"] == "Luke_Acts_reference" for r in selected),
                                    "ties": sum(r["nearest_reference"] == "tie" for r in selected),
                                    "median_margin": statistics.median(margins) if margins else "",
                                    "min_margin": min(margins) if margins else "",
                                    "max_margin": max(margins) if margins else "",
                                })
    outputs = {
        "book_counts.csv": books_rows,
        "whole_book_distances.csv": whole_rows,
        "calibration.csv": validation_rows,
        "fold_features.csv": feature_rows,
        "feature_contributions.csv": driver_rows,
        "chunk_distances.csv": chunk_rows,
        "chunk_frequencies.csv.gz": chunk_frequency_rows,
        "chunk_summaries.csv": chunk_summary_rows,
        "chunk_coverage.csv": coverage_rows,
    }
    for filename, rows in outputs.items():
        write_csv(args.output / filename, rows)
    summary = {
        "schema_version": 1,
        "analysis": "Exploratory reference-corpus style distances; not authorship probabilities",
        "corpus_expected_commit": PINNED_COMMIT,
        "corpus_files_sha256_verified_against_pinned_manifest": True,
        "corpus_files": manifest,
        "mask_filename": args.mask_file.name if args.mask_file else None,
        "mask_sha256": sha256(args.mask_file) if args.mask_file else None,
        "script_sha256": sha256(Path(__file__)),
        "groups": GROUPS,
        "comparison_texts_without_assigned_authorship_truth": CONTROLS,
        "configurations": variants,
        "metrics": ["hellinger", "burrows_delta"],
        "chunk_sizes": args.chunk_sizes,
        "methods": {
            "normalization": "MorphGNT normalized word or lemma, Unicode NFC, accents retained",
            "core_eligible_pos": sorted(BASE_POS),
            "additional_pronoun_pos": sorted(PRONOUN_POS),
            "feature_identity": "Form counted only when token POS is eligible; frequencies divide by all retained tokens",
            "feature_selection": "Top 30/50 by arithmetic mean of per-book training frequencies; ties by Unicode lexical order",
            "training_weighting": "Equal contribution of whole books in feature selection, group centroids, and scale estimation",
            "hellinger": "sqrt(0.5 * sum((sqrt(target_frequency)-sqrt(centroid_frequency))^2)); includes OTHER",
            "burrows_delta": "Mean absolute frequency difference divided by sample SD across training books; selected features only; zero-SD features omitted",
            "other": "All retained tokens not counted as selected eligible-POS feature tokens",
            "holdout": "One entire reference book excluded before feature selection, centroids and scales; reported at book level",
            "target_no_ch13": "Remove all Hebrews chapter 13 before constructing target profile; training unchanged",
            "masking": "Explicit whole-verse removal before profiles and chunks; masked chunks bridge removed spans",
            "chunks": "Fixed non-overlapping retained-token blocks; tail discarded and quantified; reference chunks use held-out-book model",
            "margin": "distance to Luke-Acts minus distance to Paul; positive means nearer Pauline reference centroid",
        },
        "limitations": [
            "Closed-set nearest reference labels do not identify an author or establish same authorship.",
            "Even perfect 9/9 held-out reference-group accuracy does not validate open-set authorship attribution.",
            "Nine reference books are not nine independent authors; only two Luke-Acts books constrain validation.",
            "Luke-Acts is a conventional corpus label, not proof of the historical identity of its author.",
            "Genre, audience, source use, collaboration, and textual transmission can affect function words.",
            "Chunk counts and multiple configurations are descriptive sensitivity analyses, not independent replicates.",
            "Philemon contributes a whole-book profile but has no complete 500- or 1000-token block.",
            "Whole-verse masks also remove authorial framing and may be incomplete; inspect supplied mask documentation.",
            "Reference holdout models differ from the full model; distances across folds are not a calibrated rejection threshold.",
            "No comparison corpus is available here for Apollos, Priscilla, or the historical Barnabas.",
            "Feature selection and scale estimates use no target or comparison-text tokens.",
        ],
        "calibration": validation_rows,
        "hebrews_whole_book": [r for r in whole_rows if r["role"] == "target"],
        "output_rows": {name: len(rows) for name, rows in outputs.items()},
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--mask-file", type=Path)
    parser.add_argument("--chunk-sizes", type=int, nargs="+", default=[1000, 500])
    args = parser.parse_args()
    if any(n < 1 for n in args.chunk_sizes) or len(set(args.chunk_sizes)) != len(args.chunk_sizes):
        parser.error("Chunk sizes must be distinct positive integers")
    summary = run(args)
    print(json.dumps({"configurations": len(summary["configurations"]),
                      "metrics": summary["metrics"], "output_rows": summary["output_rows"]}, indent=2))


if __name__ == "__main__":
    main()
