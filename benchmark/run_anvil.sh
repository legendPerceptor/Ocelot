#!/bin/bash
#SBATCH --job-name sz3bench
#SBATCH -A cis220161
#SBATCH -p shared 
#SBATCH --nodes=1
#SBATCH --ntasks=1 
#SBATCH --time=00:30:00
#SBATCH -o /home/x-yliu4/tests/sz3bench-%j.o      # Name of stdout output file
#SBATCH -e /home/x-yliu4/tests/sz3bench-%j.e      # Name of stderr error file

module load anaconda/2021.05-py38 && conda activate sz_research

python benchmark_sz3.py

