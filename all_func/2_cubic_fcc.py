import numpy as np
from concurrent.futures import ThreadPoolExecutor
from skimage import measure
from stl import mesh
import os

def Cubic_FCC( r, face_atom_radius, resolution = 50, folder='all_files'):
    def Lattice_atom_positions(a, b, c, alpha, beta, gamma,):
        alpha_rad = np.deg2rad(alpha)
        beta_rad = np.deg2rad(beta)
        gamma_rad = np.deg2rad(gamma)

        T = np.array([
            [1, 0, 0],
            [np.cos(gamma_rad), np.sin(gamma_rad), 0],
            [
                np.cos(beta_rad),
                (np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad),
                np.sqrt(
                    1
                    - np.cos(beta_rad) ** 2
                    - ((np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad)) ** 2
                ),
            ],
        ])

        positions = [
            [0, 0, 0],
            [a, 0, 0],
            [0, b, 0],
            [0, 0, c],
            [a, b, 0],
            [a, 0, c],
            [0, b, c],
            [a, b, c],
            [0.5 * a, 0.5 * b, 0],  # Face-centered atoms
            [0.5 * a, 0, 0.5 * c],
            [0, 0.5 * b, 0.5 * c],
            [0.5 * a, 0.5 * b, 1],
            [0.5 * a, 1 * b, 0.5 * c],
            [1 * a, 0.5 * b, 0.5 * c],
        ]

        return [np.dot(pos, T) for pos in positions], T

    def plane_from_points(p1, p2, p3):
        v1 = p3 - p2
        v2 = p1 - p2
        normal_vector = np.cross(v2, v1)
        D = -np.dot(normal_vector, p2)
        return normal_vector, D

    def bravais_function(x, y, z, position, r):
        return (x - position[0]) ** 2 + (y - position[1]) ** 2 + (z - position[2]) ** 2 - r ** 2

    def generate_solid_volume(resolution, atom_positions, T, atom_radius, face_atom_radius, a, b, c, plane_equation):

        v1, v2, v3 = atom_positions[1], atom_positions[2], atom_positions[3]

        # Create meshgrid for fractional coordinates
        u = np.linspace(0, 1, int(a * resolution))
        v = np.linspace(0, 1, int(b * resolution))
        w = np.linspace(0, 1, int(c * resolution))
        u_grid, v_grid, w_grid = np.meshgrid(u, v, w, indexing='ij')

        # Vectorized grid transformation to Cartesian coordinates
        parallelepiped_grid = (
            u_grid[..., None] * v1 + v_grid[..., None] * v2 + w_grid[..., None] * v3
        )  # Shape (Nx, Ny, Nz, 3)
        x = parallelepiped_grid[..., 0]
        y = parallelepiped_grid[..., 1]
        z = parallelepiped_grid[..., 2]

        positions = atom_positions
        radii = [atom_radius] * 8 + [face_atom_radius] * 6

        def compute_values(pos, radius):
            return bravais_function(x, y, z, pos, radius)

        # Parallel computation of distance fields
        with ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(lambda pr: compute_values(*pr), zip(positions, radii)))

        # Element-wise minimum across all atoms
        values = np.minimum.reduce(results)

        # Apply plane clipping, vectorized
        for normal, D in plane_equation.values():
            plane_vals = np.round(normal[0] * x + normal[1] * y + normal[2] * z + D, 3)
            values[plane_vals == 0] = 1  # Set values on plane to 1 (outside surface)

        # Extract surface mesh using marching cubes
        verts, faces, _, _ = measure.marching_cubes(values, level=0)
        verts = np.dot(verts, T)  # Transform vertices back to lattice space
        return verts, faces

    def create_stl_from_mesh(verts, faces, folder, filename):
        if not os.path.exists(folder):
            os.makedirs(folder)
        full_path = os.path.join(folder, filename)

        tpms_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                tpms_mesh.vectors[i][j] = verts[f[j], :]
        tpms_mesh.save(full_path)
        print(f"STL file saved as {full_path}")

    # Lattice parameters
    alpha, beta, gamma = 90.0, 90.0, 90.0
    atom_radius = r
    
    a, b, c=1,1,1
    atom_positions, T = Lattice_atom_positions(a, b, c, alpha, beta, gamma)
    positions = np.array(atom_positions)

    # Define faces for plane clipping
    faces = {
        "bottom": (positions[0], positions[1], positions[4]),
        "top": (positions[7], positions[5], positions[3]),
        "front": (positions[1], positions[5], positions[7]),
        "back": (positions[6], positions[3], positions[0]),
        "right": (positions[1], positions[0], positions[3]),
        "left": (positions[7], positions[6], positions[2]),
    }

    # Compute plane equations
    plane_equation = {face: plane_from_points(*verts) for face, verts in faces.items()}

    # Compute face_atom_radius using FCC geometry (0.355 as before)
    
    filename = f"2Cubic_FCC_{r:.2f}_{face_atom_radius}_{resolution}.stl" 
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume(resolution, atom_positions, T, atom_radius, face_atom_radius, a, b, c, plane_equation)
    create_stl_from_mesh(verts, faces, folder, filename) 
    cached_file = os.path.join(folder, filename) 
    return cached_file
    