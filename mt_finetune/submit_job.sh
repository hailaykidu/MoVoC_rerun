#!/usr/bin/env bash

#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=60G
#SBATCH --job-name="papermt_repro"
#SBATCH --output=papermt_repro_train.out
#SBATCH --error=papermt_repro_train.err
#SBATCH --partition=ampere
#SBATCH --gres=gpu:a100:1
#SBATCH --time=16:00:00

source /homes/neumann/teklehaymanot/envs/papermt_repro/bin/activate

cd /homes/neumann/teklehaymanot/TigrinyaTokenizer/MPETokenization/Paralleldata/MoVoC/mt_finetune

# init_model/ already exists (built once, seeded, deterministic) -- not rebuilt here.
python -u train_mt.py --output_dir ./mt_output --resume_from_checkpoint ./mt_output/checkpoint-2500
