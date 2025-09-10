#!/bin/bash
#SBATCH --job-name=DUAITERATE
#SBATCH --partition=paul-long
#SBATCH --time=240:00:00
#SBATCH --mem-per-cpu=20GB
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --ntasks-per-node=1

module load SUMO/1.22.0-foss-2023a

if [ -d "$HOME/sumo" ]; then
    echo "Repository exists. Updating..."
    cd "$HOME/sumo"
    git pull
    git submodule update --init --recursive
    cd -
else
    echo "Repository not found. Cloning..."
    git clone --recursive https://github.com/eclipse-sumo/sumo.git "$HOME/sumo"
fi

mkdir results_duaiterate
cd results_duaiterate

COMMON_PATH="../../data/open_street_map/berlin/"
NETWORK_NAME="berlin"
TRIPS_FILE="../../results/baseline-monday-berlin-sumo/trips.xml"

python3 ~/sumo/tools/assign/duaIterate.py \
    -n "${COMMON_PATH}${NETWORK_NAME}.net.xml" \
    -t "${TRIPS_FILE}" \
    --additional "${COMMON_PATH}vtypes.xml,${COMMON_PATH}gtfs_pt_stops.add.xml,${COMMON_PATH}gtfs_pt_vehicles.add.xml" \
    --duarouter-additional-files "${COMMON_PATH}vtypes.xml,${COMMON_PATH}gtfs_pt_stops.add.xml,${COMMON_PATH}gtfs_pt_vehicles.add.xml" \
    --duarouter-routing-threads 8 \
    --duarouter-ignore-errors \
    --continue-on-unbuild \
    --sumo-ignore-route-errors \
    --time-inc 8640 \
    --weight-memory \
    --pessimism 1 \
    --router-verbose \
    --inc-start 0.033 \
    --inc-base 30 \
    --inc-max 1 \
    --incrementation 1 \
    --time-to-teleport 20 \
    --log "duaiterate.log"
