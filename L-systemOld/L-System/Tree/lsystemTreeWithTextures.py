import trimesh
import numpy as np
from mpmath import mp

import branchWithLeafs

PI_PRECISION = 100000
mp.dps = PI_PRECISION + 5  


PI_DIGITS = str(mp.pi)[2:2 + PI_PRECISION]
pi_index = 0  


def get_pi_digit(index):
    index = index % PI_PRECISION  
    global pi_index
    pi_index= index
    return int(PI_DIGITS[index])

def expand_lsystem(axiom, rules, iterations, seed=893):
    global pi_index
    result = axiom
    pi_index = seed  
    for _ in range(iterations):
        next_result = []
        for symbol in result:
            if symbol in {'B', 'C', 'D', 'E'}:
                digit = get_pi_digit(pi_index)
                pi_index += 1
                if digit >= 4:
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

def rotate_direction(direction, angle_deg, axis):
    rotation = trimesh.transformations.rotation_matrix(
        np.radians(angle_deg),
        axis,
        point=[0, 0, 0]
    )
    new_dir = trimesh.transformations.transform_points([direction], rotation)[0]
    return new_dir / np.linalg.norm(new_dir)

def interpret_lsystem(lsys_string, start, direction, length, initial_radius, taper, angle_deg=15):
    meshes = []
    current_pos = np.array(start)
    current_dir = np.array(direction) / np.linalg.norm(direction)
    current_radius = initial_radius
    stack = []

    global pi_index
    for symbol in lsys_string:
        if symbol == 'F':
            bottom_radius = current_radius * 1.05
            top_radius = current_radius * taper
            frustum, new_pos = create_frustum(current_pos - current_dir*2, current_dir, length, bottom_radius, top_radius)
            meshes.append(frustum)
            current_pos = new_pos
            current_radius = top_radius
            
            

            angle_digit = get_pi_digit(pi_index)
            axis_digit = get_pi_digit(pi_index + 1)
            pi_index += 2
            

            random_angle = (angle_digit / 9.0) * 20 - 10

            if axis_digit < 3:
                random_axis = [1, 0, 0]
            elif axis_digit < 6:
                random_axis = [0, 1, 0]
            else:
                random_axis = [0, 0, 1]

            current_dir = rotate_direction(current_dir, random_angle, random_axis)

        elif symbol == 'f':
            iteration = 12
            branch_axiom = 'A'
            branch_rules = {
                't>1': 'AFF[+J][-J][^J][&J]',
                't==1': 'AF[J]'
            }
            branchLSystem = branchWithLeafs.expand_lsystem_branch(
                branch_axiom,
                branch_rules,
                iteration
            )
            get_pi_digit(pi_index + 200)
            branch_mesh = branchWithLeafs.interpret_lsystem_Branch(
                branchLSystem,
                start=current_pos,
                direction=current_dir ,
                length=length * 0.5,
                initial_radius=current_radius * 1,
                taper= 0.9,
                random_pi=PI_DIGITS[pi_index: pi_index + iteration * 10]
            )
            pi_index += iteration * 10

            if branch_mesh:
                meshes.append(branch_mesh)

        elif symbol == '+':
            current_dir = rotate_direction(current_dir, +angle_deg, axis=[1, 0, 0])
        elif symbol == '-':
            current_dir = rotate_direction(current_dir, -angle_deg, axis=[1, 0, 0])
        elif symbol == '&':
            current_dir = rotate_direction(current_dir, +angle_deg, axis=[0, 1, 0])
        elif symbol == '^':
            current_dir = rotate_direction(current_dir, -angle_deg, axis=[0, 1, 0])
        elif symbol == '\\':
            current_dir = rotate_direction(current_dir, +angle_deg, axis=[0, 0, 1])
        elif symbol == '/':
            current_dir = rotate_direction(current_dir, - angle_deg, axis=[0, 0, 1])
        elif symbol == '|':
            current_dir = rotate_direction(current_dir, 180, axis=[1, 0, 0])
        elif symbol == '[':
            stack.append((current_pos.copy(), current_dir.copy(), current_radius))
        elif symbol == ']':
            if stack:
                current_pos, current_dir, current_radius = stack.pop()

    return trimesh.util.concatenate(meshes)

rules = {
    'S': 'FFFL', 
    'L': 'FFFFFF[BBCCDDEEL]',
    'B': '[++FFFFFFFFFFFFf[&&&&&FFFFFFFFFf]FFFFFFFFFFf]',
    'C': '[--FFFFFFFFFFFf[&&&&&FFFFFFFFFFf]FFFFFFFFFFf]',
    'D': '[&&&&&FFFFFFFf[++FFFFFFFf]FFFFFFFFf]',
    'E': '[^^FFFFFFFFf[--FFFFFFFFf]FFFFFFFFf]'
}





axiom = 'S'
# axiom = 'FFFL'

lsystem = expand_lsystem(axiom, rules, iterations=8)
print(lsystem)

mesh = interpret_lsystem(
    lsystem,
    start=[0, 0, 0],
    direction=[0, 0, 1],
    length=10,
    initial_radius=10.0,
    taper=0.9
)


mesh.export("generated_lsystem.obj")
