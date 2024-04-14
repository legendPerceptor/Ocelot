#!/bin/bash
#SBATCH --job-name=64g16th
#SBATCH --account=yliu4
#SBATCH --output=/home/yliu4/tests/genome_benchmark.out
#SBATCH --error=/home/yliu4/tests/genome_benchmark.err
#SBATCH --time=06:00:00
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16

module load anaconda/2020.07
conda activate benchmark

python benchmark.py -c genome_rockfish.yml