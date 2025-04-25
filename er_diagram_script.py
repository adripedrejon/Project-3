import bpy
import sys
import os
import math
import io

# Get the output image path from command-line arguments
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

# Parse the output path from arguments
output_path = None
for i in range(len(argv) - 1):
    if argv[i] == "--output" and i + 1 < len(argv):
        output_path = argv[i + 1]
        break

# Use default path if not provided
if not output_path:
    output_path = os.path.join(os.getcwd(), "generated_er_diagram.png")

print(f"Output path: {output_path}")

# Clear existing objects in the Blender scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helper: Create an entity box with a properly positioned label
def create_entity(name, location, color):
    # Create cube as entity box
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    cube = bpy.context.active_object
    cube.name = f"{name}_box"
    cube.scale = (3, 1.5, 0.3)  # Adjust proportions
    
    # Apply material and color to the entity box
    mat = bpy.data.materials.new(name=f"{name}_Material")
    mat.diffuse_color = (*color, 1.0)  # RGBA
    cube.data.materials.append(mat)

    # Add text label positioned above the box
    text_location = (location[0], location[1], location[2] + 0.6)
    bpy.ops.object.text_add(location=text_location)
    text = bpy.context.active_object
    text.data.body = name  # Set the label text
    text.data.size = 0.5   # Smaller text size to avoid oversized text
    text.name = f"{name}_label"
    
    # Create black material for text
    text_mat = bpy.data.materials.new(name=f"{name}_text_material")
    text_mat.diffuse_color = (0, 0, 0, 1)  # Black color (RGBA)
    text.data.materials.append(text_mat)
    
    # Center text horizontally
    text.data.align_x = 'CENTER'
    
    # Ensure text is oriented towards the camera
    text.rotation_euler = (1.5708, 0, 0)  # 90 degrees in X (facing up)
    
    # Set extrude for better visibility
    text.data.extrude = 0.02
    
    return cube

# Helper: Create a relationship line with a label
def create_line(start_entity, end_entity, label, color, thickness=0.05):
    start = start_entity.location
    end = end_entity.location
    
    # Create curve for the relationship line
    curve_data = bpy.data.curves.new(f'{label}_curve', type='CURVE')
    curve_data.dimensions = '3D'

    # Add points to the curve
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(1)
    polyline.points[0].co = (start[0], start[1], start[2], 1.0)  # Using 4D coordinates
    polyline.points[1].co = (end[0], end[1], end[2], 1.0)
    
    # Create the line object
    curve_obj = bpy.data.objects.new(f'{label}_line', curve_data)
    bpy.context.collection.objects.link(curve_obj)

    # Add material and color to the line
    mat = bpy.data.materials.new(name=f"{label}_line_material")
    mat.diffuse_color = (*color, 1.0)  # RGBA
    curve_obj.data.materials.append(mat)

    # Add thickness to the curve
    curve_data.bevel_depth = thickness

    # Calculate midpoint for the relationship label
    mid_point = (
        (start[0] + end[0]) / 2,
        (start[1] + end[1]) / 2,
        (start[2] + end[2]) / 2 + 0.4  # Slightly above the line
    )
    
    # Add label for the relationship
    bpy.ops.object.text_add(location=mid_point)
    rel_label = bpy.context.active_object
    rel_label.data.body = label
    rel_label.data.size = 0.4  # Smaller text size for relationships
    rel_label.name = f"{label}_rel_label"
    rel_label.data.align_x = 'CENTER'
    
    # Create black material for relationship text
    rel_text_mat = bpy.data.materials.new(name=f"{label}_rel_text_material")
    rel_text_mat.diffuse_color = (0, 0, 0, 1)  # Black color (RGBA)
    rel_label.data.materials.append(rel_text_mat)
    
    # Ensure relationship text is oriented towards the camera
    rel_label.rotation_euler = (1.5708, 0, 0)  # 90 degrees in X (facing up)
    
    # Set extrude for better visibility
    rel_label.data.extrude = 0.02
    
    return curve_obj

# Generate a random ER diagram
import random

