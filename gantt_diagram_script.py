import bpy
import sys
import os
import math
import json
import random
from datetime import datetime, timedelta

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
    output_path = os.path.join(os.getcwd(), "generated_gantt_diagram.png")

print(f"Output path: {output_path}")

# Clear existing objects in the Blender scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define an improved color palette - more vibrant and with better contrast
COLOR_PALETTE = [
    (0.3, 0.7, 1.0, 1.0),   # Brighter Blue
    (1.0, 0.3, 0.3, 1.0),   # Bright Red
    (0.4, 1.0, 0.4, 1.0),   # Bright Green
    (1.0, 0.7, 0.2, 1.0),   # Bright Orange
    (0.8, 0.3, 1.0, 1.0),   # Bright Purple
    (0.2, 1.0, 1.0, 1.0),   # Vivid Turquoise
    (1.0, 0.4, 0.8, 1.0),   # Bright Pink
    (0.7, 0.9, 0.2, 1.0),   # Vivid Lime Green
]

# Helper function to create text with better visibility
def create_text(text_content, location, size=0.6, color=(0, 0, 0, 1), align='LEFT', extrude=0.03):
    bpy.ops.object.text_add(location=location)
    text_obj = bpy.context.active_object
    text_obj.data.body = text_content
    text_obj.data.size = size
    text_obj.name = f"{text_content.replace(' ', '_')[:20]}_text"  # Limit name length
    text_obj.data.align_x = align
    
    # Create material for text
    text_mat = bpy.data.materials.new(name=f"text_material_{random.randint(1000,9999)}")
    text_mat.diffuse_color = color
    text_obj.data.materials.append(text_mat)
    
    # Ensure text is oriented properly
    text_obj.rotation_euler = (0, 0, 0)
    
    # Increase extrude for better visibility
    text_obj.data.extrude = extrude
    
    # Add slight bevel for smoother text
    text_obj.data.bevel_depth = 0.01
    text_obj.data.bevel_resolution = 2
    
    return text_obj

