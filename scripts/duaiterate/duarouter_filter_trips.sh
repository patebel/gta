#!/bin/bash
#SBATCH --job-name=DUAROUTER_FILTER
#SBATCH --partition=paula
#SBATCH --time=48:00:00
#SBATCH --mem-per-cpu=100GB
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --ntasks-per-node=1

module load SUMO/1.22.0-foss-2023a

mkdir duarouter_filter_trips
cd duarouter_filter_trips

DATA_DIR="../../data/open_street_map/berlin"
TRIPS_DIR="../../results/baseline-monday-berlin-sumo-checkpoint/"

# Filters only normal trips
duarouter \
  -n $DATA_DIR/berlin.net.xml \
  -r $TRIPS_DIR/trips.xml \
  --additional-files $DATA_DIR/gtfs_pt_stops.add.xml,$DATA_DIR/validated.gtfs_pt_vehicles.add.xml \
  --routing-threads 8 \
  --ignore-errors \
  --write-trips true \
  -o validated.trips.xml \
  --log duarouter_filter.log
