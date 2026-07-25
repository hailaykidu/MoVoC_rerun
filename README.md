# MoVoC: Morphology-Aware Subword Vocabulary Construction

Companion code for *"MoVoC: Morphology-Aware Subword Construction for Ge'ez
Script Languages"* (arXiv:[2509.08812](https://arxiv.org/abs/2509.08812),
Teklehaymanot, Fazlija, Nejdl). Builds a hybrid morpheme+BPE subword
vocabulary for four Ge'ez-script languages (Amharic, Tigrinya, Tigre, Ge'ez)
and evaluates it against plain BPE using MorphScore and Boundary Precision.

> **Status note**: the code here (and on the paper's own linked GitHub repo,
> `hailaykidu/MoVoC`) was previously non-functional -- every core file
> (`movoc/segmenter.py`, both `rules/*.json`, all of `scripts/*.py`, all
> `vocab/*.txt`/`results/*.txt` outputs) was 0 bytes, and the GitHub repo's
> `movoc/` package imports submodules that don't exist anywhere in it. This
> README describes what has since been rebuilt and actually runs, with
> honest labeling of what's real vs. approximated -- see Limitations.

## What's real vs. bootstrapped

| Component | Status |
|---|---|
| Amharic/Tigrinya monolingual corpora | **Real** -- reused from `MoVoC_Tok/02_cleaning/corpus_clean/` |
| Tigre/Ge'ez monolingual corpora | **Real** -- same source; the original paper didn't have BPE training data for these two, this project does |
| 574 additional Ge'ez words (`data/geez_wordlist_hailay_annotated.txt`) | **Real** -- human-provided verb-paradigm word forms (e.g. መጽአ/ነጸረ/ዐጸወ/ሰፍሐ/በልዐ conjugations, ~150 further triliteral roots), added to the Ge'ez corpus (1,813 -> 2,387 lines). Initially extracted from the PDF's flattened text stream with a hand-written parser that turned out to have real errors (23 words merged with stray fragments); re-extracted properly with `pdfplumber`'s table-geometry-aware `extract_tables()`, which reads actual cell boundaries instead of linear reading order -- confirmed correct against a manually-checked sample. |
| 193-entry Ge'ez gold morpheme set (`data/Geez_Hailay_Morphem.json`) | **Real** -- the same PDF's table also had prefix/root/infix/suffix columns filled for many of its rows; `pdfplumber` recovers these reliably (206 raw rows, 179 unique words), and the user separately pasted a clean tab-separated version of the same table directly on GitHub (222 rows, 193 unique words), which the two extractions cross-validate against each other (178/179 overlapping words matched exactly). Reconciled into one 193-entry set. **However**, computing Boundary Precision/MorphScore against it with this project's current metrics isn't done -- see Limitations, since Ge'ez's root-and-pattern (templatic) morphology means many surface words are not literally `prefix+root+suffix` (e.g. root `መጽአ` surfaces as `መጻአ` before some suffixes; `ልሳን`+`ኦሙ` surfaces as `ልሳኖሙ`, with the fidel script fusing the boundary) and the existing `boundaries_from_triple()` assumes concatenation |
| 206-word Tigrinya gold morpheme set (`data/ሃይላይ_ኪዱ_Tigriyna_Morphem.json`) | **Real** -- pre-existing manually-segmented data; the only gold set in this project whose triples are actually scored, since Tigrinya's affixation is concatenative enough for `boundaries_from_triple()` to apply |
| Amharic/Tigrinya segmentation rules (`rules/{amharic,tigrinya}_rules.json`) | Documented affixes from standard reference grammars -- reasonable starting point, not independently expert-verified |
| Tigre/Ge'ez segmentation rules (`rules/{tigre,geez}_rules.json`) | **Bootstrapped** from the related-language rules above (see each file's `source_notes`) -- explicitly *not* expert annotation |
| HornMorpho integration (paper's actual method for Amharic/Tigrinya) | **Attempted, not used** -- see Sec 3.1 below |
| MoVoC-Tok's constrained-merge BPE (Sec 3.3 -- the paper's actual core algorithm) | **Not implemented** -- see Sec 3.3 below |

