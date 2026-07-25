#!/usr/bin/env bash

#SBATCH --nodes=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=32G
#SBATCH --job-name="papermt_repro_am"
#SBATCH --output=papermt_repro_train_am.out
#SBATCH --error=papermt_repro_train_am.err
#SBATCH --partition=ampere
#SBATCH --gres=gpu:a100:1
#SBATCH --time=24:00:00

source /homes/neumann/teklehaymanot/envs/papermt_repro/bin/activate

cd /homes/neumann/teklehaymanot/TigrinyaTokenizer/MPETokenization/Paralleldata/MoVoC/mt_finetune

# init_model_am/ already exists (built once, seeded, deterministic) -- not rebuilt here.
python -u train_mt_am.py --output_dir ./mt_output_am --resume_from_checkpoint ./mt_output_am/checkpoint-66000
