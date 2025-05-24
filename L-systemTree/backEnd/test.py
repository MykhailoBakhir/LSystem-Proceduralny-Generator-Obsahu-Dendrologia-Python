import numpy as np
import trimesh
from trimesh.collision import CollisionManager
import os
from mpmath import mp
import subprocess
import platform
from scipy.spatial.transform import Rotation as R
import time
import branchWithLeafs


start_time = time.time()

PI_PRECISION = 100000
mp.dps = PI_PRECISION + 5  

PI_DIGITS = str(mp.pi)[2:2 + PI_PRECISION]
pi_index = 0  

def get_pi_digit(index=None):
    global pi_index
    if index is None:
        index = pi_index
        pi_index += 1
    return int(PI_DIGITS[index % len(PI_DIGITS)])



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

def create_centered_tilted_frustum(start, direction, length, bottom_radius, top_radius, tilt_angle=0.0, tilt_axis=[0,0,1]):
    start = np.array(start)
    direction = np.array(direction)

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
        np.zeros_like(angles)
    ])

    rot = R.from_rotvec(np.radians(tilt_angle) * np.array(tilt_axis))
    top_circle = rot.apply(top_circle)

    top_circle += np.array([0, 0, height])

    vertices = np.vstack((bottom_circle, top_circle))
    faces = []
    uvs = []

    # Generate UV coordinates for the side faces
    for i in range(sections):
        next_i = (i + 1) % sections
        faces.append([i, next_i, sections + i])
        faces.append([next_i, sections + next_i, sections + i])

        # UV mapping for side faces
        u_bottom = i / sections
        u_top = (i + 1) / sections
        uvs.append([u_bottom, 0])  # bottom vertex of first triangle
        uvs.append([u_top, 0])    # bottom vertex of second triangle
        uvs.append([u_bottom, 1])  # top vertex of first triangle
        uvs.append([u_top, 1])     # top vertex of second triangle

    # Add centers for top and bottom caps
    center_bottom = len(vertices)
    center_top = len(vertices) + 1
    vertices = np.vstack((vertices, [[0, 0, 0], [0, 0, height]]))

    # UV coordinates for cap centers
    uvs.append([0.5, 0.5])  # center bottom
    uvs.append([0.5, 0.5])  # center top

    # Create cap faces and their UV coordinates
    for i in range(sections):
        next_i = (i + 1) % sections
        
        # Bottom cap
        faces.append([center_bottom, next_i, i])
        u_bottom1 = 0.5 + 0.5 * np.cos(angles[i]) / bottom_radius
        v_bottom1 = 0.5 + 0.5 * np.sin(angles[i]) / bottom_radius
        uvs.append([u_bottom1, v_bottom1])
        
        # Top cap
        faces.append([center_top, sections + i, sections + next_i])
        u_top1 = 0.5 + 0.5 * np.cos(angles[i]) / top_radius
        v_top1 = 0.5 + 0.5 * np.sin(angles[i]) / top_radius
        uvs.append([u_top1, v_top1])

    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

     # Orient the mesh in the specified direction
    z_axis = np.array([0, 0, 1])
    direction_norm = direction / np.linalg.norm(direction)
    if not np.allclose(direction_norm, z_axis):
        rotation = trimesh.geometry.align_vectors(z_axis, direction)
        mesh.apply_transform(rotation)

    mesh.apply_translation(start)



    return mesh, end


