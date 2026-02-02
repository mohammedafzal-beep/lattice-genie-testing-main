import numpy as np
from skimage import measure
from stl import mesh
import os
from concurrent.futures import ThreadPoolExecutor

def Inverse_Hexa(a, b, c, r=0.75, alpha=90, beta=90, gamma=120,    resolution = 200, folder='all_files'):
    def Lattice_atom_positions(a, b, c, alpha, beta, gamma):
        alpha_rad, beta_rad, gamma_rad = np.deg2rad([alpha, beta, gamma])
        T = np.array([
            [1, 0, 0],
            [np.cos(gamma_rad), np.sin(gamma_rad), 0],
            [
                np.cos(beta_rad),
                (np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad),
                np.sqrt(
                    1 - np.cos(beta_rad) ** 2 -
                    ((np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad)) ** 2
                )
            ]
        ])
        base = [[0, 0, 0], [a, 0, 0], [0, b, 0], [0, 0, c],
                [a, b, 0], [a, 0, c], [0, b, c], [a, b, c]]
        return [np.dot(p, T) for p in base], T

    def bravais_function(x, y, z, pos):
        return (x - pos[0]) ** 2 + (y - pos[1]) ** 2 + (z - pos[2]) ** 2 - r ** 2

    def plane_from_points(p1, p2, p3):
        v1, v2 = p3 - p2, p1 - p2
        normal = np.cross(v2, v1)
        D = -np.dot(normal, p2)
        return normal, D

    def plane_mask(x, y, z, normal, D):
        return np.round(normal[0] * x + normal[1] * y + normal[2] * z + D, 3) == 0

    def generate_solid_volume(res, positions, T, r, a, b, c, planes):
        v1, v2, v3 = positions[1], positions[2], positions[3]
        u, v, w = np.meshgrid(
            np.linspace(0, 1, int(a * res)),
            np.linspace(0, 1, int(b * res)),
            np.linspace(0, 1, int(c * res)),
            indexing='ij'
        )
        grid = (u[..., None] * v1 + v[..., None] * v2 + w[..., None] * v3).reshape(-1, 3)
        x, y, z = grid[:, 0], grid[:, 1], grid[:, 2]

        def single_atom_value(pos):
            return bravais_function(x, y, z, pos)

        with ThreadPoolExecutor() as executor:
            all_values = list(executor.map(single_atom_value, positions))

        min_values = np.minimum.reduce(all_values)

        for normal, D in planes.values():
            mask = plane_mask(x, y, z, normal, D)
            min_values[mask] = -1

        values = min_values.reshape(int(a * res), int(b * res), int(c * res))

        vmin, vmax = values.min(), values.max()
        if not (vmin <= 0 <= vmax):
            raise ValueError(f"No isosurface at level 0: value range = ({vmin:.3f}, {vmax:.3f})")

        verts, faces, _, _ = measure.marching_cubes(values, level=0)
        verts = verts @ T
        return verts, faces

    def create_stl(verts, faces, folder, filename):
        os.makedirs(folder, exist_ok=True)
        m = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                m.vectors[i][j] = verts[f[j]]
        m.vectors[:, [0, 1]] = m.vectors[:, [1, 0]]
        m.update_normals()
        path = os.path.join(folder, filename)
        m.save(path)
        print(f"Saved: {path}")
        return path


    atom_positions, T = Lattice_atom_positions(a, b, c, alpha, beta, gamma)
    positions = np.array(atom_positions)

    faces_def = {
        'bottom': (positions[0], positions[1], positions[4]),
        'top':    (positions[7], positions[5], positions[3]),
        'front':  (positions[1], positions[5], positions[7]),
        'back':   (positions[6], positions[3], positions[0]),
        'right':  (positions[1], positions[0], positions[3]),
        'left':   (positions[7], positions[6], positions[2]),
    }
    plane_equation = {name: plane_from_points(*verts) for name, verts in faces_def.items()}

    filename = f"28Inverse_Hexa_{a:.1f}_{b:.1f}_{c:.1f}_{r:.2f}_{alpha}_{beta}_{gamma}_{resolution}.stl"
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume(resolution, atom_positions, T, r, a, b, c, plane_equation)
    create_stl(verts, faces, folder, filename) 
    return cached_file