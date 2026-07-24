# MoVoC (MT reproduction): Exact Reproduction of the Paper's Original en->ti MarianMT Run

> **Naming note**: this project is unrelated to, and separate from, the
> other `MoVoC` repo at `MPETokenization/Paralleldata/MoVoC` (pushed to
> `github.com/hailaykidu/MoVoC`), which holds the paper's
> vocabulary-construction code (BPE/hybrid vocab, morphology rules).
> That repo is not touched by anything here. This directory exists at
> `TigrinyaTokenizer/MoVoC` -- a different path, same name, deliberately
> chosen despite the collision risk.

A from-scratch MarianMT model, single language pair, single direction
(English -> Tigrinya), built to match `checkpoint-524316` -- the real,
verified checkpoint of the paper's own original training run -- as
exactly as the evidence in this environment allows. Also includes two
further parallel experiments reusing the same tokenizer, architecture,
and seed: English->Amharic and English->Classical Ge'ez (see below).

This is deliberately **not** MoVoC_MT: that project evaluates MoVoC_Tok
downstream with a 120k shared vocabulary and bidirectional en<->am/en<->ti
training. This project instead reproduces the original single-pair en-ti
run itself, using its own real 63,050-token tokenizer, closing the
specific reproducibility gaps identified in MoVoC_MT's audit.

## What's verified vs. assumed

Everything below was confirmed directly from files on disk, not inferred:

| Fact | Evidence |
|---|---|
| Architecture (6+6 layers, 8 heads, d_model=512, ffn=2048, swish, shared embeddings, static position embeddings) | `MPETokenization/Paralleldata/results/checkpoint-524316/config.json` |
| `transformers==4.51.3` | Same `config.json`: `"transformers_version": "4.51.3"` |
| `vocab_size=63050`, `pad_token_id=63049`, `eos_token_id=0` | Same `config.json` |
| Single direction: English in, Tigrinya out | `Paralleldata/Run.py` and `Paralleldata/pp.py` both feed English text to the model and treat the output as Tigrinya |
| No direction tags / single pair only | Checked the real vocab.json for `>>amh<<`/`>>tir<<`/`>>eng<<` tokens -- none exist |
| `train_batch_size=8` | `checkpoint-524316/trainer_state.json` |
| `max_length=128` | `pp.py`'s `model.generate(..., max_length=128)`, and the paper's own README claim (`MT_tig_Model/README.md`) |
| Peak LR ~5e-5, linear decay | `trainer_state.json` log_history: LR climbs from 9.9e-6 (step 100) to 4.999e-05 (step ~500), consistent with 500 warmup steps |
| fp32, not fp16 | `checkpoint-524316/config.json`: `"torch_dtype": "float32"` |
| No held-out eval set used originally | `trainer_state.json`: `best_metric`, `best_global_step`, `best_model_checkpoint` are all `null`, and zero `eval_loss` entries exist in `log_history` |
| Training data = raw, unfiltered NLLB en-ti mine (not any deduplicated version) | `trainer_state.json`'s `global_step=524316` over 3 epochs at batch 8 implies 1,398,176 examples/epoch; `EnTiMT/01_collection/raw/opus_nllb.en`/`.ti` has 1,398,173 lines -- a 3-line difference plausibly from empty-line filtering |

## Provenance

- `tokenizer/` -- copied verbatim from `checkpoint-524316` (`source.spm`,
  `target.spm`, `vocab.json`, `tokenizer_config.json`,
  `special_tokens_map.json`). Not reconstructed.
- `data/all.en` / `data/all.ti` -- copied verbatim from
  `EnTiMT/01_collection/raw/opus_nllb.en`/`.ti`, the raw mined corpus
  before EnTiMT's own dedup/cleaning pipeline runs.
- `CHECKSUMS.sha256` -- SHA-256 of both data files and all three
  tokenizer artifacts, recorded at copy time, so this project doesn't
  repeat MoVoC_MT's "external, unversioned dependency" gap.

## What's fixed relative to MoVoC_MT's reproducibility audit

- **Model init is seeded before construction** (`build_model.py`, uses
  `torch.manual_seed(args.seed)` before `MarianMTModel(config)`) --
  MoVoC_MT's `build_model.py` had no seed at all. Verified here: two
  independent runs of `build_model.py --seed 42` produce byte-identical
  `model.safetensors`.
- **Dependencies are pinned in a committed lockfile**
  (`requirements.lock.txt`, generated via `pip freeze` from a dedicated
  venv at `/homes/teklehaymanot/envs/papermt_repro` with
  `transformers==4.51.3` installed explicitly) -- MoVoC_MT had none.
- **No external, unversioned file paths** -- tokenizer and data are
  copied into this project with recorded checksums, not referenced from
  sibling directories by absolute path.

## Not fixed / still open

- fp32 training is still not forced-deterministic (no
  `torch.use_deterministic_algorithms`); CPU/GPU floating-point
  reduction order can still vary run to run even with a fixed seed.
- No held-out eval set is used, matching what the evidence says the
  original did -- but this also means there's no independent BLEU/chrF
  signal produced by this run itself; that would need a separate
  evaluation step against a real, disjoint test set.