def interpret_lsystem(lsys_string, start, direction, length, initial_radius, taper, angle_deg=15):
    meshes = []
    current_pos = np.array(start)
    current_dir = np.array(direction) / np.linalg.norm(direction)
    current_radius = initial_radius
    stack = []

    global pi_index
    i = 0
    while i < len(lsys_string):
        symbol = lsys_string[i]
    
        if symbol == 'F':
            count = 1
            while i + count < len(lsys_string) and lsys_string[i + count] == 'F':
                count += 1
        
            next_angle_digit = get_pi_digit(pi_index)
            next_axis_digit = get_pi_digit(pi_index + 1)
            pi_index += 2
        
            for _ in range(count):
                bottom_radius = current_radius
                top_radius = current_radius * taper
            
                angle_digit = next_angle_digit
                axis_digit = next_axis_digit
            
                future_angle_digit = get_pi_digit(pi_index)
                future_axis_digit = get_pi_digit(pi_index + 1)
                pi_index += 2
            
                angle_now = (angle_digit / 9.0) * 20 - 10
                angle_next = (future_angle_digit / 9.0) * 20 - 10
                smoothed_angle = (angle_now + angle_next) / 2
            
                if axis_digit < 3:
                    axis_now = np.array([1, 0, 0])
                elif axis_digit < 6:
                    axis_now = np.array([0, 1, 0])
                else:
                    axis_now = np.array([0, 0, 1])
            
                if future_axis_digit < 3:
                    axis_next = np.array([1, 0, 0])
                elif future_axis_digit < 6:
                    axis_next = np.array([0, 1, 0])
                else:
                    axis_next = np.array([0, 0, 1])
            
                smoothed_axis = axis_now.astype(float) + axis_next.astype(float)
                norm = np.linalg.norm(smoothed_axis)
                if norm > 0:
                    smoothed_axis /= norm
                else:
                    smoothed_axis = axis_now.astype(float)

            
                frustum, new_pos = create_centered_tilted_frustum(
                    start=current_pos,
                    direction=current_dir,
                    length=length,
                    bottom_radius=bottom_radius,
                    top_radius=top_radius,
                    tilt_angle=smoothed_angle,
                    tilt_axis=smoothed_axis
                )
            
                meshes.append(frustum)
                current_pos = new_pos
            
                rot = R.from_rotvec(np.radians(smoothed_angle) * smoothed_axis)
                current_dir = rot.apply(current_dir)
            
                current_radius = top_radius
            
                next_angle_digit = future_angle_digit
                next_axis_digit = future_axis_digit
                    

    
            i += count
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
                taper= 0.8,
                random_pi=PI_DIGITS[pi_index: pi_index + iteration * 10]
            )
            pi_index += iteration * 10

            if branch_mesh:
                meshes.append(branch_mesh)
            i += 1
        elif symbol == '+':
            current_dir = rotate_direction(current_dir, +angle_deg, axis=[1, 0, 0])
            i += 1
        elif symbol == '-':
            current_dir = rotate_direction(current_dir, -angle_deg, axis=[1, 0, 0])
            i += 1
        elif symbol == '&':
            current_dir = rotate_direction(current_dir, +angle_deg, axis=[0, 1, 0])
            i += 1
        elif symbol == '^':
            current_dir = rotate_direction(current_dir, -angle_deg, axis=[0, 1, 0])
            i += 1
        elif symbol == '\\':
            current_dir = rotate_direction(current_dir, +angle_deg, axis=[0, 0, 1])
            i += 1
        elif symbol == '/':
            current_dir = rotate_direction(current_dir, -angle_deg, axis=[0, 0, 1])
            i += 1
        elif symbol == '|':
            current_dir = rotate_direction(current_dir, 180, axis=[1, 0, 0])
            i += 1
        elif symbol == '[':
            stack.append((current_pos.copy(), current_dir.copy(), current_radius))
            i += 1
        elif symbol == ']':
            if stack:
                current_pos, current_dir, current_radius = stack.pop()
            i += 1
        else:
            i += 1

    return trimesh.util.concatenate(meshes)

def rotate_direction(direction, angle_deg, axis):
    rotation = trimesh.transformations.rotation_matrix(
        np.radians(angle_deg),
        axis,
        point=[0, 0, 0]
    )
    new_dir = trimesh.transformations.transform_points([direction], rotation)[0]
    return new_dir / np.linalg.norm(new_dir)



rules = {
        'S': 'FFFFFL', 
        'L': 'FFF[BCDEL]',
        'B': '[+++FFFf[&&&FFFf]FFFf]',
        'C': '[---FFFf[&&&FFFf]FFFf]',
        'D': '[&&&FFFf[+++FFFf]FFFf]',
        'E': '[^^^FFFf[---FFFf]FFFf]'
    }

axiom = 'S'


lsystem = expand_lsystem(axiom, rules, iterations=8)
print(lsystem)
print("Size:", len(lsystem))

mesh = interpret_lsystem(
    lsystem,
    start=[0, 0, 0],
    direction=[0, 0, 1],
    length=10,
    initial_radius=10.0,
    taper=0.9
)



print("Number of polygons (triangles):", len(mesh.faces))

obj_path = "generated_lsystem.obj"

mesh.export(obj_path, include_texture=False)



if platform.system() == 'Windows':
    os.startfile(obj_path)
elif platform.system() == 'Darwin':
    subprocess.run(['open', obj_path])
else:
    subprocess.run(['xdg-open', obj_path])


