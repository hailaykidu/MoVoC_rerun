# MoVoC: Morphology-Aware Subword Vocabulary Construction for Geʿez-Script Languages

MoVoC introduces a morphology-aware vocabulary construction approach for
low-resource Geʿez-script languages. The method combines linguistically
motivated morpheme units with BPE subword units to construct a hybrid
vocabulary and evaluates its impact on segmentation quality and downstream
machine translation.

This implementation extends the original study from Amharic and Tigrinya
to four Geʿez-script languages:

- Amharic
- Tigrinya
- Tigre
- Geʿez

The repository provides:

- Morphological resource integration
- Hybrid morpheme + BPE vocabulary construction
- MoVoC-Tok tokenizer training
- Intrinsic morphological evaluation
- Downstream MarianMT machine translation experiments

---

# Overview

The original MoVoC paper focuses on:

1. Linguistically informed morphological analysis.
2. Morphology-aware vocabulary construction.
3. Hybrid tokenization combining morphemes and subwords.
4. Evaluation on low-resource Geʿez-script languages.

This repository reproduces and extends the methodology by incorporating
additional annotated resources and extending the evaluation to four languages.

---

# What's Real vs. Constructed

| Component | Status |
|---|---|
| Amharic corpus | Real corpus used for vocabulary construction and tokenizer training |
| Tigrinya corpus | Real corpus used for vocabulary construction and tokenizer training |
| Tigre corpus | Real corpus added for extended evaluation |
| Geʿez corpus | Real corpus expanded with additional manually collected linguistic data |
| Tigrinya morphological gold data | Real manually annotated gold-standard segmentation data |
| Geʿez morphological data | Real human-annotated morphological data |
| Tigre morphological resources | Real human-annotated examples and linguistic validation |
| Amharic morphology | Based on HornMorpho resources and linguistic resources with post-editing |
| Segmentation rules | Combination of linguistic resources, annotation, and language-specific adaptation |
| MoVoC hybrid vocabulary | Implemented |
| MoVoC-Tok tokenizer | Implemented using hybrid BPE + morpheme vocabulary |
| Machine Translation evaluation | Implemented using MarianMT models |

---

# Method Implementation

## 1. Morphological Analysis and Pre-processing

The original paper uses:

- Corpus normalization and cleaning.
- Morphological information from linguistic resources.
- Morpheme-aware vocabulary construction.

This implementation follows the same principle but extends the resources:

### Amharic

- Morphological information obtained from HornMorpho and existing linguistic resources.
- Additional post-processing applied for consistency.

### Tigrinya

- Human-annotated morphological gold-standard data.
- Linguistic validation and post-edited morphological resources.

### Tigre

- Human-annotated morphological examples.
- Linguistic validation used to construct segmentation resources.

### Geʿez

- Human-annotated morphological resources.
- Additional manually collected lexical and morphological examples.
- Evaluation considers the complexity of Geʿez root-and-pattern morphology.

---

# Gold Morphological Resources

## Tigrinya

A manually annotated gold-standard dataset is available:

The dataset contains:

- Prefix
- Root
- Infix
- Suffix information

However, Geʿez morphology is highly non-concatenative. Many forms involve
root-and-pattern alternations, making simple prefix/root/suffix boundary
evaluation insufficient.

Therefore, Geʿez evaluation requires morphology-aware alignment methods
beyond simple string-boundary matching.

---

# MoVoC Vocabulary Construction

The original MoVoC algorithm constructs a hybrid vocabulary:

\[
V_{MoVoC}=V_{BPE}\cup V_{Morpheme}
\]

where:

- BPE tokens capture frequent subword patterns.
- Morpheme tokens preserve linguistic structure.

This implementation extends the vocabulary construction from two languages
(Amharic and Tigrinya in the original paper) to four languages:

- Amharic
- Tigrinya
- Tigre
- Geʿez

---

# Vocabulary Configuration

Experimental configuration:

| Parameter | Value |
|---|---:|
| Languages | 4 |
| Total vocabulary size | 8,000 |
| Vocabulary per language | 2,000 |
| BPE proportion | 70% |
| Morpheme proportion | 30% |
| BPE vocabulary per language | 1,400 |
| Morpheme vocabulary per language | 600 |

The final hybrid vocabulary is created by merging:

BPE vocabulary + Morphological vocabulary

with duplicate tokens removed.

---

# MoVoC-Tok Tokenizer

MoVoC-Tok is trained from the hybrid vocabulary.

The tokenizer combines:

- Statistical subword learning from BPE.
- Linguistic information from morphological units.

The resulting tokenizer aims to reduce:

- Fragmentation of morphological units.
- Loss of linguistic structure.
- Inefficient representation of rare words.

---

# Downstream Machine Translation Evaluation

The tokenizer is evaluated using MarianMT models.

Experiments include:

## English → Amharic

Training and evaluation using parallel English-Amharic data.

## English → Tigrinya

Training and evaluation using parallel English-Tigrinya data.

## English → Geʿez

Evaluation using English-Classical Geʿez parallel resources.

## English → Tigre

Evaluation using available Tigre resources.

Evaluation datasets include:

- OPUS-based datasets.
- Tatoeba datasets.
- Available benchmark datasets for low-resource translation.

---

# Data Scale

The experiments use the following approximate corpus sizes:

| Language | Clean Corpus |
|---|---:|
| Amharic | ~12M sentences |
| Tigrinya | ~2.6M sentences |
| Tigre | ~730K sentences |
| Geʿez | Expanded manually curated corpus |

For verification experiments, subsets are used to reduce computational cost.

---

# Repository Structure

---

# Limitations and Future Work

## Morphological Complexity

Although the current system integrates real linguistic resources and human
annotations, several challenges remain:

- Complex multi-affix stacking.
- Root-and-pattern morphology.
- Morphological ambiguity.
- Lexical disambiguation.

Future work will incorporate richer morphological analyzers and
morphosyntactic information.

---

## Morphological Categories

Current segmentation focuses mainly on:

- Prefixes.
- Roots.
- Suffixes.

Future extensions will include:

- Infixes.
- Clitics.
- Reduplication.
- Language-specific morphological processes.

---

## Vocabulary Scale

The current experiments use an 8K vocabulary for reproducibility and
efficient verification.

The original paper uses larger vocabulary settings. Future experiments will
investigate larger-scale vocabulary construction.

---

## Machine Translation Evaluation

Current MT experiments demonstrate the effect of morphology-aware
tokenization.

Future work will include:

- Larger multilingual training.
- Additional tokenizer comparisons.
- More extensive benchmark evaluation.
- Larger-scale language model adaptation.

---

# Citation

If you use this repository, please cite:

```bibtex
@article{teklehaymanot2025movoc,
title={MoVoC: Morphology-Aware Subword Construction for Ge'ez Script Languages},
author={Teklehaymanot, Hailay Kidu and Fazlija, Emir and Nejdl, Wolfgang},
year={2025},
journal={arXiv preprint arXiv:2509.08812}
}
