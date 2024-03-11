#!/bin/bash
#SBATCH --job-name sz3bench
#SBATCH -A bcnl-delta-cpu
#SBATCH -p cpu 
#SBATCH --nodes=1
#SBATCH --ntasks=1 
#SBATCH --time=00:30:00
#SBATCH -o /u/yliu4/tests/sz3bench-%j.o      # Name of stdout output file
#SBATCH -e /u/yliu4/tests/sz3bench-%j.e      # Name of stderr error file

module load anaconda3_x86_64/23.3.1 && conda activate sz_research

python benchmark_sz3.py -c ./ncsa-delta_benchmark_config.yml

