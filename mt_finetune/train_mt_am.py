"""
train_mt_am.py

Same setup as train_mt.py (single direction, batch=8, seq_len=128, lr 5e-5/
500 warmup, 3 epochs, fp32), but English->Amharic instead of English->
Tigrinya, reusing the SAME checkpoint-524316 tokenizer (63,050 vocab,
trained for English/Tigrinya, not Amharic).

This is a deliberate, disclosed mismatch: the tokenizer's target-side
SentencePiece model (target.spm) was fit on Tigrinya text, not Amharic.
A quick check before building this (50-line Amharic sample) measured a
2.1% <unk> rate -- low enough to be viable, since Amharic and Tigrinya
share substantial Ge'ez-script subword overlap, but real, non-zero OOV
loss that a purpose-built Amharic tokenizer would not have. Reported
here, not hidden.

Data: ./data_am/all.en / ./data_am/all.am -- the first 1,398,173 raw
lines of the NLLB en-am mined corpus (MPETokenization/Paralleldata/
NLLB.am-en.{en,am}, 16,137,053 lines total), capped to match the en-ti
run's exact corpus size so the two experiments are comparable in step
count and wall-clock time -- not because the paper states this cap for
Amharic specifically (it doesn't, for this single-pair scenario); this
is this project's own choice, disclosed. See ../CHECKSUMS.sha256.

Model init: build_model.py is reused unchanged with --outdir
./init_model_am --seed 42 -- same architecture, same tokenizer, same
seed as the en-ti run, so both experiments start from literally
identical weights and differ only in training data.

USAGE
    python build_model.py --outdir ./init_model_am --seed 42
    python train_mt_am.py --output_dir ./mt_output_am
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
    log_path = Path(log_dir) / f"train_am_{timestamp}.log"

    logger = logging.getLogger("papermt_repro_am")
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


def read_parallel(en_path, am_path):
    en_lines = [l.rstrip("\n") for l in open(en_path, encoding="utf-8")]
    am_lines = [l.rstrip("\n") for l in open(am_path, encoding="utf-8")]
    n = min(len(en_lines), len(am_lines))
    pairs = [(en, am) for en, am in zip(en_lines[:n], am_lines[:n]) if en.strip() and am.strip()]
    return pairs


def build_dataset(pairs):
    sources = [en for en, am in pairs]
    targets = [am for en, am in pairs]
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
    parser.add_argument("--model_dir", default="./init_model_am")
    parser.add_argument("--train_en", default="./data_am/all.en")
    parser.add_argument("--train_am", default="./data_am/all.am")
    parser.add_argument("--output_dir", default="./mt_output_am")
    parser.add_argument("--log_dir", default="./logs")
    parser.add_argument("--per_device_train_batch_size", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=5e-5)
    parser.add_argument("--warmup_steps", type=int, default=500)
    parser.add_argument("--num_train_epochs", type=float, default=3.0)
    parser.add_argument("--save_steps", type=int, default=500)
    parser.add_argument("--logging_steps", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    logger = setup_logging(args.log_dir)
    logger.info(f"args: {vars(args)}")

    logger.info("--- loading seeded from-scratch model + real checkpoint-524316 (en-ti) tokenizer ---")
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model_dir)
    logger.info(f"  vocab_size={tokenizer.vocab_size}, pad_token_id={tokenizer.pad_token_id}")
    logger.info("  NOTE: this tokenizer's target.spm was trained on Tigrinya, not Amharic -- "
                "expect a non-zero <unk> rate on Amharic text (measured ~2.1% on a small sample)")

    logger.info("--- building English->Amharic dataset (single direction, single pair) ---")
    pairs = read_parallel(args.train_en, args.train_am)
    logger.info(f"  {len(pairs)} pairs (source: raw NLLB en-am, capped to match en-ti run size, "
                f"see ../CHECKSUMS.sha256)")
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
