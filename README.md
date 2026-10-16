# Hebrews authorship research

An exploratory, reproducible investigation of who composed Hebrews. **The author
has not been identified.** This repository separates historical testimony,
internal evidence and measurable Greek style instead of treating them as votes.

## First result — 16 October 2026

Across 32 deliberately varied comparisons, Hebrews is nearer the Luke–Acts
reference corpus in 21 and the Pauline reference corpus in 11. **These counts
are not authorship probabilities.** All 32 also put 1 Peter nearer Paul and
Matthew, Mark and John nearer Luke–Acts. The method measures relative similarity
and has no validated way to recognize an author outside its two reference groups.

Removing chapter 13 preserves the nearest-group result in 29/32 settings. Thus
the personal ending is not the sole cause of the measured similarities. This
does not establish the ending's authorship or originality.

Start with the [research report](research/report-2026-10-16.md).

## Contents

- [Experiment design and interpretation rules](research/design.md)
- [Historical witnesses and their dependencies](research/historical-evidence.md)
- [Internal textual evidence and candidate constraints](research/internal-evidence.md)
- [Quotation-mask source, exact references and limitations](research/quotation-mask.md)
- [Machine-readable summary](results/summary.json)
- [Every whole-book result](results/whole_book_distances.csv) and
  [whole-book holdout calibration](results/calibration.csv)
- [Feature selection and centroids for every fold](results/fold_features.csv)
- [Feature contributions](results/feature_contributions.csv),
  [chunk results](results/chunk_distances.csv),
  [chunk frequencies](results/chunk_frequencies.csv.gz),
  [chunk summaries](results/chunk_summaries.csv), and
  [coverage/tails](results/chunk_coverage.csv)

## Reproduce

Python 3.10+; standard library only. No packages or model/API credentials needed.
The first command downloads the 27 pinned upstream corpus files and verifies
their hashes; the analysis uses 16 books. Subsequent analysis is offline.

```sh
python3 scripts/fetch_corpus.py
python3 scripts/analyze.py --corpus .cache/sblgnt --mask-file data/quote_verses.json --output results
python3 scripts/verify_results.py --corpus .cache/sblgnt --mask-file data/quote_verses.json --results results
```

To use an existing upstream checkout, pass its path as `--corpus`. The analysis
refuses input files that differ from the pinned SHA-256 manifest. All 32 settings
are retained; no winning method was selected after seeing Hebrews' score.

## Sources and attribution

Greek input: Tauber, J. K., ed. (2017), *MorphGNT: SBLGNT Edition*, version 6.12,
[DOI 10.5281/zenodo.376200](https://doi.org/10.5281/zenodo.376200),
[upstream repository](https://github.com/morphgnt/sblgnt), commit
`aaed91e57c8e4a8dc9a2383e129ca5e75fe6393d`.

MorphGNT's morphological parsing and lemmatization are CC BY-SA 3.0. The
upstream README also points to the SBLGNT text licence. The SBLGNT publisher's
[repository](https://github.com/LogosBible/SBLGNT) now specifies CC BY 4.0 and
credits the Society of Biblical Literature and Logos Bible Software (2010),
edited by Michael W. Holmes. Downloaded raw text is kept outside version control;
this repository records hashes, verse-reference masks and derived measurements.
Any reuse of upstream text or annotations remains subject to their licences.

The historical notes link primary texts and modern research. This is a first
research notebook, not a peer-reviewed attribution claim.
