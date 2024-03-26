#!/bin/bash
#SBATCH --job-name=genome_sdsc
#SBATCH --account chi151
#SBATCH --output=/home/yliu4/tests/genome_benchmark.out
#SBATCH --error=/home/yliu4/tests/genome_benchmark.err
#SBATCH --time=01:30:00
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16

module load anaconda3/2021.05/q4munrg
source /home/yliu4/.bashrc
conda activate benchmark

python benchmark.py -c genome_sdsc.yml