# This script is intended to take a .poly.xml file with the parameters from open street maps retained, as well as
# parameters that should be kept and filter out all other parameters as well as the polygons that have none of the
# parameters that should be kept. This potentially decreases the size of the poly file and increases performance.
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) < 4:
    print("Usage: python script.py <input_file> <key1> <key2>...")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]
keys_to_keep = sys.argv[3:]

tree = ET.parse(input_file)
root = tree.getroot()

for poly in root.findall('.//poly'):
    params_to_remove = [param for param in poly.findall('param') if param.get('key') not in keys_to_keep]
    for param in params_to_remove:
        poly.remove(param)
    # For more realistic maps, remove the following if statements
    if not poly.findall('param'):
        root.remove(poly)

tree.write(output_file)
print(f"Modified XML file saved to {output_file}")
