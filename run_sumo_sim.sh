#!/bin/bash

# change all of this according to the configuration of your cluster
#SBATCH --time=48:00:00
#SBATCH --mem=250G
#SBATCH --ntasks=8
#SBATCH --job-name=traffic-simulacra
#SBATCH --partition=paula
#SBATCH --gres=gpu:a30:8
#SBATCH --cpus-per-task=1


module load Python/3.11.5-GCCcore-13.2.0
module load CUDA/12.4.0
module load SUMO/1.22.0-foss-2023a

if [ ! -d "venv" ]; then
    python -m venv venv
fi

source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

pip install -e .
python -m traffic_simulacra
