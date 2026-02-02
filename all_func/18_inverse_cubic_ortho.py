from concurrent.futures import ThreadPoolExecutor
import numpy as np
import numpy as np
from skimage import measure
from stl import mesh
import os
def Inverse_Cubic_Ortho(a, b, c,r=0.7,    resolution = 200, folder='all_files'):
    
    # Function to generate atomic positions for orthorhombic lattice
    def Lattice_atom_positions(a, b, c, alpha, beta, gamma):

        alpha_rad = np.deg2rad(alpha)
        beta_rad = np.deg2rad(beta)
        gamma_rad = np.deg2rad(gamma)

        T = np.array([
            [1, 0, 0],
            [np.cos(gamma_rad), np.sin(gamma_rad), 0],
            [np.cos(beta_rad), (np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad), 
            np.sqrt(1 - np.cos(beta_rad)**2 - ((np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad))**2)]
        ])
        positions = [
            [0, 0, 0], [a, 0, 0], [0, b, 0], [0, 0, c],
            [a, b, 0], [a, 0, c], [0, b, c], [a, b, c]
        ]
        return [np.dot(pos, T) for pos in positions], T

    def plane_from_points(p1, p2, p3):
        v1 = p3 - p2
        v2 = p1 - p2
        normal_vector =  np.cross(v2, v1)
        D = -np.dot(normal_vector, p2)
        return normal_vector, D

    def bravais_function(x, y, z, position, r):
        return (x - position[0])**2 + (y - position[1])**2 + (z - position[2])**2 - r**2
        
    def plane(x, y, z, normal, D):
        a =  round(normal[0],5)*x + round(normal[1],5)*y + round(normal[2],5)*z +round(D,5)
        return np.round(a,3)

    def generate_solid_volume(resolution, position, T, r, a, b, c, plane_equation):
        v1 = position[1]
        v2 = position[2]
        v3 = position[3]

        u, v, w = np.meshgrid(
            np.linspace(0, 1, int(a * resolution)),
            np.linspace(0, 1, int(b * resolution)),
            np.linspace(0, 1, int(c * resolution)),
            indexing='ij'
        )

        shape = (int(a * resolution), int(b * resolution), int(c * resolution))
        parallelepiped_grid = np.empty((*shape, 3))

        parallelepiped_grid = (
    u[..., None] * v1 +
    v[..., None] * v2 +
    w[..., None] * v3)


        x = parallelepiped_grid[:, :, :, 0]
        y = parallelepiped_grid[:, :, :, 1]
        z = parallelepiped_grid[:, :, :, 2]

        def bravais_fn_wrapper(pos):
            return (x - pos[0]) ** 2 + (y - pos[1]) ** 2 + (z - pos[2]) ** 2 - r**2

        with ThreadPoolExecutor() as executor:
            all_values = list(executor.map(bravais_fn_wrapper, position))

        values = all_values[0]
        for val in all_values[1:]:
            values = np.minimum(values, val)

        for normal_vector, D in plane_equation.values():
            mask = np.round(normal_vector[0]*x + normal_vector[1]*y + normal_vector[2]*z + D, 3) == 0
            values[mask] = -1

        verts, faces, _, _ = measure.marching_cubes(values, level=0)
        verts = np.dot(verts, T)
        return verts, faces

    def create_stl_from_mesh(verts, faces, folder, filename):
        if not os.path.exists(folder):
            os.makedirs(folder)
        full_path = os.path.join(folder, filename)
        
        tpms_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                tpms_mesh.vectors[i][j] = verts[f[j], :]
        tpms_mesh.vectors[:, [0, 1]] = tpms_mesh.vectors[:, [1, 0]]
        tpms_mesh.update_normals()
        tpms_mesh.save(full_path)
        print(f"STL file saved as {full_path}")

    # Set lattice parameters and generate atomic positions

    alpha, beta, gamma = 90.0, 90.0, 90.0
    # atom_radius = 0.4
    atom_radius_range = np.arange(0.65, 0.75, 0.01)  # Considered lower tolerance than 0.03 to generate atleast 4+ structures

    atom_positions, T = Lattice_atom_positions(a, b, c, alpha, beta, gamma)

    # Convert to numpy array for easier manipulation and define faces
    positions = np.array(atom_positions)
    faces = {
        'bottom' : (positions[0], positions[1], positions[4]),  # Bottom face
        'top' : (positions[7], positions[5], positions[3]),  # Top face
        'front' : (positions[1], positions[5], positions[7]),
        'back' : (positions[6], positions[3], positions[0]),
        'right' : (positions[1], positions[0], positions[3]),
        'left' : (positions[7], positions[6], positions[2]),
    }

    # Calculate and store plane equations
    plane_equation = {}
    for face_name, vertices in faces.items():
        normal_vector, D = plane_from_points(*vertices)
        plane_equation[face_name] = (normal_vector, D)

    filename = f"18Inverse_CubicOrtho_{a:.1f}_{b:.1f}_{c:.1f}_{r:.2f}_{resolution}.stl"
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume(resolution, atom_positions, T, r, a, b, c, plane_equation)
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file