## Pipeline

```
build_model.py   -> seeded from-scratch MarianMT + real checkpoint-524316 tokenizer
train_mt.py      -> single-direction en->ti training, batch=8, seq_len=128, fp32, logging to ./logs/
submit_job.sh    -> SLURM job wrapper (both steps)
```

## Reproducing

```bash
source /homes/neumann/teklehaymanot/envs/papermt_repro/bin/activate
python build_model.py --outdir ./init_model --seed 42
python train_mt.py --output_dir ./mt_output
```

or via SLURM: `sbatch submit_job.sh` (expected runtime ~12-16h on a
single A100, matching the original's real 43,376.7s / ~12h wall time
stated in `MT_tig_Model/README.md`).

## English->Amharic experiment

A second, parallel run: same architecture, same real checkpoint-524316
tokenizer, same seed (42) -- so `init_model/` and `init_model_am/` are
byte-identical, verified -- same batch=8/seq_len=128/lr=5e-5/3 epochs/
fp32, but trained on English->Amharic instead of English->Tigrinya.

**Deliberate, disclosed mismatch**: the tokenizer's `target.spm` was
fit on Tigrinya, not Amharic. A quick check before building this (50
real Amharic lines from the raw NLLB en-am corpus) measured a **2.1%
`<unk>` rate** -- low enough to be viable (Amharic and Tigrinya share
substantial Ge'ez-script subword overlap) but real, non-zero OOV loss
a purpose-built Amharic tokenizer wouldn't have. This is not a claim
that the paper used this exact setup for Amharic -- it's this
project's own choice, made explicit here and in `train_mt_am.py`'s
docstring.

**Data**: `data_am/all.en` / `data_am/all.am` -- the first 1,398,173
raw lines of `MPETokenization/Paralleldata/NLLB.am-en.{en,am}`
(16,137,053 lines total), capped to match the en-ti run's exact corpus
size so the two experiments are directly comparable in step count and
wall-clock time. Checksums recorded in `CHECKSUMS.sha256`.

```
build_model.py    -> reused unchanged: python build_model.py --outdir ./init_model_am --seed 42
train_mt_am.py    -> single-direction en->am training, same hyperparameters as train_mt.py
submit_job_am.sh  -> SLURM job wrapper (both steps)
```

Reproducing:

```bash
source /homes/neumann/teklehaymanot/envs/papermt_repro/bin/activate
python build_model.py --outdir ./init_model_am --seed 42
python train_mt_am.py --output_dir ./mt_output_am
```

or via SLURM: `sbatch submit_job_am.sh` (expected runtime similar to
the en-ti run, ~12-16h on a single A100, since corpus size and
hyperparameters are matched).

## English->Classical Ge'ez experiment

A third parallel experiment, same architecture/tokenizer/seed as the
other two (`init_model_gez/` is byte-identical to `init_model/` and
`init_model_am/`, verified) -- this time English -> Classical Ge'ez.

**Real parallel data, not synthetic**: `data_gez/all.en` / `all.gez` is
a genuine, verse-aligned English<->Ge'ez corpus -- `Bedru/Eng-Geez` on
the HF Hub, 2,107 rows (Genesis creation narrative), exported via
`datasets.load_dataset("Bedru/Eng-Geez")`. Already referenced in
MoVoC_Tok's own `01_collection/corpus_raw/manifest.json` ("Eng-Geez",
2107 rows), but MoVoC_Tok only kept the monolingual Ge'ez side for
tokenizer training -- this is the first place in this project family
that trains on it as an aligned MT pair. Checksums in
`CHECKSUMS.sha256`.

**Tokenizer mismatch, disclosed**: same caveat as the Amharic
experiment -- `target.spm` was fit on Tigrinya, not Classical Ge'ez.
Measured **0.9% `<unk>` rate** on a 200-line sample, even lower than
Amharic's 2.1%, plausibly because Ge'ez is the common ancestor script
both Tigrinya and Amharic derive their Fidel characters from.

**Scale, disclosed**: 2,107 pairs is dramatically smaller than the
en-ti/en-am runs (1,398,173 each). At batch=8, 3 epochs is only ~790
total steps -- meaning the shared `warmup_steps=500` default consumes
most of this run's schedule, unlike the other two where it's a small
fraction of ~524,000 steps. Kept identical anyway for a controlled
three-way comparison, not changed silently -- see `train_mt_gez.py`'s
docstring if a stronger-converged model matters more than
comparability here.

```
build_model.py     -> reused unchanged: python build_model.py --outdir ./init_model_gez --seed 42
train_mt_gez.py    -> single-direction en->gez training, same hyperparameters
submit_job_gez.sh  -> SLURM job wrapper (--time=00:30:00 -- ~790 steps, not 12-16h)
```

Reproducing:

```bash
source /homes/neumann/teklehaymanot/envs/papermt_repro/bin/activate
python build_model.py --outdir ./init_model_gez --seed 42
python train_mt_gez.py --output_dir ./mt_output_gez
```

or via SLURM: `sbatch submit_job_gez.sh` (expected runtime well under
an hour, given the small corpus).
