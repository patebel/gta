#!/bin/bash
set -e

OUTPUT_DIR=../../data/open_street_map/wedding

# Boundaries of specific areas can be retrieved using overpass turbo (https://overpass-turbo.eu/#)
# Example query for wedding:
# [out:json];
# relation(28267);
# out geom;

# Helper functions for colored messages
print_message() {
    echo -e "\033[1;34m$1\033[0m"
}

print_error() {
    echo -e "\033[1;31m$1\033[0m"
    exit 1
}

# Create necessary directories
print_message "Creating necessary directories..."
mkdir -p $OUTPUT_DIR

# Retrieve boundaries using Python script
print_message "Retrieving boundaries using get_geojson_boundaries.py..."
boundaries=$(python get_geojson_boundaries.py)

# Ensure boundaries are not empty
if [[ -z "$boundaries" ]]; then
    print_error "Error: Boundaries are empty."
fi

# Download and convert Berlin OSM data
print_message "Downloading and processing Berlin OSM data..."
wget -q http://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf
osmosis --read-pbf berlin-latest.osm.pbf --write-xml berlin.osm

# Run netconvert with the boundaries
# TODO --osm.sidewalks --crossings.guess \
print_message "Running netconvert with boundaries..."
netconvert --keep-edges.in-geo-boundary "$boundaries" \
           --osm-files berlin.osm \
           -o $OUTPUT_DIR/wedding.net.xml \
           --geometry.remove --ramps.guess --junctions.join --tls.guess-signals --tls.discard-simple --tls.join --tls.default-type actuated \
           --sidewalks.guess --crossings.guess \
           --osm.bike-access \
           --remove-edges.isolated \
           --osm.lane-access \
           --osm.stop-output.length 20 --ptstop-output additional.xml --ptline-output ptlines.xml --ptline-clean-up \
           --railway.topology.repair \
           --type-files "../../sumo/data/typemap/osmNetconvert.typ.xml,../../sumo/data/typemap/osmNetconvertUrbanDe.typ.xml,../../sumo/data/typemap/osmNetconvertPedestrians.typ.xml,../../sumo/data/typemap/osmNetconvertBicycle.typ.xml,../../sumo/data/typemap/osmNetconvertRailUsage.typ.xml"\
           --verbose

print_message "Importing gtfs data..."
python ../../sumo/tools/import/gtfs/gtfs2pt.py -n $OUTPUT_DIR/wedding.net.xml --gtfs $OUTPUT_DIR/GTFS.zip --date 20240719 --repair
python remove_bus_stops_same_location.py
mv additional.xml gtfs_pt_stops.add.xml gtfs_pt_vehicles.add.xml vtypes.xml $OUTPUT_DIR/
# THEN DO: Modify and correct the connection from "1132406756#1" to "160130963#2" in netedit.
# Its somehow malformed and only allows delivery and bicycle. Dont know why. Maybe a highway.service problem???

# Run polyconvert with the boundaries
print_message "Generating poly file from OSM data..."
polyconvert --prune.boundary "539.5518409553915,552.7931781457737,5588.805469288782,3639.675442736596" --net-file $OUTPUT_DIR/wedding.net.xml --osm-files berlin.osm -o $OUTPUT_DIR/cluttered_wedding.poly.xml --all-attributes

# Filter poly file to keep only necessary attributes
print_message "Filtering poly file to keep only necessary attributes..."
python poly_keep_params_with_keys.py $OUTPUT_DIR/cluttered_wedding.poly.xml $OUTPUT_DIR/wedding.poly.xml building amenity office shop craft

# Clean up
rm berlin-latest.osm.pbf berlin.osm $OUTPUT_DIR/cluttered_wedding.poly.xml

print_message "Script completed successfully."
print_message "Remember to modify and correct the connection from 1132406756#1 to 160130963#2 in netedit."
print_message "Use connection mode and check whether the connection from 1132406756#1 to the other lane is there (almost turnaround)."
