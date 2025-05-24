import bpy
import sys
import os


module_dir = "C:/Users/mykha/Desktop/BP/Python/simpleObject/L-System/ObliqueTruncatedCone"
module_name = "TreeWithObliqueTruncatedCone"

if module_dir not in sys.path:
    sys.path.append(module_dir)

import importlib
TreeWithObliqueTruncatedCone = importlib.import_module(module_name)


tree_mesh = TreeWithObliqueTruncatedCone.generate_tree(
    iterations=5,
    length=10,
    radius=20.0,
    taper=0.9,
    angle_deg=15
)


temp_obj_path = os.path.join(module_dir, "generated_lsystem.obj")
tree_mesh.export(temp_obj_path)


bpy.ops.import_scene.obj(filepath=temp_obj_path)


for obj in bpy.context.selected_objects:
    obj.location = (0, 0, 0)

print("Tree imported successfully into Blender.")
