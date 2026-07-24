#!/usr/bin/env bash

#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=30G
#SBATCH --job-name="papermt_repro_gez"
#SBATCH --output=papermt_repro_train_gez.out
#SBATCH --error=papermt_repro_train_gez.err
#SBATCH --partition=ampere
#SBATCH --gres=gpu:a100:1
#SBATCH --time=00:30:00

source /homes/neumann/teklehaymanot/envs/papermt_repro/bin/activate

cd /homes/neumann/teklehaymanot/TigrinyaTokenizer/MPETokenization/Paralleldata/MoVoC/mt_finetune

python -u build_model.py --outdir ./init_model_gez --seed 42
python -u train_mt_gez.py --output_dir ./mt_output_gez
