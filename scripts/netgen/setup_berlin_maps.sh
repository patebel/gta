#!/bin/bash
set -e

OUTPUT_DIR=../../data/open_street_map/berlin

echo -e "\n\033[1;32mSetting up Berlin maps for traffic simulation...\033[0m\n"

echo -e "\n\033[1;34mDownloading Berlin OSM data...\033[0m"
wget http://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf

echo -e "\n\033[1;34mConverting OSM data to XML...\033[0m"
osmosis --read-pbf berlin-latest.osm.pbf --write-xml berlin.osm

echo -e "\n\033[1;34mRunning netconvert...\033[0m"
netconvert --osm-files berlin.osm \
           -o $OUTPUT_DIR/berlin.net.xml \
           --geometry.remove --ramps.guess --junctions.join --tls.guess-signals --tls.discard-simple --tls.join --tls.default-type actuated \
           --sidewalks.guess --crossings.guess \
           --osm.bike-access \
           --remove-edges.isolated \
           --osm.lane-access \
           --osm.stop-output.length 20 --ptstop-output additional.xml --ptline-output ptlines.xml --ptline-clean-up \
           --railway.topology.repair \
           --type-files "../../sumo/data/typemap/osmNetconvert.typ.xml,../../sumo/data/typemap/osmNetconvertUrbanDe.typ.xml,../../sumo/data/typemap/osmNetconvertPedestrians.typ.xml,../../sumo/data/typemap/osmNetconvertBicycle.typ.xml,../../sumo/data/typemap/osmNetconvertRailUsage.typ.xml"\
           --verbose

echo -e "\n\033[1;34mImporting GTFS data...\033[0m"
python ../../sumo/tools/import/gtfs/gtfs2pt.py -n $OUTPUT_DIR/berlin.net.xml --gtfs ../../data/open_street_map/GTFS.zip --date 20240719 --osm-routes ptlines.xml --repair
python remove_bus_stops_same_location.py
mv additional.xml gtfs_pt_stops.add.xml gtfs_pt_vehicles.add.xml vtypes.xml $OUTPUT_DIR

# THEN DO: Modify and correct the connection from "1132406756#1" to "160130963#2" in netedit.
# It's somehow malformed and only allows delivery and bicycle. Don't know why. Maybe a highway.service problem?

echo -e "\n\033[1;34mGenerating poly file from OSM data...\033[0m"
polyconvert --prune.in-net=true --net-file $OUTPUT_DIR/berlin.net.xml --osm-files berlin.osm -o $OUTPUT_DIR/cluttered_berlin.poly.xml --all-attributes

echo -e "\n\033[1;34mFiltering poly file to keep only necessary attributes...\033[0m"
python poly_keep_params_with_keys.py $OUTPUT_DIR/cluttered_berlin.poly.xml $OUTPUT_DIR/berlin.poly.xml building amenity office shop craft

echo -e "\n\033[1;34mCleaning up temporary files...\033[0m"
rm berlin-latest.osm.pbf berlin.osm $OUTPUT_DIR/cluttered_berlin.poly.xml

echo -e "\n\033[1;32mBerlin maps setup complete!\033[0m\n"
