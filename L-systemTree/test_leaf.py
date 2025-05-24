import trimesh
import numpy as np

def expand_lsystem(axiom, rules, iterations):
    result = axiom
    for _ in range(iterations):
        next_result = []
        for symbol in result:
            next_result.append(rules.get(symbol, symbol))
        result = ''.join(next_result)
    return result

def rotate_vector(vector, angle_deg, axis):
    rotation_matrix = trimesh.transformations.rotation_matrix(
        np.radians(angle_deg),
        axis
    )
    rotated = trimesh.transformations.transform_points([vector], rotation_matrix)[0]
    return rotated

def create_triangle_between_points(p1, p2, p3):
    vertices = np.array([p1, p2, p3])
    faces = np.array([[0, 1, 2]])  
    triangle = trimesh.Trimesh(vertices=vertices, faces=faces)
    return triangle

def sort_lines_by_length(lines):
    lengths = [np.linalg.norm(np.array(line[1]) - np.array(line[0])) for line in lines]
    sorted_indices = np.argsort(lengths)  
    sorted_lines = [lines[i] for i in sorted_indices]
    
    middle_index = len(sorted_lines) // 2
    sorted_lines = sorted_lines[:middle_index] + [sorted_lines[middle_index]] + sorted_lines[middle_index+1:]
    return sorted_lines

def create_leaf_geometry(lsystem_string, angle_deg=16, step_length=1.0):
    current_pos = np.array([0.0, 0.0, 0.0])
    current_dir = np.array([0.0, 1.0, 0.0]) 
    stack = []
    mesh_lines = []
    triangles = []
    startTriangles = []

    i = 0
    while i < len(lsystem_string):
        symbol = lsystem_string[i]
        if symbol == 'F':
            # Починаємо збирати сумарний рух вперед
            length = step_length
            j = i + 1
            # Поки далі йде F без поворотів, збираємо довжину
            while j < len(lsystem_string) and lsystem_string[j] == 'F':
                length += step_length
                j += 1
            
            # Створюємо циліндр на довжину length
            cylinder = trimesh.creation.cylinder(radius=0.0001, height=length, sections=3)
            
            direction = current_dir / np.linalg.norm(current_dir)
            rotation_axis = np.cross([0, 0, 1], direction)
            if np.linalg.norm(rotation_axis) < 1e-6:
                rotation_matrix = np.eye(4)
            else:
                rotation_angle = np.arccos(np.dot([0, 0, 1], direction))
                rotation_matrix = trimesh.transformations.rotation_matrix(rotation_angle, rotation_axis)
            
            cylinder.apply_transform(rotation_matrix)
            cylinder.apply_translation(current_pos)
            mesh_lines.append(cylinder)
            
            current_pos = current_pos + current_dir * length
            
            i = j
            continue
        
        elif symbol == '+':
            current_dir = rotate_vector(current_dir, +angle_deg, axis=[0, 0, 1])
        elif symbol == '-':
            current_dir = rotate_vector(current_dir, -angle_deg, axis=[0, 0, 1])
        elif symbol == '[':
            stack.append((current_pos.copy(), current_dir.copy()))
        elif symbol == ']':
            if i > 3:
                if lsystem_string[i - 1] == 'C' and lsystem_string[i - 2] == 'F':
                    startTriangles.append(current_pos.copy())
            if stack:
                current_pos, current_dir = stack.pop()
        i += 1

    i = 0
    while i < len(startTriangles) - 1:
        triangle = create_triangle_between_points(startTriangles[i], startTriangles[i+1], [0.0, 0.0, 0.0])
        triangles.append(triangle)
        i += 1

    if mesh_lines or triangles:
        return trimesh.util.concatenate(mesh_lines + triangles)
    else:
        return None


# rules = {
#     'A': '[+A]C',
#     'B': '[-B]C',
#     'C': 'FFFC'
# }


# axiom = '[A][B]'


# leaf_lsystem = expand_lsystem(axiom, rules, iterations=12)
# print(leaf_lsystem)
# print("Size:", len(leaf_lsystem))
# print("L-system for Leaf:")
# print(leaf_lsystem)


# leaf_mesh = create_leaf_geometry(leaf_lsystem, angle_deg=16, step_length=0.3)
# if leaf_mesh:
#     leaf_mesh.export('leaf.obj')
#     print("Leaf was generated and saved in leaf.obj")
# else:
#     print("Error. Can't generate leaf")
