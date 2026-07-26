# MoVoC: Morphology-Aware Subword Vocabulary Construction for Geʿez-Script Languages

MoVoC introduces a morphology-aware vocabulary construction approach for low-resource Geʿez-script languages. The method combines linguistically motivated morpheme units with BPE subword units to construct a hybrid vocabulary and evaluates its impact on segmentation quality and downstream machine translation.

This implementation extends the original study from Amharic and Tigrinya to four Geʿez-script languages:

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

This repository reproduces and extends the methodology by incorporating additional annotated resources and extending the evaluation to four languages.

---

# Corpus and Data Sources

The following datasets and resources were used throughout the development and evaluation of **MoVoC**.

| **Resource** | **Description** |
|--------------|-----------------|
| **Amharic corpus** | Sourced from publicly available corpora used for vocabulary construction and tokenizer training. |
| **Tigrinya corpus** | Sourced from publicly available corpora used for vocabulary construction and tokenizer training. |
| **Amharic and Tigrinya morphology** | Based on HornMorpho resources and other linguistic resources, with manual post-editing. |
| **Tigrinya morphological gold-standard data** | Sourced from manually annotated gold-standard segmentation data and HornMorpho resources, with manual post-editing. |
| **Geʿez morphological data** | Sourced from manually annotated morphological data. This resource was **not** used for vocabulary construction. |
| **Tigre morphological resources** | Sourced from manually annotated linguistic examples. This resource was **not** used for vocabulary construction. |
| **MoVoC hybrid vocabulary** | Constructed by merging token-based and morpheme-based vocabularies from Amharic and Tigrinya. |
| **MoVoC-Tok tokenizer** | Implemented using a hybrid BPE and morphology-aware vocabulary. |
| **Machine Translation evaluation** | Conducted using MarianMT models. |

---

# Method Implementation

## 1. Morphological Analysis and Pre-processing

- Corpus normalization and cleaning.
- Morphological information from linguistic resources.
- Morpheme-aware vocabulary construction.

### The implementation

### Amharic

- Morphological information obtained from HornMorpho and existing linguistic resources.
- Additional post-processing was applied for consistency and supplemented with data collected from other sources.

### Tigrinya

- Human-annotated morphological gold-standard data were collected.
- Linguistically validated and post-edited morphological resources from HornMorpho.

### Tigre

- Human-annotated morphological examples.
- Linguistic validation was used to construct segmentation resources.

### Geʿez

- Human-annotated morphological resources.
- Additional manually collected lexical and morphological examples.
- Evaluation considers the complexity of Geʿez root-and-pattern morphology.

---

# Gold Morphological Resources

## Tigrinya, Geʿez

A manually annotated gold-standard dataset is available.

The dataset contains:

| Language | Word | Prefix | Root | Suffix | Infix | Clitic |
|----------|------|--------|------|---------|--------|---------|
| Tigrinya | ምሕዳራት | ም- | ሓደረ | -ት | – | – |
| Amharic | መምህርነት | መ- | ምህር | -ነት | – | – |
| Geʿez | እምነት | እ- | አመነ | -ት | – | – |
| Tigre | ኣብይና | ኣ- | ብይ | – | – | -ና |

However, Geʿez morphology is highly non-concatenative. Many forms involve root-and-pattern alternations, making simple prefix/root/suffix boundary evaluation insufficient, and more work is needed.

Therefore, Geʿez evaluation requires morphology-aware alignment methods beyond simple string-boundary matching.

---

# MoVoC Vocabulary Construction

The MoVoC algorithm constructs a hybrid vocabulary:

```text
V_MoVoC = V_BPE ∪ V_Morpheme
```

where:

- BPE tokens capture frequent subword patterns.
- Morpheme tokens preserve linguistic structure.

The implementation extends vocabulary construction for testing from two languages to four languages:

- Amharic
- Tigrinya
- Tigre
- Geʿez

---

# MoVoC Vocabulary Construction

We first extract **Amharic** and **Tigrinya** words from their respective text corpora.

Next, we perform both **token-based** and **morpheme-based** segmentation, producing four distinct vocabularies:

- Amharic token-based vocabulary
- Amharic morpheme-based vocabulary
- Tigrinya token-based vocabulary
- Tigrinya morpheme-based vocabulary

Finally, we merge these four vocabularies into a single **MoVoC-based vocabulary** (**V_MoVoC**).

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

Training and evaluation using parallel English–Amharic data.

## English → Tigrinya

Training and evaluation using parallel English–Tigrinya data.

## English → Geʿez

Evaluation using English–Classical Geʿez parallel resources.

## English → Tigre

Evaluation using available Tigre resources.

Evaluation datasets include:

- OPUS-based datasets.
- Tatoeba datasets.
- Available benchmark datasets for low-resource translation.

---

# Testing Data Scale

For testing, each language pair includes 100 sentence pairs from OPUS and, where necessary, human-annotated data, as follows:

- Amharic: 100 of 213 available sentence pairs from OPUS.
- Tigrinya: 74 sentence pairs from OPUS plus 26 human-validated sentence pairs.
- Tigre: 45 sentence pairs from OPUS plus 55 human-validated sentence pairs.
- Geʿez: 100 newly created and manually validated sentence pairs.

---

# Limitations and Future Work

## Morphological Complexity

Although the current system integrates real linguistic resources and human annotations, several challenges remain:

- Complex multi-affix stacking.
- Root-and-pattern morphology.
- Morphological ambiguity.
- Lexical disambiguation.

Future work will incorporate richer morphological analyzers and morphosyntactic information.

---

## Morphological Categories

Current segmentation focuses mainly on:

- Language-specific morphological processes.

## Machine Translation Evaluation

The downstream MT experiments demonstrate the effect of morphology-aware tokenization.

Future work will include:

- Larger multilingual training.
- Additional tokenizer comparisons.
- More extensive benchmark evaluation.
- Larger-scale language model adaptation.
- Extending the tokenizer.

---

# Citation

If you use this repository, please cite:

```bibtex
@inproceedings{teklehaymanot-etal-2025-movoc,
    title = "{M}o{V}o{C}: Morphology-Aware Subword Construction for {G}e{'}ez Script Languages",
    author = "Teklehaymanot, Hailay Kidu and
      Fazlija, Dren and
      Nejdl, Wolfgang",
    editor = "Christodoulopoulos, Christos and
      Chakraborty, Tanmoy and
      Rose, Carolyn and
      Peng, Violet",
    booktitle = "Findings of the Association for Computational Linguistics: EMNLP 2025",
    month = nov,
    year = "2025",
    address = "Suzhou, China",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2025.findings-emnlp.706/",
    doi = "10.18653/v1/2025.findings-emnlp.706",
    pages = "13131--13144",
    ISBN = "979-8-89176-335-7",
}
```
