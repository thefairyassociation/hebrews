# Experiment 001: can a simple Greek style comparison distinguish candidates?

Design recorded during the 16 October 2026 research session before inspecting
the experiment's numerical results. This is an exploratory study, not an
independently registered protocol or a replication of a published classifier.

## Question and reference labels

Does Hebrews' proximity to the seven conventionally undisputed Pauline letters
or to Luke–Acts remain stable under reasonable analysis choices? Can the same
method distinguish held-out reference books and avoid misleading assignments
of comparison texts?

Pauline references: Romans, 1–2 Corinthians, Galatians, Philippians,
1 Thessalonians, Philemon. Luke–Acts references: Luke and Acts. These are
conventional reference groupings, not fresh proofs of authorship or of the
historical identity of Luke. Coauthors, secretaries, sources and internal
composition histories remain possible influences on these reference texts.

James, 1 Peter and 1 John are non-training epistolary comparisons. Matthew,
Mark and John are non-training narrative comparisons. The experiment does
not need to identify their individual historical authors. Their nearest
reference family demonstrates what a forced choice does to texts outside
the proposed two-family problem.

## Decisions fixed before results

- Input: pinned MorphGNT/SBLGNT Greek, never English translation. All corpus
  files have SHA-256 hashes in `data/corpus-manifest.json`.
- Two representations: normalized surface word and lemma, Unicode NFC.
- Grammatical feature eligibility: conjunctions, prepositions, articles and
  particles (`C-`, `P-`, `RA`, `X-`), with a separate setting also including
  pronouns (`RD`, `RI`, `RP`, `RR`). This is a restricted feature family, not
  a claim to include every Greek function word; adverbs are excluded.
- Feature budgets: 30 and 50, selected using training books only. Rank by
  mean book-level relative frequency, so a long book cannot dominate merely
  through token count. No feature selection using Hebrews or comparison texts.
- Each book contributes one normalized profile. Average the reference books
  equally within each family. Retain short Philemon explicitly.
- Two distance measures: Hellinger on selected frequencies plus an OTHER
  category, and standardized L1/Burrows Delta on selected frequencies.
  Standard deviations are fitted to training books only. These are distances,
  not probabilities of historical authorship.
- Refit feature selection and scaling after withholding an entire reference
  book. No chunk of the held-out book enters training.
- Repeat on the full text and on a symmetric, source-derived coarse mask of
  verses containing Old Testament quotations. Mask all reference and comparison
  books by the same rule. The mask is imperfect and removes authorial framing
  too; it is not a reconstruction of quotation-free prose.
- Compare full Hebrews with Hebrews 1–12. Omitting chapter 13 is a coarse
  sensitivity analysis, not a test proving interpolation or multiple authors.
- Score fixed, non-overlapping 1,000-token chunks, with 500-token blocks as
  an additional descriptive sensitivity, and report leftover tails.
  Chunk agreement is descriptive. Chunks are dependent pieces of the same
  document, not independent authors or independent experiments.

## Interpretation rules

Publish every setting, including reversals and failed holdouts. Do not select
the configuration that supports a preferred candidate. A configuration count
is not a posterior probability or a vote of independent experiments.

If other epistles are also closer to Paul, that limits the specificity of a
Paul-like score for Hebrews. If a setting fails a conventional reference-book
holdout, it cannot support a strong Hebrews attribution. Even successful
holdouts do not validate identifying an unseen author: the two Luke–Acts books
give only two tests, and their genre differs from Hebrews.

A nearest family cannot identify Apollos, Barnabas or Priscilla. No authenticated
comparison writing from those candidates is supplied. A historical unknown
author remains possible regardless of the nearest-family label.

## Prior art

[Ebrahimpour et al. (2013)](https://doi.org/10.1371/journal.pone.0054998)
obtained different Hebrews assignments with MDA and SVM. Their reference texts
were concatenated by author and split into four samples. We instead hold out
whole books and expose the forced-choice behaviour on additional texts. We do
not reproduce their models or claim to overturn their paper.

[Erickson (2024)](https://digitalcommons.liberty.edu/honors/1392/) reports a
Luke–Acts proximity without a significant distinction; it is an undergraduate
thesis, not a consensus result.

[Pracht and McCauley (2025)](https://doi.org/10.3390/rel16010055) investigate
shared stylistic patterns within early Christian literary networks. That is a
reason to distinguish stylistic association from a uniquely individual signature.

Our contribution is the reproducible sensitivity and calibration exercise,
not a newly invented attribution method or a claimed solution.
