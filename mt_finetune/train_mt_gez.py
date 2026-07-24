"""
train_mt_gez.py

Third parallel experiment: same architecture, same real checkpoint-524316
tokenizer, same seed (42) as train_mt.py (en-ti) and train_mt_am.py
(en-am), same batch=8/seq_len=128/lr=5e-5+500 warmup/3 epochs/fp32 --
this time English -> Classical Ge'ez.

Data: ./data_gez/all.en / ./data_gez/all.gez -- a genuine, verse-aligned
English<->Ge'ez parallel corpus (Bedru/Eng-Geez on the HF Hub, 2,107
rows, Genesis creation narrative), exported verbatim via
`datasets.load_dataset("Bedru/Eng-Geez")`. This is real parallel data,
not a synthetic pairing -- already referenced in MoVoC_Tok's own
01_collection/corpus_raw/manifest.json ("Eng-Geez", 2107 rows, license
per HF dataset card), but MoVoC_Tok only kept the monolingual Ge'ez
side for tokenizer training; this script is the first place in this
project family that uses it as an aligned MT pair. See
../CHECKSUMS.sha256.

Tokenizer mismatch, disclosed: checkpoint-524316's tokenizer was fit on
Tigrinya, not Classical Ge'ez. A 200-line check measured a 0.9% <unk>
rate -- even lower than the Amharic experiment's 2.1%, plausibly
because Ge'ez is the common ancestor script both Tigrinya and Amharic
derive their Fidel characters from.

Scale, disclosed: 2,107 pairs is dramatically smaller than the en-ti
(1,398,173) and en-am (1,398,173) runs -- 3 epochs at batch 8 is only
~790 total steps, meaning the shared --warmup_steps=500 default
consumes most of this run's schedule (unlike the other two, where 500
steps is a small fraction of ~524,000). Kept identical anyway for a
controlled comparison across all three experiments, not changed
silently. If a stronger converged model matters more than
comparability here, --num_train_epochs and --warmup_steps are worth
revisiting for this run specifically.

No held-out eval set, matching the same choice made in train_mt.py
(mirroring what the evidence says checkpoint-524316 itself did).

USAGE
    python build_model.py --outdir ./init_model_gez --seed 42
    python train_mt_gez.py --output_dir ./mt_output_gez
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from datasets import Dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

MAX_LENGTH = 128


def setup_logging(log_dir: str) -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = Path(log_dir) / f"train_gez_{timestamp}.log"

    logger = logging.getLogger("papermt_repro_gez")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(fmt)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.info(f"logging to {log_path}")
    return logger


def read_parallel(en_path, gez_path):
    en_lines = [l.rstrip("\n") for l in open(en_path, encoding="utf-8")]
    gez_lines = [l.rstrip("\n") for l in open(gez_path, encoding="utf-8")]
    n = min(len(en_lines), len(gez_lines))
    pairs = [(en, gz) for en, gz in zip(en_lines[:n], gez_lines[:n]) if en.strip() and gz.strip()]
    return pairs


def build_dataset(pairs):
    sources = [en for en, gz in pairs]
    targets = [gz for en, gz in pairs]
    return Dataset.from_dict({"source": sources, "target": targets})


def make_preprocess_fn(tokenizer):
    eos_id = tokenizer.eos_token_id

    def preprocess(examples):
        model_inputs = tokenizer(examples["source"], max_length=MAX_LENGTH, truncation=True)
        labels = tokenizer(examples["target"], max_length=MAX_LENGTH, truncation=True)
        model_inputs["input_ids"] = [ids[: MAX_LENGTH - 1] + [eos_id] for ids in model_inputs["input_ids"]]
        model_inputs["attention_mask"] = [m[: MAX_LENGTH - 1] + [1] for m in model_inputs["attention_mask"]]
        model_inputs["labels"] = [ids[: MAX_LENGTH - 1] + [eos_id] for ids in labels["input_ids"]]
        return model_inputs

    return preprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_dir", default="./init_model_gez")
    parser.add_argument("--train_en", default="./data_gez/all.en")
    parser.add_argument("--train_gez", default="./data_gez/all.gez")
    parser.add_argument("--output_dir", default="./mt_output_gez")
    parser.add_argument("--log_dir", default="./logs")
    parser.add_argument("--per_device_train_batch_size", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=5e-5)
    parser.add_argument("--warmup_steps", type=int, default=500)
    parser.add_argument("--num_train_epochs", type=float, default=3.0)
    parser.add_argument("--save_steps", type=int, default=500)
    parser.add_argument("--logging_steps", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    logger = setup_logging(args.log_dir)
    logger.info(f"args: {vars(args)}")

    logger.info("--- loading seeded from-scratch model + real checkpoint-524316 (en-ti) tokenizer ---")
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model_dir)
    logger.info(f"  vocab_size={tokenizer.vocab_size}, pad_token_id={tokenizer.pad_token_id}")
    logger.info("  NOTE: this tokenizer's target.spm was trained on Tigrinya, not Classical Ge'ez -- "
                "measured ~0.9% <unk> rate on a Ge'ez sample")

    logger.info("--- building English->Ge'ez dataset (single direction, single pair) ---")
    pairs = read_parallel(args.train_en, args.train_gez)
    logger.info(f"  {len(pairs)} pairs (source: Bedru/Eng-Geez, real verse-aligned parallel data, "
                f"see ../CHECKSUMS.sha256)")
    logger.info(f"  NOTE: at batch={args.per_device_train_batch_size}, {args.num_train_epochs} epochs "
                f"is ~{int(len(pairs) * args.num_train_epochs / args.per_device_train_batch_size)} total steps -- "
                f"warmup_steps={args.warmup_steps} consumes most of this run's schedule, unlike the "
                f"en-ti/en-am runs where 500 steps is a small fraction of ~524,000")
    train_ds = build_dataset(pairs)

    preprocess = make_preprocess_fn(tokenizer)
    train_ds = train_ds.map(preprocess, batched=True, remove_columns=["source", "target"])

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, label_pad_token_id=-100)

    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        overwrite_output_dir=True,
        per_device_train_batch_size=args.per_device_train_batch_size,
        learning_rate=args.learning_rate,
        lr_scheduler_type="linear",
        warmup_steps=args.warmup_steps,
        num_train_epochs=args.num_train_epochs,
        eval_strategy="no",
        save_strategy="steps",
        save_steps=args.save_steps,
        save_total_limit=3,
        predict_with_generate=False,
        generation_max_length=MAX_LENGTH,
        fp16=False,
        logging_steps=args.logging_steps,
        seed=args.seed,
        report_to=[],
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        data_collator=data_collator,
        processing_class=tokenizer,
    )

    logger.info("--- training ---")
    result = trainer.train()
    logger.info(f"train result: {result}")

    logger.info("--- saving final model ---")
    trainer.save_model(args.output_dir + "/final")
    tokenizer.save_pretrained(args.output_dir + "/final")
    logger.info("done.")


if __name__ == "__main__":
    main()
