# MoVoC: Morphology-Aware Subword Vocabulary Construction for Geʿez-Script Languages

[![Paper](https://img.shields.io/badge/ACL%20Anthology-2025.findings--emnlp.706-blue)](https://aclanthology.org/2025.findings-emnlp.706/)
[![Conference](https://img.shields.io/badge/EMNLP%202025-Findings-b31b1b)](https://2025.emnlp.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](#license)

Official implementation of **MoVoC**, a morphology-aware vocabulary construction method for low-resource Geʿez-script languages. MoVoC combines linguistically motivated morpheme units with Byte Pair Encoding (BPE) subword units into a hybrid vocabulary, and evaluates its impact on tokenization quality and downstream machine translation.

📄 **Paper:** [MoVoC: Morphology-Aware Subword Construction for Geʿez Script Languages](https://aclanthology.org/2025.findings-emnlp.706/) (Findings of ACL: EMNLP 2025)

---

## Table of Contents

- [Overview](#overview)
- [Repository Contents](#repository-contents)
- [Installation](#installation)
- [Data and Resources](#data-and-resources)
- [Methodology](#methodology)
  - [Supervised Morphological Analysis](#31-pre-tokenization-and-supervised-morphological-analysis)
  - [Vocabulary Construction](#32-vocabulary-construction-movoc)
  - [MoVoC-Tok Segmentation](#33-movoc-tok-morpheme-aware-subword-segmentation)
- [Experimental Setup](#experimental-setup)
- [Evaluation Framework](#evaluation-framework)
- [Reproducibility](#reproducibility)
- [Citation](#citation)
- [License](#license)
- [Contact](#contact)

---

## Overview

Subword tokenization methods such as BPE often fragment morphologically rich words, especially in low-resource languages. **MoVoC** addresses this limitation by incorporating morphological knowledge directly into vocabulary construction.

The framework combines:

1. Linguistically informed morphological analysis.
2. Morphology-aware vocabulary construction.
3. Hybrid tokenization using morpheme and subword units.
4. Evaluation on low-resource Geʿez-script languages.

Vocabulary construction and downstream experiments focus on:

- **Amharic**
- **Tigrinya**

Additional human-annotated morphological resources from **Geʿez** and **Tigre** are used for morphological evaluation.

---

## Repository Contents

This repository provides:

- Supervised morphological analysis pipeline
- Hybrid morpheme + BPE vocabulary construction
- **MoVoC-Tok** — morpheme-aware subword segmentation
- Morphological evaluation scripts
- Machine translation fine-tuning and evaluation experiments

---

## Installation

```bash
git clone https://github.com/<org>/MoVoC.git
cd MoVoC
pip install -r requirements.txt
```

> Requires Python 3.9+. Core dependencies include the Hugging Face `tokenizers` and `transformers` libraries.

---

## Data and Resources

| Resource | Description |
|----------|-------------|
| **Amharic corpus** | Publicly available corpus used for vocabulary construction and tokenizer training. |
| **Tigrinya corpus** | Publicly available corpus used for vocabulary construction and tokenizer training. |
| **Amharic and Tigrinya morphology** | Based on HornMorpho resources and additional linguistic resources with manual post-editing. |
| **Tigrinya morphological gold-standard data** | Manually annotated segmentation data combined with HornMorpho resources. |
| **Geʿez morphological data** | Human-annotated morphological data used for morphological evaluation. |
| **Tigre morphological resources** | Human-annotated morphological examples used for evaluation purposes. |

**External data sources:**

- **[HornMorpho](https://github.com/hltdi/HornMorpho)** — supervised morphological analysis and morpheme annotation resources (Amharic and Tigrinya only).
- **[NLLB (No Language Left Behind)](https://github.com/facebookresearch/fairseq/tree/nllb)** (Costa-Jussà et al., 2022) — Amharic and Tigrinya BPE vocabulary construction and parallel data for MT **fine-tuning**. NLLB is not used for evaluation.
- **[Stopes](https://github.com/facebookresearch/stopes)** — NLLB data-mining toolkit, used for mined multilingual parallel corpora.
- **[FLORES-200](https://github.com/facebookresearch/flores)** (Goyal et al., 2022) — used for **evaluation** (dev/test sets), Amharic and Tigrinya only.
- **[OPUS](https://opus.nlpl.eu/)** (Tiedemann, 2012) — used for **evaluation** across all four languages (Amharic, Tigrinya, Tigre, Geʿez), since Geʿez and Tigre are not covered by FLORES-200 or NLLB.

---

## Methodology

### 3.1. Pre-tokenization and Supervised Morphological Analysis

The MoVoC pipeline begins with corpus preprocessing and supervised morphological analysis:

- Corpus normalization and cleaning.
- Morphological segmentation (via **HornMorpho** for Amharic and Tigrinya).
- Extraction of morpheme units from linguistic resources, with manual post-editing applied to additional resources.

The resulting morphological information provides the basis for constructing a morphology-aware vocabulary.

### 3.2. Vocabulary Construction (MoVoC)

MoVoC constructs a hybrid vocabulary by combining BPE subword units and morpheme units:

```text
V_MoVoC = V_BPE,am ∪ V_BPE,ti ∪ V_morpheme,am ∪ V_morpheme,ti
```

where `V_BPE` denotes BPE subword units and `V_morpheme` denotes morphology-aware units.

**Construction process:**

1. Perform morphological segmentation on Amharic and Tigrinya corpora.
2. Train BPE models on the corresponding corpora.
3. Extract morpheme units from segmented data.
4. Combine BPE and morpheme vocabularies into the final MoVoC vocabulary.

### 3.3. MoVoC-Tok (Morpheme-Aware Subword Segmentation)

**MoVoC-Tok** integrates morphological boundaries into the BPE segmentation process. Unlike standard BPE, it restricts merge operations so generated subword units do not cross valid morpheme boundaries. This:

- Preserves morphological structure.
- Reduces invalid subword merges.
- Maintains the flexibility of subword tokenization.

---

## Experimental Setup

### Target Languages

**Vocabulary construction and MoVoC-Tok training** focus on two Geʿez-script languages — **Amharic** and **Tigrinya**. The **downstream evaluation**, however, extends to four languages: **Amharic**, **Tigrinya**, **Tigre**, and **Geʿez**.

### Dataset Details

**Training data:**
- Amharic and Tigrinya corpora for BPE training.
- HornMorpho-based resources for morphological information (Amharic and Tigrinya only).

**Fine-tuning data (machine translation):**
- English–Amharic and English–Tigrinya parallel corpora from the **NLLB** project (Costa-Jussà et al., 2022), mined and released by Meta AI.

**Evaluation data:**
- **Amharic and Tigrinya:** both languages are directly supported by **FLORES-200** (Goyal et al., 2022). We use the corresponding development and test sets for automatic evaluation using **BLEU** (Papineni et al., 2002) and **chrF++** (Popović, 2017).
- **Geʿez and Tigre:** since neither language is included in the FLORES-200 benchmark, nor part of the NLLB fine-tuning data (Costa-Jussà et al., 2022), we use 100 sentence pairs from the **OPUS** parallel corpus (Tiedemann, 2012) as the final evaluation set, applied consistently across all four languages for comparability.

**Test data composition (extrinsic evaluation):**

Extrinsic evaluation uses an unseen subset of the first 100 sentence pairs from OPUS (Tiedemann, 2012) for each target language. To balance the evaluation set at 100 pairs per language:

| Language | Test set composition | Extrinsic (MT) evaluation |
|---|---|---|
| Amharic | 100 of 213 available OPUS pairs | ✓ |
| Tigrinya | 74 from OPUS + 26 human-validated | ✓ |
| Tigre | 45 from OPUS + 55 human-validated | ✓ |
| Geʿez | 100 newly created and human-validated | ✗ — no parallel data available |

Because no parallel data exists for Geʿez, it is evaluated **intrinsically only**.

**Intrinsic evaluation data:**
- All four languages (Amharic, Tigrinya, Tigre, Geʿez) are evaluated against our annotated morpheme test set, designed to assess segmentation quality.
- This same annotated morphological data also supports tokenizer training for Amharic and Tigrinya.

### Training Setup and Configuration

- MoVoC-Tok is trained using the Hugging Face `tokenizers` library.
- Training includes: BPE model training for Amharic and Tigrinya → integration of morpheme-aware vocabulary units → construction of the final MoVoC vocabulary → training of the MoVoC-Tok tokenizer on the hybrid vocabulary.
- Downstream evaluation fine-tunes **MarianMT** models using English–Amharic and English–Tigrinya parallel corpora.

---

## Evaluation Framework

MoVoC is evaluated using both intrinsic and extrinsic settings.

### Intrinsic Evaluation

Measures the quality of morphology-aware tokenization against annotated morphological resources:

- Morpheme boundary preservation.
- Morphological segmentation quality.
- Vocabulary consistency.

### Extrinsic Evaluation: Machine Translation

Evaluates the downstream effect of MoVoC-Tok on:

- English ↔ Amharic
- English ↔ Tigrinya
- English ↔ Tigre

using standard automatic metrics: **BLEU** (Papineni et al., 2002) and **chrF++** (Popović, 2017). Amharic and Tigrinya are evaluated on FLORES-200 (Goyal et al., 2022); Tigre is evaluated on the 100-pair OPUS test set described above. **Geʿez has no available parallel data and is therefore excluded from extrinsic evaluation**, relying solely on the intrinsic morpheme test set. The comparison contrasts standard subword tokenization (BPE, WordPiece) against MoVoC-Tok's morphology-aware segmentation. Full results are reported in the paper.

---

## Reproducibility

This repository provides everything needed to reproduce the vocabulary construction and tokenizer evaluation experiments from the paper:

- Data processing scripts
- Vocabulary construction pipeline
- MoVoC-Tok tokenizer implementation
- Training and evaluation configurations

---

## Citation

If you use this repository, please cite:

```bibtex
@inproceedings{teklehaymanot-etal-2025-movoc,
    title = "{M}o{V}o{C}: Morphology-Aware Subword Construction for {G}e{'}ez Script Languages",
    author = "Teklehaymanot, Hailay Kidu and
      Fazlija, Dren and
      Nejdl, Wolfgang",
    booktitle = "Findings of the Association for Computational Linguistics: EMNLP 2025",
    year = "2025",
    pages = "13131--13144",
    publisher = "Association for Computational Linguistics",
    doi = "10.18653/v1/2025.findings-emnlp.706",
    url = "https://aclanthology.org/2025.findings-emnlp.706/"
}
```

---

## References

- Costa-Jussà, M. R., et al. (2022). *No Language Left Behind: Scaling Human-Centered Machine Translation.* NLLB Team, arXiv:2207.04672.
- Goyal, N., Gao, C., Chaudhary, V., Chen, P.-J., Wenzek, G., Ju, D., Krishnan, S., Ranzato, M., Guzmán, F., & Fan, A. (2022). *The Flores-101 Evaluation Benchmark for Low-Resource and Multilingual Machine Translation.* Transactions of the Association for Computational Linguistics, 10, 522–538.
- Papineni, K., Roukos, S., Ward, T., & Zhu, W.-J. (2002). *BLEU: a Method for Automatic Evaluation of Machine Translation.* Proceedings of the 40th Annual Meeting of the ACL, 311–318.
- Popović, M. (2017). *chrF++: words helping character n-grams.* Proceedings of the Second Conference on Machine Translation, 612–618.
- Tiedemann, J. (2012). *Parallel Data, Tools and Interfaces in OPUS.* Proceedings of LREC 2012.

---

## License

[Specify license here, e.g. MIT / Apache 2.0]

## Contact

For questions about the paper or code, please open an issue or contact **Hailay Kidu Teklehaymanot**.