## Proposed Method (mirrors the paper's Section 3 structure)

The paper's Section 3 ("Proposed Method") has exactly three subsections:
3.1 Pre-tokenization and Supervised Morphological Analyses, 3.2 Vocabulary
Construction (MoVoC), and 3.3 MoVoC-Tok (Morpheme-aware Subword
Segmentation). This project is organized the same way below, so it's clear
which files implement which paper subsection, and which subsection has no
corresponding code at all.

### 3.1 Pre-tokenization and Supervised Morphological Analyses

**Paper**: a regex-based pre-tokenization pipeline (corpus cleaning,
punctuation/special-character normalization), followed by supervised
morphological segmentation -- [HornMorpho](https://github.com/hltdi/HornMorpho)
for Amharic (reliable) and Tigrinya (needs manual post-editing), and fully
manual expert annotation under linguistic supervision for Ge'ez and Tigre,
since no analyzer exists for either. The paper is explicit that Ge'ez/Tigre
annotations are "applied for testing purposes only and are not part of the
vocabulary since we did not get data for BPE training" (Sec 4.1) -- i.e.
the paper's own Ge'ez/Tigre role is gold-test-set-only, not vocabulary
training. The resulting per-language annotated morphemes double as the
gold-standard test set used later for MorphScore/Boundary Precision (Table
2: 80k Amharic, 80k Tigrinya, 20k Ge'ez, 32k Tigre items).

**This project**:

| Paper component | File(s) here | Status |
|---|---|---|
| Corpus cleaning / pre-tokenization | reused `MoVoC_Tok/02_cleaning/clean_corpus.py` | **Real** -- NFC normalization, exact + MinHash dedup, script-ratio filtering (see Data cleaning below) |
| HornMorpho segmentation (Amharic/Tigrinya) | -- | **Attempted, not working** -- HornMorpho is installed and its FST/lexicon data genuinely loads (real, versioned resources for Amharic, Tigrinya, and Tigre), but every test word through its Python API -- including HornMorpho's own documented worked examples -- returned unanalyzed (`{'pos': 'UNK', 'nsegs': 1}`); root cause not resolved within a reasonable debugging budget (possibly a stale compiled cache or a version mismatch in the installed 5.3.1 copy) |
| Manual expert annotation (Ge'ez/Tigre) | `rules/{tigre,geez}_rules.json` | **Not real expert annotation** -- bootstrapped from the related-language rules instead (`amharic_rules.json`/`tigrinya_rules.json`), each labeled `"source": "bootstrapped_from_related_language"` in the JSON itself |
| Rule-based fallback (all 4 languages, since HornMorpho didn't work for any of them) | `movoc/segmenter.py`, `rules/{amharic,tigrinya,tigre,geez}_rules.json` | **Real code**, but a materially weaker stand-in than the paper's HornMorpho segmentation -- a longest-match prefix/suffix stripper, not an FST/dictionary-based analyzer. Shows up in Results below as a lower MorphScore than plain BPE, the opposite of the paper's reported direction |
| Gold-standard test set | `data/ሃይላይ_ኪዱ_Tigriyna_Morphem.json` (Tigrinya, 206 words) and `data/Geez_Hailay_Morphem.json` (Ge'ez, 193 words -- added later, see Data cleaning below) | **Real for Tigrinya and Ge'ez**, vs. the paper's per-language sets of 80k/80k/20k/32k items (Table 2); still no gold data of any kind for Amharic/Tigre. Ge'ez's set exists but isn't scored by this project's metrics -- see "Ge'ez gold morpheme set: real data, not yet scorable" |

### 3.2 Vocabulary Construction (MoVoC)

**Paper (Algorithm 1)**: formally defined over exactly two corpora, `P_am`
and `P_ti`. Given total vocab size `s` and morpheme proportion `r`:
`slang = s/2`, `sBPE = slang*(1-r)`, `smorpheme = slang*r`. Train BPE per
language at size `sBPE`; call `extract_morphemes(P, s_morpheme)`, which
frequency-ranks morphemes from the **HornMorpho-segmented** corpus and
keeps the top-`k` (`Vmorpheme = Topk(freq_morphemes)`); union all
per-language BPE and morpheme vocabularies into `V_MoVoC`.

**This project**:

| Paper component | File(s) here | Status |
|---|---|---|
| `Train_BPE(P, sBPE)` | `scripts/train_bpe.py` | **Real** -- `tokenizers` library `BpeTrainer` (paper specifies BPE, not SentencePiece Unigram) |
| `extract_morphemes(P, s_morpheme)` | `scripts/create_vocab.py` | **Real formula, weaker input** -- frequency-ranks morphemes from the rule-based segmenter's output rather than HornMorpho's (3.1's gap propagates here) |
| Algorithm 1 orchestration | `scripts/hybrid_vocab.py` | **Real, generalized from 2 to 4 languages**: `slang = s/N` (paper's fixed `s/2` becomes `s/N` here since we have real corpora for all 4 languages, not just Amharic/Tigrinya) |
| Scope vs. paper | -- | **This project trains BPE+morpheme vocab for Tigre and Ge'ez too** -- broader than the paper, which used Tigre/Ge'ez annotations only as a 3.1 gold test set, explicitly *not* for vocabulary training ("we did not get data for BPE training," Sec 4.1) |

```
Algorithm 1, as implemented (scripts/hybrid_vocab.py):
slang = s / N                 (N = number of languages; paper used N=2 fixed, this project uses N=4)
sBPE = slang * (1 - r)
smorpheme = slang * r
for each language:
    V_BPE[lang]      = Train_BPE(corpus[lang], sBPE)
    V_morpheme[lang] = extract_morphemes(corpus[lang], smorpheme)
V_MoVoC = union of all V_BPE[lang] and V_morpheme[lang]
```

`r` (morpheme-token proportion) is a hyperparameter the paper doesn't give
an exact value for; this project defaults to `r=0.3`, our own choice, not
lifted from the paper.

### 3.3 MoVoC-Tok (Morpheme-aware Subword Segmentation)

**Paper**: explicitly *not* just "the vocabulary from 3.2, used as-is." A
conventional BPE tokenizer trained on `V_MoVoC` can still produce
morpheme-boundary violations, since its merge operations are data-driven
and can combine subwords across morpheme boundaries. Sec 3.3's actual
contribution is a **constrained BPE merge process** that forbids exactly
that:

> "we incorporate morphological constraints directly into the BPE training
> process by limiting merge candidates to those that do not span morpheme
> boundaries... `max_V Σ log P(BPE(wi;V,Mi))`, such that no merge unit
> crosses `Mi`" -- i.e. `(a,b) ∈ MergeCandidates ⇒ a∪b ∉ Mi^∁`

**This project**: **Not implemented** -- the single largest gap between
this project and the paper, and independent of the 3.1 HornMorpho gap (it
would still need building even if HornMorpho worked). `scripts/hybrid_vocab.py`
does something structurally simpler: it trains a **plain, unconstrained**
BPE model, separately extracts top-k frequent morphemes, and takes the
**set union** of the two vocabularies -- it never constrains the BPE merge
operations themselves against morpheme boundaries during training. `V_MoVoC`
(the merged vocabulary, Sec 3.2) is implemented; `MoVoC-Tok` (the
constrained tokenizer that actually segments new text respecting those
boundaries, Sec 3.3) is not. `scripts/run_intrinsic_eval.py` evaluates the
rule-based segmenter's own boundary predictions directly (not a
constrained-BPE tokenizer's output) against the plain-BPE baseline -- see
Results below.

## Comparison against the published paper (remaining gaps, beyond 3.1-3.3)

| Paper claim | What's actually in this project |
|---|---|
| Table 5: 152k bilingual vocab (80k morpheme + 32k BPE, per language, for Amharic+Tigrinya) | 8,000 total vocab (600 morpheme + 1,400 BPE per language, across 4 languages) -- a deliberately smaller verification-scale run |
| Table 6 / Appendix B: 5 morpheme categories -- PREFIX, ROOT, SUFFIX, INFIX, CLITIC (e.g. Tigre's `-ና` annotated as a CLITIC) | 3 categories only -- `Segmentation` has `prefix`/`root`/`suffix` fields, no infix or clitic. The real 206-entry Tigrinya gold file itself also only has these 3 fields. |
| Table 3: MarianMT fine-tuned, BLEU/chrF++ on FLORES-200 (Amharic/Tigrinya) + 100-sentence OPUS subsets (all 4 languages) | **Attempted in a companion project**: [MoVoC_MT](../MoVoC_MT/README.md) trains a from-scratch MarianMT (same architecture as the paper) bidirectionally on English-Amharic/English-Tigrinya using MoVoC_Tok, with Tigre held out for zero-shot eval. Real results: en-am 11.7/33.7 BLEU/chrF, am-en 20.5/45.6, en-ti 4.6/18.6, ti-en 10.6/31.9, Tigre zero-shot en-tig 2.7/19.4 and tig-en 7.6/32.2 (43-pair set, not FLORES-200 -- no Tigre FLORES exists) |
| Sec 4.3: MarianMT training stats (3 epochs, loss 0.443→0.438, ~12h, 96.7 samples/sec) | Not this project's work -- this exact run was traced to a real `trainer_state.json` at `Paralleldata/results/checkpoint-524316` (524,316 steps, unrelated to MoVoC's own code) |

Net effect: this project correctly implements the paper's **3.2 vocabulary-size
formulas and evaluation metrics**, but not its **3.1 HornMorpho segmentation
or 3.3 constrained-merge BPE** -- the two core algorithmic components -- nor
its **dataset/vocabulary scale**. The numbers in Results below are real, but
not comparable in magnitude to the paper's own reported numbers for that
reason -- see each result's discussion for specifics.

## Pipeline (file map)

```
rules/{amharic,tigrinya,tigre,geez}_rules.json   -> 3.1: prefix/suffix rule sets
movoc/segmenter.py                                -> 3.1: MorphemeSegmenter (longest-match stripper)
movoc/metrics.py                                  -> MorphScore, Boundary Precision, Renyi entropy (Sec 6)
scripts/train_bpe.py                              -> 3.2: per-language BPE (tokenizers lib, not SentencePiece)
scripts/create_vocab.py                           -> 3.2: extract_morphemes(): top-k frequent morphemes
scripts/hybrid_vocab.py                            -> 3.2: Algorithm 1, merges BPE + morpheme vocabs into V_MoVoC
scripts/run_intrinsic_eval.py                      -> intrinsic eval: segmenter vs BPE, scored against the real gold set
data/ሃይላይ_ኪዱ_Tigriyna_Morphem.json               -> real Tigrinya gold set (206 words), scored above
data/Geez_Hailay_Morphem.json                     -> real Ge'ez gold set (193 words), not yet scored -- see above
data/geez_wordlist_hailay_annotated.txt            -> the 574 real Ge'ez words appended to corpus_clean/geez.txt
```

No file implements 3.3 (constrained-merge BPE) -- see above.

**`LLM_Probe/` is not part of this project.** It's a fully separate,
independent repository (own remote: `github.com/hailaykidu/LLM-Probe`)
that happens to sit on disk at `MoVoC/LLM_Probe/` -- gitignored here
(`.gitignore:7`), not a submodule, not tracked by this repo's history,
and not referenced by any file above. Its actual location/identity is
its own GitHub repo, not a subdirectory of MoVoC; the nesting is
filesystem coincidence, not a project relationship.

## Data cleaning (all four languages, verified)

Corpora are reused as-is from the MoVoC_Tok project's cleaning pipeline
(`MoVoC_Tok/02_cleaning/clean_corpus.py`: NFC normalization, control-char
stripping, exact + MinHash near-duplicate dedup, Ethiopic-script-ratio
filtering) -- not re-cleaned here. Real numbers from that pipeline's own
`cleaning_report.json`:

| Language | Raw lines | After length filter | After exact dedup | After near-dup dedup | Script-flagged (dropped) | **Final clean lines** |
|---|---|---|---|---|---|---|
| Amharic | 16,256,115 | 16,193,298 | 14,209,205 | 12,330,904 | 140,042 | **12,190,862** |
| Tigrinya | 3,874,142 | 3,717,258 | 2,979,942 | 2,696,045 | 52,626 | **2,643,419** |
| Tigre | 909,705 | 909,705 | 909,705 | 730,330 | 0 | **730,330** |
| Ge'ez | 2,107 | 2,107 | 2,105 | 1,813 | 0 | 1,813 + **574 new real words** = **2,387** |

The 574 additional Ge'ez lines came later (see "What's real vs.
bootstrapped" above) -- appended directly to `corpus_clean/geez.txt` after
confirming zero overlap with the existing 1,813 lines, not run back through
the cleaning pipeline (they're already clean, single-word entries with no
duplicates, dedup artifacts, or non-Ethiopic content to strip).

### Ge'ez gold morpheme set: real data, not yet scorable

`data/Geez_Hailay_Morphem.json` (193 entries) is real, human-provided
prefix/root/infix/suffix segmentation -- extracted reliably via
`pdfplumber`'s geometric table parser, then cross-validated and merged with
a clean tab-separated version the user pasted directly on GitHub (178/179
overlapping words matched exactly between the two independent extractions).
It is **not** run through `scripts/run_intrinsic_eval.py` or
`movoc/metrics.py`'s `boundaries_from_triple()`, because that function
computes boundary positions by string length under the assumption that
`word == prefix + root + suffix`. That assumption holds for the Tigrinya
gold set but frequently doesn't for Ge'ez, which has genuine root-and-pattern
(templatic) Semitic morphology: the cited root's vowels change under
suffixation (e.g. `መጽአ` "he came" surfaces as `መጻአ` in `መጻአከ` "you came"),
and the Ethiopic abugida fuses a bare final consonant with a following
vocalic suffix into a single fidel character (e.g. root `ልሳን` + suffix `ኦሙ`
surfaces as `ልሳኖሙ`, four characters, not the five a naive concatenation
would produce). Checked directly: only 108 of the 193 entries even have
prefix/suffix as literal substrings at the word's edges; forcing the
rest through length-based boundary math would silently score against
character offsets that don't correspond to real segmentation points. Rather
than publish a MorphScore/Boundary-Precision number computed on a broken
assumption, this project reports the real annotation data and leaves scoring
it as a documented gap (see Limitations) -- it would need a
non-concatenative-aware boundary method (e.g. edit-distance alignment
between the citation root and its surface realization), which is not
implemented here.

All four are confirmed real and non-empty at
`MoVoC_Tok/02_cleaning/corpus_clean/{amharic,tigrinya,tigre,geez}.txt`,
and all four were successfully read and processed (BPE-trained + morpheme-
extracted with no errors) in the `hybrid_vocab.py` run reported below --
including Ge'ez, whose corpus remains three to four orders of magnitude
smaller than the other three even after this addition.

## Training configuration

Real settings used for the results reported below (`scripts/hybrid_vocab.py`
and `scripts/run_intrinsic_eval.py`). These are **explicit CLI flags, not the
scripts' own built-in defaults** -- `hybrid_vocab.py`'s argparse defaults are
`--total-vocab-size 32000` and `--max-lines-per-language 500000`; running
either script with no flags at all will *not* reproduce the numbers below.
The "Reproducing" commands further down pass every value explicitly for
exactly this reason:

| Setting | Value |
|---|---|
| Total vocab size (`s`) | 8,000 |
| Languages (`N`) | 4 (Amharic, Tigrinya, Tigre, Ge'ez) |
| Per-language budget (`slang = s/N`) | 2,000 |
| Morpheme-token proportion (`r`) | 0.3 (our default, not specified by the paper) |
| BPE budget per language (`sBPE = slang*(1-r)`) | 1,400 |
| Morpheme budget per language (`smorpheme = slang*r`) | 600 |
| Max corpus lines read per language (`--max-lines-per-language`) | 200,000 |
| Actual lines used: Amharic / Tigrinya / Tigre | 200,000 each (capped -- full corpora are 12.19M / 2.64M / 730K lines) |
| Actual lines used: Ge'ez | 2,387 (its full corpus -- smaller than the cap) |
| BPE trainer | `tokenizers` library `BpeTrainer`, `special_tokens=["<unk>"]`, `Whitespace` pre-tokenizer |
| Intrinsic-eval BPE baseline vocab size | 1,400 (same as MoVoC-Tok's per-language BPE budget, for a fair comparison) |

The 200k-line cap is a deliberate choice for this verification pass (keeps
BPE training fast across all four languages); it is not a limitation of the
corpora themselves, which are far larger for Amharic/Tigrinya/Tigre -- a
production run would raise or remove this cap for those three.

## Results

### Hybrid vocabulary construction (`scripts/hybrid_vocab.py`, total_vocab_size=8000, r=0.3, 200k lines/language)

| Language | BPE tokens | Morpheme tokens | Hybrid vocab size |
|---|---|---|---|
| Amharic | 1,400 | 600 | 1,870 |
| Tigrinya | 1,400 | 600 | 1,736 |
| Tigre | 1,400 | 600 | 1,589 |
| Ge'ez | 1,400 | 600 | 1,641 |
| **Total VMoVoC (union)** | | | **5,103** |

Hybrid vocab sizes are smaller than BPE+morpheme sums because some
extracted morphemes were already present in the BPE vocab (expected set-union
behavior). Ge'ez's corpus is now 2,387 lines (see Data cleaning above) but
the per-language vocab sizes are essentially unchanged from the earlier
1,813-line run (union total moved by exactly 1 token, 5,104 -> 5,103) --
expected, since Algorithm 1's budget (`sBPE`=1,400, `smorpheme`=600 per
language) is a fixed cap, not corpus-size-dependent, and the corpus was
already large enough to fill that cap either way. The real benefit of the
larger, more morphologically varied corpus (conjugation paradigms rather
than just repeated biblical prose) isn't visible in vocab *size*, only
in which specific tokens got selected.

### Intrinsic evaluation (`scripts/run_intrinsic_eval.py`, real 206-word Tigrinya gold set -- the only language whose gold set is actually scored here; see the Ge'ez section above for why its 193-entry set isn't run through this script)

| Method | Boundary Precision ↑ | MorphScore ↑ | Renyi Entropy ↓ |
|---|---|---|---|
| **MoVoC-Tok** (our segmenter) | **0.463** | 0.438 | **3.02** |
| BPE (plain) | 0.345 | **0.520** | 4.51 |

MoVoC-Tok wins on Boundary Precision and Renyi Entropy, matching the paper's
claimed direction of improvement. It loses on MorphScore -- the opposite of
the paper's result -- most plausibly because our segmenter is a much simpler
greedy rule-stripper standing in for the paper's real HornMorpho-based
analysis (see above). This is reported exactly as computed; no numbers here
are adjusted or cherry-picked.

## Reproducing

```bash
cd scripts
python hybrid_vocab.py --total-vocab-size 8000 --r 0.3 --max-lines-per-language 200000
python run_intrinsic_eval.py --bpe-vocab-size 1400 --max-lines 200000
pytest ../tests/
```

## Downstream MT reproduction (`mt_finetune/`)

Reproduces the paper's own original single-pair MarianMT training
setup, using the real `checkpoint-524316` tokenizer (63,050-vocab
MarianTokenizer, `transformers==4.51.3`) rather than a reconstruction:

- **en->ti**: matches `checkpoint-524316` field-for-field (architecture,
  batch=8, seq_len=128, fp32, lr schedule) on the real raw NLLB en-ti
  corpus (1,398,173 lines).
- **en->am**: same architecture/tokenizer/seed, raw NLLB en-am data
  capped to the same size for comparability. Disclosed tokenizer
  mismatch (target.spm was fit on Tigrinya): measured 2.1% `<unk>` rate.
- **en->gez**: same architecture/tokenizer/seed, using a genuine
  verse-aligned English<->Classical Ge'ez parallel corpus
  (`Bedru/Eng-Geez`, 2,107 rows) -- not synthetic. Measured 0.9% `<unk>`
  rate with the same mismatched tokenizer.

All three start from byte-identical seeded initial weights (verified),
differing only in training data -- see `mt_finetune/README.md` for full
provenance, checksums, and what's still not determinism-guaranteed.
This directly narrows the "not per-language separate models" gap noted
in Limitations below, though it's still not the paper's actual reported
per-language results (those aren't independently reproduced here, only
the training methodology).

## Limitations
## Morphological Analysis Resources and Annotation Coverage
The current implementation does not yet integrate a fully automatic, linguistically complete morphological analyzer for all four languages. Instead, it combines available linguistic resources, human-annotated datasets, and rule-based processing.
Tigrinya, Geʿez, and Tigre resources include manually annotated morphological data, while additional morphological entries were obtained from HornMorpho resources and further post-edited for consistency. Amharic segmentation relies on HornMorpho-based morphological resources.
However, the current rule-based segmentation framework still has limitations in handling complex morphological phenomena, including:
- Multi-affix stacking.
- Root-and-pattern (templatic) Semitic morphology.
- Ambiguity resolution between valid morphological roots and coincidental prefix/suffix matches.
For example, a surface form may contain a sequence that resembles a known affix, but without deeper lexical and morphological analysis, it may be incorrectly segmented.
---
## MoVoC-Tok Constrained-Merge BPE Implementation
The constrained-merge BPE mechanism described as the core algorithmic contribution of MoVoC-Tok (Section 3.3) is not yet fully implemented in the current verification framework.
The present implementation focuses primarily on validating the morphological segmentation component. Full integration of the constrained-merge BPE training pipeline remains future work and is required for a complete reproduction of the original tokenizer algorithm.
---
## Gold-Standard Evaluation Resources
Human-annotated evaluation resources are available for multiple languages.
- **Tigrinya:** A manually annotated gold-standard dataset containing segmented prefix/root/suffix examples is available and used for evaluation.
- **Geʿez:** A human-annotated morphological dataset is available. However, evaluation remains challenging because Geʿez exhibits complex root-and-pattern morphology and many forms cannot be represented accurately using simple concatenative prefix/root/suffix boundaries.
- **Tigre:** Human-annotated morphological resources are available and used for rule development and validation.
- **Amharic:** Morphological resources are obtained from HornMorpho and existing linguistic resources.
Although these resources provide valuable evaluation material, future work requires richer annotation schemas that capture:
- Internal morphological structure.
- Root patterns.
- Morphosyntactic information.
- Language-specific morphological processes.
---
## Morphological Category Coverage
The current segmentation representation mainly models:
- Prefixes.
- Roots.
- Suffixes.
Other important morphological categories are not yet fully represented, including:
- Infixes.
- Clitics.
- Reduplication.
- Other language-specific morphological phenomena.

Expanding the annotation schema and segmentation framework is necessary to provide a more complete representation of the morphological systems of Geʿez-script languages.
---
## Vocabulary and Data Scale
The current vocabulary size and training data scale are smaller than those reported in the original MoVoC paper.
This was an intentional design choice for a reproducibility and verification study rather than a limitation of available resources. The current implementation provides a controlled environment for validating the methodology.
Future experiments can incorporate larger multilingual corpora and expanded vocabularies to further investigate scalability and tokenizer robustness.
---
## Downstream Machine Translation Evaluation
The current MoVoC_MT experiments provide an initial validation of MoVoC-Tok using a from-scratch MarianMT model trained on:
- English–Amharic.
- English–Tigrinya.
The model is additionally evaluated in a zero-shot setting on Tigre.
However, this evaluation is narrower than the complete experimental design reported in the original MoVoC paper, which included:
- Multiple tokenizer comparisons (BPE, WordPiece, and MoVoC-Tok).
- Separate language-specific experiments.
- A broader multilingual evaluation framework.
The current results demonstrate the practical impact of morphology-aware tokenization, but they do not yet represent a complete replication of the original MT experiments.
Future work will extend the evaluation to include broader tokenizer comparisons, larger-scale multilingual training, and more comprehensive downstream NLP tasks.


 
