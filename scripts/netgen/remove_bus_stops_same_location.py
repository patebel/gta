import xml.etree.ElementTree as ET


def remove_unwanted_stops(file_path):
    try:
        # Load XML string from file
        with open(file_path, 'r', encoding='utf-8') as file:
            xml_string = file.read()

        tree = ET.ElementTree(ET.fromstring(xml_string))
        root = tree.getroot()

        for vehicle in root.findall('vehicle'):
            stops = vehicle.findall('stop')
            remove_next = False
            for stop in stops:
                bus_stop = stop.get('busStop')
                if bus_stop == "de:11000:900009202::9_2":
                    remove_next = True
                elif bus_stop == "de:11000:900009202::14_0" and remove_next:
                    vehicle.remove(stop)
                    remove_next = False
                else:
                    remove_next = False

        return ET.tostring(root, encoding='unicode')

    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None


def save_xml_to_file(xml_string, output_file_path):
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(xml_string)
    except IOError as e:
        print(f"Error writing to file: {e}")


# File paths
input_file_path = 'gtfs_pt_vehicles.add.xml'  # Change this to the path of your input file
output_file_path = 'gtfs_pt_vehicles.add.xml'  # Change this to the path of your output file

# Process the XML file
modified_xml = remove_unwanted_stops(input_file_path)

# Save the modified XML back to a file
save_xml_to_file(modified_xml, output_file_path)

print(f'Modified XML has been saved to {output_file_path}')
