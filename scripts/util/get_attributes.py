import json
import logging

import geopandas as gpd

# Configure logging
logging.basicConfig(
    filename='geodata_attributes.log',  # Log file name
    filemode='a',  # Append mode
    level=logging.DEBUG,  # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    try:
        logger.info("Loading geospatial data...")
        buildings_file = "/data/taz/berlin_buildings.gpkg"
        buildings = gpd.read_file(buildings_file)

        # Define candidate attributes
        candidate_attributes = ["building", "amenity", "office", "shop", "craft"]
        candidate_attributes = [attr for attr in candidate_attributes if attr in buildings.columns]

        # Extract attribute values
        attribute_values = {
            attr: buildings[attr].dropna().unique().tolist()
            for attr in candidate_attributes
        }

        # Print the attribute values in JSON format
        output_json = json.dumps(attribute_values, indent=4)
        print(output_json)

        # Log the attribute values
        logger.info("Attribute values extracted successfully")
        logger.debug(f"Attribute values: {output_json}")

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
