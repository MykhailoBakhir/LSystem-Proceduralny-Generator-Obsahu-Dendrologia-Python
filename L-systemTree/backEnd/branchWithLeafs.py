import trimesh
import numpy as np

import test_leaf

def create_frustum_branch(start, direction, length, bottom_radius, top_radius):
    # start = start -  direction;
    end = start + direction * length
    height = np.linalg.norm(direction) * length
    sections = 128
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

def rotate_direction_branch(direction, angle_deg, axis):
    rotation = trimesh.transformations.rotation_matrix(
        np.radians(angle_deg),
        axis,
        point=[0, 0, 0]
    )
    new_dir = trimesh.transformations.transform_points([direction], rotation)[0]
    return new_dir / np.linalg.norm(new_dir)

def expand_lsystem_branch(axiom, rules, iterations):
    result = axiom
    for iteration in range(1, iterations + 1):
        next_result = []
        for symbol in result:
            if symbol == 'A':
                if iteration == 1:
                    next_result.append(rules['t==1'])
                else:
                    next_result.append(rules['t>1'])
            else:
                next_result.append(symbol)
        result = ''.join(next_result)
    return result

def interpret_lsystem_Branch(lsys_string, start, direction, length, initial_radius, taper, random_pi, angle_deg=60, ):
    stack = []
    segments = []
    leaves = []

    current_pos = np.array(start, dtype=float)
    current_dir = np.array(direction, dtype=float) / np.linalg.norm(direction)
    current_radius = initial_radius
    pi_index = 0
    for symbol in lsys_string:
        if symbol == 'F':

            bottom_radius = current_radius * 1.0
            top_radius = current_radius * taper
            frustum, new_pos = create_frustum_branch(current_pos, current_dir, length, bottom_radius, top_radius)
            segments.append(frustum)
            current_pos = new_pos
            current_radius = top_radius
            
            angle_digit = int(random_pi[pi_index])
            axis_digit = int(random_pi[pi_index + 1])
            pi_index += 2  

            random_angle = (angle_digit / 9.0) * 30  - 15
        
            if axis_digit < 3:
                random_axis = [1, 0, 0]
            elif axis_digit < 6:
                random_axis = [0, 1, 0]
            else:
                random_axis = [0, 0, 1]
        
            current_dir = rotate_direction_branch(current_dir, random_angle, random_axis)

        elif symbol == 'J':
            if (int)(random_pi[pi_index]) > 4:
                leaf_axiom = '[A][B]'
                leaf_rules = {
                    'A': '[+A]C',
                    'B': '[-B]C',
                    'C': 'FFFC'
                }
                if current_radius < 1:
                    leaf_lsystem = test_leaf.expand_lsystem(leaf_axiom, leaf_rules, iterations=6)
                    leaf_mesh = test_leaf.create_leaf_geometry(leaf_lsystem, angle_deg=16, step_length=length/8)
            
                    if leaf_mesh:
                        leaf_pos = current_pos
                    
                        source_direction = np.array([0, 1, 0]) 
                        target_direction = current_dir / np.linalg.norm(current_dir)
                    
                        if not np.allclose(source_direction, target_direction):
                            rotation = trimesh.geometry.align_vectors(source_direction, target_direction)
                            leaf_mesh.apply_transform(rotation)
                    
                        translation = trimesh.transformations.translation_matrix(leaf_pos)
                        leaf_mesh.apply_transform(translation)
                    
                        leaves.append(leaf_mesh)
            pi_index += 1

        elif symbol == '+':
            current_dir = rotate_direction_branch(current_dir, +60, axis=[1, 0, 0])

        elif symbol == '-':
            current_dir = rotate_direction_branch(current_dir, -60, axis=[1, 0, 0])
            
        elif symbol == '&':
            current_dir = rotate_direction_branch(current_dir, +angle_deg, axis=[0, 1, 0])
        elif symbol == '^':
            current_dir = rotate_direction_branch(current_dir, -angle_deg, axis=[0, 1, 0])
        elif symbol == '[':
            stack.append((current_pos.copy(), current_dir.copy(), current_radius))
        elif symbol == ']':
            if stack:
                current_pos, current_dir, current_radius = stack.pop()

    all_parts = segments + leaves
    if all_parts:
        return trimesh.util.concatenate(all_parts)
    else:
        return None

    

# axiom = 'A'
# rules = {
#     't>1': 'AFF[+J][-J][^J][&J]',
#     't==1': 'AF[J]'
# }

# lsystem_result = expand_lsystem_branch(axiom, rules, iterations=7)
# print(lsystem_result)

# from mpmath import mp

# mp.dps = 100

# pi_digits_str = str(mp.pi).replace('.', '')  

# pi_digits_96 = pi_digits_str[1:1+96]

# pi_numbers = [int(digit) for digit in pi_digits_96]

# print(pi_numbers)

# branch_mesh = interpret_lsystem_Branch(
#     lsystem_result,
#     start=[0, 0, 0],
#     direction=[0, 0, 1],
#     length=1.5,
#     initial_radius=0.05,
#     taper=0.8,
#     random_pi = pi_numbers
# )



# if branch_mesh:
#     branch_mesh.export('Branch.obj')
