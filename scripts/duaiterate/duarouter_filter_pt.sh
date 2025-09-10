#!/bin/bash
#SBATCH --job-name=DUAROUTER_FILTER_PT
#SBATCH --partition=paula
#SBATCH --time=48:00:00
#SBATCH --mem-per-cpu=100GB
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --ntasks-per-node=1

module load SUMO/1.22.0-foss-2023a

mkdir duarouter_filter_pt
cd duarouter_filter_pt

DATA_DIR="../../data/open_street_map/berlin"

# Filters only public transport
duarouter \
  -n $DATA_DIR/berlin_no_walkingareas.net.xml \
  -r $DATA_DIR/gtfs_pt_vehicles.add.xml \
  --additional-files $DATA_DIR/vtypes.xml,$DATA_DIR/gtfs_pt_stops.add.xml \
  --routing-threads 8 \
  --ignore-errors \
  --repair \
  --write-trips true \
  --ptline-routing true \
  -o validated.gtfs_pt_vehicles.add.xml \
  --log duarouter_pt_filter.log
