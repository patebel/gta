#!/bin/bash
#SBATCH --job-name=OTP
#SBATCH --partition=paula
#SBATCH --time=48:00:00
#SBATCH --mem-per-cpu=100GB
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --ntasks-per-node=1

echo "OTP is running on node: $(hostname)"

# Create directory for data and config
mkdir berlin

# Download OSM data
curl -L https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf -o berlin/osm.pbf

# Download GTFS data
curl -L https://vbb.de/vbbgtfs -o berlin/vbb-gtfs.zip

# Build graph and save it onto the host system
singularity run --bind "$(pwd)/berlin:/var/opentripplanner" docker://opentripplanner/opentripplanner:latest --build --save

# Load and serve graph
singularity run --bind "$(pwd)/berlin:/var/opentripplanner" docker://opentripplanner/opentripplanner:latest --load --serve
