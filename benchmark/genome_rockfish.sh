#!/bin/bash
#SBATCH --job-name=genome
#SBATCH -A PI-yliu4_gpu
#SBATCH --output=/home/yliu4/tests/genome-donut.out
#SBATCH --error=/home/yliu4/tests/genome-donut.err
#SBATCH --time=00:30:00
#SBATCH --partition=parallel
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16
#SBATCH --mem-per-cpu=4GB

export PATH=/home/yliu4/apps/blender-4.0.2-linux-x64:$PATH
blender -b lecture2-donut.blend -E CYCLES -s 10 -e 11 -t 2 -o ./render-1/ -a

