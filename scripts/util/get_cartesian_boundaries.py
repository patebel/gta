from pyproj import Proj, transform

# Define the projection parameters from the SUMO network file
proj_parameters = "+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
net_offset = (-384261.29, -5821421.26)
conv_boundary = (0.00, 0.00, 5937.72, 4069.58)  # from the SUMO network file

# Create projection objects
proj_geo = Proj(init='epsg:4326')  # WGS84
proj_cartesian = Proj(proj_parameters)

# prune.boundary coordinates to convert (from your polyconvert configuration)
prune_boundary_geo = (13.3015376, 52.5356604, 13.3749244, 52.5644452)

# Convert prune.boundary coordinates to Cartesian coordinates
x_min_prune, y_min_prune = transform(proj_geo, proj_cartesian, prune_boundary_geo[0], prune_boundary_geo[1])
x_max_prune, y_max_prune = transform(proj_geo, proj_cartesian, prune_boundary_geo[2], prune_boundary_geo[3])

# Apply netOffset to Cartesian coordinates
x_min_prune += net_offset[0]
y_min_prune += net_offset[1]
x_max_prune += net_offset[0]
y_max_prune += net_offset[1]

# Print Cartesian coordinates in CSV format
print(f"{x_min_prune},{y_min_prune},{x_max_prune},{y_max_prune}")
