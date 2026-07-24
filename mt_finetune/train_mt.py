"""
train_mt.py

Trains a from-scratch MarianMT model on English->Tigrinya only, single
direction, single language pair -- matching checkpoint-524316 exactly
(../MPETokenization/Paralleldata/results/checkpoint-524316): batch size 8,
max sequence length 128, peak LR 5e-5 with 500 warmup steps and linear
decay, 3 epochs, fp32 (checkpoint-524316's own config.json records
"torch_dtype": "float32", not fp16), transformers==4.51.3 (also stated
in that config.json, and pinned in ../requirements.lock.txt).

Data: ./data/all.en / ./data/all.ti -- the raw, unfiltered NLLB en-ti
mined corpus (copied verbatim from EnTiMT/01_collection/raw/opus_nllb.*,
see ../CHECKSUMS.sha256), not any deduplicated/cleaned version. This
matches checkpoint-524316's own real step count: 524316 steps / 3 epochs
* batch 8 = 1,398,176 implied examples/epoch, against this corpus's
1,398,173 lines -- a 3-line difference plausibly from empty-line
filtering, not a coincidence. checkpoint-524316's own trainer_state.json
has zero eval_loss entries and best_metric=null, indicating no held-out
eval set was used during the original training either, so none is used
here -- eval_strategy is "no", matching that.

Seeding: model initialization is seeded in build_model.py (before this
script runs, not here) -- the deviation from MoVoC_MT's build_model.py,
which left initialization unseeded. This script also seeds its own
data-order/dropout randomness via --seed, passed to
Seq2SeqTrainingArguments.

Logging: writes to both stdout (captured by SLURM into submit_job.sh's
--output/--error) and a dedicated timestamped file under ./logs/, via
the standard logging module, so training progress survives independent
of SLURM's log retention.

USAGE
    python train_mt.py --output_dir ./mt_output
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

MODEL_DIR = "./init_model"
MAX_LENGTH = 128


def setup_logging(log_dir: str) -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = Path(log_dir) / f"train_{timestamp}.log"

    logger = logging.getLogger("papermt_repro")
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


def read_parallel(en_path, ti_path):
    en_lines = [l.rstrip("\n") for l in open(en_path, encoding="utf-8")]
    ti_lines = [l.rstrip("\n") for l in open(ti_path, encoding="utf-8")]
    n = min(len(en_lines), len(ti_lines))
    pairs = [(en, ti) for en, ti in zip(en_lines[:n], ti_lines[:n]) if en.strip() and ti.strip()]
    return pairs


def build_dataset(pairs):
    sources = [en for en, ti in pairs]
    targets = [ti for en, ti in pairs]
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
    parser.add_argument("--train_en", default="./data/all.en")
    parser.add_argument("--train_ti", default="./data/all.ti")
    parser.add_argument("--output_dir", default="./mt_output")
    parser.add_argument("--log_dir", default="./logs")
    parser.add_argument("--per_device_train_batch_size", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=5e-5)
    parser.add_argument("--warmup_steps", type=int, default=500)
    parser.add_argument("--num_train_epochs", type=float, default=3.0)
    parser.add_argument("--save_steps", type=int, default=500)
    parser.add_argument("--logging_steps", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume_from_checkpoint", default=None,
                         help="path to a checkpoint dir to resume from (model/optimizer/scheduler/RNG state)")
    args = parser.parse_args()

    logger = setup_logging(args.log_dir)
    logger.info(f"args: {vars(args)}")

    logger.info("--- loading seeded from-scratch model + real checkpoint-524316 tokenizer ---")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR)
    logger.info(f"  vocab_size={tokenizer.vocab_size}, pad_token_id={tokenizer.pad_token_id}")

    logger.info("--- building English->Tigrinya dataset (single direction, single pair) ---")
    pairs = read_parallel(args.train_en, args.train_ti)
    logger.info(f"  {len(pairs)} pairs (source: raw NLLB en-ti, see ../CHECKSUMS.sha256)")
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

    logger.info(f"--- training (resume_from_checkpoint={args.resume_from_checkpoint}) ---")
    result = trainer.train(resume_from_checkpoint=args.resume_from_checkpoint)
    logger.info(f"train result: {result}")

    logger.info("--- saving final model ---")
    trainer.save_model(args.output_dir + "/final")
    tokenizer.save_pretrained(args.output_dir + "/final")
    logger.info("done.")


if __name__ == "__main__":
    main()
