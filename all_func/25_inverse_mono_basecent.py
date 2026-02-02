import numpy as np
from skimage import measure
from stl import mesh
import os
from concurrent.futures import ThreadPoolExecutor

def Inverse_Mono_BaseCent(a, b, c, alpha, beta, gamma, face_atom_radius=0.37, r=0.47,    resolution = 200, folder='all_files'):
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
            [a, b, 0], [a, 0, c], [0, b, c], [a, b, c],
            [0.5*a, 0.5*b, 1*c],      # Face-centered atom on xy-plane
            [0.5*a, 0.5*b, 0],        # Face-centered atom on yz-plane
        ]

        return [np.dot(pos, T) for pos in positions], T

    def plane_from_points(p1, p2, p3):
        v1 = p3 - p2
        v2 = p1 - p2
        normal_vector = np.cross(v2, v1)
        D = -np.dot(normal_vector, p2)
        return normal_vector, D

    def bravais_function(x, y, z, position, r):
        return (x - position[0])**2 + (y - position[1])**2 + (z - position[2])**2 - r**2

    def generate_solid_volume(resolution, atom_positions, T, atom_radius, face_atom_radius, a, b, c, plane_equation):
        v1 = atom_positions[1]
        v2 = atom_positions[2]
        v3 = atom_positions[3]

        nx, ny, nz = int(a * resolution), int(b * resolution), int(c * resolution)

        u, v, w = np.meshgrid(
            np.linspace(0, 1, nx),
            np.linspace(0, 1, ny),
            np.linspace(0, 1, nz),
            indexing='ij'
        )  # shape: (nx, ny, nz)

        # Vectorized computation of 3D coordinates in the unit cell
        parallelepiped_grid = (
            u[..., None] * v1 +
            v[..., None] * v2 +
            w[..., None] * v3
        )  # shape: (nx, ny, nz, 3)

        x = parallelepiped_grid[..., 0]
        y = parallelepiped_grid[..., 1]
        z = parallelepiped_grid[..., 2]

        values = np.minimum.reduce([
            bravais_function(x, y, z, atom_positions[i], atom_radius if i < 8 else face_atom_radius)
            for i in range(10)
        ])

        for normal_vector, D in plane_equation.values():
            values[np.round(normal_vector[0]*x + normal_vector[1]*y + normal_vector[2]*z + D, 3) == 0] = -1

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

    # Generate atomic positions and lattice transform
    atom_positions, T = Lattice_atom_positions(a, b, c, alpha, beta, gamma)
    positions = np.array(atom_positions)

    faces = {
        'bottom': (positions[0], positions[1], positions[4]),
        'top': (positions[7], positions[5], positions[3]),
        'front': (positions[1], positions[5], positions[7]),
        'back': (positions[6], positions[3], positions[0]),
        'right': (positions[1], positions[0], positions[3]),
        'left': (positions[7], positions[6], positions[2]),
    }

    plane_equation = {}
    for face_name, vertices in faces.items():
        normal_vector, D = plane_from_points(*vertices)
        plane_equation[face_name] = (normal_vector, D)

    filename = f"25Inverse_Mono_Basecent_{a:.1f}_{b:.1f}_{c:.1f}_{r:.2f}_{face_atom_radius:.2f}_{alpha}_{beta}_{gamma}_{resolution}.stl"
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume(resolution, atom_positions, T, r, face_atom_radius, a, b, c, plane_equation)
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file