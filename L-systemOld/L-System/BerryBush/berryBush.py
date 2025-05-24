import trimesh
import numpy as np
from mpmath import mp

import leafForBush

PI_PRECISION = 100000
mp.dps = PI_PRECISION + 5  

PI_DIGITS = str(mp.pi)[2:2 + PI_PRECISION]
pi_index = 0  

def get_pi_digit(index):
    index = index % PI_PRECISION  
    global pi_index
    pi_index = index
    return int(PI_DIGITS[index])

def expand_lsystem(axiom, rules, iterations, seed=893):
    global pi_index
    result = axiom
    pi_index = seed  
    for _ in range(iterations):
        next_result = []
        for symbol in result:
            if symbol in {'B', 'A'}:
                digit = get_pi_digit(pi_index)
                pi_index += 1
                if digit >= 0:
                    next_result.append(rules[symbol])
                else:
                    next_result.append('')
            else:
                next_result.append(rules.get(symbol, symbol))
        result = ''.join(next_result)
    return result

def create_frustum(start, direction, length, bottom_radius, top_radius):
    start = np.array(start)  
    direction = np.array(direction)

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
    uvs = []

    for i in range(sections):
        next_i = (i + 1) % sections
        faces.append([i, next_i, sections + i])
        faces.append([next_i, sections + next_i, sections + i])

        u = i / sections
        u_next = (i + 1) / sections
        uvs.append([u, 0])
        uvs.append([u_next, 0])
        uvs.append([u, 1])
        uvs.append([u_next, 1])

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

    visual = trimesh.visual.TextureVisuals(uv=np.array(uvs)[:len(mesh.vertices)])
    mesh.visual = visual

    return mesh, end

def rotate_direction_set(forward, up, right, angle_deg, axis):
    rotation = trimesh.transformations.rotation_matrix(
        np.radians(angle_deg),
        axis
    )
    forward = trimesh.transformations.transform_points([forward], rotation)[0]
    up = trimesh.transformations.transform_points([up], rotation)[0]
    right = trimesh.transformations.transform_points([right], rotation)[0]
    return forward / np.linalg.norm(forward), up / np.linalg.norm(up), right / np.linalg.norm(right)

def interpret_lsystem(lsys_string, start, direction, length, initial_radius, taper, angle_deg=28):
    meshes = []
    current_pos = np.array(start)
    current_forward = np.array(direction) / np.linalg.norm(direction)
    current_up = np.array([0, 1, 0])
    current_right = np.cross(current_forward, current_up)
    current_radius = initial_radius
    stack = []
    leaves = []

    global pi_index
    for symbol in lsys_string:
        if symbol == 'F':
            bottom_radius = current_radius
            top_radius = current_radius * taper
            frustum, new_pos = create_frustum(current_pos, current_forward, length, bottom_radius, top_radius)
            meshes.append(frustum)
            current_pos = new_pos
            current_radius = top_radius

        elif symbol == 'J':
            leaf_axiom = '[A][B]'
            leaf_rules = {
                'A': '[+A]C',
                'B': '[-B]C',
                'C': 'FFFC'
            }
            leaf_lsystem = leafForBush.expand_lsystem(leaf_axiom, leaf_rules, iterations=4)
            leaf_mesh = leafForBush.create_leaf_geometry(leaf_lsystem, angle_deg=16, step_length=length/8)
        
            if leaf_mesh:
                source_direction = np.array([0, 1, 0])
                target_direction = current_forward / np.linalg.norm(current_forward)
                if not np.allclose(source_direction, target_direction):
                    rotation = trimesh.geometry.align_vectors(source_direction, target_direction)
                    leaf_mesh.apply_transform(rotation)
        
                translation = trimesh.transformations.translation_matrix(current_pos)
                leaf_mesh.apply_transform(translation)
        
                green_color = np.array([[34, 139, 34, 255]], dtype=np.uint8)
                leaf_mesh.visual = trimesh.visual.ColorVisuals(leaf_mesh, vertex_colors=np.repeat(green_color, len(leaf_mesh.vertices), axis=0))

        
                leaves.append(leaf_mesh)


        elif symbol == 'K':
            berry_radius = 0.5  
            berry_mesh = create_berry(current_pos, berry_radius)
            red_color = np.array([255, 0, 0, 255], dtype=np.uint8)
            berry_mesh.visual.vertex_colors = np.tile(red_color, (len(berry_mesh.vertices), 1))
            leaf_mesh.visual = trimesh.visual.ColorVisuals(leaf_mesh, vertex_colors=np.repeat(green_color, len(leaf_mesh.vertices), axis=0))
            leaves.append(berry_mesh)


        elif symbol == '+':
            current_forward, current_up, current_right = rotate_direction_set(current_forward, current_up, current_right, +angle_deg, current_right)
        elif symbol == '-':
            current_forward, current_up, current_right = rotate_direction_set(current_forward, current_up, current_right, -angle_deg, current_right)
        elif symbol == '&':
            current_forward, current_up, current_right = rotate_direction_set(current_forward, current_up, current_right, +angle_deg, current_up)
        elif symbol == '^':
            current_forward, current_up, current_right = rotate_direction_set(current_forward, current_up, current_right, -angle_deg, current_up)
        elif symbol == '\\':
            current_forward, current_up, current_right = rotate_direction_set(current_forward, current_up, current_right, +angle_deg, current_forward)
        elif symbol == '/':
            current_forward, current_up, current_right = rotate_direction_set(current_forward, current_up, current_right, -angle_deg, current_forward)
        elif symbol == '|':
            current_forward, current_up, current_right = rotate_direction_set(current_forward, current_up, current_right, 180, current_up)
        elif symbol == '[':
            stack.append((current_pos.copy(), current_forward.copy(), current_up.copy(), current_right.copy(), current_radius))
        elif symbol == ']':
            if stack:
                current_pos, current_forward, current_up, current_right, current_radius = stack.pop()

    all_parts = meshes + leaves
    if all_parts:
        return trimesh.util.concatenate(all_parts)
    else:
        return None

def create_berry(position, radius):
    sphere = trimesh.creation.icosphere(radius=radius, subdivisions=3)
    sphere.apply_translation(np.array(position))
    return sphere


rules = {
    'S': 'FFFA', 
    'A': '[&&J][B]////[&&J][B]////[&&J]B',
    'B': '&FFFAK'
}

axiom = 'S'
lsystem = expand_lsystem(axiom, rules, iterations=10)

print("L-система for Berry bush:")
print(lsystem)
mesh = interpret_lsystem(
    lsystem,
    start=[0, 0, 0],
    direction=[0, 0, 1],
    length=3,
    initial_radius=.2,
    taper=1
)

mesh.export("generated_lsystem.obj")
print("L-System tree was generated in file generated_lsystem.obj")
