# Coarse Old Testament quotation mask

This is a sensitivity-analysis mask, not a definitive annotation of quotation boundaries or an authorship result. It was specified without examining the stylometric outcomes.

## Source and scope

Henry Barclay Swete, *An Introduction to the Old Testament in Greek*, chapter II, [“Quotations from the LXX in the New Testament”](https://www.biblehub.com/library/swete/an_introduction_to_the_old_testament_in_greek_additional_notes/chapter_ii_quotations_from_the.htm), sections 1–2; accessed 16 October 2026. The public-domain work is used through Bible Hub's transcription. The downloaded HTML had SHA-256 `9efa0df6f3fa1e4bed07d4ec58bf82c730a509558115779312a38916b65729be`; HTML presentation changes may change this checksum.

The source distinguishes formal citations from allusions, counting introductory formulas and contextually recognizable or verbatim quotations. We use **the union of both tables**, the OT-order table and all six NT-order subtables, for every sampled book. References found only in the later explanatory prose are not added. Parenthetical NT cross-references and tentative entries marked with a question mark are included. Books with no table entries have empty masks; this does not mean they contain no biblical allusions.

## Mechanical rule

1. Manually transcribe every NT reference in the two tables for the 16 sampled books; resolve abbreviated book/chapter references and flattened Synoptic columns by the named OT passage and the parallel table. The normalized transcriptions below are the reproducibility record.
2. Expand `f.` to the immediately following verse. Expand open-ended `ff.` to the starting verse plus the next **two** verses, a declared fixed three-verse approximation applied in every book. The affected NT references are Luke 2:22–24, John 6:31–33, Acts 7:32–34, and 2 Corinthians 6:16–18. This is a computational convention, not a claim about exact quote endpoints.
3. Resolve four internally cross-checkable transcription anomalies: Matthew 2:16 in table 2 becomes 2:18; John 13:16 becomes 13:18; 1 Corinthians 2:20 becomes 3:20; Acts 7:27 in the Deuteronomy parenthesis becomes 7:37. For Genesis 15:6, table 1's Galatians 3:8 becomes 3:6; 3:8 remains independently listed for Genesis 12:3. The counterpart table supports each correction. No contextual prose is used to expand ranges.
4. Take the union of both transcriptions. Remove references absent from the target SBLGNT corpus: **Mark 15:28 only**, a verse not included in that edition. Do not move its mask to adjacent verses.
5. Merge consecutive masked verses within each chapter. JSON triples are `[chapter, first_verse, last_verse]`, inclusive. Remove **all words in those verses**, including introductions and comments.

## Limitations and interpretation

This single historical index has omissions, inconsistent endpoints and editorial/transcription issues. Whole-verse deletion also removes authorial framing; retaining unlisted verses leaves some quotation language behind. In particular, repeated Psalm 95 wording in Hebrews 3:15, 4:3, 4:5 and 4:7 is not added because neither table lists these repetitions. Hebrews 10:8–9 is already covered by table 2's 10:5–10; 10:16–17 is explicitly listed. The mask preserves source endpoints such as Hebrews 3:7–12 and 8:8–13 even where they include interpretation.

Therefore call this condition **“Swete-listed quotation verses removed”**, not “quotations removed” or “author-only Greek.” A result that changes under this mask indicates sensitivity to these passages; a stable result does not establish that Septuagint influence has been eliminated. Allusions, shared scriptural style, genre and topic remain possible confounds. Independent modern word-level annotation is the appropriate follow-up before stronger inference.

## Normalized table transcriptions

Each cell contains chapter:verse or chapter:first-last. Table 1 is OT order; table 2 is NT order. These are normalized reference data, not quotations of prose. Empty cells mean no entries.

| Book | Table 1 | Table 2 | Unique masked verses |
|---|---|---|---:|
| Mt | 1:23 2:5-6 2:15 2:18 3:3 4:4 4:6-7 4:10 4:15-16 5:21 5:27 5:31 5:38 5:43 8:17 9:13 11:10 12:7 12:18-21 13:14-15 13:35 15:4-6 15:8-9 18:16 19:4-7 19:18-19 21:5 21:13 21:16 21:42 22:32 22:37-39 22:44 24:15 27:9-10 27:43 27:46 | 1:23 2:6 2:15 2:18 3:3 4:4 4:6-7 4:10 4:15-16 5:21 5:27 5:31 5:33 5:38 5:43 8:17 9:13 11:10 12:7 12:18-21 13:14-15 13:35 15:4 15:8-9 19:5-6 19:18-19 21:4-5 21:13 21:16 21:42 22:24 22:32 22:37 22:39 22:44 24:15 26:31 27:9-10 27:46 | 58 |
| Mk | 1:2-3 4:12 7:6-7 7:10 9:48 10:4 10:6-8 10:19 11:17 12:10-11 12:26 12:29-33 12:36 13:14 15:28 15:34 | 1:2-3 7:6 7:10 9:48 10:6-8 10:19 11:17 12:10 12:19 12:26 12:29-32 12:36 13:14 14:27 15:34 | 26 |
| Lk | 2:22-24 3:4-6 4:4 4:8 4:10-12 4:18-19 7:27 8:10 10:27 18:20 19:46 20:17 20:37 20:42-43 22:37 | 2:23 3:4-6 4:4 4:8 4:10-12 4:18-19 7:27 10:27 18:20-21 19:46 20:17 20:28 20:37 20:42-43 22:37 | 25 |
| Jn | 1:23 2:17 6:31-33 6:45 7:42 8:17 10:34 12:15 12:38 12:40-41 13:18 15:25 19:24 19:36 | 1:23 2:17 6:31 6:45 10:34 12:15 12:38 12:40 13:18 15:25 19:24 19:36-37 | 18 |
| Ac | 1:20 2:17-21 2:25-28 2:34-35 3:22-23 3:25 4:25-26 7:3 7:6-7 7:27-28 7:32-34 7:37 7:40 7:42-43 7:49-50 8:32-33 13:22 13:33-34 13:41 13:47 15:15-17 23:5 28:26-27 | 1:20 2:17-21 2:25-28 2:34-35 3:22-23 3:25 4:25-26 7:3 7:6-7 7:27-28 7:35 7:37 7:33-34 7:40 7:42-43 7:49-50 8:32-33 13:22 13:33-35 13:41 13:47 15:16-18 28:26-27 | 47 |
| Ro | 1:17 2:24 3:4 3:10-18 4:3 4:6-8 4:17-18 7:7 8:36 9:7 9:9 9:12-13 9:15 9:17 9:25-29 9:33 10:5-8 10:11 10:15-16 10:18-21 11:3-4 11:8-10 11:26-27 11:34-35 12:19-20 13:9 14:11 15:3 15:9 15:11-12 15:21 | 1:17 2:24 3:4 3:10-18 3:20 4:3 4:22 4:7-8 4:17-18 7:7 8:36 9:7 9:9 9:12-13 9:15 9:17 9:26-27 9:29 9:33 10:6-9 10:15-16 10:18-21 11:1-4 11:8-9 11:26-27 11:34-35 12:20-21 13:9 14:11 15:3 15:9-12 15:21 | 68 |
| 1Co | 1:19 1:31 2:9 2:16 3:19-20 6:16 9:9 10:7 10:26 14:21 15:27 15:32 15:45 15:54-56 | 1:19 1:31 2:9 3:20 6:16 9:9 10:7 10:26 14:21 15:32 15:45 15:54-55 | 17 |
| 2Co | 4:13 6:2 6:16-18 8:15 9:9 10:17 13:1 | 4:13 6:2 6:16-18 8:15 9:9 10:17 | 9 |
| Ga | 3:6 3:8 3:10-13 4:27 4:30 5:14 | 2:16 3:6 3:8 3:10-13 4:27 4:30 5:14 | 10 |
| Php | — | — | 0 |
| 1Th | — | — | 0 |
| Phm | — | — | 0 |
| Heb | 1:5-13 2:6-8 2:12-13 3:7-11 4:4 5:5-6 6:13-14 7:17 7:21 8:5 8:8-12 9:19-20 10:5-7 10:30 10:37-38 11:5 11:18 11:21 12:5-6 12:15 12:20-21 13:5-6 | 1:5-13 2:6-8 2:12-13 3:7-12 4:4 5:6 6:13-14 7:17 7:21 8:5 8:8-13 9:20 10:5-10 10:16-17 10:30 10:37 11:5 11:18 11:21 12:5-6 12:15 12:20 12:26 13:5-6 | 58 |
| Jas | 2:8 2:11 2:23 4:6 | 2:8 2:11 2:23 4:6 | 4 |
| 1Pe | 1:16 1:24-25 2:6-8 2:24-25 3:10-12 4:18 5:5 5:7 | 1:24-25 2:6 3:10-12 4:18 5:7 | 14 |
| 1Jn | — | — | 0 |

## Reproduction and validation

Read the two reference columns above, split on spaces, expand inclusive numeric ranges, union each book's sets, intersect with the `(chapter, verse)` identifiers in its MorphGNT file, and merge adjacent verses by chapter. The only source-listed reference excluded by corpus intersection was Mark 15:28. All output ranges were checked against the local SBLGNT/MorphGNT corpus; every included verse exists. The 16 keys match the experiment's book abbreviations exactly.

Total: **354 unique verses**; Hebrews: **58 verses**. The actual machine-readable mask is [`../data/quote_verses.json`](../data/quote_verses.json).