# Define possible entities and their attributes
possible_entities = [
    {"name": "User", "color": (0.8, 0.2, 0.2)},  # Red
    {"name": "Order", "color": (0.2, 0.8, 0.2)},  # Green
    {"name": "Product", "color": (0.2, 0.2, 0.8)},  # Blue
    {"name": "Customer", "color": (0.8, 0.6, 0.2)},  # Orange
    {"name": "Employee", "color": (0.5, 0.2, 0.8)},  # Purple
    {"name": "Department", "color": (0.2, 0.6, 0.6)},  # Teal
    {"name": "Invoice", "color": (0.8, 0.2, 0.6)},  # Pink
    {"name": "Payment", "color": (0.4, 0.4, 0.8)},  # Light Blue
    {"name": "Category", "color": (0.6, 0.8, 0.2)}   # Light Green
]

# Define possible relationships
possible_relationships = [
    "places", "contains", "manages", "works_in", "pays", "belongs_to", 
    "processes", "employs", "orders", "delivers", "owns", "creates"
]

# Randomly select 3-5 entities
num_entities = random.randint(3, 5)
selected_entities = random.sample(possible_entities, num_entities)

# Assign positions in a circle layout
radius = 5
entities = {}
angle_step = 2 * 3.14159 / num_entities

for i, entity in enumerate(selected_entities):
    angle = i * angle_step
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    entities[entity["name"]] = {"location": (x, y, 0), "color": entity["color"]}

# Randomly create relationships between entities
relationships = []
entity_names = list(entities.keys())

# Ensure each entity has at least one relationship
for i in range(len(entity_names)):
    start = entity_names[i]
    # Connect to the next entity in the list (circular)
    end = entity_names[(i + 1) % len(entity_names)]
    rel = random.choice(possible_relationships)
    relationships.append({
        "start": start,
        "end": end,
        "label": rel,
        "color": (0.9, 0.9, 0.0)  # Yellow
    })

# Add a few more random relationships
num_extra_rels = random.randint(0, 2)
for _ in range(num_extra_rels):
    # Choose two random different entities
    start, end = random.sample(entity_names, 2)
    rel = random.choice(possible_relationships)
    relationships.append({
        "start": start,
        "end": end,
        "label": rel,
        "color": (0.9, 0.5, 0.0)  # Orange
    })

# Create entity objects and store references
entity_objects = {}
for name, data in entities.items():
    entity_objects[name] = create_entity(name, data["location"], data["color"])

# Create relationships
for rel in relationships:
    create_line(
        entity_objects[rel["start"]],
        entity_objects[rel["end"]],
        rel["label"],
        rel["color"]
    )

# Add lighting
bpy.ops.object.light_add(type='SUN', location=(0, 0, 15))
light = bpy.context.active_object
light.data.energy = 5  # More moderate lighting energy

# Setup camera with correct orientation for viewing the diagram
bpy.ops.object.camera_add(location=(0, -10, 15), rotation=(0.5, 0, 0))
camera = bpy.context.active_object
bpy.context.scene.camera = camera

# Set render background
bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.95, 0.95, 0.95, 1)  # Light gray background

# Adjust the view to make sure all entities are in frame
def setup_camera_view():
    # Create a group of all diagram objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if 'box' in obj.name or 'label' in obj.name or 'line' in obj.name:
            obj.select_set(True)
    
    # Focus the view on all diagram objects
    if bpy.context.selected_objects:
        bpy.ops.view3d.camera_to_view_selected()

setup_camera_view()

# Render settings
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.filepath = output_path
bpy.context.scene.render.resolution_x = 1280  # High resolution for clarity
bpy.context.scene.render.resolution_y = 720

# Render and save the diagram
bpy.ops.render.render(write_still=True)
print(f"ER diagram saved to: {output_path}")

# Save the diagram information as JSON for easier question generation
import json
import math  # For circular layout

# Create a structured representation of the diagram
diagram_data = {
    "entities": [{"name": name} for name in entities.keys()],
    "relationships": [
        {
            "from": rel["start"],
            "to": rel["end"],
            "type": rel["label"]
        }
        for rel in relationships
    ]
}

# Save the JSON data alongside the image
json_path = os.path.splitext(output_path)[0] + ".json"
with open(json_path, 'w') as f:
    json.dump(diagram_data, f, indent=2)

print(f"Diagram data saved to: {json_path}")