#!/bin/bash
#SBATCH --job-name=32g8th
#SBATCH --account chi151
#SBATCH --output=/home/yliu4/tests/genome_benchmark.out
#SBATCH --error=/home/yliu4/tests/genome_benchmark.err
#SBATCH --time=00:30:00
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --mem=32G

module load anaconda3/2021.05/q4munrg
conda activate benchmark

python benchmark.py -c genome_sdsc.yml