# Helper function to create a task bar with progress indicator and better styling
def create_task_bar(task_name, start_day, duration, row, row_height, color, progress=None):
    # Calculate positions
    left_x = start_day
    right_x = start_day + duration
    bottom_y = -row * row_height
    top_y = bottom_y + (row_height * 0.75)  # Make bars taller
    
    # Create vertices for the bar with slight rounding
    verts = [
        (left_x, bottom_y, 0),
        (right_x, bottom_y, 0),
        (right_x, top_y, 0),
        (left_x, top_y, 0)
    ]
    
    # Create faces
    faces = [(0, 1, 2, 3)]
    
    # Create the mesh
    mesh = bpy.data.meshes.new(f"{task_name.replace(' ', '_')[:15]}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    # Create the object
    obj = bpy.data.objects.new(f"{task_name.replace(' ', '_')[:15]}_bar", mesh)
    bpy.context.collection.objects.link(obj)
    
    # Create and assign material with better appearance
    mat = bpy.data.materials.new(name=f"task_material_{random.randint(1000,9999)}")
    mat.diffuse_color = color
    
    # Make material slightly glossy for better appearance
    mat.use_nodes = False
    
    obj.data.materials.append(mat)


# Helper function to create milestones with better visibility
def create_milestone(name, day, row, row_height, color=(0.9, 0.2, 0.2, 1)):
    # Calculate position
    x = day
    y = -row * row_height + (row_height * 0.35)  # Center in row
    
    # Create a diamond shape for the milestone
    size = 0.7  # Larger milestone markers
    verts = [
        (x, y, 0),               # Top
        (x + size/2, y - size/2, 0),  # Right
        (x, y - size, 0),        # Bottom
        (x - size/2, y - size/2, 0)   # Left
    ]
    
    # Create faces
    faces = [(0, 1, 2, 3)]
    
    # Create the mesh
    mesh = bpy.data.meshes.new(f"{name.replace(' ', '_')[:15]}_milestone_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    # Create the object
    obj = bpy.data.objects.new(f"{name.replace(' ', '_')[:15]}_milestone", mesh)
    bpy.context.collection.objects.link(obj)
    
    # Create and assign material with more vibrant appearance
    mat = bpy.data.materials.new(name=f"milestone_material_{random.randint(1000,9999)}")
    
    # Make milestones really stand out with vibrant red
    mat.diffuse_color = (0.95, 0.2, 0.2, 1.0)
    
    # Add glossiness to milestone
# Add glossiness to milestone
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = nodes.get('Principled BSDF')
    if principled:
    # Remove or comment out this line:
    # principled.inputs['Specular'].default_value = 0.5
    # Keep just this line:
        principled.inputs['Roughness'].default_value = 0.5
        
    obj.data.materials.append(mat)
    
    # Add a subtle bevel for better 3D appearance
    bevel_mod = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = 0.05
    bevel_mod.segments = 3
    
    # Add milestone text
    text_obj = create_text(
        name,
        (x, y + 0.8, 0),  # Positioned higher above the diamond
        size=0.5,
        align='CENTER',
        color=(0.95, 0.2, 0.2, 1.0)  # Match diamond color
    )
    
    # Make milestone text bold
    text_obj.data.extrude = 0.04
    
    return obj

# Helper function to create vertical grid lines with better visibility
def create_grid_lines(days, grid_height, header_y, task_label_width):
    for day in range(0, days + 1, 1):  # Create line for each day
        day_x = day + task_label_width  # Offset X by label width
        
        # Create vertices for the vertical grid line
        verts = [
            (day_x, -header_y, -0.05),  # Start just below header
            (day_x, -header_y - grid_height, -0.05)  # End at bottom of grid
        ]
        
        # Create edges
        edges = [(0, 1)]
        
        # Create the mesh
        mesh = bpy.data.meshes.new(f"grid_line_{day}_mesh")
        mesh.from_pydata(verts, edges, [])
        mesh.update()
        
        # Create the object
        obj = bpy.data.objects.new(f"grid_line_{day}", mesh)
        bpy.context.collection.objects.link(obj)
        
        # Create and assign material
        mat = bpy.data.materials.new(name=f"grid_line_{day}_material")
        
        # Make grid lines less obtrusive but still visible
        # Major lines (5-day intervals) are more prominent
        if day % 5 == 0:
            alpha = 0.5
            width = 0.02  # Thicker for major lines
        else:
            alpha = 0.2
            width = 0.01  # Thinner for minor lines
            
        mat.diffuse_color = (0.5, 0.5, 0.5, alpha)
        obj.data.materials.append(mat)
        
        # Make lines thicker based on importance
        if day % 5 == 0:
            # Create a curve for the line for better thickness control
            curve_data = bpy.data.curves.new(f'grid_curve_{day}', type='CURVE')
            curve_data.dimensions = '3D'
            curve_data.resolution_u = 2
            
            # Create a path for the line
            polyline = curve_data.splines.new('POLY')
            polyline.points.add(1)  # Two points for start and end
            
            # Set the points
            polyline.points[0].co = (day_x, -header_y, -0.05, 1)
            polyline.points[1].co = (day_x, -header_y - grid_height, -0.05, 1)
            
            # Create the curve object
            curve_obj = bpy.data.objects.new(f'grid_curve_{day}', curve_data)
            bpy.context.collection.objects.link(curve_obj)
            
            # Add thickness to the curve
            curve_data.bevel_depth = width
            
            # Assign material
            curve_obj.data.materials.append(mat)

# Generate a random Gantt chart with more realistic features
def generate_random_gantt():
    # Define possible project tasks
    possible_tasks = [
        {"name": "Planning", "min_duration": 3, "max_duration": 7},
        {"name": "Analysis", "min_duration": 4, "max_duration": 8},
        {"name": "Design", "min_duration": 5, "max_duration": 10},
        {"name": "Development", "min_duration": 7, "max_duration": 15},
        {"name": "Testing", "min_duration": 4, "max_duration": 8},
        {"name": "Deployment", "min_duration": 2, "max_duration": 5},
        {"name": "Documentation", "min_duration": 3, "max_duration": 6},
        {"name": "Training", "min_duration": 2, "max_duration": 4},
        {"name": "Quality Assurance", "min_duration": 3, "max_duration": 7},
        {"name": "User Acceptance", "min_duration": 2, "max_duration": 5},
        {"name": "Review", "min_duration": 1, "max_duration": 3},
        {"name": "Integration", "min_duration": 4, "max_duration": 8},
        {"name": "Maintenance", "min_duration": 2, "max_duration": 5}
    ]
    
    # Setup random project data
    num_tasks = random.randint(5, 8)
    selected_tasks = random.sample(possible_tasks, num_tasks)
    
    # Add 1-2 milestones
    num_milestones = random.randint(1, 2)
    milestone_positions = []
    
    # Project start date
    start_date = datetime(2023, 1, 1)
    
    # Generate tasks with dependencies
    tasks = []
    current_date = start_date
    
    
    for i, task in enumerate(selected_tasks):
        duration = random.randint(task["min_duration"], task["max_duration"])
        
        # Assign task to a random person/resource
        resources = ["Alex", "Maria", "John", "Sarah", "Dev Team", "QA Team"]
        assigned_to = random.choice(resources)
        
        # Generate random progress percentage
        progress = random.randint(0, 100)
        
        # Randomly determine if this task depends on previous tasks
        depends_on_previous = random.choice([True, False]) if i > 0 else False
        
        # Generate more complex dependencies
        dependencies = []
        if depends_on_previous and i > 0:
            # Can depend on multiple previous tasks
            for j in range(i):
                if random.random() < 0.3:  # 30% chance to depend on any previous task
                    dependencies.append(j)
            
            # Ensure at least one dependency if depends_on_previous is True
            if not dependencies:
                dependencies.append(i-1)
            
            # Find the latest end date of all dependencies
            latest_end = start_date
            for dep_id in dependencies:
                dep_end = tasks[dep_id]["start_date"] + timedelta(days=tasks[dep_id]["duration"])
                if dep_end > latest_end:
                    latest_end = dep_end
            
            # Start after the latest dependency
            start = latest_end
        else:
            # Start with some random offset from current date
            offset = random.randint(0, 3) if i > 0 else 0
            start = current_date + timedelta(days=offset)
            current_date = start + timedelta(days=duration)
        
        # Convert datetime to days from project start
        start_day = (start - start_date).days

        
        # Get color from palette
        color_index = i % len(COLOR_PALETTE)
        color = COLOR_PALETTE[color_index]
        
        tasks.append({
            "id": i + 1,
            "name": task["name"],
            "start_date": start,
            "start_day": start_day,
            "duration": duration,
            "color": color,
            "depends_on": dependencies,
            "assigned_to": assigned_to,
            "progress": progress,
        })
    
    # Generate milestone data
    milestones = []
    project_duration = (max([t["start_date"] + timedelta(days=t["duration"]) for t in tasks]) - start_date).days
    
    for i in range(num_milestones):
        # Place milestone at a strategic point (after key tasks)
        if i == 0:  # First milestone around 1/3 of project
            day = int(project_duration * 0.35)
        else:  # Second milestone around 2/3 of project
            day = int(project_duration * 0.7)
        
        milestone_name = random.choice([
            "Prototype Approval", 
            "Client Review", 
            "Phase Completion", 
            "Stakeholder Meeting",
            "Go/No-Go Decision"
        ])
        
        milestones.append({
            "name": milestone_name,
            "day": day
        })
    
    # Add today marker (current progress point)
    today = random.randint(int(project_duration * 0.3), int(project_duration * 0.7))
    
    return tasks, milestones, today, project_duration + 5  # Project duration plus margin

# Create the Gantt chart visualization
tasks, milestones, today, project_duration = generate_random_gantt()

# Grid settings - CHANGED: Increased row height for better spacing
row_height = 2.2
task_label_width = 9  # Width for the task labels column (increased for better readability)
grid_width = project_duration + task_label_width
grid_height = len(tasks) * row_height + 5  # Extra space for header and milestones

# Create header with better styling
header_y = 3
header_text = create_text(
    "Project Timeline",
    (grid_width / 2, 1.5, 0),
    size=1.3,
    align='CENTER',
    color=(0.1, 0.1, 0.6, 1.0)  # Dark blue for header
)
# Add an underline for the header
header_line_verts = [
    (grid_width / 2 - 6, 1, 0),
    (grid_width / 2 + 6, 1, 0)
]
header_line_edges = [(0, 1)]
header_line_mesh = bpy.data.meshes.new("header_line_mesh")
header_line_mesh.from_pydata(header_line_verts, header_line_edges, [])
header_line_mesh.update()
header_line_obj = bpy.data.objects.new("header_line", header_line_mesh)
bpy.context.collection.objects.link(header_line_obj)
header_line_mat = bpy.data.materials.new(name="header_line_material")
header_line_mat.diffuse_color = (0.2, 0.2, 0.7, 1.0)
header_line_obj.data.materials.append(header_line_mat)

# Create horizontal timeline with better styling
days_label = create_text("Days:", (task_label_width - 2, -header_y, 0), size=0.6, color=(0.2, 0.2, 0.7, 1.0))

for day in range(0, project_duration + 1, 5):  # Mark every 5 days
    day_x = day + task_label_width  # Offset by label width
    # Only add text for multiples of 5
    if day % 5 == 0:
        day_text = create_text(
            str(day),
            (day_x, -header_y, 0),
            size=0.8,
            align='CENTER',
            color=(0.2, 0.2, 0.5, 1.0)  # Dark blue for better visibility
        )

# Create day markers with better styling
for day in range(0, project_duration + 1):
    day_x = day + task_label_width  # Offset by label width
    
    # Only create visible markers for every 5 days
    if day % 5 == 0:
        height = 0.4  # Taller for better visibility
        width = 0.08  # Thicker lines
        
        # Create a cylinder for day marker instead of a line
        bpy.ops.mesh.primitive_cylinder_add(
            radius=width/2,
            depth=height,
            location=(day_x, -header_y - height/2, 0)
        )
        
        marker = bpy.context.active_object
        marker.name = f"day_{day}_marker"
        
        # Create and assign material
        marker_mat = bpy.data.materials.new(name=f"day_{day}_marker_material")
        marker_mat.diffuse_color = (0.2, 0.2, 0.7, 1.0)  # Dark blue for markers
        marker.data.materials.append(marker_mat)

# Create vertical grid lines with improved visibility
create_grid_lines(project_duration, grid_height, header_y, task_label_width)

# Create today marker (vertical line showing current progress) with better visibility
today_x = today + task_label_width  # Offset by label width

# Create a more visible today marker using a cylinder
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.08,  # Thicker for visibility
    depth=grid_height,
    location=(today_x, -header_y - grid_height/2, 0.05)
)

today_obj = bpy.context.active_object
today_obj.name = "today_marker"

# Create and assign material with more vibrant color
today_mat = bpy.data.materials.new(name="today_marker_material")
today_mat.diffuse_color = (1.0, 0.3, 0.3, 1.0)  # Brighter red for today line

# Make today marker slightly translucent
today_mat.use_nodes = True
nodes = today_mat.node_tree.nodes
principled = nodes.get('Principled BSDF')
if principled:
    principled.inputs['Base Color'].default_value = (1.0, 0.3, 0.3, 1.0)
    principled.inputs['Alpha'].default_value = 0.8

today_obj.data.materials.append(today_mat)

# Create "Today" label with better styling
today_text = create_text(
    "TODAY",
    (today_x, -header_y + 0.7, 0.1),
    size=0.6,
    color=(1.0, 0.3, 0.3, 1.0),  # Match the today line color
    align='CENTER'
)
# Make today text bold
today_text.data.extrude = 0.05

# Create background for task labels column
label_bg_verts = [
    (0, -header_y, -0.08),
    (task_label_width, -header_y, -0.08),
    (task_label_width, -header_y - grid_height, -0.08),
    (0, -header_y - grid_height, -0.08)
]
label_bg_faces = [(0, 1, 2, 3)]
label_bg_mesh = bpy.data.meshes.new("label_bg_mesh")
label_bg_mesh.from_pydata(label_bg_verts, [], label_bg_faces)
label_bg_mesh.update()
label_bg_obj = bpy.data.objects.new("label_background", label_bg_mesh)
bpy.context.collection.objects.link(label_bg_obj)
label_bg_mat = bpy.data.materials.new(name="label_bg_material")
label_bg_mat.diffuse_color = (0.95, 0.95, 1.0, 1.0)  # Very light blue tint
label_bg_obj.data.materials.append(label_bg_mat)

# Create "Today" label
create_text(
    "Tasks",
    (task_label_width / 2, -header_y, 0),
    size=0.6,
    color=(0.2, 0.2, 0.7, 1.0),
    align='CENTER'
)

# Create task bars and labels
for i, task in enumerate(tasks):
    row = i + 2  # Start after header rows
    
    # Create task label - CHANGED: Positioned at fixed left position
    label_x = 1  # Fixed position for all labels
    create_text(f"{task['id']}. {task['name']}", (label_x, -row * row_height + 0.5, 0), size=0.8)
    
    # Create assigned resource label (small text under task name)
    create_text(
        f"Assigned to: {task['assigned_to']}",
        (label_x, -row * row_height, 0),
        size=0.4,
        color=(0.3, 0.3, 0.7, 1.0)
    )
    
    # Create task bar with progress indicator - CHANGED: Offset X position by label width
    bar = create_task_bar(
        task["name"],
        task["start_day"] + task_label_width,  # Offset X by label width
        task["duration"],
        row,
        row_height,
        task["color"],
        progress=task["progress"]
    )
    
    
    # Create duration label - CHANGED: Offset X position
    create_text(
        f"{task['duration']} days",
        (task["start_day"] + task_label_width + task["duration"] / 2, -row * row_height + 0.5, 0.1),
        size=0.8,
        align='CENTER'
    )

    
    # Draw dependencies - CHANGED: Offset X positions
    for dep_id in task["depends_on"]:
        # Find the dependent task (adjusting for 0-based indexing)
        dep_task = tasks[dep_id]
        
        # Draw an arrow from dependent task end to this task start
        start_x = dep_task["start_day"] + task_label_width + dep_task["duration"]
        start_y = -(dep_id + 2) * row_height + (row_height * 0.35)  # +2 for header offset
        end_x = task["start_day"] + task_label_width
        end_y = -row * row_height + (row_height * 0.35)
        
        # Create curve for the dependency arrow
        curve_data = bpy.data.curves.new(f'dep_{dep_task["id"]}_{task["id"]}_curve', type='CURVE')
        curve_data.dimensions = '3D'
        
        # Create a Bezier curve for smoother arrows
        polyline = curve_data.splines.new('BEZIER')
        polyline.bezier_points.add(1)  # Two points for start and end
        
        # Set the points
        polyline.bezier_points[0].co = (start_x, start_y, 0.1)
        polyline.bezier_points[1].co = (end_x, end_y, 0.1)
        
        # Make it a straight line with slight curve
        handle_offset = min(2.0, abs(end_x - start_x) / 2)
        
        polyline.bezier_points[0].handle_right = (start_x + handle_offset, start_y, 0.1)
        polyline.bezier_points[0].handle_left = (start_x - 0.5, start_y, 0.1)
        
        polyline.bezier_points[1].handle_left = (end_x - handle_offset, end_y, 0.1)
        polyline.bezier_points[1].handle_right = (end_x + 0.5, end_y, 0.1)
        
        # Create the curve object
        curve_obj = bpy.data.objects.new(f'dep_{dep_task["id"]}_{task["id"]}_line', curve_data)
        bpy.context.collection.objects.link(curve_obj)
        
        # Add material and color to the line
        mat = bpy.data.materials.new(name=f"dep_{dep_task['id']}_{task['id']}_line_material")
        mat.diffuse_color = (0.1, 0.1, 0.1, 0.8)
        curve_obj.data.materials.append(mat)
        
        # Add thickness to the curve
        curve_data.bevel_depth = 0.05  # CHANGED: Thicker dependency lines
        
        # Add an arrow at the end
        arrow_size = 0.2  # CHANGED: Larger arrow
        arrow_verts = [
            (end_x, end_y, 0.1),  # Tip
            (end_x - arrow_size, end_y + arrow_size/2, 0.1),  # Bottom left
            (end_x - arrow_size, end_y - arrow_size/2, 0.1)   # Bottom right
        ]
        
        # Create faces
        arrow_faces = [(0, 1, 2)]
        
        # Create the mesh
        arrow_mesh = bpy.data.meshes.new(f"arrow_{dep_task['id']}_{task['id']}_mesh")
        arrow_mesh.from_pydata(arrow_verts, [], arrow_faces)
        arrow_mesh.update()
        
        # Create the object
        arrow_obj = bpy.data.objects.new(f"arrow_{dep_task['id']}_{task['id']}", arrow_mesh)
        bpy.context.collection.objects.link(arrow_obj)
        
        # Create and assign material
        arrow_mat = bpy.data.materials.new(name=f"arrow_{dep_task['id']}_{task['id']}_material")
        arrow_mat.diffuse_color = (0.1, 0.1, 0.1, 1.0)
        arrow_obj.data.materials.append(arrow_mat)

# Create milestones - CHANGED: Offset X position
for milestone in milestones:
    milestone_x = milestone["day"] + task_label_width  # Offset X by label width
    create_milestone(milestone["name"], milestone_x, len(tasks) + 2, row_height)

# Draw grid background - CHANGED: Adjust positions with label width
grid_x = 0
grid_y = -header_y
grid_width = project_duration + task_label_width + 5  # Add label width
grid_height = len(tasks) * row_height + 5  # Extra height for milestones

# Create vertical divider between labels and chart
divider_verts = [
    (task_label_width, grid_y, 0),
    (task_label_width, grid_y - grid_height, 0)
]
divider_edges = [(0, 1)]
divider_mesh = bpy.data.meshes.new("divider_mesh")
divider_mesh.from_pydata(divider_verts, divider_edges, [])
divider_mesh.update()
divider_obj = bpy.data.objects.new("divider", divider_mesh)
bpy.context.collection.objects.link(divider_obj)
divider_mat = bpy.data.materials.new(name="divider_material")
divider_mat.diffuse_color = (0.3, 0.3, 0.3, 1.0)
divider_obj.data.materials.append(divider_mat)

# Create vertices for the grid
verts = [
    (grid_x, grid_y, -0.1),
    (grid_x + grid_width, grid_y, -0.1),
    (grid_x + grid_width, grid_y - grid_height, -0.1),
    (grid_x, grid_y - grid_height, -0.1)
]

# Create faces
faces = [(0, 1, 2, 3)]

# Create the mesh
mesh = bpy.data.meshes.new("grid_mesh")
mesh.from_pydata(verts, [], faces)
mesh.update()

# Create the object
obj = bpy.data.objects.new("grid", mesh)
bpy.context.collection.objects.link(obj)

# Create and assign material
mat = bpy.data.materials.new(name="grid_material")
mat.diffuse_color = (0.97, 0.97, 0.97, 1.0)  # Light gray background
obj.data.materials.append(mat)

# Add lighting
bpy.ops.object.light_add(type='SUN', location=(0, 0, 15))
light = bpy.context.active_object
light.data.energy = 7

# Setup camera
bpy.ops.object.camera_add(location=(grid_width/2 - 5, -grid_height/2 - 15, 30), rotation=(0, 0, 0))
camera = bpy.context.active_object
bpy.context.scene.camera = camera

# Function to adjust the view to make sure all objects are in frame
def setup_camera_view():
    # Create a group of all diagram objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if obj.type != 'CAMERA' and obj.type != 'LIGHT':
            obj.select_set(True)
    
    # Focus the view on all diagram objects
    if bpy.context.selected_objects:
        bpy.ops.view3d.camera_to_view_selected()

setup_camera_view()

# Set render background
bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1)  # Light white-gray background

# Render settings
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.filepath = output_path
bpy.context.scene.render.resolution_x = 1920  # Higher resolution
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.film_transparent = True  # Solid background

# Render and save the diagram
bpy.ops.render.render(write_still=True)
print(f"Gantt diagram saved to: {output_path}")

# Save the Gantt chart information as JSON for easier question generation
gantt_data = {
    "tasks": [
        {
            "id": task["id"],
            "name": task["name"],
            "start_day": task["start_day"],
            "duration": task["duration"],
            "depends_on": task["depends_on"],
            "assigned_to": task["assigned_to"],
            "progress": task["progress"],
        }
        for task in tasks
    ],
    "milestones": [
        {
            "name": milestone["name"],
            "day": milestone["day"]
        }
        for milestone in milestones
    ],
    "project_duration": project_duration,
    "today": today
}

# Save the JSON data alongside the image
json_path = os.path.splitext(output_path)[0] + ".json"
with open(json_path, 'w') as f:
    json.dump(gantt_data, f, indent=2)

print(f"Gantt data saved to: {json_path}")