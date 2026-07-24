"""
build_model.py

Builds a from-scratch MarianMT model matching checkpoint-524316's own
saved config.json field-for-field (../MPETokenization/Paralleldata/results/
checkpoint-524316/config.json): 6 encoder + 6 decoder layers, 8 attention
heads, d_model=512, ffn_dim=2048, Swish activation, shared
encoder/decoder embeddings, static (sinusoidal) position embeddings,
vocab_size=63050, pad_token_id=63049, eos_token_id=0. Paired with that
checkpoint's own real tokenizer (./tokenizer/, copied verbatim from
checkpoint-524316 -- see ../CHECKSUMS.sha256), not a reconstruction.

The random initialization is seeded BEFORE model construction --
unlike MoVoC_MT's build_model.py, which left this unseeded and was
flagged for it in that project's Reproducibility audit. This is the
fix applied here from the start.

USAGE
    python build_model.py --outdir ./init_model --seed 42
"""

import argparse

import torch
from transformers import MarianConfig, MarianMTModel, MarianTokenizer


def build_model(vocab_size: int, pad_token_id: int, eos_token_id: int, decoder_start_token_id: int) -> MarianMTModel:
    config = MarianConfig(
        vocab_size=vocab_size,
        decoder_vocab_size=vocab_size,
        d_model=512,
        encoder_layers=6,
        decoder_layers=6,
        encoder_attention_heads=8,
        decoder_attention_heads=8,
        encoder_ffn_dim=2048,
        decoder_ffn_dim=2048,
        activation_function="swish",
        dropout=0.1,
        attention_dropout=0.0,
        activation_dropout=0.0,
        max_position_embeddings=512,
        share_encoder_decoder_embeddings=True,
        static_position_embeddings=True,
        normalize_embedding=False,
        add_final_layer_norm=False,
        scale_embedding=True,
        pad_token_id=pad_token_id,
        eos_token_id=eos_token_id,
        bos_token_id=0,
        decoder_start_token_id=decoder_start_token_id,
        forced_eos_token_id=eos_token_id,
    )
    return MarianMTModel(config)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="./init_model")
    parser.add_argument("--tokenizer_dir", default="./tokenizer")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # Seeded before any model construction -- this is the specific gap
    # being closed relative to MoVoC_MT's build_model.py.
    torch.manual_seed(args.seed)

    print(f"--- loading real checkpoint-524316 tokenizer from {args.tokenizer_dir} ---")
    tokenizer = MarianTokenizer.from_pretrained(args.tokenizer_dir)
    print(f"  vocab_size={tokenizer.vocab_size}, pad_token_id={tokenizer.pad_token_id}, "
          f"eos_token_id={tokenizer.eos_token_id}, unk_token_id={tokenizer.unk_token_id}")
    assert tokenizer.vocab_size == 63050, f"expected vocab_size 63050, got {tokenizer.vocab_size}"
    assert tokenizer.pad_token_id == 63049, f"expected pad_token_id 63049, got {tokenizer.pad_token_id}"

    print(f"--- building from-scratch MarianMT model (random init, seed={args.seed}) ---")
    model = build_model(
        vocab_size=tokenizer.vocab_size,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
        decoder_start_token_id=tokenizer.eos_token_id,
    )
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  model built, {n_params:,} parameters")

    print(f"--- saving to {args.outdir} ---")
    model.save_pretrained(args.outdir)
    tokenizer.save_pretrained(args.outdir)
    print("done.")


if __name__ == "__main__":
    main()
