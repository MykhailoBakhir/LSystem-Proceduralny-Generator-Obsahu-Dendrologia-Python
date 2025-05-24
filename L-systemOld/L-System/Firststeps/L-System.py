import trimesh
import numpy as np

def create_frustum(start, direction, length, bottom_radius, top_radius):
    end = start + direction * length

    height = np.linalg.norm(direction) * length
    sections = 16
    angles = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    bottom_circle = np.column_stack([
        bottom_radius * np.cos(angles),
        bottom_radius * np.sin(angles),
        np.zeros_like(angles)
    ])
    top_circle = np.column_stack([
        top_radius * np.cos(angles),
        top_radius * np.sin(angles),
        np.full_like(angles, height)
    ])

    vertices = np.vstack((bottom_circle, top_circle))
    faces = []
    for i in range(sections):
        next_i = (i + 1) % sections
        faces.append([i, next_i, sections + i])
        faces.append([next_i, sections + next_i, sections + i])

    center_bottom = len(vertices)
    center_top = len(vertices) + 1
    vertices = np.vstack((vertices, [[0, 0, 0], [0, 0, height]]))

    for i in range(sections):
        next_i = (i + 1) % sections
        faces.append([center_bottom, next_i, i])
        faces.append([center_top, sections + i, sections + next_i])

    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)


    z_axis = np.array([0, 0, 1])
    direction_norm = direction / np.linalg.norm(direction)
    if not np.allclose(direction_norm, z_axis):
        rotation = trimesh.geometry.align_vectors(z_axis, direction)
        mesh.apply_transform(rotation)

    mesh.apply_translation(start)

    return mesh, end

def interpret_lsystem(lsys_string, start, direction, length, initial_radius, taper):
    meshes = []
    current_pos = np.array(start)
    current_dir = np.array(direction) / np.linalg.norm(direction)
    current_radius = initial_radius

    for symbol in lsys_string:
        if symbol == 'F':
            bottom_radius = current_radius
            top_radius = current_radius * taper
            frustum, new_pos = create_frustum(current_pos, current_dir, length, bottom_radius, top_radius)
            meshes.append(frustum)
            current_pos = new_pos
            current_radius = top_radius  

    return trimesh.util.concatenate(meshes)

lsystem = "FFFFF"
tree = interpret_lsystem(lsystem, start=[0, 0, 0], direction=[0, 0, 1], length=3, initial_radius=4.0, taper=0.8)
tree.export("lsystem_tree.obj")
print("Saved as lsystem_tree.obj")
